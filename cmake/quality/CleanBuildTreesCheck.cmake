cmake_minimum_required(VERSION 3.28)

foreach(requiredVariable
        XOAS_CLEANUP_SCRIPT
        XOAS_CLEANUP_TEST_WORKING_DIRECTORY)
  if(NOT DEFINED ${requiredVariable})
    message(FATAL_ERROR "${requiredVariable} is required.")
  endif()
endforeach()
if(XOAS_CLEANUP_TEST_WORKING_DIRECTORY STREQUAL "/" OR
   NOT XOAS_CLEANUP_TEST_WORKING_DIRECTORY MATCHES "/build/")
  message(FATAL_ERROR "Refusing an unsafe cleanup-test working directory.")
endif()

file(REMOVE_RECURSE "${XOAS_CLEANUP_TEST_WORKING_DIRECTORY}")
set(syntheticRoot
    "${XOAS_CLEANUP_TEST_WORKING_DIRECTORY}/repository")
file(MAKE_DIRECTORY "${syntheticRoot}/build/preserved")
file(WRITE "${syntheticRoot}/CMakePresets.json" "{}\n")
file(WRITE "${syntheticRoot}/build/preserved/evidence.txt" "preserved\n")
foreach(buildTree IN ITEMS dev-debug dev-release asan-ubsan)
  file(MAKE_DIRECTORY "${syntheticRoot}/build/${buildTree}")
  file(WRITE "${syntheticRoot}/build/${buildTree}/artifact.txt" "remove\n")
endforeach()

execute_process(
  COMMAND
    "${CMAKE_COMMAND}"
    "-DXOAS_REPOSITORY_ROOT=${syntheticRoot}"
    -P "${XOAS_CLEANUP_SCRIPT}"
  RESULT_VARIABLE cleanupStatus
  OUTPUT_VARIABLE cleanupOutput
  ERROR_VARIABLE cleanupError)
if(NOT cleanupStatus EQUAL 0)
  message(FATAL_ERROR
          "Bounded cleanup fixture failed:\n${cleanupOutput}${cleanupError}")
endif()
foreach(buildTree IN ITEMS dev-debug dev-release asan-ubsan)
  if(EXISTS "${syntheticRoot}/build/${buildTree}")
    message(FATAL_ERROR "Cleanup left an allowed build tree: ${buildTree}")
  endif()
endforeach()
if(NOT EXISTS "${syntheticRoot}/build/preserved/evidence.txt")
  message(FATAL_ERROR "Cleanup removed content outside its exact boundary.")
endif()

set(redirectTarget
    "${XOAS_CLEANUP_TEST_WORKING_DIRECTORY}/redirect-target")
file(MAKE_DIRECTORY "${redirectTarget}")
file(WRITE "${redirectTarget}/evidence.txt" "must survive\n")
file(CREATE_LINK
     "${redirectTarget}"
     "${syntheticRoot}/build/dev-debug"
     SYMBOLIC
     RESULT linkStatus)
if(NOT linkStatus STREQUAL "0")
  message(FATAL_ERROR "Unable to create cleanup redirection fixture: ${linkStatus}")
endif()

execute_process(
  COMMAND
    "${CMAKE_COMMAND}"
    "-DXOAS_REPOSITORY_ROOT=${syntheticRoot}"
    -P "${XOAS_CLEANUP_SCRIPT}"
  RESULT_VARIABLE redirectedStatus
  OUTPUT_VARIABLE redirectedOutput
  ERROR_VARIABLE redirectedError)
string(CONCAT redirectedDiagnostics "${redirectedOutput}" "${redirectedError}")
if(redirectedStatus EQUAL 0 OR
   NOT redirectedDiagnostics MATCHES "redirected build path")
  message(FATAL_ERROR
          "Cleanup did not reject the redirected path for the intended reason:\n"
          "${redirectedDiagnostics}")
endif()
if(NOT EXISTS "${redirectTarget}/evidence.txt")
  message(FATAL_ERROR "Redirected cleanup modified the link target.")
endif()
