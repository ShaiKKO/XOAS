cmake_minimum_required(VERSION 3.28)

function(xoasDecodeHex encodedContent outputVariable)
  string(REGEX REPLACE "[ \t\r\n]" "" normalizedContent
                       "${encodedContent}")
  string(LENGTH "${normalizedContent}" encodedLength)
  math(EXPR encodedRemainder "${encodedLength} % 2")
  if(NOT encodedRemainder EQUAL 0 OR
     NOT normalizedContent MATCHES "^[0-9A-Fa-f]+$")
    message(FATAL_ERROR "Encoded policy fixture is not valid hexadecimal.")
  endif()

  set(decodedContent "")
  if(encodedLength GREATER 0)
    math(EXPR finalOffset "${encodedLength} - 2")
    foreach(encodedOffset RANGE 0 "${finalOffset}" 2)
      string(SUBSTRING "${normalizedContent}" "${encodedOffset}" 2 encodedByte)
      math(EXPR decodedByte "0x${encodedByte}")
      string(ASCII "${decodedByte}" decodedCharacter)
      string(APPEND decodedContent "${decodedCharacter}")
    endforeach()
  endif()
  set(${outputVariable} "${decodedContent}" PARENT_SCOPE)
endfunction()

function(xoasContentRuleIdentities content outputVariable)
  set(ruleIdentities)
  if(content MATCHES "gh[pousr]_[A-Za-z0-9]+" OR
     content MATCHES "github_pat_[A-Za-z0-9_]+" OR
     content MATCHES "AKIA[0-9A-Z]+" OR
     content MATCHES "-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----")
    list(APPEND ruleIdentities xoas-secret-pattern)
  endif()

  string(CONCAT todoMarker "TO" "DO")
  string(CONCAT fixmeMarker "FIX" "ME")
  string(CONCAT hackMarker "HA" "CK")
  string(CONCAT xxxMarker "X" "XX")
  foreach(marker IN ITEMS
          "${todoMarker}" "${fixmeMarker}" "${hackMarker}" "${xxxMarker}")
    if(content MATCHES "(^|[^A-Za-z0-9_])${marker}([^A-Za-z0-9_]|$)")
      list(APPEND ruleIdentities xoas-unfinished-marker)
    endif()
  endforeach()
  list(REMOVE_DUPLICATES ruleIdentities)
  set(${outputVariable} "${ruleIdentities}" PARENT_SCOPE)
endfunction()

function(xoasArtifactRuleIdentity relativePath absolutePath outputVariable)
  set(ruleIdentity "")
  if(relativePath MATCHES "(^|/)(build|cmake-build[^/]*)/" OR
     relativePath MATCHES "(^|/)\.DS_Store$" OR
     relativePath MATCHES
       "\.(a|class|dll|dylib|exe|gcda|gcno|o|obj|pdb|profraw|pyc)$" OR
     relativePath MATCHES "\.so(\.[0-9]+)*$")
    set(ruleIdentity xoas-tracked-artifact)
  elseif(EXISTS "${absolutePath}" AND NOT IS_DIRECTORY "${absolutePath}")
    file(READ "${absolutePath}" filePrefix LIMIT 8 HEX)
    if(filePrefix MATCHES
       "^(7f454c46|4d5a|213c617263683e0a|0061736d|cafebabe|bebafeca|feedface|feedfacf|cefaedfe|cffaedfe)")
      set(ruleIdentity xoas-tracked-artifact)
    endif()
  endif()
  set(${outputVariable} "${ruleIdentity}" PARENT_SCOPE)
endfunction()

if(DEFINED XOAS_POLICY_FIXTURE_INPUT)
  foreach(requiredVariable
          XOAS_POLICY_FIXTURE_WORKING_DIRECTORY
          XOAS_POLICY_EXPECTED_RULE)
    if(NOT DEFINED ${requiredVariable})
      message(FATAL_ERROR "${requiredVariable} is required for fixture checks.")
    endif()
  endforeach()
  file(READ "${XOAS_POLICY_FIXTURE_INPUT}" encodedFixture)
  xoasDecodeHex("${encodedFixture}" decodedFixture)
  file(MAKE_DIRECTORY "${XOAS_POLICY_FIXTURE_WORKING_DIRECTORY}")
  set(decodedFixturePath
      "${XOAS_POLICY_FIXTURE_WORKING_DIRECTORY}/decoded-policy-input.txt")
  file(WRITE "${decodedFixturePath}" "${decodedFixture}")
  xoasContentRuleIdentities("${decodedFixture}" observedRules)
  if(DEFINED XOAS_POLICY_FIXTURE_RELATIVE_PATH)
    xoasArtifactRuleIdentity(
      "${XOAS_POLICY_FIXTURE_RELATIVE_PATH}"
      "${decodedFixturePath}"
      artifactRule)
    if(NOT artifactRule STREQUAL "")
      list(APPEND observedRules "${artifactRule}")
    endif()
  endif()
  if(NOT XOAS_POLICY_EXPECTED_RULE IN_LIST observedRules)
    message(FATAL_ERROR
            "Policy fixture did not trigger ${XOAS_POLICY_EXPECTED_RULE}; "
            "observed: ${observedRules}")
  endif()
  message(STATUS
          "Observed intended repository-policy rejection: "
          "${XOAS_POLICY_EXPECTED_RULE}")
  return()
endif()

foreach(requiredVariable
        XOAS_CLANG_FORMAT
        XOAS_GENERATED_FIXTURE
        XOAS_GENERATED_INPUT
        XOAS_GENERATOR
        XOAS_GIT
        XOAS_MARKDOWN_CHECKER
        XOAS_POLICY_WORKING_DIRECTORY
        XOAS_PYTHON
        XOAS_QUALITY_CONTRACT
        XOAS_REPOSITORY_ROOT
        XOAS_SHELLCHECK
        XOAS_VENDOR_ADJACENT_FIXTURE
        XOAS_VENDOR_FIXTURE)
  if(NOT DEFINED ${requiredVariable})
    message(FATAL_ERROR "${requiredVariable} is required.")
  endif()
endforeach()

file(MAKE_DIRECTORY "${XOAS_POLICY_WORKING_DIRECTORY}")

foreach(diffArguments IN ITEMS "diff;--check" "diff;--cached;--check")
  execute_process(
    COMMAND "${XOAS_GIT}" ${diffArguments}
    WORKING_DIRECTORY "${XOAS_REPOSITORY_ROOT}"
    RESULT_VARIABLE diffStatus
    OUTPUT_VARIABLE diffOutput
    ERROR_VARIABLE diffError)
  if(NOT diffStatus EQUAL 0)
    message(FATAL_ERROR
            "xoas-diff-check: Git whitespace validation failed:\n"
            "${diffOutput}${diffError}")
  endif()
endforeach()

execute_process(
  COMMAND "${XOAS_GIT}" ls-files
  WORKING_DIRECTORY "${XOAS_REPOSITORY_ROOT}"
  RESULT_VARIABLE trackedStatus
  OUTPUT_VARIABLE trackedOutput
  ERROR_VARIABLE trackedError
  OUTPUT_STRIP_TRAILING_WHITESPACE)
if(NOT trackedStatus EQUAL 0)
  message(FATAL_ERROR
          "xoas-source-classification: cannot enumerate tracked files: "
          "${trackedError}")
endif()
string(REPLACE "\n" ";" trackedPaths "${trackedOutput}")

file(READ "${XOAS_QUALITY_CONTRACT}" qualityContractJson)
foreach(classification IN ITEMS generated_roots vendored_roots)
  string(JSON classificationCount LENGTH "${qualityContractJson}"
         source_classifications "${classification}")
  set("${classification}Paths")
  if(classificationCount GREATER 0)
    math(EXPR finalClassificationIndex "${classificationCount} - 1")
    foreach(classificationIndex RANGE "${finalClassificationIndex}")
      string(JSON classificationPath GET "${qualityContractJson}"
             source_classifications "${classification}"
             "${classificationIndex}")
      if(IS_ABSOLUTE "${classificationPath}" OR
         classificationPath MATCHES "(^|/)\.\.(/|$)")
        message(FATAL_ERROR
                "xoas-source-classification: invalid classified root: "
                "${classificationPath}")
      endif()
      execute_process(
        COMMAND "${XOAS_GIT}" ls-files -- "${classificationPath}"
        WORKING_DIRECTORY "${XOAS_REPOSITORY_ROOT}"
        RESULT_VARIABLE classifiedStatus
        OUTPUT_VARIABLE classifiedOutput
        ERROR_VARIABLE classifiedError
        OUTPUT_STRIP_TRAILING_WHITESPACE)
      if(NOT classifiedStatus EQUAL 0 OR classifiedOutput STREQUAL "")
        message(FATAL_ERROR
                "xoas-source-classification: classified root has no tracked "
                "content: ${classificationPath}\n${classifiedError}")
      endif()
      list(APPEND "${classification}Paths" "${classificationPath}")
    endforeach()
  endif()
endforeach()

function(xoasPathHasRoot relativePath rootList outputVariable)
  set(hasRoot FALSE)
  foreach(classifiedRoot IN LISTS rootList)
    if(relativePath STREQUAL classifiedRoot OR
       relativePath MATCHES "^${classifiedRoot}/")
      set(hasRoot TRUE)
    endif()
  endforeach()
  set(${outputVariable} "${hasRoot}" PARENT_SCOPE)
endfunction()

set(approvedGeneratorInputs
    tests/quality/fixtures/generated/generate.cmake
    tests/quality/fixtures/generated/input.json)
foreach(trackedPath IN LISTS trackedPaths)
  if(trackedPath STREQUAL "")
    continue()
  endif()
  xoasArtifactRuleIdentity(
    "${trackedPath}" "${XOAS_REPOSITORY_ROOT}/${trackedPath}" artifactRule)
  if(NOT artifactRule STREQUAL "")
    message(FATAL_ERROR
            "xoas-tracked-artifact: tracked build artifact: ${trackedPath}")
  endif()

  xoasPathHasRoot("${trackedPath}" "${vendored_rootsPaths}"
                  pathIsVendored)
  if(trackedPath MATCHES "(^|/)(vendor|vendored|third_party|third-party|external)/"
     AND NOT pathIsVendored)
    message(FATAL_ERROR
            "xoas-source-classification: unapproved vendored path: "
            "${trackedPath}")
  endif()

  xoasPathHasRoot("${trackedPath}" "${generated_rootsPaths}"
                  pathIsGenerated)
  if(trackedPath MATCHES "(^|/)generated/" AND
     NOT pathIsGenerated AND
     NOT trackedPath IN_LIST approvedGeneratorInputs)
    message(FATAL_ERROR
            "xoas-source-classification: unapproved generated path: "
            "${trackedPath}")
  endif()
endforeach()

execute_process(
  COMMAND "${XOAS_GIT}" ls-files --stage
  WORKING_DIRECTORY "${XOAS_REPOSITORY_ROOT}"
  RESULT_VARIABLE stageStatus
  OUTPUT_VARIABLE stageOutput
  ERROR_VARIABLE stageError
  OUTPUT_STRIP_TRAILING_WHITESPACE)
if(NOT stageStatus EQUAL 0)
  message(FATAL_ERROR "xoas-tracked-artifact: ${stageError}")
endif()
string(REPLACE "\n" ";" stageEntries "${stageOutput}")
foreach(stageEntry IN LISTS stageEntries)
  if(stageEntry MATCHES "^100755 [0-9a-f]+ [0-9]+\t(.+)$")
    set(executablePath "${CMAKE_MATCH_1}")
    if(NOT executablePath MATCHES "\.(bash|py|sh)$")
      message(FATAL_ERROR
              "xoas-tracked-artifact: non-script executable path: "
              "${executablePath}")
    endif()
  endif()
endforeach()

set(schemaScript [=[
import json
import subprocess
import sys
from pathlib import Path

from jsonschema import Draft202012Validator


root = Path(sys.argv[1])
git = sys.argv[2]
tracked_json = subprocess.run(
    [git, "-C", str(root), "ls-files", "*.json"],
    check=True,
    capture_output=True,
    text=True,
).stdout.splitlines()
documents = {}
for relative_path in tracked_json:
    documents[relative_path] = json.loads(
        (root / relative_path).read_text(encoding="utf-8")
    )

schema_instances = {
    "schemas/branch-protection-v1.schema.json": [
        "docs/engineering/main-branch-protection-v1.json"
    ],
    "schemas/github-actions-lock-v1.schema.json": [
        "toolchains/github-actions-v1.lock.json"
    ],
    "schemas/benchmark-result-v1.schema.json": [
        "benchmarks/manifests/benchmark-result-v1.example.json"
    ],
    "schemas/development-toolchain-v1.schema.json": [
        "toolchains/gpu-2-development-toolchain-v1.lock.json"
    ],
    "schemas/quality-gates-v1.schema.json": [
        "tests/quality/contracts/expected-gates.json"
    ],
}
tracked_schemas = {
    path for path in tracked_json if path.startswith("schemas/") and path.endswith(".schema.json")
}
if tracked_schemas != set(schema_instances):
    missing = sorted(tracked_schemas.symmetric_difference(schema_instances))
    raise RuntimeError(f"unmapped repository schemas: {missing}")
for schema_path, instance_paths in schema_instances.items():
    schema = documents[schema_path]
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    for instance_path in instance_paths:
        validator.validate(documents[instance_path])
]=])
execute_process(
  COMMAND
    "${XOAS_PYTHON}" -c "${schemaScript}"
    "${XOAS_REPOSITORY_ROOT}" "${XOAS_GIT}"
  RESULT_VARIABLE schemaStatus
  OUTPUT_VARIABLE schemaOutput
  ERROR_VARIABLE schemaError)
if(NOT schemaStatus EQUAL 0)
  message(FATAL_ERROR
          "xoas-json-schema: validation failed:\n"
          "${schemaOutput}${schemaError}")
endif()

string(CONCAT privateKeyExpression
       "-----BEGIN " "([A-Z0-9 ]+ )?PRIVATE KEY-----")
string(CONCAT secretExpression
       "(AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{36,}|"
       "github_pat_[A-Za-z0-9_]{50,}|${privateKeyExpression})")
execute_process(
  COMMAND "${XOAS_GIT}" grep -n -I -E "${secretExpression}" -- .
  WORKING_DIRECTORY "${XOAS_REPOSITORY_ROOT}"
  RESULT_VARIABLE secretStatus
  OUTPUT_VARIABLE secretOutput
  ERROR_VARIABLE secretError)
if(secretStatus EQUAL 0)
  message(FATAL_ERROR
          "xoas-secret-pattern: tracked credential pattern detected:\n"
          "${secretOutput}")
elseif(NOT secretStatus EQUAL 1)
  message(FATAL_ERROR "xoas-secret-pattern: scan failed: ${secretError}")
endif()

string(CONCAT todoMarker "TO" "DO")
string(CONCAT fixmeMarker "FIX" "ME")
string(CONCAT hackMarker "HA" "CK")
string(CONCAT xxxMarker "X" "XX")
set(unfinishedExpression
    "(^|[^[:alnum:]_])(${todoMarker}|${fixmeMarker}|${hackMarker}|${xxxMarker})([^[:alnum:]_]|$)")
execute_process(
  COMMAND "${XOAS_GIT}" grep -n -I -E "${unfinishedExpression}" -- .
  WORKING_DIRECTORY "${XOAS_REPOSITORY_ROOT}"
  RESULT_VARIABLE unfinishedStatus
  OUTPUT_VARIABLE unfinishedOutput
  ERROR_VARIABLE unfinishedError)
if(unfinishedStatus EQUAL 0)
  message(FATAL_ERROR
          "xoas-unfinished-marker: prohibited marker detected:\n"
          "${unfinishedOutput}")
elseif(NOT unfinishedStatus EQUAL 1)
  message(FATAL_ERROR
          "xoas-unfinished-marker: scan failed: ${unfinishedError}")
endif()

execute_process(
  COMMAND
    "${CMAKE_COMMAND}"
    "-DXOAS_GIT=${XOAS_GIT}"
    "-DXOAS_PYTHON=${XOAS_PYTHON}"
    "-DXOAS_REPOSITORY_ROOT=${XOAS_REPOSITORY_ROOT}"
    -P "${XOAS_MARKDOWN_CHECKER}"
  RESULT_VARIABLE markdownStatus
  OUTPUT_VARIABLE markdownOutput
  ERROR_VARIABLE markdownError)
if(NOT markdownStatus EQUAL 0)
  message(FATAL_ERROR
          "xoas-markdown-link: validation failed:\n"
          "${markdownOutput}${markdownError}")
endif()

execute_process(
  COMMAND
    "${CMAKE_COMMAND}"
    "-DXOAS_GENERATED_INPUT=${XOAS_GENERATED_INPUT}"
    "-DXOAS_GENERATED_OUTPUT=${XOAS_POLICY_WORKING_DIRECTORY}/generated-one.cpp"
    -P "${XOAS_GENERATOR}"
  RESULT_VARIABLE firstGenerationStatus
  OUTPUT_VARIABLE firstGenerationOutput
  ERROR_VARIABLE firstGenerationError)
execute_process(
  COMMAND
    "${CMAKE_COMMAND}"
    "-DXOAS_GENERATED_INPUT=${XOAS_GENERATED_INPUT}"
    "-DXOAS_GENERATED_OUTPUT=${XOAS_POLICY_WORKING_DIRECTORY}/generated-two.cpp"
    -P "${XOAS_GENERATOR}"
  RESULT_VARIABLE secondGenerationStatus
  OUTPUT_VARIABLE secondGenerationOutput
  ERROR_VARIABLE secondGenerationError)
if(NOT firstGenerationStatus EQUAL 0 OR NOT secondGenerationStatus EQUAL 0)
  message(FATAL_ERROR
          "xoas-generated-determinism: generation failed:\n"
          "${firstGenerationOutput}${firstGenerationError}"
          "${secondGenerationOutput}${secondGenerationError}")
endif()
file(SHA256 "${XOAS_POLICY_WORKING_DIRECTORY}/generated-one.cpp"
     firstGeneratedSha256)
file(SHA256 "${XOAS_POLICY_WORKING_DIRECTORY}/generated-two.cpp"
     secondGeneratedSha256)
file(SHA256 "${XOAS_GENERATED_FIXTURE}" trackedGeneratedSha256)
if(NOT firstGeneratedSha256 STREQUAL secondGeneratedSha256 OR
   NOT firstGeneratedSha256 STREQUAL trackedGeneratedSha256)
  message(FATAL_ERROR
          "xoas-generated-determinism: generated bytes differ from the "
          "second run or tracked artifact.")
endif()
file(READ "${XOAS_POLICY_WORKING_DIRECTORY}/generated-one.cpp"
     generatedContent)
if(NOT generatedContent MATCHES
     "Generated by xoas-quality-fixture-generator-v1" OR
   NOT generatedContent MATCHES "DO NOT EDIT")
  message(FATAL_ERROR
          "xoas-generated-provenance: generated fixture lacks identity or "
          "do-not-edit notice.")
endif()
execute_process(
  COMMAND
    "${XOAS_CLANG_FORMAT}" --dry-run --Werror
    "${XOAS_POLICY_WORKING_DIRECTORY}/generated-one.cpp"
  RESULT_VARIABLE generatedFormatStatus
  OUTPUT_VARIABLE generatedFormatOutput
  ERROR_VARIABLE generatedFormatError)
if(NOT generatedFormatStatus EQUAL 0)
  message(FATAL_ERROR
          "xoas-generated-format: generated fixture is not formatted:\n"
          "${generatedFormatOutput}${generatedFormatError}")
endif()

execute_process(
  COMMAND "${XOAS_CLANG_FORMAT}" --dry-run --Werror "${XOAS_VENDOR_FIXTURE}"
  RESULT_VARIABLE vendorFormatStatus
  OUTPUT_QUIET
  ERROR_QUIET)
if(vendorFormatStatus EQUAL 0)
  message(FATAL_ERROR
          "xoas-vendor-isolation: vendor fixture must prove exclusion with a "
          "nonconforming input.")
endif()
execute_process(
  COMMAND
    "${XOAS_CLANG_FORMAT}" --dry-run --Werror
    "${XOAS_VENDOR_ADJACENT_FIXTURE}"
  RESULT_VARIABLE adjacentFormatStatus
  OUTPUT_VARIABLE adjacentFormatOutput
  ERROR_VARIABLE adjacentFormatError)
if(NOT adjacentFormatStatus EQUAL 0)
  message(FATAL_ERROR
          "xoas-vendor-isolation: adjacent handwritten fixture is not "
          "compliant:\n${adjacentFormatOutput}${adjacentFormatError}")
endif()

execute_process(
  COMMAND "${XOAS_GIT}" ls-files -- "*.bash" "*.bats" "*.sh"
  WORKING_DIRECTORY "${XOAS_REPOSITORY_ROOT}"
  RESULT_VARIABLE shellListStatus
  OUTPUT_VARIABLE shellOutput
  ERROR_VARIABLE shellError
  OUTPUT_STRIP_TRAILING_WHITESPACE)
if(NOT shellListStatus EQUAL 0)
  message(FATAL_ERROR "xoas-shellcheck: ${shellError}")
endif()
set(shellPaths)
if(NOT shellOutput STREQUAL "")
  string(REPLACE "\n" ";" shellPaths "${shellOutput}")
endif()
foreach(trackedPath IN LISTS trackedPaths)
  xoasPathHasRoot("${trackedPath}" "${vendored_rootsPaths}"
                  pathIsVendored)
  if(pathIsVendored OR IS_DIRECTORY "${XOAS_REPOSITORY_ROOT}/${trackedPath}")
    continue()
  endif()
  file(STRINGS
       "${XOAS_REPOSITORY_ROOT}/${trackedPath}"
       firstLine
       LIMIT_COUNT 1
       LIMIT_INPUT 256)
  if(firstLine MATCHES "^#!.*(/|env )(ba)?(da|k)?sh([ \t]|$)")
    list(APPEND shellPaths "${trackedPath}")
  endif()
endforeach()
list(REMOVE_DUPLICATES shellPaths)
if(shellPaths)
  foreach(shellPath IN LISTS shellPaths)
    execute_process(
      COMMAND
        "${XOAS_SHELLCHECK}" --external-sources --severity=style
        "${XOAS_REPOSITORY_ROOT}/${shellPath}"
      RESULT_VARIABLE shellcheckStatus
      OUTPUT_VARIABLE shellcheckOutput
      ERROR_VARIABLE shellcheckError)
    if(NOT shellcheckStatus EQUAL 0)
      message(FATAL_ERROR
              "xoas-shellcheck: ${shellPath} failed:\n"
              "${shellcheckOutput}${shellcheckError}")
    endif()
  endforeach()
endif()

message(STATUS
        "Repository policy passed; generated fixture SHA-256: "
        "${trackedGeneratedSha256}")
