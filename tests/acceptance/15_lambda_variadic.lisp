((lambda args args) 1 2 3)
((lambda (a b . rest) rest) 1 2 3 4)
((lambda (x) (define y 3) (+ x y)) 4)
