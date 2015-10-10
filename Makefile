# System variables
ENV_DIR=$(CURDIR)/.env
PYTHON=$(ENV_DIR)/bin/python
COVERAGE=$(ENV_DIR)/bin/coverage
NOSE=$(ENV_DIR)/bin/nosetests


help:
# target: help - Display callable targets
	@grep -e "^# target:" [Mm]akefile | sed -e 's/^# target: //g'


.PHONY: clean
# target: clean - Display callable targets
clean:
	rm -rf build/ dist/ docs/_build *.egg-info
	find $(CURDIR) -name "*.py[co]" -delete
	find $(CURDIR) -name "*.orig" -delete
	find $(CURDIR)/$(MODULE) -name "__pycache__" | xargs rm -rf


.PHONY: env
env:
# target: env - create virtualenv and install packages
	@virtualenv $(ENV_DIR)
	@$(ENV_DIR)/bin/pip install -r $(CURDIR)/requirements-test.txt


# ===============
#  Test commands
# ===============

.PHONY: test
test: env
# target: test - Run tests
	@$(NOSE) --with-coverage .


.PHONY: test_ci
test_ci: env
# target: test_ci - Run tests command adapt for CI systems
	@$(NOSE) --with-coverage .


# ===============
#  Build package
# ===============

.PHONY: register
# target: register - Register package on PyPi
register:
	@$(VIRTUAL_ENV)/bin/python setup.py register


.PHONY: upload
upload: clean
# target: upload - Upload package on PyPi
	@$(ENV_DIR)/bin/pip install wheel
	@$(PYTHON) setup.py sdist bdist bdist_wheel upload -r pypi
