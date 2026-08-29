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

function(xoasAddTidyFixtureTest testName inputName expectedCheck)
  add_test(
    NAME "quality-tidy-${testName}"
    COMMAND
      "${CMAKE_COMMAND}"
      "-DXOAS_CLANG_TIDY=${XOAS_CLANG_TIDY_EXECUTABLE}"
      "-DXOAS_TIDY_CONFIG=${PROJECT_SOURCE_DIR}/.clang-tidy"
      "-DXOAS_TIDY_INPUT=${CMAKE_CURRENT_SOURCE_DIR}/fixtures/tidy/${inputName}"
      "-DXOAS_TIDY_WORKING_DIRECTORY=${CMAKE_CURRENT_BINARY_DIR}/tidy-${testName}"
      "-DXOAS_TIDY_EXPECTED_CHECK=${expectedCheck}"
      -DXOAS_TIDY_EXPECT_FAILURE=ON
      -P "${PROJECT_SOURCE_DIR}/cmake/quality/TidyFixtureCheck.cmake")
endfunction()

xoasAddTidyFixtureTest(
  reserved-identifier reserved-identifier.cpp.in bugprone-reserved-identifier)
xoasAddTidyFixtureTest(
  identifier-naming identifier-naming.cpp.in readability-identifier-naming)
xoasAddTidyFixtureTest(
  performance performance.cpp.in performance-unnecessary-value-param)
xoasAddTidyFixtureTest(
  suspicious-control suspicious-control.cpp.in bugprone-suspicious-semicolon)
xoasAddTidyFixtureTest(
  header-guard header-guard.h.in llvm-header-guard)

add_test(
  NAME quality-tidy-portable-header-guard-negative
  COMMAND
    "${CMAKE_COMMAND}"
    "-DXOAS_HEADER_GUARD_INPUT=${CMAKE_CURRENT_SOURCE_DIR}/fixtures/tidy/header-guard.h.in"
    -DXOAS_HEADER_GUARD_RELATIVE_PATH=tests/quality/fixtures/tidy/header-guard.h
    -DXOAS_HEADER_GUARD_EXPECT_FAILURE=ON
    -P "${PROJECT_SOURCE_DIR}/cmake/quality/HeaderGuardCheck.cmake")

add_test(
  NAME quality-tidy-portable-header-guard-positive
  COMMAND
    "${CMAKE_COMMAND}"
    "-DXOAS_HEADER_GUARD_INPUT=${CMAKE_CURRENT_SOURCE_DIR}/fixtures/compiler/compliant.h"
    -DXOAS_HEADER_GUARD_RELATIVE_PATH=tests/quality/fixtures/compiler/compliant.h
    -P "${PROJECT_SOURCE_DIR}/cmake/quality/HeaderGuardCheck.cmake")

add_library(
  xoas_quality_format_compliant OBJECT
  fixtures/format/compliant.cpp)
target_link_libraries(xoas_quality_format_compliant PRIVATE xoas_warnings)

add_library(
  xoas_quality_tidy_compliant OBJECT
  fixtures/tidy/compliant.cpp)
target_link_libraries(xoas_quality_tidy_compliant PRIVATE xoas_warnings)

add_test(
  NAME quality-tidy-compliant
  COMMAND
    "${CMAKE_COMMAND}"
    "-DXOAS_CLANG_TIDY=${XOAS_CLANG_TIDY_EXECUTABLE}"
    "-DXOAS_TIDY_CONFIG=${PROJECT_SOURCE_DIR}/.clang-tidy"
    "-DXOAS_TIDY_INPUT=${CMAKE_CURRENT_SOURCE_DIR}/fixtures/tidy/compliant.cpp"
    "-DXOAS_TIDY_WORKING_DIRECTORY=${CMAKE_CURRENT_BINARY_DIR}/tidy-compliant"
    -P "${PROJECT_SOURCE_DIR}/cmake/quality/TidyFixtureCheck.cmake")

add_custom_target(
  tidy
  COMMAND
    "${CMAKE_COMMAND}"
    "-DXOAS_CLANG_TIDY=${XOAS_CLANG_TIDY_EXECUTABLE}"
    "-DXOAS_GIT=${GIT_EXECUTABLE}"
    "-DXOAS_REPOSITORY_ROOT=${PROJECT_SOURCE_DIR}"
    "-DXOAS_COMPILATION_DATABASE=${PROJECT_BINARY_DIR}"
    -P "${PROJECT_SOURCE_DIR}/cmake/quality/TidyCheck.cmake"
  DEPENDS
    xoas_quality_compiler_header_self_sufficient
    xoas_quality_compiler_positive
    xoas_quality_format_compliant
    xoas_quality_tidy_compliant
  COMMENT "Running the explicit Clang-Tidy policy"
  VERBATIM)
