set(XOAS_QUALITY_CONTRACT
    "${CMAKE_CURRENT_SOURCE_DIR}/contracts/expected-gates.json")

file(READ "${XOAS_QUALITY_CONTRACT}" xoasQualityContractJson)
string(JSON xoasGateCount LENGTH "${xoasQualityContractJson}" gates)

set(xoasExpectedGateNames
    format-check
    warnings
    tidy
    docs-check
    test
    asan-ubsan
    repository-policy
    quality)
list(LENGTH xoasExpectedGateNames xoasExpectedGateCount)

if(NOT xoasGateCount EQUAL xoasExpectedGateCount)
  message(FATAL_ERROR
          "Quality gate contract declares ${xoasGateCount} gates; "
          "${xoasExpectedGateCount} are required.")
endif()

math(EXPR xoasLastGateIndex "${xoasGateCount} - 1")
foreach(xoasGateIndex RANGE "${xoasLastGateIndex}")
  string(JSON xoasGateName GET "${xoasQualityContractJson}" gates
         "${xoasGateIndex}" name)
  list(GET xoasExpectedGateNames "${xoasGateIndex}" xoasExpectedGateName)
  if(NOT xoasGateName STREQUAL xoasExpectedGateName)
    message(FATAL_ERROR
            "Quality gate ${xoasGateIndex} is '${xoasGateName}'; "
            "expected '${xoasExpectedGateName}'.")
  endif()
endforeach()

add_test(
  NAME quality-format-negative
  COMMAND
    "${CMAKE_COMMAND}"
    "-DXOAS_CLANG_FORMAT=${XOAS_CLANG_FORMAT_EXECUTABLE}"
    "-DXOAS_FORMAT_INPUT=${CMAKE_CURRENT_SOURCE_DIR}/fixtures/format/noncompliant.cpp.in"
    "-DXOAS_FORMAT_WORKING_DIRECTORY=${CMAKE_CURRENT_BINARY_DIR}/format-negative"
    -DXOAS_FORMAT_EXPECT_FAILURE=ON
    -P "${PROJECT_SOURCE_DIR}/cmake/quality/FormatCheck.cmake")

add_test(
  NAME quality-format-positive
  COMMAND
    "${CMAKE_COMMAND}"
    "-DXOAS_CLANG_FORMAT=${XOAS_CLANG_FORMAT_EXECUTABLE}"
    "-DXOAS_FORMAT_INPUT=${CMAKE_CURRENT_SOURCE_DIR}/fixtures/format/compliant.cpp"
    "-DXOAS_FORMAT_WORKING_DIRECTORY=${CMAKE_CURRENT_BINARY_DIR}/format-positive"
    -P "${PROJECT_SOURCE_DIR}/cmake/quality/FormatCheck.cmake")

add_test(
  NAME quality-format-nonmutation
  COMMAND
    "${CMAKE_COMMAND}"
    "-DXOAS_CLANG_FORMAT=${XOAS_CLANG_FORMAT_EXECUTABLE}"
    "-DXOAS_FORMAT_INPUT=${CMAKE_CURRENT_SOURCE_DIR}/fixtures/format/noncompliant.cpp.in"
    "-DXOAS_FORMAT_WORKING_DIRECTORY=${CMAKE_CURRENT_BINARY_DIR}/format-nonmutation"
    -DXOAS_FORMAT_EXPECT_FAILURE=ON
    -DXOAS_FORMAT_VERIFY_NONMUTATION=ON
    -P "${PROJECT_SOURCE_DIR}/cmake/quality/FormatCheck.cmake")

add_test(
  NAME quality-compiler-warning-negative
  COMMAND
    "${CMAKE_COMMAND}"
    "-DXOAS_CXX_COMPILER=${CMAKE_CXX_COMPILER}"
    "-DXOAS_COMPILER_INPUT=${CMAKE_CURRENT_SOURCE_DIR}/fixtures/compiler/warning-negative.cpp.in"
    "-DXOAS_COMPILER_WORKING_DIRECTORY=${CMAKE_CURRENT_BINARY_DIR}/compiler-warning-negative"
    "-DXOAS_WARNING_FLAGS_ENCODED=${xoasWarningFlagsEncoded}"
    -DXOAS_COMPILER_EXPECT_FAILURE=ON
    -P "${PROJECT_SOURCE_DIR}/cmake/quality/CompilerCheck.cmake")

add_library(
  xoas_quality_compiler_positive OBJECT
  fixtures/compiler/compliant.cpp)
target_include_directories(
  xoas_quality_compiler_positive
  PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/fixtures/compiler")
target_link_libraries(xoas_quality_compiler_positive PRIVATE xoas_warnings)

set(xoasHeaderSelfSufficientSource
    "${CMAKE_CURRENT_BINARY_DIR}/compiler-header-self-sufficient.cpp")
file(
  GENERATE
  OUTPUT "${xoasHeaderSelfSufficientSource}"
  CONTENT
    "/// \\file\n/// Verifies that the compiler fixture header is self-sufficient.\n\n#include \"compliant.h\"\n")
add_library(
  xoas_quality_compiler_header_self_sufficient OBJECT
  "${xoasHeaderSelfSufficientSource}")
target_include_directories(
  xoas_quality_compiler_header_self_sufficient
  PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/fixtures/compiler")
target_link_libraries(
  xoas_quality_compiler_header_self_sufficient PRIVATE xoas_warnings)

add_custom_target(
  warnings
  DEPENDS
    xoas_quality_compiler_positive
    xoas_quality_compiler_header_self_sufficient)

add_test(
  NAME quality-compiler-positive
  COMMAND
    "${CMAKE_COMMAND}"
    "-DXOAS_CXX_COMPILER=${CMAKE_CXX_COMPILER}"
    "-DXOAS_COMPILER_INPUT=${CMAKE_CURRENT_SOURCE_DIR}/fixtures/compiler/compliant.cpp"
    "-DXOAS_COMPILER_INCLUDE_DIRECTORY=${CMAKE_CURRENT_SOURCE_DIR}/fixtures/compiler"
    "-DXOAS_COMPILER_WORKING_DIRECTORY=${CMAKE_CURRENT_BINARY_DIR}/compiler-positive"
    "-DXOAS_WARNING_FLAGS_ENCODED=${xoasWarningFlagsEncoded}"
    -P "${PROJECT_SOURCE_DIR}/cmake/quality/CompilerCheck.cmake")
