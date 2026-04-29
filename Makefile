.PHONY: all test acceptance lint typecheck repl clean

SHELL := /bin/bash

PYTHON ?= $(shell { python3 -c '' >/dev/null 2>&1 && echo python3; } || { py -c '' >/dev/null 2>&1 && echo py; } || echo python)

all: lint typecheck test acceptance

test:
	$(PYTHON) -m pytest tests/unit -q

acceptance:
	@pass=0; total=0; \
	tmpout=$$(mktemp); tmperr=$$(mktemp); \
	tmpoutn=$$(mktemp); tmpexpn=$$(mktemp); \
	trap 'rm -f "$$tmpout" "$$tmperr" "$$tmpoutn" "$$tmpexpn"' EXIT; \
	for f in tests/acceptance/*.lisp; do \
		total=$$((total+1)); \
		expected=$${f%.lisp}.expected; \
		base=$$(basename "$$f"); \
		$(PYTHON) -m mylisp "$$f" >"$$tmpout" 2>"$$tmperr"; code=$$?; \
		tr -d '\r' < "$$expected" > "$$tmpexpn"; \
		case "$$base" in \
			err_*) \
				tr -d '\r' < "$$tmperr" > "$$tmpoutn"; \
				if [ $$code -eq 1 ] && cmp -s "$$tmpoutn" "$$tmpexpn"; then \
					pass=$$((pass+1)); \
				fi; \
				;; \
			*) \
				tr -d '\r' < "$$tmpout" > "$$tmpoutn"; \
				if [ $$code -eq 0 ] && cmp -s "$$tmpoutn" "$$tmpexpn"; then \
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
