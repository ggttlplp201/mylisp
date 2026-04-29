.PHONY: all test acceptance lint typecheck repl clean

all: lint typecheck test acceptance

test:
	py -m pytest tests/unit -q

acceptance:
	@pass=0; total=0; \
	for f in tests/acceptance/*.lisp; do \
		total=$$((total+1)); \
		expected=$${f%.lisp}.expected; \
		if [[ "$$f" == *err_* ]]; then \
			actual=$$(py -m mylisp "$$f" 2>&1); code=$$?; \
			if [ $$code -eq 1 ] && grep -qF "$$actual" "$$expected"; then \
				pass=$$((pass+1)); \
			fi; \
		else \
			actual=$$(py -m mylisp "$$f" 2>/dev/null); \
			if [ "$$actual" = "$$(cat $$expected)" ]; then \
				pass=$$((pass+1)); \
			fi; \
		fi; \
	done; \
	echo "acceptance: $$pass/$$total passed"; \
	[ $$pass -eq $$total ]

lint:
	py -m ruff check src tests

typecheck:
	py -m mypy --strict src/mylisp

repl:
	py -m mylisp

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; \
	rm -rf .pytest_cache .mypy_cache
