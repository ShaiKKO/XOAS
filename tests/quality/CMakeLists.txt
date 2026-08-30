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

add_test(
  NAME quality-docs-undocumented-negative
  COMMAND
    "${CMAKE_COMMAND}"
    "-DXOAS_DOXYGEN=${DOXYGEN_EXECUTABLE}"
    "-DXOAS_DOXYFILE_TEMPLATE=${PROJECT_SOURCE_DIR}/Doxyfile.in"
    "-DXOAS_DOCUMENTATION_INPUT=${CMAKE_CURRENT_SOURCE_DIR}/fixtures/docs/undocumented-public.h.in"
    "-DXOAS_DOCUMENTATION_WORKING_DIRECTORY=${CMAKE_CURRENT_BINARY_DIR}/docs-undocumented"
    -DXOAS_DOCUMENTATION_EXPECT_FAILURE=ON
    -DXOAS_DOCUMENTATION_EXPECTED_DIAGNOSTIC=xoas-undocumented-file
    -P "${PROJECT_SOURCE_DIR}/cmake/quality/DocumentationCheck.cmake")

add_test(
  NAME quality-docs-malformed-negative
  COMMAND
    "${CMAKE_COMMAND}"
    "-DXOAS_DOXYGEN=${DOXYGEN_EXECUTABLE}"
    "-DXOAS_DOXYFILE_TEMPLATE=${PROJECT_SOURCE_DIR}/Doxyfile.in"
    "-DXOAS_DOCUMENTATION_INPUT=${CMAKE_CURRENT_SOURCE_DIR}/fixtures/docs/malformed.h.in"
    "-DXOAS_DOCUMENTATION_WORKING_DIRECTORY=${CMAKE_CURRENT_BINARY_DIR}/docs-malformed"
    -DXOAS_DOCUMENTATION_EXPECT_FAILURE=ON
    "-DXOAS_DOCUMENTATION_EXPECTED_DIAGNOSTIC=Found unknown command"
    -P "${PROJECT_SOURCE_DIR}/cmake/quality/DocumentationCheck.cmake")

add_test(
  NAME quality-docs-compliant
  COMMAND
    "${CMAKE_COMMAND}"
    "-DXOAS_DOXYGEN=${DOXYGEN_EXECUTABLE}"
    "-DXOAS_DOXYFILE_TEMPLATE=${PROJECT_SOURCE_DIR}/Doxyfile.in"
    "-DXOAS_DOCUMENTATION_INPUT=${CMAKE_CURRENT_SOURCE_DIR}/fixtures/docs/compliant.h"
    "-DXOAS_DOCUMENTATION_WORKING_DIRECTORY=${CMAKE_CURRENT_BINARY_DIR}/docs-compliant"
    -P "${PROJECT_SOURCE_DIR}/cmake/quality/DocumentationCheck.cmake")

set(xoasDocsHeaderSelfSufficientSource
    "${CMAKE_CURRENT_BINARY_DIR}/docs-header-self-sufficient.cpp")
file(
  GENERATE
  OUTPUT "${xoasDocsHeaderSelfSufficientSource}"
  CONTENT
    "/// \\file\n/// Verifies that the documentation fixture header is self-sufficient.\n\n#include \"compliant.h\"\n")
add_library(
  xoas_quality_docs_header_self_sufficient OBJECT
  "${xoasDocsHeaderSelfSufficientSource}")
target_include_directories(
  xoas_quality_docs_header_self_sufficient
  PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/fixtures/docs")
target_link_libraries(
  xoas_quality_docs_header_self_sufficient PRIVATE xoas_warnings)
add_dependencies(warnings xoas_quality_docs_header_self_sufficient)
add_dependencies(tidy xoas_quality_docs_header_self_sufficient)

add_executable(
  xoas_quality_runtime_positive
  fixtures/runtime/positive.cpp)
target_link_libraries(
  xoas_quality_runtime_positive
  PRIVATE xoas_sanitizers xoas_warnings)
add_dependencies(warnings xoas_quality_runtime_positive)
add_dependencies(tidy xoas_quality_runtime_positive)

add_test(
  NAME quality-runtime-positive
  COMMAND xoas_quality_runtime_positive)

if(XOAS_ENABLE_SANITIZERS)
  add_test(
    NAME quality-sanitizer-address-negative
    COMMAND
      "${CMAKE_COMMAND}"
      "-DXOAS_CXX_COMPILER=${CMAKE_CXX_COMPILER}"
      "-DXOAS_RUNTIME_INPUT=${CMAKE_CURRENT_SOURCE_DIR}/fixtures/runtime/address-negative.cpp.in"
      "-DXOAS_RUNTIME_WORKING_DIRECTORY=${CMAKE_CURRENT_BINARY_DIR}/sanitizer-address-negative"
      "-DXOAS_RUNTIME_EXPECTED_DIAGNOSTIC=AddressSanitizer: heap-use-after-free"
      -P "${PROJECT_SOURCE_DIR}/cmake/quality/ExpectRuntimeFailure.cmake")

  add_test(
    NAME quality-sanitizer-undefined-negative
    COMMAND
      "${CMAKE_COMMAND}"
      "-DXOAS_CXX_COMPILER=${CMAKE_CXX_COMPILER}"
      "-DXOAS_RUNTIME_INPUT=${CMAKE_CURRENT_SOURCE_DIR}/fixtures/runtime/undefined-negative.cpp.in"
      "-DXOAS_RUNTIME_WORKING_DIRECTORY=${CMAKE_CURRENT_BINARY_DIR}/sanitizer-undefined-negative"
      "-DXOAS_RUNTIME_EXPECTED_DIAGNOSTIC=runtime error: signed integer overflow"
      -P "${PROJECT_SOURCE_DIR}/cmake/quality/ExpectRuntimeFailure.cmake")

  add_test(
    NAME quality-sanitizer-positive
    COMMAND xoas_quality_runtime_positive)

  add_custom_target(
    asan-ubsan
    COMMAND
      "${CMAKE_COMMAND}" -E env
      ASAN_OPTIONS=abort_on_error=1:halt_on_error=1:detect_leaks=1
      UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1
      "${CMAKE_CTEST_COMMAND}" --test-dir "${PROJECT_BINARY_DIR}"
      -R quality-sanitizer --output-on-failure
    DEPENDS xoas_quality_runtime_positive
    COMMENT "Running fail-fast AddressSanitizer and UndefinedBehaviorSanitizer"
    VERBATIM)
endif()

function(xoasAddPolicyFixtureTest testName inputName expectedRule)
  add_test(
    NAME "quality-policy-${testName}"
    COMMAND
      "${CMAKE_COMMAND}"
      "-DXOAS_POLICY_FIXTURE_INPUT=${CMAKE_CURRENT_SOURCE_DIR}/fixtures/policy/${inputName}"
      "-DXOAS_POLICY_FIXTURE_WORKING_DIRECTORY=${CMAKE_CURRENT_BINARY_DIR}/policy-${testName}"
      "-DXOAS_POLICY_EXPECTED_RULE=${expectedRule}"
      -P "${PROJECT_SOURCE_DIR}/cmake/quality/RepositoryPolicy.cmake")
endfunction()

xoasAddPolicyFixtureTest(
  secret-negative secret-negative.txt.in xoas-secret-pattern)
xoasAddPolicyFixtureTest(
  server-coordinate-negative
  server-coordinate-negative.txt.in
  xoas-server-coordinate)
xoasAddPolicyFixtureTest(
  unfinished-marker-negative
  unfinished-marker-negative.txt.in
  xoas-unfinished-marker)

add_test(
  NAME quality-policy-artifact-negative
  COMMAND
    "${CMAKE_COMMAND}"
    "-DXOAS_POLICY_FIXTURE_INPUT=${CMAKE_CURRENT_SOURCE_DIR}/fixtures/policy/artifact-negative.bin.in"
    "-DXOAS_POLICY_FIXTURE_RELATIVE_PATH=evidence/synthetic-binary"
    "-DXOAS_POLICY_FIXTURE_WORKING_DIRECTORY=${CMAKE_CURRENT_BINARY_DIR}/policy-artifact-negative"
    -DXOAS_POLICY_EXPECTED_RULE=xoas-tracked-artifact
    -P "${PROJECT_SOURCE_DIR}/cmake/quality/RepositoryPolicy.cmake")

function(xoasAddMarkdownFixtureTest testName inputName expectedDiagnostic)
  add_test(
    NAME "quality-policy-markdown-${testName}"
    COMMAND
      "${CMAKE_COMMAND}"
      "-DXOAS_GIT=${GIT_EXECUTABLE}"
      "-DXOAS_MARKDOWN_INPUT=${CMAKE_CURRENT_SOURCE_DIR}/fixtures/policy/${inputName}"
      -DXOAS_MARKDOWN_LOGICAL_PATH=tests/quality/fixtures/policy/markdown-positive.md
      -DXOAS_MARKDOWN_EXPECT_FAILURE=ON
      "-DXOAS_MARKDOWN_EXPECTED_DIAGNOSTIC=${expectedDiagnostic}"
      "-DXOAS_PYTHON=${Python3_EXECUTABLE}"
      "-DXOAS_REPOSITORY_ROOT=${PROJECT_SOURCE_DIR}"
      -P "${PROJECT_SOURCE_DIR}/cmake/quality/MarkdownLinks.cmake")
endfunction()

xoasAddMarkdownFixtureTest(
  missing markdown-missing.md.in "target is not tracked")
xoasAddMarkdownFixtureTest(
  traversal markdown-traversal.md.in "target escapes the repository")
xoasAddMarkdownFixtureTest(
  malformed markdown-malformed.md.in
  "unterminated angle-bracket destination")
xoasAddMarkdownFixtureTest(
  anchor markdown-anchor.md.in "missing anchor")

add_test(
  NAME quality-policy-markdown-positive
  COMMAND
    "${CMAKE_COMMAND}"
    "-DXOAS_GIT=${GIT_EXECUTABLE}"
    "-DXOAS_PYTHON=${Python3_EXECUTABLE}"
    "-DXOAS_REPOSITORY_ROOT=${PROJECT_SOURCE_DIR}"
    -P "${PROJECT_SOURCE_DIR}/cmake/quality/MarkdownLinks.cmake")

add_library(
  xoas_quality_generated_fixture OBJECT
  fixtures/generated/output/generated-fixture.cpp)
target_link_libraries(xoas_quality_generated_fixture PRIVATE xoas_warnings)

add_library(
  xoas_quality_vendor_adjacent OBJECT
  fixtures/vendor-adjacent.cpp)
target_link_libraries(xoas_quality_vendor_adjacent PRIVATE xoas_warnings)
add_dependencies(warnings
                 xoas_quality_generated_fixture
                 xoas_quality_vendor_adjacent)
add_dependencies(tidy xoas_quality_vendor_adjacent)
add_dependencies(repository-policy
                 xoas_quality_generated_fixture
                 xoas_quality_vendor_adjacent)

add_test(
  NAME quality-policy-repository-positive
  COMMAND
    "${CMAKE_COMMAND}"
    "-DXOAS_CLANG_FORMAT=${XOAS_CLANG_FORMAT_EXECUTABLE}"
    "-DXOAS_GENERATED_FIXTURE=${CMAKE_CURRENT_SOURCE_DIR}/fixtures/generated/output/generated-fixture.cpp"
    "-DXOAS_GENERATED_INPUT=${CMAKE_CURRENT_SOURCE_DIR}/fixtures/generated/input.json"
    "-DXOAS_GENERATOR=${CMAKE_CURRENT_SOURCE_DIR}/fixtures/generated/generate.cmake"
    "-DXOAS_GIT=${GIT_EXECUTABLE}"
    "-DXOAS_MARKDOWN_CHECKER=${PROJECT_SOURCE_DIR}/cmake/quality/MarkdownLinks.cmake"
    "-DXOAS_POLICY_WORKING_DIRECTORY=${CMAKE_CURRENT_BINARY_DIR}/policy-repository-positive"
    "-DXOAS_PYTHON=${Python3_EXECUTABLE}"
    "-DXOAS_QUALITY_CONTRACT=${XOAS_QUALITY_CONTRACT}"
    "-DXOAS_REPOSITORY_ROOT=${PROJECT_SOURCE_DIR}"
    "-DXOAS_SHELLCHECK=${XOAS_SHELLCHECK_EXECUTABLE}"
    "-DXOAS_VENDOR_ADJACENT_FIXTURE=${CMAKE_CURRENT_SOURCE_DIR}/fixtures/vendor-adjacent.cpp"
    "-DXOAS_VENDOR_FIXTURE=${CMAKE_CURRENT_SOURCE_DIR}/fixtures/vendor/nonconforming.cpp"
    -P "${PROJECT_SOURCE_DIR}/cmake/quality/RepositoryPolicy.cmake")

add_test(
  NAME quality-aggregate-contract
  COMMAND
    "${CMAKE_COMMAND}"
    "-DXOAS_BUILD_DIRECTORY=${PROJECT_BINARY_DIR}"
    "-DXOAS_CMAKE=${CMAKE_COMMAND}"
    "-DXOAS_QUALITY_CONTRACT=${XOAS_QUALITY_CONTRACT}"
    -P "${PROJECT_SOURCE_DIR}/cmake/quality/QualityContractCheck.cmake")

add_test(
  NAME quality-cleanup-boundary
  COMMAND
    "${CMAKE_COMMAND}"
    "-DXOAS_CLEANUP_SCRIPT=${PROJECT_SOURCE_DIR}/cmake/quality/CleanBuildTrees.cmake"
    "-DXOAS_CLEANUP_TEST_WORKING_DIRECTORY=${CMAKE_CURRENT_BINARY_DIR}/cleanup-boundary"
    -P "${PROJECT_SOURCE_DIR}/cmake/quality/CleanBuildTreesCheck.cmake")

add_test(
  NAME quality-ci-workflow
  COMMAND
    "${CMAKE_COMMAND}"
    "-DXOAS_ACTION_LOCK=${PROJECT_SOURCE_DIR}/toolchains/github-actions-v1.lock.json"
    "-DXOAS_ACTION_LOCK_SCHEMA=${PROJECT_SOURCE_DIR}/schemas/github-actions-lock-v1.schema.json"
    "-DXOAS_PYTHON=${Python3_EXECUTABLE}"
    "-DXOAS_QUALITY_CONTRACT=${XOAS_QUALITY_CONTRACT}"
    "-DXOAS_WORKFLOW=${PROJECT_SOURCE_DIR}/.github/workflows/quality.yml"
    -P "${PROJECT_SOURCE_DIR}/cmake/quality/CiWorkflowCheck.cmake")

add_test(
  NAME quality-branch-protection-record
  COMMAND
    "${CMAKE_COMMAND}"
    "-DXOAS_BRANCH_PROTECTION_RECORD=${PROJECT_SOURCE_DIR}/docs/engineering/main-branch-protection-v1.json"
    "-DXOAS_BRANCH_PROTECTION_REQUEST=${PROJECT_SOURCE_DIR}/docs/engineering/main-branch-protection-v1.request.json"
    "-DXOAS_BRANCH_PROTECTION_SCHEMA=${PROJECT_SOURCE_DIR}/schemas/branch-protection-v1.schema.json"
    "-DXOAS_PYTHON=${Python3_EXECUTABLE}"
    "-DXOAS_QUALITY_CONTRACT=${XOAS_QUALITY_CONTRACT}"
    -P "${PROJECT_SOURCE_DIR}/cmake/quality/BranchProtectionRecordCheck.cmake")

execute_process(
  COMMAND "${GIT_EXECUTABLE}" ls-files
  WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}"
  RESULT_VARIABLE qualityDependencyStatus
  OUTPUT_VARIABLE qualityDependencyOutput
  ERROR_VARIABLE qualityDependencyError
  OUTPUT_STRIP_TRAILING_WHITESPACE)
if(NOT qualityDependencyStatus EQUAL 0)
  message(FATAL_ERROR
          "Unable to enumerate aggregate quality dependencies: "
          "${qualityDependencyError}")
endif()
string(REPLACE "\n" ";" qualityDependencyPaths
               "${qualityDependencyOutput}")
set(qualityTrackedDependencies)
foreach(qualityDependencyPath IN LISTS qualityDependencyPaths)
  list(APPEND qualityTrackedDependencies
       "${PROJECT_SOURCE_DIR}/${qualityDependencyPath}")
endforeach()

add_custom_target(
  quality-tests
  COMMAND
    "${CMAKE_CTEST_COMMAND}" --test-dir "${PROJECT_BINARY_DIR}"
    --output-on-failure
  DEPENDS warnings
  COMMENT "Running the complete local CTest surface"
  VERBATIM)

if(NOT TARGET asan-ubsan)
  set(sanitizerStampDirectory
      "${PROJECT_BINARY_DIR}/quality-stamps")
  set(sanitizerStamp
      "${sanitizerStampDirectory}/asan-ubsan.stamp")
  add_custom_command(
    OUTPUT "${sanitizerStamp}"
    COMMAND "${CMAKE_COMMAND}" -E make_directory "${sanitizerStampDirectory}"
    COMMAND "${CMAKE_COMMAND}" --preset asan-ubsan
    COMMAND
      "${CMAKE_COMMAND}" --build --preset asan-ubsan
      --target asan-ubsan
    COMMAND "${CMAKE_COMMAND}" -E touch "${sanitizerStamp}"
    DEPENDS ${qualityTrackedDependencies}
    WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}"
    COMMENT "Verifying the isolated sanitizer preset"
    VERBATIM)
  add_custom_target(asan-ubsan DEPENDS "${sanitizerStamp}")
endif()

add_custom_target(
  quality
  DEPENDS
    asan-ubsan
    docs-check
    format-check
    quality-tests
    repository-policy
    tidy
    warnings)
