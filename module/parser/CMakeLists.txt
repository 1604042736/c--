file(GLOB_RECURSE PARSER_SOURCE CONFIGURE_DEPENDS *.c)

target_sources(c-- PUBLIC ${PARSER_SOURCE})
target_include_directories(c-- PUBLIC .)