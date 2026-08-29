set(XOAS_QUALITY_CONTRACT
    "${CMAKE_CURRENT_SOURCE_DIR}/contracts/expected-gates.json")

file(READ "${XOAS_QUALITY_CONTRACT}" xoasQualityContractJson)
string(JSON xoasGateCount LENGTH "${xoasQualityContractJson}" gates)

set(xoasExpectedGateNames
    format-check
    warnings
    tidy
    docs-check
    test
    asan-ubsan
    repository-policy
    quality)
list(LENGTH xoasExpectedGateNames xoasExpectedGateCount)

if(NOT xoasGateCount EQUAL xoasExpectedGateCount)
  message(FATAL_ERROR
          "Quality gate contract declares ${xoasGateCount} gates; "
          "${xoasExpectedGateCount} are required.")
endif()

math(EXPR xoasLastGateIndex "${xoasGateCount} - 1")
foreach(xoasGateIndex RANGE "${xoasLastGateIndex}")
  string(JSON xoasGateName GET "${xoasQualityContractJson}" gates
         "${xoasGateIndex}" name)
  list(GET xoasExpectedGateNames "${xoasGateIndex}" xoasExpectedGateName)
  if(NOT xoasGateName STREQUAL xoasExpectedGateName)
    message(FATAL_ERROR
            "Quality gate ${xoasGateIndex} is '${xoasGateName}'; "
            "expected '${xoasExpectedGateName}'.")
  endif()
endforeach()
