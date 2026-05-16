; SPEC §5.12.2: load evaluates against the global environment and does
; not deduplicate repeated paths; side effects compound.
(define counter 0)
(define (trigger-load)
  (let ((counter 100))
    (load "fixtures/load_increment_counter.lisp")))
(trigger-load)
counter
(trigger-load)
counter
