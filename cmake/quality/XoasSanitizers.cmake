include_guard(GLOBAL)

option(XOAS_ENABLE_SANITIZERS
       "Enable fail-fast AddressSanitizer and UndefinedBehaviorSanitizer" OFF)

add_library(xoas_sanitizers INTERFACE)
add_library(xoas::sanitizers ALIAS xoas_sanitizers)

if(XOAS_ENABLE_SANITIZERS)
  if(NOT CMAKE_CXX_COMPILER_ID STREQUAL "Clang" OR
     NOT CMAKE_CXX_COMPILER_VERSION VERSION_EQUAL "21.1.8")
    message(FATAL_ERROR
            "XOAS sanitizer gates require the locked Clang 21.1.8 compiler.")
  endif()

  target_compile_options(
    xoas_sanitizers
    INTERFACE
      -fsanitize=address,undefined
      -fno-omit-frame-pointer
      -fno-sanitize-recover=all)
  target_link_options(
    xoas_sanitizers
    INTERFACE
      -fsanitize=address,undefined
      -fno-sanitize-recover=all)
endif()
