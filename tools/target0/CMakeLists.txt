add_executable(
  xoas-target0-qualification-probe
  qualification_probe.cpp)
target_link_libraries(
  xoas-target0-qualification-probe
  PRIVATE xoas_sanitizers xoas_warnings)

add_dependencies(warnings xoas-target0-qualification-probe)
add_dependencies(tidy xoas-target0-qualification-probe)
