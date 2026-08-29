cmake_minimum_required(VERSION 3.28)

foreach(requiredVariable
        XOAS_CLANG_TIDY
        XOAS_GIT
        XOAS_REPOSITORY_ROOT
        XOAS_COMPILATION_DATABASE)
  if(NOT DEFINED ${requiredVariable})
    message(FATAL_ERROR "${requiredVariable} is required.")
  endif()
endforeach()

if(NOT EXISTS "${XOAS_COMPILATION_DATABASE}/compile_commands.json")
  message(FATAL_ERROR "The debug compilation database is missing.")
endif()

execute_process(
  COMMAND
    "${XOAS_CLANG_TIDY}"
    "--config-file=${XOAS_REPOSITORY_ROOT}/.clang-tidy" --verify-config
  RESULT_VARIABLE configStatus
  OUTPUT_VARIABLE configOutput
  ERROR_VARIABLE configError)
if(NOT configStatus EQUAL 0)
  message(FATAL_ERROR
          "Clang-Tidy configuration is invalid:\n${configOutput}${configError}")
endif()

execute_process(
  COMMAND "${XOAS_GIT}" ls-files -- "*.c" "*.cc" "*.cpp" "*.cxx"
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

execute_process(
  COMMAND "${XOAS_GIT}" ls-files -- "*.h" "*.hh" "*.hpp" "*.hxx"
  WORKING_DIRECTORY "${XOAS_REPOSITORY_ROOT}"
  RESULT_VARIABLE headerGitStatus
  OUTPUT_VARIABLE trackedHeaderOutput
  ERROR_VARIABLE headerGitError
  OUTPUT_STRIP_TRAILING_WHITESPACE)
if(NOT headerGitStatus EQUAL 0)
  message(FATAL_ERROR
          "Unable to enumerate tracked headers: ${headerGitError}")
endif()

set(headerCount 0)
if(NOT trackedHeaderOutput STREQUAL "")
  string(REPLACE "\n" ";" trackedHeaderPaths "${trackedHeaderOutput}")
  foreach(trackedHeaderPath IN LISTS trackedHeaderPaths)
    if(trackedHeaderPath MATCHES
       "^tests/quality/fixtures/(generated/output|vendor)/")
      continue()
    endif()
    if(NOT trackedHeaderPath MATCHES "^(include|src|tests|cmake|tools)/")
      message(FATAL_ERROR
              "Tracked header has no approved classification: "
              "${trackedHeaderPath}")
    endif()

    execute_process(
      COMMAND
        "${CMAKE_COMMAND}"
        "-DXOAS_HEADER_GUARD_INPUT=${XOAS_REPOSITORY_ROOT}/${trackedHeaderPath}"
        "-DXOAS_HEADER_GUARD_RELATIVE_PATH=${trackedHeaderPath}"
        -P "${XOAS_REPOSITORY_ROOT}/cmake/quality/HeaderGuardCheck.cmake"
      RESULT_VARIABLE headerStatus
      OUTPUT_VARIABLE headerOutput
      ERROR_VARIABLE headerError)
    if(NOT headerStatus EQUAL 0)
      message(FATAL_ERROR
              "Portable header-guard check failed for ${trackedHeaderPath}:\n"
              "${headerOutput}${headerError}")
    endif()
    math(EXPR headerCount "${headerCount} + 1")
  endforeach()
endif()

file(READ
     "${XOAS_COMPILATION_DATABASE}/compile_commands.json"
     compilationDatabaseJson)
string(REPLACE "\n" ";" trackedPaths "${trackedOutput}")
set(tidySourceCount 0)
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
  string(FIND "${compilationDatabaseJson}" "${sourcePath}" commandOffset)
  if(commandOffset EQUAL -1)
    message(FATAL_ERROR
            "Tracked handwritten source lacks a compile command: ${trackedPath}")
  endif()

  execute_process(
    COMMAND
      "${XOAS_CLANG_TIDY}" "--config-file=${XOAS_REPOSITORY_ROOT}/.clang-tidy"
      -checks=-llvm-header-guard -p "${XOAS_COMPILATION_DATABASE}"
      "${sourcePath}"
    WORKING_DIRECTORY "${XOAS_REPOSITORY_ROOT}"
    RESULT_VARIABLE tidyStatus
    OUTPUT_VARIABLE tidyOutput
    ERROR_VARIABLE tidyError)
  if(NOT tidyStatus EQUAL 0)
    message(FATAL_ERROR
            "Clang-Tidy failed for ${trackedPath}:\n${tidyOutput}${tidyError}")
  endif()
  math(EXPR tidySourceCount "${tidySourceCount} + 1")
endforeach()

message(STATUS
        "Clang-Tidy passed for ${tidySourceCount} tracked sources and "
        "${headerCount} portable header guards.")
