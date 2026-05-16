; SPEC §5.12: load is silent, evaluates in the global env, and resolves
; relative paths against the file containing the load call, including closures.
(load "fixtures/load_helpers.lisp")
(define (root-loader) (load "fixtures/rel/outer.lisp"))
(root-loader)
(load-inner)
loaded-from-helper
(loaded-double inner-value)
