cmake_minimum_required(VERSION 3.28)

foreach(requiredVariable
        XOAS_CXX_COMPILER
        XOAS_RUNTIME_INPUT
        XOAS_RUNTIME_WORKING_DIRECTORY
        XOAS_RUNTIME_EXPECTED_DIAGNOSTIC)
  if(NOT DEFINED ${requiredVariable})
    message(FATAL_ERROR "${requiredVariable} is required.")
  endif()
endforeach()

if(NOT EXISTS "${XOAS_CXX_COMPILER}")
  message(FATAL_ERROR "XOAS_CXX_COMPILER does not exist: ${XOAS_CXX_COMPILER}")
endif()

file(MAKE_DIRECTORY "${XOAS_RUNTIME_WORKING_DIRECTORY}")
get_filename_component(runtimeInputName "${XOAS_RUNTIME_INPUT}" NAME)
string(REGEX REPLACE "\\.in$" "" runtimeCopyName "${runtimeInputName}")
set(runtimeCopyPath
    "${XOAS_RUNTIME_WORKING_DIRECTORY}/${runtimeCopyName}")
set(runtimeBinaryPath
    "${XOAS_RUNTIME_WORKING_DIRECTORY}/${runtimeCopyName}.bin")
set(runtimeLogPath
    "${XOAS_RUNTIME_WORKING_DIRECTORY}/${runtimeCopyName}.log")
configure_file("${XOAS_RUNTIME_INPUT}" "${runtimeCopyPath}" COPYONLY)

execute_process(
  COMMAND
    "${XOAS_CXX_COMPILER}" -std=c++23 -O0 -g
    -fsanitize=address,undefined -fno-omit-frame-pointer
    -fno-sanitize-recover=all -fuse-ld=/usr/bin/ld.lld-21
    "${runtimeCopyPath}" -o "${runtimeBinaryPath}"
  RESULT_VARIABLE compileStatus
  OUTPUT_VARIABLE compileOutput
  ERROR_VARIABLE compileError)
if(NOT compileStatus EQUAL 0)
  message(FATAL_ERROR
          "Sanitizer negative fixture did not compile:\n"
          "${compileOutput}${compileError}")
endif()

execute_process(
  COMMAND
    "${CMAKE_COMMAND}" -E env
    ASAN_OPTIONS=abort_on_error=1:halt_on_error=1:detect_leaks=1
    UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1
    "${runtimeBinaryPath}"
  RESULT_VARIABLE runtimeStatus
  OUTPUT_VARIABLE runtimeOutput
  ERROR_VARIABLE runtimeError)
string(CONCAT runtimeDiagnostics "${runtimeOutput}" "${runtimeError}")
file(WRITE "${runtimeLogPath}" "${runtimeDiagnostics}")

if(runtimeStatus EQUAL 0)
  message(FATAL_ERROR "Sanitizer negative fixture unexpectedly passed.")
endif()
if(NOT runtimeDiagnostics MATCHES "${XOAS_RUNTIME_EXPECTED_DIAGNOSTIC}")
  message(FATAL_ERROR
          "Runtime failed without ${XOAS_RUNTIME_EXPECTED_DIAGNOSTIC}:\n"
          "${runtimeDiagnostics}")
endif()

message(STATUS
        "Observed intended sanitizer rejection: "
        "${XOAS_RUNTIME_EXPECTED_DIAGNOSTIC}")
