cmake_minimum_required(VERSION 3.28)

foreach(requiredVariable
        XOAS_BRANCH_PROTECTION_RECORD
        XOAS_BRANCH_PROTECTION_REQUEST
        XOAS_BRANCH_PROTECTION_SCHEMA
        XOAS_PYTHON
        XOAS_QUALITY_CONTRACT)
  if(NOT DEFINED ${requiredVariable})
    message(FATAL_ERROR "${requiredVariable} is required.")
  endif()
endforeach()

set(branchProtectionCheckScript [=[
import hashlib
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator


record_path = Path(sys.argv[1])
request_path = Path(sys.argv[2])
schema_path = Path(sys.argv[3])
contract_path = Path(sys.argv[4])

record = json.loads(record_path.read_text(encoding="utf-8"))
request_bytes = request_path.read_bytes()
request = json.loads(request_bytes)
schema = json.loads(schema_path.read_text(encoding="utf-8"))
contract = json.loads(contract_path.read_text(encoding="utf-8"))

Draft202012Validator.check_schema(schema)
Draft202012Validator(schema).validate(record)

request_reference = record["protection_request"]
if request_reference["path"] != "docs/engineering/main-branch-protection-v1.request.json":
    raise RuntimeError("protection request path is not canonical")
if hashlib.sha256(request_bytes).hexdigest() != request_reference["sha256"]:
    raise RuntimeError("protection request digest differs from the evidence record")

contexts = contract["required_ci_contexts"]
required_checks = record["required_checks"]
if [check["context"] for check in required_checks] != contexts:
    raise RuntimeError("evidence record check order differs from the quality contract")
if len({check["context"] for check in required_checks}) != len(required_checks):
    raise RuntimeError("evidence record contains duplicate required checks")
if {check["app_id"] for check in required_checks} != {15368}:
    raise RuntimeError("required checks are not bound to GitHub Actions App ID 15368")

expected_request = {
    "required_status_checks": {
        "strict": True,
        "checks": required_checks,
    },
    "enforce_admins": True,
    "required_pull_request_reviews": {
        "dismiss_stale_reviews": True,
        "require_code_owner_reviews": False,
        "required_approving_review_count": 0,
        "require_last_push_approval": False,
    },
    "restrictions": None,
    "required_linear_history": True,
    "allow_force_pushes": False,
    "allow_deletions": False,
    "block_creations": False,
    "required_conversation_resolution": True,
    "lock_branch": False,
    "allow_fork_syncing": False,
}
if request != expected_request:
    raise RuntimeError("protection request differs from the closed desired state")

jobs = record["hosted_verification"]["jobs"]
if [job["name"] for job in jobs] != contexts:
    raise RuntimeError("hosted job order differs from the quality contract")
if len({job["name"] for job in jobs}) != len(jobs):
    raise RuntimeError("hosted verification contains duplicate job names")
if any(job["conclusion"] != "success" for job in jobs):
    raise RuntimeError("hosted verification includes a non-successful job")
if any(job["provider_app_id"] != 15368 for job in jobs):
    raise RuntimeError("hosted verification provider differs from the required app")

subject = record["pre_state"]["captured_subject_commit"]
if record["hosted_verification"]["subject_commit"] != subject:
    raise RuntimeError("pre-state and hosted verification commits differ")
application = record["application"]
if application["state"] == "applied":
    if application["protection_subject_commit"] != subject:
        raise RuntimeError("applied protection subject differs from the captured commit")
]=])

execute_process(
  COMMAND
    "${XOAS_PYTHON}" -c "${branchProtectionCheckScript}"
    "${XOAS_BRANCH_PROTECTION_RECORD}"
    "${XOAS_BRANCH_PROTECTION_REQUEST}"
    "${XOAS_BRANCH_PROTECTION_SCHEMA}"
    "${XOAS_QUALITY_CONTRACT}"
  RESULT_VARIABLE protectionStatus
  OUTPUT_VARIABLE protectionOutput
  ERROR_VARIABLE protectionError)
if(NOT protectionStatus EQUAL 0)
  message(FATAL_ERROR
          "Branch-protection record validation failed:\n"
          "${protectionOutput}${protectionError}")
endif()
