; src/mylisp/prelude.lisp -- mylisp standard library (SPEC §5.10).
;
; This file is read by the interpreter at startup, AFTER the §5.1–§5.8
; builtins are installed in the global environment and BEFORE any user
; program, -e expression, or REPL prompt (SPEC §5.11).
;
; Per §5.10, every function listed in §5.10.1–§5.10.5 MUST be defined
; here, not as a Python builtin. The file may use only §5.1–§5.8
; primitives and earlier prelude definitions; introducing new evaluator
; features is a SPEC violation.
;
; Subsequent commits fill in the definitions; this initial revision
; establishes the loading mechanism with an empty body.
