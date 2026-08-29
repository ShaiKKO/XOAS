cmake_minimum_required(VERSION 3.28)

foreach(requiredVariable
        XOAS_CLANG_TIDY
        XOAS_TIDY_CONFIG
        XOAS_TIDY_INPUT
        XOAS_TIDY_WORKING_DIRECTORY)
  if(NOT DEFINED ${requiredVariable})
    message(FATAL_ERROR "${requiredVariable} is required.")
  endif()
endforeach()

if(NOT EXISTS "${XOAS_CLANG_TIDY}")
  message(FATAL_ERROR "XOAS_CLANG_TIDY does not exist: ${XOAS_CLANG_TIDY}")
endif()
if(NOT EXISTS "${XOAS_TIDY_CONFIG}")
  message(FATAL_ERROR "XOAS_TIDY_CONFIG does not exist: ${XOAS_TIDY_CONFIG}")
endif()

file(MAKE_DIRECTORY "${XOAS_TIDY_WORKING_DIRECTORY}")
get_filename_component(tidyInputName "${XOAS_TIDY_INPUT}" NAME)
string(REGEX REPLACE "\\.in$" "" tidyCopyName "${tidyInputName}")
set(tidyCopyPath "${XOAS_TIDY_WORKING_DIRECTORY}/${tidyCopyName}")
configure_file("${XOAS_TIDY_INPUT}" "${tidyCopyPath}" COPYONLY)

set(tidyCompileArguments -std=c++23)
if(tidyCopyPath MATCHES "\\.(h|hh|hpp|hxx)$")
  list(APPEND tidyCompileArguments -x c++-header)
endif()

execute_process(
  COMMAND
    "${XOAS_CLANG_TIDY}" "--config-file=${XOAS_TIDY_CONFIG}"
    --verify-config
  RESULT_VARIABLE configStatus
  OUTPUT_VARIABLE configOutput
  ERROR_VARIABLE configError)
if(NOT configStatus EQUAL 0)
  message(FATAL_ERROR
          "Clang-Tidy configuration is invalid:\n${configOutput}${configError}")
endif()

execute_process(
  COMMAND
    "${XOAS_CLANG_TIDY}" "--config-file=${XOAS_TIDY_CONFIG}"
    "${tidyCopyPath}" -- ${tidyCompileArguments}
  RESULT_VARIABLE tidyStatus
  OUTPUT_VARIABLE tidyOutput
  ERROR_VARIABLE tidyError)
string(CONCAT tidyDiagnostics "${tidyOutput}" "${tidyError}")

if(XOAS_TIDY_EXPECT_FAILURE)
  if(tidyStatus EQUAL 0)
    message(FATAL_ERROR "Negative Clang-Tidy fixture unexpectedly passed.")
  endif()
  if(NOT DEFINED XOAS_TIDY_EXPECTED_CHECK OR
     NOT tidyDiagnostics MATCHES "${XOAS_TIDY_EXPECTED_CHECK}")
    message(FATAL_ERROR
            "Negative fixture failed without ${XOAS_TIDY_EXPECTED_CHECK}:\n"
            "${tidyDiagnostics}")
  endif()
  message(STATUS "Observed intended ${XOAS_TIDY_EXPECTED_CHECK} rejection.")
  return()
endif()

if(NOT tidyStatus EQUAL 0)
  message(FATAL_ERROR "Compliant Clang-Tidy fixture failed:\n${tidyDiagnostics}")
endif()
