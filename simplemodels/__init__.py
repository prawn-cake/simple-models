# -*- coding: utf-8 -*-
import sys

__version__ = '0.6.1'
PYTHON_VERSION = sys.version_info[0]

# Public imports interface
from .models import Document, ImmutableDocument
from .fields import *  # __all__ listed fields should be imported here
