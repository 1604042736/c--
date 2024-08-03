file(GLOB_RECURSE COMMON_SOURCE CONFIGURE_DEPENDS *.c)

target_sources(c-- PUBLIC ${COMMON_SOURCE})
target_include_directories(c-- PUBLIC .)