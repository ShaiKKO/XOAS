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

add_test(
  NAME target0-qualification-campaign-statistics
  COMMAND
    "${Python3_EXECUTABLE}"
    "${CMAKE_CURRENT_SOURCE_DIR}/qualification_campaign_test.py"
    -k QualificationCampaignStatisticsTest)
add_test(
  NAME target0-qualification-campaign-pmu
  COMMAND
    "${Python3_EXECUTABLE}"
    "${CMAKE_CURRENT_SOURCE_DIR}/qualification_campaign_test.py"
    -k QualificationCampaignPerfTest)
add_test(
  NAME target0-qualification-campaign-process
  COMMAND
    "${Python3_EXECUTABLE}"
    "${CMAKE_CURRENT_SOURCE_DIR}/qualification_campaign_test.py"
    -k QualificationCampaignProcessTest)
add_test(
  NAME target0-qualification-campaign-verifier-cli
  COMMAND
    "${Python3_EXECUTABLE}"
    "${CMAKE_CURRENT_SOURCE_DIR}/qualification_campaign_test.py"
    -k QualificationCampaignVerifierCliTest)
add_test(
  NAME target0-qualification-campaign-records
  COMMAND
    "${Python3_EXECUTABLE}"
    "${CMAKE_CURRENT_SOURCE_DIR}/qualification_campaign_test.py"
    -k QualificationCampaignRecordTest)
add_test(
  NAME target0-qualification-campaign-schema
  COMMAND
    "${Python3_EXECUTABLE}"
    "${CMAKE_CURRENT_SOURCE_DIR}/qualification_campaign_test.py"
    -k QualificationCampaignSchemaTest)
add_test(
  NAME target0-qualification-campaign-identity
  COMMAND
    "${Python3_EXECUTABLE}"
    "${CMAKE_CURRENT_SOURCE_DIR}/qualification_campaign_runner_test.py"
    -k QualificationCampaignIdentityTest)
add_test(
  NAME target0-qualification-campaign-preflight
  COMMAND
    "${Python3_EXECUTABLE}"
    "${CMAKE_CURRENT_SOURCE_DIR}/qualification_campaign_runner_test.py"
    -k QualificationCampaignPreflightTest)
add_test(
  NAME target0-qualification-campaign-primary
  COMMAND
    "${Python3_EXECUTABLE}"
    "${CMAKE_CURRENT_SOURCE_DIR}/qualification_campaign_runner_test.py"
    -k QualificationCampaignPrimaryProcessTest)
add_test(
  NAME target0-qualification-campaign-sessions
  COMMAND
    "${Python3_EXECUTABLE}"
    "${CMAKE_CURRENT_SOURCE_DIR}/qualification_campaign_runner_test.py"
    -k QualificationCampaignSessionTest)
add_test(
  NAME target0-qualification-campaign-thermal
  COMMAND
    "${Python3_EXECUTABLE}"
    "${CMAKE_CURRENT_SOURCE_DIR}/qualification_campaign_runner_test.py"
    -k QualificationCampaignThermalTest)

add_test(
  NAME target0-qualification-bundle-schema
  COMMAND
    "${Python3_EXECUTABLE}"
    "${CMAKE_CURRENT_SOURCE_DIR}/prepare_qualification_bundle_test.py"
    --schema
    "${PROJECT_SOURCE_DIR}/schemas/target0-qualification-tool-bundle-v1.schema.json"
    --example
    "${CMAKE_CURRENT_SOURCE_DIR}/fixtures/qualification-tool-bundle-v1.example.json"
    -k PrepareQualificationBundleSchemaTest)
add_test(
  NAME target0-qualification-bundle-preflight
  COMMAND
    "${Python3_EXECUTABLE}"
    "${CMAKE_CURRENT_SOURCE_DIR}/prepare_qualification_bundle_test.py"
    --schema
    "${PROJECT_SOURCE_DIR}/schemas/target0-qualification-tool-bundle-v1.schema.json"
    --example
    "${CMAKE_CURRENT_SOURCE_DIR}/fixtures/qualification-tool-bundle-v1.example.json"
    -k PrepareQualificationBundlePreflightTest)
add_test(
  NAME target0-qualification-bundle-build
  COMMAND
    "${Python3_EXECUTABLE}"
    "${CMAKE_CURRENT_SOURCE_DIR}/prepare_qualification_bundle_test.py"
    --schema
    "${PROJECT_SOURCE_DIR}/schemas/target0-qualification-tool-bundle-v1.schema.json"
    --example
    "${CMAKE_CURRENT_SOURCE_DIR}/fixtures/qualification-tool-bundle-v1.example.json"
    --cmake-cache
    "${PROJECT_BINARY_DIR}/CMakeCache.txt"
    --compile-commands
    "${PROJECT_BINARY_DIR}/compile_commands.json"
    --cmake-presets
    "${PROJECT_SOURCE_DIR}/CMakePresets.json"
    --warning-module
    "${PROJECT_SOURCE_DIR}/cmake/quality/XoasWarnings.cmake"
    -k PrepareQualificationBundleBuildTest)
add_test(
  NAME target0-qualification-bundle-inspection
  COMMAND
    "${Python3_EXECUTABLE}"
    "${CMAKE_CURRENT_SOURCE_DIR}/prepare_qualification_bundle_test.py"
    --schema
    "${PROJECT_SOURCE_DIR}/schemas/target0-qualification-tool-bundle-v1.schema.json"
    --example
    "${CMAKE_CURRENT_SOURCE_DIR}/fixtures/qualification-tool-bundle-v1.example.json"
    -k PrepareQualificationBundleInspectionTest)
add_test(
  NAME target0-qualification-bundle-finalization
  COMMAND
    "${Python3_EXECUTABLE}"
    "${CMAKE_CURRENT_SOURCE_DIR}/prepare_qualification_bundle_test.py"
    --schema
    "${PROJECT_SOURCE_DIR}/schemas/target0-qualification-tool-bundle-v1.schema.json"
    --example
    "${CMAKE_CURRENT_SOURCE_DIR}/fixtures/qualification-tool-bundle-v1.example.json"
    -k PrepareQualificationBundleFinalizationTest)
set_tests_properties(
  target0-host-tools-capture
  target0-host-tools-session
  target0-qualification-campaign-pmu
  target0-qualification-campaign-identity
  target0-qualification-campaign-preflight
  target0-qualification-campaign-process
  target0-qualification-campaign-records
  target0-qualification-campaign-schema
  target0-qualification-campaign-sessions
  target0-qualification-campaign-statistics
  target0-qualification-campaign-thermal
  target0-qualification-campaign-verifier-cli
  target0-qualification-bundle-build
  target0-qualification-bundle-finalization
  target0-qualification-bundle-inspection
  target0-qualification-bundle-preflight
  target0-qualification-bundle-schema
  PROPERTIES TIMEOUT 60)

set_tests_properties(
  target0-qualification-campaign-primary
  PROPERTIES TIMEOUT 180)
