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

function(xoasServerCoordinateExpression outputVariable)
  set(ipv4Octet "[0-9][0-9]?[0-9]?")
  string(CONCAT serverCoordinateExpression
         "\"" "${ipv4Octet}\\." "${ipv4Octet}\\."
         "${ipv4Octet}\\." "${ipv4Octet}" "\"")
  set(${outputVariable} "${serverCoordinateExpression}" PARENT_SCOPE)
endfunction()

function(xoasContentRuleIdentities content outputVariable)
  set(ruleIdentities)
  if(content MATCHES "gh[pousr]_[A-Za-z0-9]+" OR
     content MATCHES "github_pat_[A-Za-z0-9_]+" OR
     content MATCHES "AKIA[0-9A-Z]+" OR
     content MATCHES "-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----")
    list(APPEND ruleIdentities xoas-secret-pattern)
  endif()

  xoasServerCoordinateExpression(serverCoordinateExpression)
  if(content MATCHES "${serverCoordinateExpression}")
    list(APPEND ruleIdentities xoas-server-coordinate)
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
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

from jsonschema import Draft202012Validator


root = Path(sys.argv[1])
git = sys.argv[2]
tracked_paths = set(subprocess.run(
    [git, "-C", str(root), "ls-files"],
    check=True,
    capture_output=True,
    text=True,
).stdout.splitlines())
tracked_json = sorted(
    path for path in tracked_paths if path.endswith(".json")
)
documents = {}
for relative_path in tracked_json:
    documents[relative_path] = json.loads(
        (root / relative_path).read_text(encoding="utf-8")
    )

deployment_receipt_path = (
    "benchmarks/evidence/target0-amd-ryzen9-7900x-v1/"
    "qualification-tools-v1.json"
)
deployment_digest_path = (
    "benchmarks/evidence/target0-amd-ryzen9-7900x-v1/"
    "qualification-tools-v1.sha256"
)
target0_manifest_path = (
    "benchmarks/manifests/target0-amd-ryzen9-7900x-v1.json"
)
for required_path in (
    deployment_receipt_path,
    deployment_digest_path,
    target0_manifest_path,
):
    if required_path not in tracked_paths:
        raise RuntimeError(
            f"required Target 0 deployment evidence is not tracked: {required_path}"
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
    "schemas/target0-toolchain-lock-v1.schema.json": [
        "toolchains/target0-amd-ryzen9-7900x-v1.lock.json"
    ],
    "schemas/quality-gates-v1.schema.json": [
        "tests/quality/contracts/expected-gates.json"
    ],
    "schemas/target0-host-qualification-v1.schema.json": [],
    "schemas/target0-qualification-tool-bundle-v1.schema.json": [
        deployment_receipt_path,
        "tests/target0/fixtures/qualification-tool-bundle-v1.example.json"
    ],
}
runtime_validated_schemas = {
    "schemas/target0-host-qualification-v1.schema.json":
        "target0-qualification-probe",
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
    if not instance_paths and schema_path not in runtime_validated_schemas:
        raise RuntimeError(f"schema has no validation instance: {schema_path}")
    validator = Draft202012Validator(schema)
    for instance_path in instance_paths:
        validator.validate(documents[instance_path])

deployment_receipt = documents[deployment_receipt_path]
deployment_receipt_bytes = (root / deployment_receipt_path).read_bytes()
canonical_receipt_bytes = (
    json.dumps(
        deployment_receipt,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ) + "\n"
).encode("utf-8")
if deployment_receipt_bytes != canonical_receipt_bytes:
    raise RuntimeError("Target 0 deployment receipt is not canonical JSON")

digest_lines = (root / deployment_digest_path).read_text(
    encoding="utf-8"
).splitlines()
if len(digest_lines) != 5:
    raise RuntimeError("Target 0 deployment digest record has the wrong shape")
receipt_digest_fields = digest_lines[0].split("  ", maxsplit=1)
if receipt_digest_fields != [
    hashlib.sha256(deployment_receipt_bytes).hexdigest(),
    "qualification-tools-v1.json",
]:
    raise RuntimeError("Target 0 deployment receipt digest differs")
digest_annotations = {}
for line in digest_lines[1:]:
    if not line.startswith("# ") or "=" not in line:
        raise RuntimeError("Target 0 deployment digest annotation is malformed")
    name, value = line.removeprefix("# ").split("=", maxsplit=1)
    if name in digest_annotations or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise RuntimeError("Target 0 deployment digest annotation is invalid")
    digest_annotations[name] = value
if set(digest_annotations) != {
    "executable_identity_sha256",
    "executable_sha256",
    "inventory_sha256",
    "physical_boot_id_sha256",
}:
    raise RuntimeError("Target 0 deployment digest annotations differ")

target0_manifest = documents[target0_manifest_path]
deployment = target0_manifest["qualification"].get("tool_deployment")
required_deployment_fields = {
    "bundle_id",
    "bundle_manifest_sha256",
    "campaign_executed",
    "compatibility_test_count",
    "compatibility_tests_passed",
    "compiler_sha256",
    "development_replica_verification",
    "dual_build_identical",
    "evidence_path",
    "evidence_sha256",
    "executable_identity_sha256",
    "executable_sha256",
    "external_storage",
    "host_control_mutation",
    "implementation_commit",
    "implementation_tree",
    "inventory_sha256",
    "linker_sha256",
    "performance_claim",
    "physical_boot_id_sha256",
    "physical_verification",
    "provisioning_configuration_sha256",
    "qualification_claim",
    "reboot_executed",
    "replica_digest_match",
    "source_count",
    "state",
}
if not isinstance(deployment, dict) or set(deployment) != required_deployment_fields:
    raise RuntimeError("Target 0 deployment manifest record is not closed")
receipt_digest = hashlib.sha256(deployment_receipt_bytes).hexdigest()
expected_deployment_bindings = {
    "bundle_id": deployment_receipt["bundle_id"],
    "bundle_manifest_sha256": receipt_digest,
    "evidence_path": deployment_receipt_path,
    "evidence_sha256": receipt_digest,
    "executable_identity_sha256": digest_annotations[
        "executable_identity_sha256"
    ],
    "executable_sha256": deployment_receipt["build"]["executable_sha256"],
    "implementation_commit": deployment_receipt["repository"]["actual_commit"],
    "implementation_tree": deployment_receipt["repository"]["tree"],
    "inventory_sha256": digest_annotations["inventory_sha256"],
    "compiler_sha256": deployment_receipt["toolchain"]["compiler"]["sha256"],
    "linker_sha256": deployment_receipt["toolchain"]["linker"]["sha256"],
    "physical_boot_id_sha256": digest_annotations["physical_boot_id_sha256"],
    "provisioning_configuration_sha256": deployment_receipt[
        "provisioning_lock"
    ]["configuration_sha256"],
    "source_count": len(deployment_receipt["sources"]),
}
for field, expected_value in expected_deployment_bindings.items():
    if deployment[field] != expected_value:
        raise RuntimeError(f"Target 0 deployment {field} differs")
if deployment["executable_sha256"] != digest_annotations["executable_sha256"]:
    raise RuntimeError("Target 0 deployment executable digest record differs")
compatibility_tests = deployment_receipt["compatibility_tests"]
if (
    deployment["state"] != "passed"
    or deployment["dual_build_identical"] is not True
    or deployment_receipt["build"]["identical"] is not True
    or deployment["compatibility_test_count"] != len(compatibility_tests)
    or deployment["compatibility_tests_passed"] is not True
    or any(
        test["status"] != "passed" or test["exit_status"] != 0
        for test in compatibility_tests
    )
    or deployment["physical_verification"] != "passed"
    or deployment["development_replica_verification"] != "passed"
    or deployment["replica_digest_match"] is not True
    or deployment["external_storage"] != {
        "development": "external_private_evidence_root",
        "physical": "external_private_evidence_root",
    }
):
    raise RuntimeError("Target 0 deployment verification state differs")
for forbidden_claim in (
    "campaign_executed",
    "host_control_mutation",
    "performance_claim",
    "qualification_claim",
    "reboot_executed",
):
    if deployment[forbidden_claim] is not False:
        raise RuntimeError(
            f"Target 0 deployment improperly changes {forbidden_claim}"
        )
if (
    target0_manifest["status"] != "candidate_unqualified"
    or target0_manifest["target0_measurement_qualified"] is not False
    or target0_manifest["performance_claim"] is not False
    or target0_manifest["qualification"]["gate_decision"] != "open"
    or target0_manifest["qualification"]["campaigns"] != []
):
    raise RuntimeError("Target 0 deployment changed qualification authority")
deployment_gates = [
    gate for gate in target0_manifest["qualification"]["required_gates"]
    if gate["id"] == "qualification_tool_deployment"
]
if (
    len(deployment_gates) != 1
    or deployment_gates[0]["state"] != "passed"
    or deployment_gates[0]["evidence"] != deployment_receipt_path
):
    raise RuntimeError("Target 0 deployment gate evidence differs")
baseline_admission_gates = [
    gate for gate in target0_manifest["qualification"]["required_gates"]
    if gate["id"] == "baseline_numerical_admission"
]
if len(baseline_admission_gates) != 1 or baseline_admission_gates[0]["state"] != "pending":
    raise RuntimeError("Target 0 baseline numerical-admission dependency changed")

target0_lock = documents["toolchains/target0-amd-ryzen9-7900x-v1.lock.json"]
prestate = target0_lock["apt"]["prestate"]
packages = prestate["packages"]
if prestate["package_count"] != len(packages):
    raise RuntimeError("Target 0 package pre-state count does not match its array")
package_pairs = [(item["name"], item["version"]) for item in packages]
if package_pairs != sorted(package_pairs):
    raise RuntimeError("Target 0 package pre-state is not canonically sorted")
if len({item["name"] for item in packages}) != len(packages):
    raise RuntimeError("Target 0 package pre-state contains duplicate names")
package_bytes = "".join(
    f"{item['name']}\t{item['version']}\n" for item in packages
).encode("utf-8")
if hashlib.sha256(package_bytes).hexdigest() != prestate["packages_sha256"]:
    raise RuntimeError("Target 0 package pre-state digest does not match its array")
holds_bytes = "".join(f"{item}\n" for item in prestate["holds"]).encode("utf-8")
if hashlib.sha256(holds_bytes).hexdigest() != prestate["holds_sha256"]:
    raise RuntimeError("Target 0 package-hold digest does not match its array")
requested_names = {
    item["name"] for item in target0_lock["apt"]["requested_packages"]
}
expected_requested_names = {
    "build-essential",
    "doxygen",
    "gfortran",
    "graphviz",
    "hwloc",
    "libnuma-dev",
    "lm-sensors",
    "pkg-config",
    "shellcheck",
}
if requested_names != expected_requested_names:
    raise RuntimeError("Target 0 requested support-package set differs")
source_ids = {item["id"] for item in target0_lock["source_locks"]}
expected_source_ids = {
    "aocl-blas-5.3.2",
    "aocl-integration-5.3.2",
    "jitspmm-inspection",
    "libxsmm-2.1.0",
    "openblas-0.3.34",
}
if source_ids != expected_source_ids:
    raise RuntimeError("Target 0 source-lock set differs")
jitspmm = next(
    item for item in target0_lock["source_locks"]
    if item["id"] == "jitspmm-inspection"
)
if jitspmm["license"] != {
    "status": "missing_at_pinned_revision",
    "path": None,
    "sha256": None,
    "use_authorized": False,
}:
    raise RuntimeError("JITSpMM missing-license boundary changed")

if target0_lock["state"] == "installed_verified":
    expected_source_states = {
        "aocl-blas-5.3.2": "installed_verified",
        "aocl-integration-5.3.2": "identity_only",
        "jitspmm-inspection": "source_identity_pinned_adapter_deferred_M2",
        "libxsmm-2.1.0": "installed_verified",
        "openblas-0.3.34": "installed_verified",
    }
    source_states = {
        item["id"]: item["state"] for item in target0_lock["source_locks"]
    }
    if source_states != expected_source_states:
        raise RuntimeError("Target 0 installed source states differ")

    package_closure = target0_lock["installed_package_closure"]
    if len(package_closure) != 26:
        raise RuntimeError("Target 0 installed package closure must contain 26 entries")
    closure_names = [item["name"] for item in package_closure]
    if closure_names != sorted(closure_names):
        raise RuntimeError("Target 0 installed package closure is not sorted")
    if len(set(closure_names)) != len(closure_names):
        raise RuntimeError("Target 0 installed package closure contains duplicates")
    if any(item["package_file_status"] != "passed" for item in package_closure):
        raise RuntimeError("Target 0 installed package closure has failed file checks")

    installed_files = target0_lock["installed_files"]
    if len(installed_files) != 288:
        raise RuntimeError("Target 0 installed-file inventory must contain 288 entries")
    installed_paths = [item["path"] for item in installed_files]
    if installed_paths != sorted(installed_paths):
        raise RuntimeError("Target 0 installed-file inventory is not sorted")
    if len(set(installed_paths)) != len(installed_paths):
        raise RuntimeError("Target 0 installed-file inventory contains duplicates")
    required_artifacts = {
        "/opt/xoas/target0-v1/aocl-blas-5.3.2/lib/libblis.so.5.3.2":
            "0670e0fcb11ddfd39304761aae957f78d1ed48c9bde0ea3dc8254febf2ce1381",
        "/opt/xoas/target0-v1/libxsmm-2.1.0/lib/libxsmm.so.2.1.0":
            "63e8fd17a5d5a759f5ee2058cf209e855aceff2857b14fbaa608bfdb95a92625",
        "/opt/xoas/target0-v1/openblas-0.3.34/lib/libopenblas.so.0.3":
            "8a2ab96cad5195422d4880eb42afcfb57d06a036a9178c3ea5b8bc3de06297c8",
    }
    installed_digests = {
        item["path"]: item["sha256"] for item in installed_files
    }
    for artifact_path, artifact_digest in required_artifacts.items():
        if installed_digests.get(artifact_path) != artifact_digest:
            raise RuntimeError(
                f"Target 0 primary baseline artifact changed: {artifact_path}"
            )

    libxsmm = next(
        item for item in target0_lock["source_locks"]
        if item["id"] == "libxsmm-2.1.0"
    )
    for command in libxsmm["build_commands"] + libxsmm["test_commands"]:
        if "PREFIX=/opt/xoas/target0-v1/libxsmm-2.1.0" not in command:
            raise RuntimeError("LIBXSMM test/build command lacks the installed prefix")

    validation_states = {
        item["name"]: item["status"] for item in target0_lock["validations"]
    }
    required_passed_validations = {
        "aocl_blas_upstream_tests",
        "baseline_smoke_probes",
        "compiler_identity_preservation",
        "installed_file_inventory",
        "library_coexistence",
        "libxsmm_prefix_correction",
        "libxsmm_upstream_tests",
        "openblas_upstream_tests",
        "package_file_verification",
        "pkg_config_prefixes",
        "single_thread_behavior",
        "support_package_installation",
        "task4_evidence_bundle",
        "toolchain_lock_schema",
    }
    if any(
        validation_states.get(name) != "passed"
        for name in required_passed_validations
    ):
        raise RuntimeError("Target 0 required provisioning validation is not passed")

    if target0_lock["baseline_stack_verified"] is not True:
        raise RuntimeError("Target 0 installed stack is not marked verified")
    if target0_lock["target0_measurement_qualified"] is not False:
        raise RuntimeError("Target 0 was qualified during provisioning")
    if target0_lock["performance_claim"] is not False:
        raise RuntimeError("Target 0 provisioning contains a performance claim")

    digest_document = dict(target0_lock)
    configuration_digest = digest_document.pop("configuration_sha256", None)
    configuration_bytes = json.dumps(
        digest_document, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    if hashlib.sha256(configuration_bytes).hexdigest() != configuration_digest:
        raise RuntimeError("Target 0 configuration digest does not match its lock")
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

xoasServerCoordinateExpression(serverCoordinateExpression)
execute_process(
  COMMAND "${XOAS_GIT}" grep -n -I -E "${serverCoordinateExpression}" -- .
  WORKING_DIRECTORY "${XOAS_REPOSITORY_ROOT}"
  RESULT_VARIABLE serverCoordinateStatus
  OUTPUT_VARIABLE serverCoordinateOutput
  ERROR_VARIABLE serverCoordinateError)
if(serverCoordinateStatus EQUAL 0)
  message(FATAL_ERROR
          "xoas-server-coordinate: tracked server coordinate detected:\n"
          "${serverCoordinateOutput}")
elseif(NOT serverCoordinateStatus EQUAL 1)
  message(FATAL_ERROR
          "xoas-server-coordinate: scan failed: ${serverCoordinateError}")
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
