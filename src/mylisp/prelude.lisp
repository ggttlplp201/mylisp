; src/mylisp/prelude.lisp -- mylisp standard library (SPEC §5.10).
;
; Loaded into the global environment at interpreter startup, after the
; §5.1–§5.8 builtins are installed and before any user program, -e
; expression, or REPL prompt (SPEC §5.11). May use only §5.1–§5.8
; primitives and earlier prelude definitions per §5.10.

; §5.10.1 Predicates
(define (not x) (if x #f #t))

(define (list? x)
  (cond ((null? x) #t)
        ((pair? x) (list? (cdr x)))
        (else #f)))

; §5.10.2 Pair selectors
(define (caar p) (car (car p)))
(define (cadr p) (car (cdr p)))
(define (cdar p) (cdr (car p)))
(define (cddr p) (cdr (cdr p)))
(define (caaar p) (car (car (car p))))
(define (caadr p) (car (car (cdr p))))
(define (cadar p) (car (cdr (car p))))
(define (caddr p) (car (cdr (cdr p))))
(define (cdaar p) (cdr (car (car p))))
(define (cdadr p) (cdr (car (cdr p))))
(define (cddar p) (cdr (cdr (car p))))
(define (cdddr p) (cdr (cdr (cdr p))))

; §5.10.3 List construction
(define (append . lsts)
  (letrec ((append2 (lambda (xs ys)
                      (if (null? xs)
                          ys
                          (cons (car xs) (append2 (cdr xs) ys)))))
           (loop (lambda (lsts)
                   (if (null? (cdr lsts))
                       (car lsts)
                       (append2 (car lsts) (loop (cdr lsts)))))))
    (if (null? lsts)
        '()
        (loop lsts))))

(define (reverse lst)
  (letrec ((loop (lambda (lst acc)
                   (if (null? lst)
                       acc
                       (loop (cdr lst) (cons (car lst) acc))))))
    (loop lst '())))

; §5.10.4 Higher-order list operations
(define (map f lst)
  (if (null? lst)
      '()
      (cons (f (car lst)) (map f (cdr lst)))))

(define (filter pred lst)
  (cond ((null? lst) '())
        ((pred (car lst))
         (cons (car lst) (filter pred (cdr lst))))
        (else (filter pred (cdr lst)))))

(define (foldl f init lst)
  (if (null? lst)
      init
      (foldl f (f (car lst) init) (cdr lst))))

(define (foldr f init lst)
  (if (null? lst)
      init
      (f (car lst) (foldr f init (cdr lst)))))

; §5.10.5 List search
;
; `length` is invoked first on the input list so that improper inputs raise
; `type error: expected proper list, got <input>` even when the matching
; element occurs before the dotted tail.
(define (member x lst)
  (length lst)
  (letrec ((loop (lambda (l)
                   (cond ((null? l) #f)
                         ((equal? x (car l)) l)
                         (else (loop (cdr l)))))))
    (loop lst)))

(define (memq x lst)
  (length lst)
  (letrec ((loop (lambda (l)
                   (cond ((null? l) #f)
                         ((eq? x (car l)) l)
                         (else (loop (cdr l)))))))
    (loop lst)))

(define (assoc k alst)
  (length alst)
  (letrec ((loop (lambda (l)
                   (cond ((null? l) #f)
                         ((equal? k (car (car l))) (car l))
                         (else (loop (cdr l)))))))
    (loop alst)))

(define (assq k alst)
  (length alst)
  (letrec ((loop (lambda (l)
                   (cond ((null? l) #f)
                         ((eq? k (car (car l))) (car l))
                         (else (loop (cdr l)))))))
    (loop alst)))
