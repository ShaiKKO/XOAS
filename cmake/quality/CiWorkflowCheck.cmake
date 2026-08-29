cmake_minimum_required(VERSION 3.28)

foreach(requiredVariable
        XOAS_ACTION_LOCK
        XOAS_ACTION_LOCK_SCHEMA
        XOAS_PYTHON
        XOAS_QUALITY_CONTRACT
        XOAS_WORKFLOW)
  if(NOT DEFINED ${requiredVariable})
    message(FATAL_ERROR "${requiredVariable} is required.")
  endif()
endforeach()

set(workflowCheckScript [=[
import json
import re
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator


workflow_path = Path(sys.argv[1])
lock_path = Path(sys.argv[2])
schema_path = Path(sys.argv[3])
contract_path = Path(sys.argv[4])

schema = json.loads(schema_path.read_text(encoding="utf-8"))
lock = json.loads(lock_path.read_text(encoding="utf-8"))
contract = json.loads(contract_path.read_text(encoding="utf-8"))
Draft202012Validator.check_schema(schema)
Draft202012Validator(schema).validate(lock)

workflow_text = workflow_path.read_text(encoding="utf-8")
workflow = yaml.safe_load(workflow_text)
if not isinstance(workflow, dict):
    raise RuntimeError("workflow root must be a mapping")
if workflow.get("name") != "quality":
    raise RuntimeError("workflow name must be 'quality'")
if workflow.get("permissions") != {"contents": "read"}:
    raise RuntimeError("workflow permissions must be exactly contents: read")
if workflow.get("concurrency") != {
    "group": "${{ github.workflow }}-${{ github.ref }}",
    "cancel-in-progress": True,
}:
    raise RuntimeError("workflow concurrency policy is not exact")
if workflow.get("defaults", {}).get("run", {}).get("shell") != "bash":
    raise RuntimeError("workflow run shell must be Bash")
if "${{ secrets." in workflow_text:
    raise RuntimeError("workflow must not reference repository secrets")

triggers = workflow.get("on", workflow.get(True))
if not isinstance(triggers, dict) or set(triggers) != {"push", "pull_request"}:
    raise RuntimeError("workflow must trigger only on push and pull_request")
for trigger_name in ("push", "pull_request"):
    if triggers[trigger_name] != {"branches": ["main"]}:
        raise RuntimeError(f"{trigger_name} must target only main")

required_contexts = contract["required_ci_contexts"]
if lock["required_contexts"] != required_contexts:
    raise RuntimeError("action lock and quality contract contexts differ")
if lock["toolchain_lock_id"] != contract["toolchain_lock_id"]:
    raise RuntimeError("action lock and quality contract toolchain IDs differ")

jobs = workflow.get("jobs")
if not isinstance(jobs, dict) or len(jobs) != 5:
    raise RuntimeError("workflow must define exactly five jobs")
observed_contexts = sorted(job.get("name", "") for job in jobs.values())
if observed_contexts != sorted(required_contexts):
    raise RuntimeError(
        f"workflow contexts differ: expected {required_contexts}, observed {observed_contexts}"
    )

locked_actions = {
    (action["repository"], action["commit_sha"]): action for action in lock["actions"]
}
observed_actions = []
for job_id, job in jobs.items():
    if job.get("runs-on") != lock["runner_label"]:
        raise RuntimeError(f"{job_id}: runner label is not locked")
    if job.get("timeout-minutes") != 20:
        raise RuntimeError(f"{job_id}: timeout must be 20 minutes")
    steps = job.get("steps")
    if not isinstance(steps, list) or not steps:
        raise RuntimeError(f"{job_id}: steps are missing")
    for step in steps:
        if "uses" in step:
            match = re.fullmatch(
                r"([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)@([0-9a-f]{40})",
                step["uses"],
            )
            if not match:
                raise RuntimeError(f'{job_id}: action is not SHA-pinned: {step["uses"]}')
            action_identity = (match.group(1), match.group(2))
            if action_identity not in locked_actions:
                raise RuntimeError(f"{job_id}: action is absent from the lock")
            observed_actions.append(action_identity)
            if action_identity[0] == "actions/checkout":
                if step.get("with", {}).get("persist-credentials") is not False:
                    raise RuntimeError(f"{job_id}: checkout credentials must not persist")
        if "run" in step:
            first_line = step["run"].splitlines()[0].strip()
            if first_line != "set -euo pipefail":
                raise RuntimeError(f"{job_id}: run step is not explicitly fail-fast")

if set(observed_actions) != set(locked_actions):
    raise RuntimeError("workflow does not consume every and only locked action")
if len(observed_actions) != len(jobs):
    raise RuntimeError("each job must use checkout exactly once")
]=])

execute_process(
  COMMAND
    "${XOAS_PYTHON}" -c "${workflowCheckScript}"
    "${XOAS_WORKFLOW}" "${XOAS_ACTION_LOCK}"
    "${XOAS_ACTION_LOCK_SCHEMA}" "${XOAS_QUALITY_CONTRACT}"
  RESULT_VARIABLE workflowStatus
  OUTPUT_VARIABLE workflowOutput
  ERROR_VARIABLE workflowError)
if(NOT workflowStatus EQUAL 0)
  message(FATAL_ERROR
          "Hosted workflow validation failed:\n"
          "${workflowOutput}${workflowError}")
endif()
