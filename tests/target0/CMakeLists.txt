add_test(
  NAME target0-qualification-probe
  COMMAND
    "${Python3_EXECUTABLE}"
    "${CMAKE_CURRENT_SOURCE_DIR}/qualification_probe_test.py"
    --probe $<TARGET_FILE:xoas-target0-qualification-probe>
    --schema
    "${PROJECT_SOURCE_DIR}/schemas/target0-host-qualification-v1.schema.json")
set_tests_properties(target0-qualification-probe PROPERTIES TIMEOUT 180)
