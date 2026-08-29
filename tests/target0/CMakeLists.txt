add_test(
  NAME target0-qualification-probe
  COMMAND
    "${Python3_EXECUTABLE}"
    "${CMAKE_CURRENT_SOURCE_DIR}/qualification_probe_test.py"
    --probe $<TARGET_FILE:xoas-target0-qualification-probe>
    --schema
    "${PROJECT_SOURCE_DIR}/schemas/target0-host-qualification-v1.schema.json")
set_tests_properties(target0-qualification-probe PROPERTIES TIMEOUT 180)

add_test(
  NAME target0-host-tools-capture
  COMMAND
    "${Python3_EXECUTABLE}"
    "${CMAKE_CURRENT_SOURCE_DIR}/capture_host_test.py")
add_test(
  NAME target0-host-tools-session
  COMMAND
    "${Python3_EXECUTABLE}"
    "${CMAKE_CURRENT_SOURCE_DIR}/measurement_session_test.py")
set_tests_properties(
  target0-host-tools-capture
  target0-host-tools-session
  PROPERTIES TIMEOUT 30)
