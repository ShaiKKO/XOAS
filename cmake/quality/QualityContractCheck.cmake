cmake_minimum_required(VERSION 3.28)

foreach(requiredVariable
        XOAS_BUILD_DIRECTORY
        XOAS_CMAKE
        XOAS_QUALITY_CONTRACT)
  if(NOT DEFINED ${requiredVariable})
    message(FATAL_ERROR "${requiredVariable} is required.")
  endif()
endforeach()

file(READ "${XOAS_QUALITY_CONTRACT}" qualityContractJson)
string(JSON gateCount LENGTH "${qualityContractJson}" gates)
set(redGates)
math(EXPR finalGateIndex "${gateCount} - 1")
foreach(gateIndex RANGE "${finalGateIndex}")
  string(JSON gateName GET "${qualityContractJson}" gates "${gateIndex}" name)
  string(JSON gateState GET "${qualityContractJson}" gates "${gateIndex}" state)
  if(NOT gateState STREQUAL "green")
    list(APPEND redGates "${gateName}")
  endif()
endforeach()
if(redGates)
  list(JOIN redGates ", " redGateList)
  message(FATAL_ERROR
          "xoas-quality-contract: gates remain red: ${redGateList}")
endif()

execute_process(
  COMMAND "${XOAS_CMAKE}" --build "${XOAS_BUILD_DIRECTORY}" --target help
  RESULT_VARIABLE targetHelpStatus
  OUTPUT_VARIABLE targetHelpOutput
  ERROR_VARIABLE targetHelpError)
if(NOT targetHelpStatus EQUAL 0)
  message(FATAL_ERROR
          "xoas-quality-contract: cannot enumerate build targets:\n"
          "${targetHelpOutput}${targetHelpError}")
endif()

set(requiredTargets
    format-check
    warnings
    tidy
    docs-check
    quality-tests
    asan-ubsan
    repository-policy
    quality)
foreach(requiredTarget IN LISTS requiredTargets)
  if(NOT targetHelpOutput MATCHES
     "(^|\n)([^\n]*/CMakeFiles/)?${requiredTarget}:([ \t]|$)")
    message(FATAL_ERROR
            "xoas-quality-contract: required target is absent: "
            "${requiredTarget}")
  endif()
endforeach()
