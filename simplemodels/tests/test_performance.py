# -*- coding: utf-8 -*-
import unittest
import time
from datetime import datetime
from simplemodels.exceptions import ModelValidationError
from simplemodels.models import Document
from simplemodels import fields
import random
import string


class User(Document):
    """Test model"""

    id = fields.IntegerField()
    name = fields.CharField()
    password = fields.CharField()
    is_admin = fields.BooleanField(default=False)
    date_of_birth = fields.SimpleField(
        validators=[lambda value: datetime.strptime(value, '%Y-%m-%d')])
    balance = fields.DecimalField(default=0)
    extra_info = fields.SimpleField()
    tags = fields.ListField(item_types=[str])

    @staticmethod
    def validate_password(document, value):
        if document.is_admin and len(value) < 10:
            raise ModelValidationError(
                'Admin password is too short (< 10 characters)')
        return value

    @classmethod
    def get_random_instance(cls):
        return cls(
            id=cls.get_id(),
            name=cls.get_name(),
            password=cls.get_password(),
            is_admin=cls.get_is_admin(),
            date_of_birth=cls.get_date_of_birth(),
            balance=cls.get_balance(),
            extra_info=cls.get_extra_info(),
            tags=cls.get_tags()
        )

    @staticmethod
    def get_id():
        return random.randint(1, 100000)

    @staticmethod
    def get_name():
        name_length = 15
        return ''.join([random.choice(string.ascii_lowercase)
                        for _ in range(name_length)])

    @staticmethod
    def get_password():
        password_length = 15
        return ''.join([random.choice(string.ascii_lowercase)
                        for _ in range(password_length)])

    @staticmethod
    def get_is_admin():
        return random.choice([True, False])

    @staticmethod
    def get_date_of_birth():
        return '2000-01-01'

    @staticmethod
    def get_balance():
        return random.randint(0, 1000)

    @staticmethod
    def get_extra_info():
        return {}

    @staticmethod
    def get_tags():
        return ['tag1', 'tag2', 'tag3']


@unittest.skip('skip awhile')
class PerformanceTest(unittest.TestCase):
    SAMPLE_SET = 10000
    READ_OPS = 1000
    WRITE_OPS = 1000

    def setUp(self):
        self.sample_set = []
        t0 = time.time()
        for _ in range(self.SAMPLE_SET):
            self.sample_set.append(User.get_random_instance())
        self.create_time = time.time() - t0

    def test_create(self):
        print(self.create_time)

    def test_random_read(self):
        t0 = time.time()
        for _ in range(self.READ_OPS):
            random_field = random.choice(list(User._fields.keys()))
            instance = random.choice(self.sample_set)
            getattr(instance, random_field)

        elapsed = time.time() - t0
        print('test_random_read: {:.6f}s'.format(elapsed))
        # self.assertTrue(elapsed < 0.0035, elapsed)

    def test_random_write(self):
        t0 = time.time()
        for _ in range(self.WRITE_OPS):
            pass
        elapsed = time.time() - t0
