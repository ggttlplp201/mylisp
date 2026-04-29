.PHONY: all test acceptance lint typecheck repl clean

PYTHON ?= py

SHELL := /bin/bash

all: lint typecheck test acceptance

test:
	$(PYTHON) -m pytest tests/unit -q

acceptance:
	@pass=0; total=0; \
	tmpout=$$(mktemp); tmperr=$$(mktemp); \
	trap 'rm -f "$$tmpout" "$$tmperr"' EXIT; \
	for f in tests/acceptance/*.lisp; do \
		total=$$((total+1)); \
		expected=$${f%.lisp}.expected; \
		base=$$(basename "$$f"); \
		$(PYTHON) -m mylisp "$$f" >"$$tmpout" 2>"$$tmperr"; code=$$?; \
		case "$$base" in \
			err_*) \
				if [ $$code -eq 1 ] && cmp -s "$$tmperr" "$$expected"; then \
					pass=$$((pass+1)); \
				fi; \
				;; \
			*) \
				if [ $$code -eq 0 ] && cmp -s "$$tmpout" "$$expected"; then \
					pass=$$((pass+1)); \
				fi; \
				;; \
		esac; \
	done; \
	echo "acceptance: $$pass/$$total passed"; \
	[ $$pass -eq $$total ]

lint:
	$(PYTHON) -m ruff check src tests

typecheck:
	$(PYTHON) -m mypy --strict src/mylisp

repl:
	$(PYTHON) -m mylisp

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; \
	rm -rf .pytest_cache .mypy_cache
