# System variables
ENV_DIR=$(CURDIR)/.env
PYTHON=$(ENV_DIR)/bin/python


pypi_upload:
# target: pypi_upload - Upload package to pypi.python.org
	@$(PYTHON) setup.py sdist upload

help:
# target: help - Display callable targets
	@grep -e "^# target:" [Mm]akefile | sed -e 's/^# target: //g'

test:
# target: test - Run tests
	@$(PYTHON) -m unittest discover
	

.PHONY: test_ci
# target: test_ci - Run tests command adapt for CI systems
test_ci:
	@python -m unittest discover

