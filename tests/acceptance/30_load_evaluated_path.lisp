; SPEC §5.12: load is a primitive, so its path argument is evaluated.
(define dir "fixtures")
(load (string-append dir "/load_helpers.lisp"))
loaded-from-helper
