; Higher-order demo: map and fold defined in user code.
(define (map f xs)
  (if (null? xs)
      '()
      (cons (f (car xs)) (map f (cdr xs)))))

(define (foldl f acc xs)
  (if (null? xs)
      acc
      (foldl f (f acc (car xs)) (cdr xs))))

(define (square x) (* x x))

(map square '(1 2 3 4 5))
(foldl + 0 '(1 2 3 4 5))
