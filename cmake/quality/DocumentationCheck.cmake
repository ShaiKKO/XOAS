cmake_minimum_required(VERSION 3.28)

foreach(requiredVariable
        XOAS_DOXYGEN
        XOAS_DOXYFILE_TEMPLATE
        XOAS_DOCUMENTATION_WORKING_DIRECTORY)
  if(NOT DEFINED ${requiredVariable})
    message(FATAL_ERROR "${requiredVariable} is required.")
  endif()
endforeach()

if(NOT EXISTS "${XOAS_DOXYGEN}")
  message(FATAL_ERROR "XOAS_DOXYGEN does not exist: ${XOAS_DOXYGEN}")
endif()
if(NOT EXISTS "${XOAS_DOXYFILE_TEMPLATE}")
  message(FATAL_ERROR
          "Doxygen template does not exist: ${XOAS_DOXYFILE_TEMPLATE}")
endif()

file(MAKE_DIRECTORY "${XOAS_DOCUMENTATION_WORKING_DIRECTORY}")
set(documentationInputs)
if(DEFINED XOAS_DOCUMENTATION_INPUT)
  get_filename_component(documentationInputName
                         "${XOAS_DOCUMENTATION_INPUT}" NAME)
  string(REGEX REPLACE "\\.in$" "" documentationCopyName
                       "${documentationInputName}")
  set(documentationCopyPath
      "${XOAS_DOCUMENTATION_WORKING_DIRECTORY}/${documentationCopyName}")
  configure_file(
    "${XOAS_DOCUMENTATION_INPUT}" "${documentationCopyPath}" COPYONLY)
  list(APPEND documentationInputs "${documentationCopyPath}")
  get_filename_component(documentationStripPath
                         "${XOAS_DOCUMENTATION_WORKING_DIRECTORY}" ABSOLUTE)
else()
  foreach(requiredVariable XOAS_GIT XOAS_REPOSITORY_ROOT)
    if(NOT DEFINED ${requiredVariable})
      message(FATAL_ERROR "${requiredVariable} is required.")
    endif()
  endforeach()
  execute_process(
    COMMAND
      "${XOAS_GIT}" ls-files -- "*.c" "*.cc" "*.cpp" "*.cxx" "*.h" "*.hh"
      "*.hpp" "*.hxx"
    WORKING_DIRECTORY "${XOAS_REPOSITORY_ROOT}"
    RESULT_VARIABLE gitStatus
    OUTPUT_VARIABLE trackedOutput
    ERROR_VARIABLE gitError
    OUTPUT_STRIP_TRAILING_WHITESPACE)
  if(NOT gitStatus EQUAL 0)
    message(FATAL_ERROR "Unable to enumerate documentation inputs: ${gitError}")
  endif()
  string(REPLACE "\n" ";" trackedPaths "${trackedOutput}")
  foreach(trackedPath IN LISTS trackedPaths)
    if(trackedPath MATCHES
       "^tests/quality/fixtures/(generated/output|vendor)/")
      continue()
    endif()
    if(NOT trackedPath MATCHES "^(include|src|tests|cmake|tools)/")
      message(FATAL_ERROR
              "Tracked documentation path is unclassified: ${trackedPath}")
    endif()
    list(APPEND documentationInputs
         "${XOAS_REPOSITORY_ROOT}/${trackedPath}")
  endforeach()
  set(documentationStripPath "${XOAS_REPOSITORY_ROOT}")
endif()

if(documentationInputs STREQUAL "")
  message(FATAL_ERROR "No documentation inputs were selected.")
endif()

set(documentationPreflightDiagnostics "")
set(doxygenInputArguments "")
foreach(documentationInput IN LISTS documentationInputs)
  file(READ "${documentationInput}" documentationContent)
  string(FIND "${documentationContent}" "/// \\file" fileBlockOffset)
  if(fileBlockOffset EQUAL -1)
    string(APPEND documentationPreflightDiagnostics
           "xoas-undocumented-file: ${documentationInput} lacks /// \\file\n")
  endif()
  string(APPEND doxygenInputArguments "\"${documentationInput}\" ")
endforeach()

if(NOT documentationPreflightDiagnostics STREQUAL "")
  if(XOAS_DOCUMENTATION_EXPECT_FAILURE AND
     documentationPreflightDiagnostics MATCHES
       "${XOAS_DOCUMENTATION_EXPECTED_DIAGNOSTIC}")
    message(STATUS "${documentationPreflightDiagnostics}")
    return()
  endif()
  message(FATAL_ERROR "${documentationPreflightDiagnostics}")
endif()

set(doxygenOutputDirectory
    "${XOAS_DOCUMENTATION_WORKING_DIRECTORY}/output")
set(doxygenWarnLog
    "${XOAS_DOCUMENTATION_WORKING_DIRECTORY}/doxygen-warnings.log")
set(configuredDoxyfile
    "${XOAS_DOCUMENTATION_WORKING_DIRECTORY}/Doxyfile")
file(READ "${XOAS_DOXYFILE_TEMPLATE}" doxygenConfiguration)
string(REPLACE "@XOAS_DOXYGEN_OUTPUT_DIRECTORY@"
               "${doxygenOutputDirectory}"
               doxygenConfiguration "${doxygenConfiguration}")
string(REPLACE "@XOAS_DOXYGEN_STRIP_PATH@"
               "${documentationStripPath}"
               doxygenConfiguration "${doxygenConfiguration}")
string(REPLACE "@XOAS_DOXYGEN_WARN_LOG@"
               "${doxygenWarnLog}"
               doxygenConfiguration "${doxygenConfiguration}")
string(REPLACE "@XOAS_DOXYGEN_INPUTS@"
               "${doxygenInputArguments}"
               doxygenConfiguration "${doxygenConfiguration}")
file(WRITE "${configuredDoxyfile}" "${doxygenConfiguration}")

execute_process(
  COMMAND "${XOAS_DOXYGEN}" "${configuredDoxyfile}"
  RESULT_VARIABLE doxygenStatus
  OUTPUT_VARIABLE doxygenOutput
  ERROR_VARIABLE doxygenError)
if(EXISTS "${doxygenWarnLog}")
  file(READ "${doxygenWarnLog}" doxygenWarnings)
else()
  set(doxygenWarnings "")
endif()
string(CONCAT doxygenDiagnostics
       "${doxygenOutput}" "${doxygenError}" "${doxygenWarnings}")

if(XOAS_DOCUMENTATION_EXPECT_FAILURE)
  if(doxygenStatus EQUAL 0)
    message(FATAL_ERROR "Negative Doxygen fixture unexpectedly passed.")
  endif()
  if(NOT doxygenDiagnostics MATCHES
     "${XOAS_DOCUMENTATION_EXPECTED_DIAGNOSTIC}")
    message(FATAL_ERROR
            "Doxygen failed without ${XOAS_DOCUMENTATION_EXPECTED_DIAGNOSTIC}:\n"
            "${doxygenDiagnostics}")
  endif()
  message(STATUS
          "Observed intended documentation rejection: "
          "${XOAS_DOCUMENTATION_EXPECTED_DIAGNOSTIC}")
  return()
endif()

if(NOT doxygenStatus EQUAL 0)
  message(FATAL_ERROR "Doxygen documentation check failed:\n${doxygenDiagnostics}")
endif()
