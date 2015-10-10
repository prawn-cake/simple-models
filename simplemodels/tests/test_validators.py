# -*- coding: utf-8 -*-
import unittest
from datetime import datetime
from simplemodels.exceptions import ValidationError
from simplemodels.fields import SimpleField
from simplemodels.models import Document
from simplemodels.validators import is_instance


class ValidatorsTest(unittest.TestCase):
    def test_instance_validator(self):
        class Message(Document):
            ts = SimpleField(default=datetime.now,
                             validators=[is_instance(datetime)])
        message = Message()
        self.assertIsInstance(message.ts, datetime)

        # Check error case
        validator = is_instance((int, float))
        self.assertRaises(ValidationError, validator, 'str value')
