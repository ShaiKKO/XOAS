#!/usr/bin/env bash
## @file
## Applies and exactly restores one bounded Target 0 measurement session.

set -u -o pipefail

readonly UsageExit=2
readonly ApplyFailureExit=3
readonly RestorationFailureExit=70

cpu=""
sibling=""
targetUser=""
restorationRecord=""
commandArguments=()
childPid=""
commandExitStatus="null"
sessionOutcome="restored"
governorChanged=0
preferenceChanged=0
siblingChanged=0
recordTemporaryPath=""

failUsage() {
  printf 'measurement_session.sh: %s\n' "$1" >&2
  exit "$UsageExit"
}

readValue() {
  local path=$1
  [[ -r $path ]] || return 1
  local value
  value=$(<"$path") || return 1
  printf '%s' "$value"
}

writeValue() {
  local path=$1
  local value=$2
  printf '%s\n' "$value" >"$path"
}

containsWord() {
  local values=$1
  local required=$2
  local value
  for value in $values; do
    if [[ $value == "$required" ]]; then
      return 0
    fi
  done
  return 1
}

normalizeSiblingPair() {
  local pair=$1
  local first=""
  local second=""
  local extra=""
  IFS=',' read -r first second extra <<<"$pair"
  [[ $first =~ ^[0-9]+$ && $second =~ ^[0-9]+$ && -z $extra ]] || return 1
  [[ $first != "$second" ]] || return 1
  if ((first < second)); then
    printf '%s,%s' "$first" "$second"
  else
    printf '%s,%s' "$second" "$first"
  fi
}

readSelectedCpuInterrupts() {
  local interruptsPath=$1
  local selectedCpu=$2
  awk -v selected="CPU${selectedCpu}" '
    NR == 1 {
      for (columnIndex = 1; columnIndex <= NF; ++columnIndex) {
        if ($columnIndex == selected) {
          column = columnIndex + 1
        }
      }
      next
    }
    column > 0 && index($1, ":") > 0 && $column ~ /^[0-9]+$/ {
      total += $column
    }
    END {
      if (column == 0) {
        exit 1
      }
      print total + 0
    }
  ' "$interruptsPath"
}

validateStateToken() {
  [[ $1 =~ ^[A-Za-z0-9_-]+$ ]]
}

# ShellCheck cannot trace this helper through the EXIT trap call graph.
# shellcheck disable=SC2317
writeRestorationRecord() {
  local postSiblingOnline=$1
  local postGovernor=$2
  local postPreference=$3
  local postBoost=$4
  local postInterrupts=$5
  local restored=$6
  local boostUnchanged=$7
  local failureReasons='[]'
  if [[ $sessionOutcome == "apply_failed" ]]; then
    failureReasons='["apply_failed"]'
  elif [[ $sessionOutcome == "restoration_failed" ]]; then
    failureReasons='["restoration_failed"]'
  fi

  if ! {
    printf '{\n'
    printf '  "manifest_version": "xoas.target0-measurement-session-restoration.v1",\n'
    printf '  "performance_claim": false,\n'
    printf '  "cpu": %s,\n' "$cpu"
    printf '  "sibling": %s,\n' "$sibling"
    printf '  "status": "%s",\n' "$sessionOutcome"
    printf '  "command_exit_status": %s,\n' "$commandExitStatus"
    printf '  "restored": %s,\n' "$restored"
    printf '  "boost_unchanged": %s,\n' "$boostUnchanged"
    printf '  "pre_state": {\n'
    printf '    "sibling_online": %s,\n' "$preSiblingOnline"
    printf '    "governor": "%s",\n' "$preGovernor"
    printf '    "energy_performance_preference": "%s",\n' "$prePreference"
    printf '    "boost": %s,\n' "$preBoost"
    printf '    "selected_cpu_interrupts": %s\n' "$preInterrupts"
    printf '  },\n'
    printf '  "post_state": {\n'
    printf '    "sibling_online": %s,\n' "$postSiblingOnline"
    printf '    "governor": "%s",\n' "$postGovernor"
    printf '    "energy_performance_preference": "%s",\n' "$postPreference"
    printf '    "boost": %s,\n' "$postBoost"
    printf '    "selected_cpu_interrupts": %s\n' "$postInterrupts"
    printf '  },\n'
    printf '  "failure_reasons": %s\n' "$failureReasons"
    printf '}\n'
  } >"$recordTemporaryPath"; then
    return 1
  fi
  if ! ln "$recordTemporaryPath" "$restorationRecord"; then
    return 1
  fi
  if ! rm -f "$recordTemporaryPath"; then
    rm -f "$restorationRecord"
    return 1
  fi
  return 0
}

# ShellCheck cannot resolve function names installed as quoted trap handlers.
# shellcheck disable=SC2317
finishSession() {
  local originalStatus=$?
  trap - EXIT TERM INT HUP
  local restorationSucceeded=1

  if ((siblingChanged)); then
    if ! writeValue "$siblingOnlinePath" "$preSiblingOnline"; then
      restorationSucceeded=0
    fi
  fi
  if ((preferenceChanged)); then
    if ! writeValue "$preferencePath" "$prePreference"; then
      restorationSucceeded=0
    fi
  fi
  if ((governorChanged)); then
    if ! writeValue "$governorPath" "$preGovernor"; then
      restorationSucceeded=0
    fi
  fi

  local postSiblingOnline="unavailable"
  local postGovernor="unavailable"
  local postPreference="unavailable"
  local postBoost="unavailable"
  local postInterrupts="unavailable"
  postSiblingOnline=$(readValue "$siblingOnlinePath") || restorationSucceeded=0
  postGovernor=$(readValue "$governorPath") || restorationSucceeded=0
  postPreference=$(readValue "$preferencePath") || restorationSucceeded=0
  postBoost=$(readValue "$boostPath") || restorationSucceeded=0
  postInterrupts=$(readSelectedCpuInterrupts "$interruptsPath" "$cpu") ||
    restorationSucceeded=0

  if [[ $postSiblingOnline != "$preSiblingOnline" ||
    $postGovernor != "$preGovernor" ||
    $postPreference != "$prePreference" ]]; then
    restorationSucceeded=0
  fi
  local boostUnchanged=false
  if [[ $postBoost == "$preBoost" ]]; then
    boostUnchanged=true
  else
    restorationSucceeded=0
  fi

  local restored=false
  if ((restorationSucceeded)); then
    restored=true
  else
    sessionOutcome="restoration_failed"
  fi

  if ! writeRestorationRecord "$postSiblingOnline" "$postGovernor" \
    "$postPreference" "$postBoost" "$postInterrupts" "$restored" \
    "$boostUnchanged"; then
    restorationSucceeded=0
    sessionOutcome="restoration_failed"
    rm -f "$recordTemporaryPath"
  fi

  if ((!restorationSucceeded)); then
    exit "$RestorationFailureExit"
  fi
  exit "$originalStatus"
}

# ShellCheck cannot resolve function names installed as quoted trap handlers.
# shellcheck disable=SC2317
handleSignal() {
  local signalStatus=$1
  trap - TERM INT HUP
  if [[ -n $childPid ]]; then
    kill -TERM "$childPid" 2>/dev/null || true
    wait "$childPid" 2>/dev/null || true
  fi
  commandExitStatus=$signalStatus
  exit "$signalStatus"
}

while (($# > 0)); do
  case $1 in
  --cpu)
    (($# >= 2)) || failUsage '--cpu requires a value'
    cpu=$2
    shift 2
    ;;
  --sibling)
    (($# >= 2)) || failUsage '--sibling requires a value'
    sibling=$2
    shift 2
    ;;
  --target-user)
    (($# >= 2)) || failUsage '--target-user requires a value'
    targetUser=$2
    shift 2
    ;;
  --restoration-record)
    (($# >= 2)) || failUsage '--restoration-record requires a value'
    restorationRecord=$2
    shift 2
    ;;
  --)
    shift
    commandArguments=("$@")
    break
    ;;
  *)
    failUsage "unknown option: $1"
    ;;
  esac
done

[[ $cpu =~ ^[0-9]+$ ]] || failUsage 'CPU must be an unsigned integer'
[[ $sibling =~ ^[0-9]+$ ]] || failUsage 'sibling must be an unsigned integer'
[[ $cpu != "$sibling" ]] || failUsage 'CPU and sibling must differ'
[[ -n $targetUser && $targetUser != "root" ]] ||
  failUsage 'target user must be non-root'
[[ $targetUser =~ ^[a-z_][a-z0-9_-]*$ ]] ||
  failUsage 'target user has an invalid name'
[[ -n $restorationRecord ]] || failUsage 'restoration record path is required'
((${#commandArguments[@]} > 0)) || failUsage 'command must not be empty'
[[ ! -e $restorationRecord ]] || failUsage 'restoration record already exists'

testing=${XOAS_TARGET0_TESTING:-0}
if [[ $testing == "1" ]]; then
  ((EUID != 0)) || failUsage 'test mode must not run as root'
  sysfsRoot=${XOAS_TARGET0_SYSFS_ROOT:-}
  procfsRoot=${XOAS_TARGET0_PROCFS_ROOT:-}
  [[ -n $sysfsRoot && -n $procfsRoot ]] ||
    failUsage 'test mode requires explicit fixture roots'
else
  ((EUID == 0)) || failUsage 'measurement session must run as root'
  sysfsRoot=/sys
  procfsRoot=/proc
  targetUid=$(id -u "$targetUser" 2>/dev/null) ||
    failUsage 'target user does not exist'
  ((targetUid != 0)) || failUsage 'target user resolves to root'
fi

cpuRoot="$sysfsRoot/devices/system/cpu/cpu$cpu"
siblingRoot="$sysfsRoot/devices/system/cpu/cpu$sibling"
cpuSiblingPath="$cpuRoot/topology/thread_siblings_list"
siblingSiblingPath="$siblingRoot/topology/thread_siblings_list"
siblingOnlinePath="$siblingRoot/online"
governorPath="$cpuRoot/cpufreq/scaling_governor"
availableGovernorsPath="$cpuRoot/cpufreq/scaling_available_governors"
preferencePath="$cpuRoot/cpufreq/energy_performance_preference"
availablePreferencesPath="$cpuRoot/cpufreq/energy_performance_available_preferences"
boostPath="$sysfsRoot/devices/system/cpu/cpufreq/boost"
interruptsPath="$procfsRoot/interrupts"

expectedPair=$(normalizeSiblingPair "$cpu,$sibling") ||
  failUsage 'requested CPU pair is malformed'
cpuPair=$(normalizeSiblingPair "$(readValue "$cpuSiblingPath")") ||
  failUsage 'selected CPU sibling topology is unavailable'
siblingPair=$(normalizeSiblingPair "$(readValue "$siblingSiblingPath")") ||
  failUsage 'sibling CPU topology is unavailable'
[[ $cpuPair == "$expectedPair" && $siblingPair == "$expectedPair" ]] ||
  failUsage 'requested CPUs are not one symmetric SMT pair'

preSiblingOnline=$(readValue "$siblingOnlinePath") ||
  failUsage 'sibling online state is unavailable'
[[ $preSiblingOnline == "1" ]] || failUsage 'sibling is not initially online'
preGovernor=$(readValue "$governorPath") ||
  failUsage 'governor state is unavailable'
availableGovernors=$(readValue "$availableGovernorsPath") ||
  failUsage 'available governors are unavailable'
containsWord "$availableGovernors" performance ||
  failUsage 'performance governor is unavailable'
prePreference=$(readValue "$preferencePath") ||
  failUsage 'energy preference state is unavailable'
availablePreferences=$(readValue "$availablePreferencesPath") ||
  failUsage 'available energy preferences are unavailable'
containsWord "$availablePreferences" performance ||
  failUsage 'performance energy preference is unavailable'
preBoost=$(readValue "$boostPath") || failUsage 'boost state is unavailable'
preInterrupts=$(readSelectedCpuInterrupts "$interruptsPath" "$cpu") ||
  failUsage 'selected CPU interrupt state is unavailable'
validateStateToken "$preGovernor" || failUsage 'governor state is malformed'
validateStateToken "$prePreference" || failUsage 'energy preference is malformed'
[[ $preBoost =~ ^[01]$ ]] || failUsage 'boost state is malformed'

recordTemporaryPath="${restorationRecord}.tmp.$$"
(
  set -o noclobber
  : >"$recordTemporaryPath"
) 2>/dev/null || failUsage 'restoration record directory is not writable'

trap finishSession EXIT
trap 'handleSignal 143' TERM
trap 'handleSignal 130' INT
trap 'handleSignal 129' HUP

if ! writeValue "$governorPath" performance; then
  sessionOutcome="apply_failed"
  exit "$ApplyFailureExit"
fi
governorChanged=1
appliedGovernor=$(readValue "$governorPath") || appliedGovernor="unavailable"
if [[ $appliedGovernor != "performance" ]]; then
  sessionOutcome="apply_failed"
  exit "$ApplyFailureExit"
fi
if ! writeValue "$preferencePath" performance; then
  sessionOutcome="apply_failed"
  exit "$ApplyFailureExit"
fi
preferenceChanged=1
appliedPreference=$(readValue "$preferencePath") ||
  appliedPreference="unavailable"
if [[ $appliedPreference != "performance" ]]; then
  sessionOutcome="apply_failed"
  exit "$ApplyFailureExit"
fi
if ! writeValue "$siblingOnlinePath" 0; then
  sessionOutcome="apply_failed"
  exit "$ApplyFailureExit"
fi
siblingChanged=1
appliedSiblingOnline=$(readValue "$siblingOnlinePath") ||
  appliedSiblingOnline="unavailable"
if [[ $appliedSiblingOnline != "0" ]]; then
  sessionOutcome="apply_failed"
  exit "$ApplyFailureExit"
fi

if [[ $testing == "1" ]]; then
  env -i HOME=/nonexistent LANG=C.UTF-8 PATH=/usr/bin:/usr/sbin \
    "${commandArguments[@]}" &
else
  runuser --user "$targetUser" -- \
    env -i HOME=/nonexistent LANG=C.UTF-8 PATH=/usr/bin:/usr/sbin \
    "${commandArguments[@]}" &
fi
childPid=$!
wait "$childPid"
commandExitStatus=$?
childPid=""
exit "$commandExitStatus"
