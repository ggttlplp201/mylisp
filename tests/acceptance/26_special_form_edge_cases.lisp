(if #t 1 (undefined))
(if #f (undefined) 2)
(define x 1)
(let ((x 2) (y x)) y)
(let* ((x 2) (y x)) y)
(define outer 1)
((lambda () (set! outer 7)))
outer
