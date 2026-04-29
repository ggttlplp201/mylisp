; Recursion demo: classic factorial and Fibonacci.
(define (fact n)
  (if (= n 0)
      1
      (* n (fact (- n 1)))))

(define (fib n)
  (cond ((= n 0) 0)
        ((= n 1) 1)
        (else (+ (fib (- n 1)) (fib (- n 2))))))

(fact 10)
(fib 15)
