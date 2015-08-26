# -*- coding: utf-8 -*-
from simplemodels import PYTHON_VERSION

__all__ = []  # no public methods and variables


# Python 3 compatibility utils
basestring = basestring if PYTHON_VERSION == 2 else str
