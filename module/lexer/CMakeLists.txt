file(GLOB_RECURSE LEXER_SOURCE CONFIGURE_DEPENDS *.c)

target_sources(c-- PUBLIC ${LEXER_SOURCE})
target_include_directories(c-- PUBLIC .)