/// \file
/// Runs the deterministic single-CPU Target 0 host-qualification workload.

#include <algorithm>
#include <cerrno>
#include <charconv>
#include <chrono>
#include <cstdint>
#include <cstring>
#include <exception>
#include <fcntl.h>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <optional>
#include <sched.h>
#include <sstream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <sys/types.h>
#include <system_error>
#include <time.h>
#include <unistd.h>
#include <utility>
#include <vector>

namespace {

constexpr std::uint64_t QualificationWarmupRounds = 5;
constexpr std::uint64_t QualificationRetainedRounds = 30;
constexpr std::uint64_t QualificationIterations = UINT64_C(16777216);
constexpr std::size_t TimerOverheadSampleCount = 10000;
constexpr std::uint64_t XorShiftMultiplier = UINT64_C(2685821657736338717);

// Glibc exposes this Linux clock ID through <time.h>, but include-cleaner
// cannot attribute the macro to that public header.
constexpr auto MonotonicRawClock =
    CLOCK_MONOTONIC_RAW; // NOLINT(misc-include-cleaner)

struct Options {
  unsigned requestedCpu;
  std::uint64_t warmupRounds;
  std::uint64_t retainedRounds;
  std::uint64_t iterations;
  std::uint64_t seed;
  std::filesystem::path outputPath;
};

struct ProcessStatus {
  std::uint64_t threads;
  std::uint64_t voluntaryContextSwitches;
  std::uint64_t involuntaryContextSwitches;
};

struct Sample {
  std::uint64_t round;
  std::uint64_t elapsedNanoseconds;
  int observedCpuStart;
  int observedCpuEnd;
  std::uint64_t checksum;
  std::uint64_t voluntaryContextSwitches;
  std::uint64_t involuntaryContextSwitches;
};

template <typename Value>
Value parseUnsigned(std::string_view text, std::string_view optionName) {
  Value value = 0;
  const auto [End, Error] =
      std::from_chars(text.data(), text.data() + text.size(), value);
  if (Error != std::errc() || End != text.data() + text.size()) {
    throw std::invalid_argument("invalid unsigned value for " +
                                std::string(optionName));
  }
  return value;
}

Options parseOptions(int argumentCount, char **argumentValues) {
  std::optional<std::uint64_t> requestedCpu;
  std::optional<std::uint64_t> warmupRounds;
  std::optional<std::uint64_t> retainedRounds;
  std::optional<std::uint64_t> iterations;
  std::optional<std::uint64_t> seed;
  std::optional<std::filesystem::path> outputPath;

  for (int argumentIndex = 1; argumentIndex < argumentCount;
       argumentIndex += 2) {
    if (argumentIndex + 1 >= argumentCount) {
      throw std::invalid_argument("every option requires one value");
    }

    const std::string_view Option = argumentValues[argumentIndex];
    const std::string_view Value = argumentValues[argumentIndex + 1];
    if (Option == "--cpu" && !requestedCpu.has_value()) {
      requestedCpu = parseUnsigned<std::uint64_t>(Value, Option);
    } else if (Option == "--warmup-rounds" && !warmupRounds.has_value()) {
      warmupRounds = parseUnsigned<std::uint64_t>(Value, Option);
    } else if (Option == "--rounds" && !retainedRounds.has_value()) {
      retainedRounds = parseUnsigned<std::uint64_t>(Value, Option);
    } else if (Option == "--iterations" && !iterations.has_value()) {
      iterations = parseUnsigned<std::uint64_t>(Value, Option);
    } else if (Option == "--seed" && !seed.has_value()) {
      seed = parseUnsigned<std::uint64_t>(Value, Option);
    } else if (Option == "--output" && !outputPath.has_value()) {
      outputPath = std::filesystem::path(Value);
    } else {
      throw std::invalid_argument("unknown or duplicate option: " +
                                  std::string(Option));
    }
  }

  if (!requestedCpu.has_value() || !warmupRounds.has_value() ||
      !retainedRounds.has_value() || !iterations.has_value() ||
      !seed.has_value() || !outputPath.has_value()) {
    throw std::invalid_argument("all qualification options are required");
  }
  if (*requestedCpu >= CPU_SETSIZE ||
      *requestedCpu > std::numeric_limits<unsigned>::max()) {
    throw std::invalid_argument("requested CPU exceeds the affinity set");
  }
  if (*warmupRounds != QualificationWarmupRounds ||
      *retainedRounds != QualificationRetainedRounds ||
      *iterations != QualificationIterations) {
    throw std::invalid_argument(
        "qualification counts must match the fixed v1 contract");
  }
  if (outputPath->empty()) {
    throw std::invalid_argument("output path must not be empty");
  }

  return Options{static_cast<unsigned>(*requestedCpu),
                 *warmupRounds,
                 *retainedRounds,
                 *iterations,
                 *seed,
                 std::move(*outputPath)};
}

std::uint64_t parseStatusValue(std::string_view line,
                               std::string_view fieldName) {
  const std::string_view Value = line.substr(fieldName.size());
  const std::size_t FirstDigit = Value.find_first_of("0123456789");
  if (FirstDigit == std::string_view::npos) {
    throw std::runtime_error("missing numeric process-status value");
  }
  return parseUnsigned<std::uint64_t>(Value.substr(FirstDigit), fieldName);
}

ProcessStatus readProcessStatus() {
  std::ifstream statusFile("/proc/self/status");
  if (!statusFile) {
    throw std::runtime_error("unable to open /proc/self/status");
  }

  std::optional<std::uint64_t> threads;
  std::optional<std::uint64_t> voluntaryContextSwitches;
  std::optional<std::uint64_t> involuntaryContextSwitches;
  std::string line;
  while (std::getline(statusFile, line)) {
    const std::string_view View = line;
    if (View.starts_with("Threads:")) {
      threads = parseStatusValue(View, "Threads:");
    } else if (View.starts_with("voluntary_ctxt_switches:")) {
      voluntaryContextSwitches =
          parseStatusValue(View, "voluntary_ctxt_switches:");
    } else if (View.starts_with("nonvoluntary_ctxt_switches:")) {
      involuntaryContextSwitches =
          parseStatusValue(View, "nonvoluntary_ctxt_switches:");
    }
  }

  if (!threads.has_value() || !voluntaryContextSwitches.has_value() ||
      !involuntaryContextSwitches.has_value()) {
    throw std::runtime_error("incomplete /proc/self/status record");
  }
  return ProcessStatus{
      *threads, *voluntaryContextSwitches, *involuntaryContextSwitches};
}

std::uint64_t readMonotonicRawNanoseconds() {
  timespec timestamp{};
  if (::clock_gettime(MonotonicRawClock, &timestamp) != 0) {
    throw std::system_error(
        errno, std::generic_category(), "clock_gettime failed");
  }
  constexpr std::uint64_t NanosecondsPerSecond = UINT64_C(1000000000);
  return static_cast<std::uint64_t>(timestamp.tv_sec) * NanosecondsPerSecond +
         static_cast<std::uint64_t>(timestamp.tv_nsec);
}

std::vector<unsigned> pinToCpu(unsigned requestedCpu) {
  cpu_set_t allowedCpus;
  CPU_ZERO(&allowedCpus);
  if (::sched_getaffinity(0, sizeof(allowedCpus), &allowedCpus) != 0) {
    throw std::system_error(
        errno, std::generic_category(), "sched_getaffinity failed");
  }
  if (!CPU_ISSET(static_cast<int>(requestedCpu), &allowedCpus)) {
    throw std::invalid_argument(
        "requested CPU is outside the allowed online affinity set");
  }

  cpu_set_t requestedSet;
  CPU_ZERO(&requestedSet);
  CPU_SET(static_cast<int>(requestedCpu), &requestedSet);
  if (::sched_setaffinity(0, sizeof(requestedSet), &requestedSet) != 0) {
    throw std::system_error(
        errno, std::generic_category(), "sched_setaffinity failed");
  }

  cpu_set_t observedSet;
  CPU_ZERO(&observedSet);
  if (::sched_getaffinity(0, sizeof(observedSet), &observedSet) != 0) {
    throw std::system_error(
        errno, std::generic_category(), "post-pin sched_getaffinity failed");
  }
  std::vector<unsigned> observedCpus;
  for (unsigned cpu = 0; cpu < CPU_SETSIZE; ++cpu) {
    if (CPU_ISSET(static_cast<int>(cpu), &observedSet)) {
      observedCpus.push_back(cpu);
    }
  }
  if (observedCpus.size() != 1 || observedCpus.front() != requestedCpu) {
    throw std::runtime_error("kernel did not retain the requested affinity");
  }
  return observedCpus;
}

std::uint64_t
runWorkload(std::uint64_t seed, std::uint64_t round, std::uint64_t iterations) {
  std::uint64_t state = seed ^ round;
  std::uint64_t checksum = 0;
  for (std::uint64_t iteration = 0; iteration < iterations; ++iteration) {
    state ^= state >> 12U;
    state ^= state << 25U;
    state ^= state >> 27U;
    checksum += state * XorShiftMultiplier;
  }
  return checksum;
}

std::string formatChecksum(std::uint64_t checksum) {
  std::ostringstream formatted;
  formatted << std::hex << std::setfill('0') << std::setw(16) << checksum;
  return formatted.str();
}

void appendFailureReason(std::vector<std::string> &failureReasons,
                         std::string reason) {
  if (std::find(failureReasons.begin(), failureReasons.end(), reason) ==
      failureReasons.end()) {
    failureReasons.push_back(std::move(reason));
  }
}

std::string serializeRecord(const Options &options,
                            const std::vector<unsigned> &affinityCpus,
                            const std::vector<std::uint64_t> &timerOverhead,
                            const ProcessStatus &initialStatus,
                            const ProcessStatus &finalStatus,
                            std::uint64_t maximumObservedThreads,
                            std::uint64_t warmupChecksum,
                            const std::vector<Sample> &samples,
                            std::uint64_t checksum,
                            const std::vector<std::string> &failureReasons) {
  std::ostringstream json;
  json << "{\n"
       << "  \"manifest_version\": "
          "\"xoas.target0-qualification-process.v1\",\n"
       << "  \"performance_claim\": false,\n"
       << "  \"requested_cpu\": " << options.requestedCpu << ",\n"
       << "  \"affinity_cpus\": [" << affinityCpus.front() << "],\n"
       << "  \"warmup_rounds\": " << options.warmupRounds << ",\n"
       << "  \"retained_rounds\": " << options.retainedRounds << ",\n"
       << "  \"iterations\": " << options.iterations << ",\n"
       << "  \"seed\": " << options.seed << ",\n"
       << "  \"timer_clock\": \"CLOCK_MONOTONIC_RAW\",\n"
       << "  \"timer_overhead_ns\": [";
  for (std::size_t index = 0; index < timerOverhead.size(); ++index) {
    if (index != 0) {
      json << ',';
    }
    json << timerOverhead[index];
  }
  json << "],\n"
       << "  \"process_id\": " << ::getpid() << ",\n"
       << "  \"process_context_switches\": {\"voluntary_delta\": "
       << finalStatus.voluntaryContextSwitches -
              initialStatus.voluntaryContextSwitches
       << ", \"involuntary_delta\": "
       << finalStatus.involuntaryContextSwitches -
              initialStatus.involuntaryContextSwitches
       << "},\n"
       << "  \"max_observed_threads\": " << maximumObservedThreads << ",\n"
       << "  \"warmup_checksum\": \"" << formatChecksum(warmupChecksum)
       << "\",\n"
       << "  \"samples\": [\n";
  for (std::size_t index = 0; index < samples.size(); ++index) {
    const Sample &sampleRecord = samples[index];
    json << "    {\"round\": " << sampleRecord.round
         << ", \"elapsed_ns\": " << sampleRecord.elapsedNanoseconds
         << ", \"observed_cpu_start\": " << sampleRecord.observedCpuStart
         << ", \"observed_cpu_end\": " << sampleRecord.observedCpuEnd
         << ", \"checksum\": \"" << formatChecksum(sampleRecord.checksum)
         << "\", \"voluntary_context_switches\": "
         << sampleRecord.voluntaryContextSwitches
         << ", \"involuntary_context_switches\": "
         << sampleRecord.involuntaryContextSwitches << '}';
    if (index + 1 != samples.size()) {
      json << ',';
    }
    json << '\n';
  }
  json << "  ],\n"
       << "  \"checksum\": \"" << formatChecksum(checksum) << "\",\n"
       << "  \"status\": \"" << (failureReasons.empty() ? "passed" : "failed")
       << "\",\n"
       << "  \"failure_reasons\": [";
  for (std::size_t index = 0; index < failureReasons.size(); ++index) {
    if (index != 0) {
      json << ", ";
    }
    json << '"' << failureReasons[index] << '"';
  }
  json << "]\n}\n";
  return json.str();
}

void writeRecordWithoutReplacement(const std::filesystem::path &outputPath,
                                   std::string_view record) {
  std::filesystem::path temporaryPath = outputPath;
  temporaryPath += ".tmp." + std::to_string(::getpid());

  int descriptor =
      ::open(temporaryPath.c_str(), O_WRONLY | O_CREAT | O_EXCL, 0644);
  if (descriptor < 0) {
    throw std::system_error(
        errno, std::generic_category(), "unable to create temporary output");
  }

  bool published = false;
  try {
    std::size_t written = 0;
    while (written < record.size()) {
      const ssize_t WriteResult =
          ::write(descriptor, record.data() + written, record.size() - written);
      if (WriteResult < 0) {
        if (errno == EINTR) {
          continue;
        }
        throw std::system_error(
            errno, std::generic_category(), "unable to write output");
      }
      written += static_cast<std::size_t>(WriteResult);
    }
    if (::fsync(descriptor) != 0) {
      throw std::system_error(
          errno, std::generic_category(), "unable to synchronize output");
    }
    if (::close(descriptor) != 0) {
      descriptor = -1;
      throw std::system_error(
          errno, std::generic_category(), "unable to close output");
    }
    descriptor = -1;
    if (::link(temporaryPath.c_str(), outputPath.c_str()) != 0) {
      throw std::system_error(errno,
                              std::generic_category(),
                              "unable to publish output without replacement");
    }
    published = true;
    if (::unlink(temporaryPath.c_str()) != 0) {
      throw std::system_error(
          errno, std::generic_category(), "unable to remove temporary output");
    }
  } catch (...) {
    if (descriptor >= 0) {
      static_cast<void>(::close(descriptor));
    }
    static_cast<void>(::unlink(temporaryPath.c_str()));
    if (published) {
      static_cast<void>(::unlink(outputPath.c_str()));
    }
    throw;
  }
}

int runProbe(const Options &options) {
  if (!std::chrono::steady_clock::is_steady) {
    throw std::runtime_error("std::chrono::steady_clock is not steady");
  }

  const std::vector<unsigned> AffinityCpus = pinToCpu(options.requestedCpu);
  const ProcessStatus InitialStatus = readProcessStatus();
  std::uint64_t maximumObservedThreads = InitialStatus.threads;

  std::vector<std::uint64_t> timerOverhead;
  timerOverhead.reserve(TimerOverheadSampleCount);
  for (std::size_t index = 0; index < TimerOverheadSampleCount; ++index) {
    const std::uint64_t Start = readMonotonicRawNanoseconds();
    const std::uint64_t End = readMonotonicRawNanoseconds();
    timerOverhead.push_back(End - Start);
  }

  std::uint64_t warmupChecksum = 0;
  for (std::uint64_t round = 0; round < options.warmupRounds; ++round) {
    warmupChecksum += runWorkload(options.seed, round, options.iterations);
  }

  std::vector<Sample> samples;
  samples.reserve(static_cast<std::size_t>(options.retainedRounds));
  std::vector<std::string> failureReasons;
  std::uint64_t aggregateChecksum = 0;
  for (std::uint64_t round = 0; round < options.retainedRounds; ++round) {
    const ProcessStatus BeforeStatus = readProcessStatus();
    maximumObservedThreads =
        std::max(maximumObservedThreads, BeforeStatus.threads);
    const int ObservedCpuStart = ::sched_getcpu();
    if (ObservedCpuStart < 0) {
      throw std::system_error(
          errno, std::generic_category(), "sched_getcpu before sample failed");
    }
    const std::uint64_t Start = readMonotonicRawNanoseconds();
    const std::uint64_t SampleChecksum =
        runWorkload(options.seed, round, options.iterations);
    const std::uint64_t End = readMonotonicRawNanoseconds();
    const int ObservedCpuEnd = ::sched_getcpu();
    if (ObservedCpuEnd < 0) {
      throw std::system_error(
          errno, std::generic_category(), "sched_getcpu after sample failed");
    }
    const ProcessStatus AfterStatus = readProcessStatus();
    maximumObservedThreads =
        std::max(maximumObservedThreads, AfterStatus.threads);

    if (ObservedCpuStart != static_cast<int>(options.requestedCpu) ||
        ObservedCpuEnd != static_cast<int>(options.requestedCpu)) {
      appendFailureReason(failureReasons, "cpu_migration");
    }
    if (BeforeStatus.threads != 1 || AfterStatus.threads != 1) {
      appendFailureReason(failureReasons, "thread_count_changed");
    }
    aggregateChecksum += SampleChecksum;
    samples.push_back(Sample{
        round,
        End - Start,
        ObservedCpuStart,
        ObservedCpuEnd,
        SampleChecksum,
        AfterStatus.voluntaryContextSwitches -
            BeforeStatus.voluntaryContextSwitches,
        AfterStatus.involuntaryContextSwitches -
            BeforeStatus.involuntaryContextSwitches,
    });
  }

  const ProcessStatus FinalStatus = readProcessStatus();
  maximumObservedThreads =
      std::max(maximumObservedThreads, FinalStatus.threads);
  if (maximumObservedThreads != 1) {
    appendFailureReason(failureReasons, "thread_count_changed");
  }

  const std::string Record = serializeRecord(options,
                                             AffinityCpus,
                                             timerOverhead,
                                             InitialStatus,
                                             FinalStatus,
                                             maximumObservedThreads,
                                             warmupChecksum,
                                             samples,
                                             aggregateChecksum,
                                             failureReasons);
  writeRecordWithoutReplacement(options.outputPath, Record);
  return failureReasons.empty() ? 0 : 3;
}

} // namespace

/// Runs one fixed Target 0 qualification process and writes its closed record.
/// \param argumentCount Number of command-line arguments.
/// \param argumentValues Required qualification option and value pairs.
/// \returns Zero for a valid process, two for setup or I/O failure, and three
/// for a completed process whose observations violate qualification rules.
int main(int argumentCount, char **argumentValues) {
  try {
    return runProbe(parseOptions(argumentCount, argumentValues));
  } catch (const std::exception &error) {
    std::cerr << "xoas-target0-qualification-probe: " << error.what() << '\n';
    return 2;
  }
}
