cmake_minimum_required(VERSION 3.28)

if(NOT DEFINED XOAS_REPOSITORY_ROOT)
  message(FATAL_ERROR "XOAS_REPOSITORY_ROOT is required.")
endif()
file(REAL_PATH "${XOAS_REPOSITORY_ROOT}" repositoryRoot)
if(repositoryRoot STREQUAL "/" OR
   NOT EXISTS "${repositoryRoot}/CMakePresets.json")
  message(FATAL_ERROR "Refusing cleanup outside the XOAS repository root.")
endif()

set(qualityBuildTrees dev-debug dev-release asan-ubsan)
foreach(buildTree IN LISTS qualityBuildTrees)
  set(expectedPath "${repositoryRoot}/build/${buildTree}")
  if(NOT EXISTS "${expectedPath}")
    continue()
  endif()
  file(REAL_PATH "${expectedPath}" resolvedPath)
  if(NOT resolvedPath STREQUAL expectedPath)
    message(FATAL_ERROR
            "Refusing cleanup through a redirected build path: "
            "${expectedPath} -> ${resolvedPath}")
  endif()
  file(REMOVE_RECURSE "${resolvedPath}")
  if(EXISTS "${resolvedPath}")
    message(FATAL_ERROR "Failed to remove quality build tree: ${resolvedPath}")
  endif()
  message(STATUS "Removed quality build tree: ${resolvedPath}")
endforeach()
