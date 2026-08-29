add_executable(
  xoas-target0-qualification-probe
  qualification_probe.cpp)
target_link_libraries(
  xoas-target0-qualification-probe
  PRIVATE xoas_sanitizers xoas_warnings)

add_dependencies(warnings xoas-target0-qualification-probe)
add_dependencies(tidy xoas-target0-qualification-probe)

add_custom_target(
  target0-host-tools
  COMMAND
    "${CMAKE_COMMAND}" -E env
    "PYTHONPYCACHEPREFIX=${CMAKE_CURRENT_BINARY_DIR}/python-cache"
    "${Python3_EXECUTABLE}" -m py_compile
    "${CMAKE_CURRENT_SOURCE_DIR}/capture_host.py"
    "${CMAKE_CURRENT_SOURCE_DIR}/prepare_qualification_bundle.py"
  COMMAND
    "${XOAS_SHELLCHECK_EXECUTABLE}"
    "${CMAKE_CURRENT_SOURCE_DIR}/measurement_session.sh"
  COMMENT "Checking Target 0 host qualification tools"
  VERBATIM)

add_dependencies(repository-policy target0-host-tools)
add_dependencies(quality target0-host-tools)
