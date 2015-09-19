# System variables
ENV_DIR=$(CURDIR)/.env
PYTHON=$(ENV_DIR)/bin/python
COVERAGE=$(ENV_DIR)/bin/coverage
NOSE=$(ENV_DIR)/bin/nosetests

help:
# target: help - Display callable targets
	@grep -e "^# target:" [Mm]akefile | sed -e 's/^# target: //g'

.PHONY: env
env:
# target: env - create virtualenv and install packages
	@virtualenv $(ENV_DIR)
	@$(ENV_DIR)/bin/pip install -r $(CURDIR)/requirements.txt

.PHONY: pypi_upload
pypi_upload:
# target: pypi_upload - Upload package to pypi.python.org
	@$(PYTHON) setup.py sdist upload

.PHONY: test
test: env
# target: test - Run tests
	@$(NOSE) --with-coverage .

.PHONY: test_ci
test_ci: env
# target: test_ci - Run tests command adapt for CI systems
	@$(NOSE) --with-coverage .
