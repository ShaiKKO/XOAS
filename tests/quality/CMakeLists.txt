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
