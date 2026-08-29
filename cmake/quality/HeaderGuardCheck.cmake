cmake_minimum_required(VERSION 3.28)

foreach(requiredVariable
        XOAS_HEADER_GUARD_INPUT
        XOAS_HEADER_GUARD_RELATIVE_PATH)
  if(NOT DEFINED ${requiredVariable})
    message(FATAL_ERROR "${requiredVariable} is required.")
  endif()
endforeach()

if(NOT EXISTS "${XOAS_HEADER_GUARD_INPUT}")
  message(FATAL_ERROR
          "Header guard input does not exist: ${XOAS_HEADER_GUARD_INPUT}")
endif()
if(XOAS_HEADER_GUARD_RELATIVE_PATH MATCHES "(^|/)\\.\\.(/|$)" OR
   XOAS_HEADER_GUARD_RELATIVE_PATH MATCHES "^/")
  message(FATAL_ERROR "Header guard paths must be repository-relative.")
endif()

string(TOUPPER "XOAS_${XOAS_HEADER_GUARD_RELATIVE_PATH}" expectedGuard)
string(REGEX REPLACE "[^A-Z0-9]" "_" expectedGuard "${expectedGuard}")
file(READ "${XOAS_HEADER_GUARD_INPUT}" headerContent)

string(REGEX MATCH
       "^#ifndef[ \t]+${expectedGuard}\n#define[ \t]+${expectedGuard}([ \t]*\n)"
       openingMatch
       "${headerContent}")
string(REGEX MATCH
       "#endif[ \t]+//[ \t]+${expectedGuard}[ \t]*\n?$"
       closingMatch
       "${headerContent}")
set(guardValid TRUE)
if(openingMatch STREQUAL "" OR closingMatch STREQUAL "")
  set(guardValid FALSE)
endif()

if(XOAS_HEADER_GUARD_EXPECT_FAILURE)
  if(guardValid)
    message(FATAL_ERROR "Negative portable header-guard fixture passed.")
  endif()
  message(STATUS
          "Observed intended xoas-portable-header-guard rejection; expected "
          "${expectedGuard}.")
  return()
endif()

if(NOT guardValid)
  message(FATAL_ERROR
          "Header guard for ${XOAS_HEADER_GUARD_RELATIVE_PATH} must be "
          "${expectedGuard}.")
endif()
