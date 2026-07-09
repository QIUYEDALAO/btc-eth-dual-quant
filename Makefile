.PHONY: m0-validate test

m0-validate:
	bash scripts/m0_validate.sh

test:
	PYTHONPATH=.deps:src $${PYTHON:-python3} -m unittest discover -s tests -v
