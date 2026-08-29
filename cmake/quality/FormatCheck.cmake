cmake_minimum_required(VERSION 3.28)

if(NOT DEFINED XOAS_CLANG_FORMAT OR NOT EXISTS "${XOAS_CLANG_FORMAT}")
  message(FATAL_ERROR "XOAS_CLANG_FORMAT must name the locked formatter.")
endif()

function(xoasCheckFormat inputPath expectFailure verifyNonmutation)
  file(SHA256 "${inputPath}" beforeSha256)
  execute_process(
    COMMAND "${XOAS_CLANG_FORMAT}" --dry-run --Werror "${inputPath}"
    RESULT_VARIABLE formatStatus
    OUTPUT_VARIABLE formatOutput
    ERROR_VARIABLE formatError)
  file(SHA256 "${inputPath}" afterSha256)

  if(verifyNonmutation AND NOT beforeSha256 STREQUAL afterSha256)
    message(FATAL_ERROR "Formatter check mutated ${inputPath}.")
  endif()

  if(expectFailure)
    if(formatStatus EQUAL 0)
      message(FATAL_ERROR
              "Negative formatting fixture unexpectedly passed: ${inputPath}")
    endif()
    string(CONCAT formatDiagnostics "${formatOutput}" "${formatError}")
    if(NOT formatDiagnostics MATCHES "code should be clang-formatted")
      message(FATAL_ERROR
              "Negative fixture failed without the formatting diagnostic:\n"
              "${formatDiagnostics}")
    endif()
    message(STATUS "Observed intended formatting rejection for ${inputPath}")
    return()
  endif()

  if(NOT formatStatus EQUAL 0)
    message(FATAL_ERROR
            "Formatting check failed for ${inputPath}:\n"
            "${formatOutput}${formatError}")
  endif()
endfunction()

if(DEFINED XOAS_FORMAT_INPUT)
  if(NOT DEFINED XOAS_FORMAT_WORKING_DIRECTORY)
    message(FATAL_ERROR
            "XOAS_FORMAT_WORKING_DIRECTORY is required for fixture checks.")
  endif()
  file(MAKE_DIRECTORY "${XOAS_FORMAT_WORKING_DIRECTORY}")
  get_filename_component(formatInputName "${XOAS_FORMAT_INPUT}" NAME)
  string(REGEX REPLACE "\\.in$" "" formatCopyName "${formatInputName}")
  set(formatCopyPath "${XOAS_FORMAT_WORKING_DIRECTORY}/${formatCopyName}")
  configure_file("${XOAS_FORMAT_INPUT}" "${formatCopyPath}" COPYONLY)
  xoasCheckFormat(
    "${formatCopyPath}"
    "${XOAS_FORMAT_EXPECT_FAILURE}"
    "${XOAS_FORMAT_VERIFY_NONMUTATION}")
  return()
endif()

if(NOT DEFINED XOAS_GIT OR NOT EXISTS "${XOAS_GIT}")
  message(FATAL_ERROR "XOAS_GIT must name the Git executable.")
endif()
if(NOT DEFINED XOAS_REPOSITORY_ROOT OR
   NOT EXISTS "${XOAS_REPOSITORY_ROOT}/.git")
  message(FATAL_ERROR "XOAS_REPOSITORY_ROOT must name the repository root.")
endif()

execute_process(
  COMMAND
    "${XOAS_GIT}" ls-files -- "*.c" "*.cc" "*.cpp" "*.cxx" "*.h" "*.hh"
    "*.hpp" "*.hxx"
  WORKING_DIRECTORY "${XOAS_REPOSITORY_ROOT}"
  RESULT_VARIABLE gitStatus
  OUTPUT_VARIABLE trackedOutput
  ERROR_VARIABLE gitError
  OUTPUT_STRIP_TRAILING_WHITESPACE)
if(NOT gitStatus EQUAL 0)
  message(FATAL_ERROR "Unable to enumerate tracked sources: ${gitError}")
endif()

if(trackedOutput STREQUAL "")
  message(FATAL_ERROR "No tracked handwritten C or C++ source was found.")
endif()

string(REPLACE "\n" ";" trackedPaths "${trackedOutput}")
foreach(trackedPath IN LISTS trackedPaths)
  if(trackedPath MATCHES
     "^tests/quality/fixtures/(generated/output|vendor)/")
    continue()
  endif()
  if(NOT trackedPath MATCHES "^(include|src|tests|cmake|tools)/")
    message(FATAL_ERROR
            "Tracked C/C++ path has no approved classification: ${trackedPath}")
  endif()

  set(sourcePath "${XOAS_REPOSITORY_ROOT}/${trackedPath}")
  if(XOAS_FORMAT_APPLY)
    execute_process(
      COMMAND "${XOAS_CLANG_FORMAT}" -i "${sourcePath}"
      RESULT_VARIABLE formatStatus
      OUTPUT_VARIABLE formatOutput
      ERROR_VARIABLE formatError)
    if(NOT formatStatus EQUAL 0)
      message(FATAL_ERROR
              "Formatting failed for ${trackedPath}:\n"
              "${formatOutput}${formatError}")
    endif()
  else()
    xoasCheckFormat("${sourcePath}" FALSE TRUE)
  endif()
endforeach()
