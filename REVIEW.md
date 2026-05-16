STATUS: CHANGES_REQUESTED
ITERATION: 17
FINDINGS:
- src/mylisp/prelude.lisp:74, src/mylisp/prelude.lisp:79, src/mylisp/prelude.lisp:84, and src/mylisp/prelude.lisp:89 return a matching `member`/`memq`/`assoc`/`assq` result before validating that the input list is proper. SPEC §5.10.5 says the list argument MUST be a proper list for all four functions, so `(member 1 (cons 1 2))`, `(memq 'a (cons 'a 2))`, `(assoc 'a (cons (cons 'a 1) 2))`, and `(assq 'a (cons (cons 'a 1) 2))` must raise a `type error:` instead of succeeding. Added failing acceptance coverage in `tests/acceptance/err_prelude_*_improper_match.*`.
NEXT_ACTIONS_FOR_BUILDER:
- Validate the full list/alist properness before `member`, `memq`, `assoc`, and `assq` can return an early match; using the existing `length` primitive before the search is one acceptable way to preserve the §5.9 `type error:` prefix.
- Re-run `make test acceptance lint typecheck`; the new improper-match acceptance tests should pass without weakening existing tests.
