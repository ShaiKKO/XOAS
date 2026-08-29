cmake_minimum_required(VERSION 3.28)

project(XOAS LANGUAGES CXX)

set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include(CTest)

find_package(Git REQUIRED)
find_package(Python3 3.12.3 EXACT COMPONENTS Interpreter REQUIRED)
find_program(XOAS_CLANG_FORMAT_EXECUTABLE NAMES clang-format-21 REQUIRED)
find_program(XOAS_CLANG_TIDY_EXECUTABLE NAMES clang-tidy-21 REQUIRED)
find_program(XOAS_SHELLCHECK_EXECUTABLE NAMES shellcheck REQUIRED)
find_package(Doxygen 1.9.8 EXACT REQUIRED)

include(cmake/quality/XoasWarnings.cmake)
include(cmake/quality/XoasSanitizers.cmake)

add_custom_target(
  format-check
  COMMAND
    "${CMAKE_COMMAND}"
    "-DXOAS_CLANG_FORMAT=${XOAS_CLANG_FORMAT_EXECUTABLE}"
    "-DXOAS_GIT=${GIT_EXECUTABLE}"
    "-DXOAS_REPOSITORY_ROOT=${PROJECT_SOURCE_DIR}"
    -P "${PROJECT_SOURCE_DIR}/cmake/quality/FormatCheck.cmake"
  COMMENT "Checking tracked handwritten C and C++ formatting"
  VERBATIM)

add_custom_target(
  format
  COMMAND
    "${CMAKE_COMMAND}"
    "-DXOAS_CLANG_FORMAT=${XOAS_CLANG_FORMAT_EXECUTABLE}"
    "-DXOAS_FORMAT_APPLY=ON"
    "-DXOAS_GIT=${GIT_EXECUTABLE}"
    "-DXOAS_REPOSITORY_ROOT=${PROJECT_SOURCE_DIR}"
    -P "${PROJECT_SOURCE_DIR}/cmake/quality/FormatCheck.cmake"
  COMMENT "Formatting tracked handwritten C and C++ files"
  VERBATIM)

add_custom_target(
  docs-check
  COMMAND
    "${CMAKE_COMMAND}"
    "-DXOAS_DOXYGEN=${DOXYGEN_EXECUTABLE}"
    "-DXOAS_DOXYFILE_TEMPLATE=${PROJECT_SOURCE_DIR}/Doxyfile.in"
    "-DXOAS_DOCUMENTATION_WORKING_DIRECTORY=${PROJECT_BINARY_DIR}/documentation"
    "-DXOAS_GIT=${GIT_EXECUTABLE}"
    "-DXOAS_REPOSITORY_ROOT=${PROJECT_SOURCE_DIR}"
    -P "${PROJECT_SOURCE_DIR}/cmake/quality/DocumentationCheck.cmake"
  COMMENT "Checking first-party public documentation"
  VERBATIM)

add_custom_target(
  repository-policy
  COMMAND
    "${CMAKE_COMMAND}"
    "-DXOAS_CLANG_FORMAT=${XOAS_CLANG_FORMAT_EXECUTABLE}"
    "-DXOAS_GENERATED_FIXTURE=${PROJECT_SOURCE_DIR}/tests/quality/fixtures/generated/output/generated-fixture.cpp"
    "-DXOAS_GENERATED_INPUT=${PROJECT_SOURCE_DIR}/tests/quality/fixtures/generated/input.json"
    "-DXOAS_GENERATOR=${PROJECT_SOURCE_DIR}/tests/quality/fixtures/generated/generate.cmake"
    "-DXOAS_GIT=${GIT_EXECUTABLE}"
    "-DXOAS_MARKDOWN_CHECKER=${PROJECT_SOURCE_DIR}/cmake/quality/MarkdownLinks.cmake"
    "-DXOAS_POLICY_WORKING_DIRECTORY=${PROJECT_BINARY_DIR}/repository-policy"
    "-DXOAS_PYTHON=${Python3_EXECUTABLE}"
    "-DXOAS_QUALITY_CONTRACT=${PROJECT_SOURCE_DIR}/tests/quality/contracts/expected-gates.json"
    "-DXOAS_REPOSITORY_ROOT=${PROJECT_SOURCE_DIR}"
    "-DXOAS_SHELLCHECK=${XOAS_SHELLCHECK_EXECUTABLE}"
    "-DXOAS_VENDOR_ADJACENT_FIXTURE=${PROJECT_SOURCE_DIR}/tests/quality/fixtures/vendor-adjacent.cpp"
    "-DXOAS_VENDOR_FIXTURE=${PROJECT_SOURCE_DIR}/tests/quality/fixtures/vendor/nonconforming.cpp"
    -P "${PROJECT_SOURCE_DIR}/cmake/quality/RepositoryPolicy.cmake"
  COMMENT "Checking repository evidence and source classification policy"
  VERBATIM)

add_subdirectory(tests/quality)
