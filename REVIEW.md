STATUS: CHANGES_REQUESTED
ITERATION: 15
FINDINGS:
- tests/acceptance/err_load_missing.expected:1 hardcodes `/Users/leon/mylisp` into the expected stderr, as do `err_load_lex_error.expected:1` and `err_load_parse_error.expected:1`. `make acceptance` is therefore path-bound to this machine; a clean checkout under any other directory will produce a different resolved-path string for the same §5.12.3 errors and fail SPEC §9.1.
NEXT_ACTIONS_FOR_BUILDER:
- Remove the checkout-specific absolute paths from load-error acceptance expectations without weakening the §5.12.3 check that load errors include the resolved path.
