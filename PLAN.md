# Implementation plan

## Phase 1: lexer
- [ ] Implement tokenizer for parens, integers, booleans, strings, symbols (SPEC §4.1)
- [ ] LexError with line/col reporting (SPEC §4.2)
- [ ] Unit tests for each token class

## Phase 2: parser
- [ ] Parse S-expressions into AST nodes
- [ ] Handle quote sugar 'X -> (quote X)
- [ ] ParseError with location

## Phase 3: minimal evaluator
- [ ] Environment class with frames
- [ ] Self-evaluating literals
- [ ] Symbol lookup with unbound-symbol error
- [ ] Special forms: quote, if, define, lambda
- [ ] Procedure application

(more phases live in this file as they emerge)
