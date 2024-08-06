file(GLOB_RECURSE DECLANALYZER_SOURCE CONFIGURE_DEPENDS *.c)

target_sources(c-- PUBLIC ${DECLANALYZER_SOURCE})
target_include_directories(c-- PUBLIC .)