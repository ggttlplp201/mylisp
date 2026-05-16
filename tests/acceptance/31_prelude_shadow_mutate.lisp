; SPEC §5.10 visibility: prelude bindings are ordinary global bindings.
(define original-not not)
(not #f)
(define not (lambda (x) 'shadowed))
(not #f)
(set! not original-not)
(not #f)
(set! map (lambda (f lst) 'mutated))
(map (lambda (x) x) '(1 2 3))
