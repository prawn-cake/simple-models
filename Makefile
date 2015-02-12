# System variables
ENV_DIR=$(CURDIR)/.env
PYTHON=$(ENV_DIR)/bin/python
COVERAGE=$(ENV_DIR)/bin/coverage

help:
# target: help - Display callable targets
	@grep -e "^# target:" [Mm]akefile | sed -e 's/^# target: //g'

.PHONY: env
env:
# target: env - create virtualenv and install packages
	@virtualenv $(ENV_DIR)

.PHONY: pypi_upload
pypi_upload:
# target: pypi_upload - Upload package to pypi.python.org
	@$(PYTHON) setup.py sdist upload

.PHONY: test
test: env
# target: test - Run tests
	@$(PYTHON) -m unittest discover
	

.PHONY: test_ci
test_ci: env
# target: test_ci - Run tests command adapt for CI systems
	@$(PYTHON) -m unittest discover

.PHONY: test_coverage
# target: test_coverage - Run tests with coverage
test_coverage: env
	@$(COVERAGE) run --source=simplemodels $(PYTHON) -m unittest discover