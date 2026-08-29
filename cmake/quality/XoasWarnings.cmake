include_guard(GLOBAL)

include(CheckCXXCompilerFlag)

if(NOT CMAKE_CXX_COMPILER_ID STREQUAL "Clang")
  message(FATAL_ERROR "XOAS first-party builds require the locked Clang compiler.")
endif()
if(NOT CMAKE_CXX_COMPILER_VERSION VERSION_EQUAL "21.1.8")
  message(FATAL_ERROR
          "XOAS requires Clang 21.1.8; found ${CMAKE_CXX_COMPILER_VERSION}.")
endif()

set(XOAS_BASE_WARNING_FLAGS
    -Wall
    -Wextra
    -Wpedantic
    -Werror)
set(XOAS_ADDITIONAL_WARNING_FLAGS
    -Wcast-align
    -Wconversion
    -Wdouble-promotion
    -Wextra-semi
    -Wformat=2
    -Wimplicit-fallthrough
    -Wnon-virtual-dtor
    -Wold-style-cast
    -Woverloaded-virtual
    -Wshadow
    -Wsign-conversion
    -Wundef
    -Wzero-as-null-pointer-constant)

set(XOAS_WARNING_FLAGS ${XOAS_BASE_WARNING_FLAGS})
foreach(xoasWarningFlag IN LISTS XOAS_ADDITIONAL_WARNING_FLAGS)
  string(MAKE_C_IDENTIFIER "${xoasWarningFlag}" xoasWarningIdentifier)
  set(xoasProbeVariable "XOAS_SUPPORTS${xoasWarningIdentifier}")
  check_cxx_compiler_flag("${xoasWarningFlag}" "${xoasProbeVariable}")
  if(NOT ${xoasProbeVariable})
    message(FATAL_ERROR
            "Locked Clang does not support required warning ${xoasWarningFlag}.")
  endif()
  list(APPEND XOAS_WARNING_FLAGS "${xoasWarningFlag}")
endforeach()

add_library(xoas_warnings INTERFACE)
add_library(xoas::warnings ALIAS xoas_warnings)
target_compile_options(
  xoas_warnings
  INTERFACE "$<$<COMPILE_LANGUAGE:CXX>:${XOAS_WARNING_FLAGS}>")

string(JOIN "|" xoasWarningFlagsEncoded ${XOAS_WARNING_FLAGS})
