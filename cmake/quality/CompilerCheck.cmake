cmake_minimum_required(VERSION 3.28)

foreach(requiredVariable
        XOAS_CXX_COMPILER
        XOAS_COMPILER_INPUT
        XOAS_COMPILER_WORKING_DIRECTORY
        XOAS_WARNING_FLAGS_ENCODED)
  if(NOT DEFINED ${requiredVariable})
    message(FATAL_ERROR "${requiredVariable} is required.")
  endif()
endforeach()

if(NOT EXISTS "${XOAS_CXX_COMPILER}")
  message(FATAL_ERROR "XOAS_CXX_COMPILER does not exist: ${XOAS_CXX_COMPILER}")
endif()

file(MAKE_DIRECTORY "${XOAS_COMPILER_WORKING_DIRECTORY}")
get_filename_component(compilerInputName "${XOAS_COMPILER_INPUT}" NAME)
string(REGEX REPLACE "\\.in$" "" compilerCopyName "${compilerInputName}")
set(compilerCopyPath
    "${XOAS_COMPILER_WORKING_DIRECTORY}/${compilerCopyName}")
set(compilerObjectPath
    "${XOAS_COMPILER_WORKING_DIRECTORY}/${compilerCopyName}.o")
configure_file("${XOAS_COMPILER_INPUT}" "${compilerCopyPath}" COPYONLY)

string(REPLACE "|" ";" xoasWarningFlags "${XOAS_WARNING_FLAGS_ENCODED}")
set(compilerArguments -std=c++23)
if(DEFINED XOAS_COMPILER_INCLUDE_DIRECTORY)
  list(APPEND compilerArguments "-I${XOAS_COMPILER_INCLUDE_DIRECTORY}")
endif()
list(APPEND compilerArguments ${xoasWarningFlags})
list(APPEND compilerArguments -c "${compilerCopyPath}" -o
     "${compilerObjectPath}")

execute_process(
  COMMAND "${XOAS_CXX_COMPILER}" ${compilerArguments}
  RESULT_VARIABLE compilerStatus
  OUTPUT_VARIABLE compilerOutput
  ERROR_VARIABLE compilerError)
string(CONCAT compilerDiagnostics "${compilerOutput}" "${compilerError}")

if(XOAS_COMPILER_EXPECT_FAILURE)
  if(compilerStatus EQUAL 0)
    message(FATAL_ERROR "Negative compiler fixture unexpectedly passed.")
  endif()
  if(NOT compilerDiagnostics MATCHES "-Wsign-conversion")
    message(FATAL_ERROR
            "Negative fixture failed without -Wsign-conversion:\n"
            "${compilerDiagnostics}")
  endif()
  message(STATUS "Observed intended -Wsign-conversion rejection.")
  return()
endif()

if(NOT compilerStatus EQUAL 0)
  message(FATAL_ERROR
          "Compliant compiler fixture failed:\n${compilerDiagnostics}")
endif()
