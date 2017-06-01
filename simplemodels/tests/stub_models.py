# -*- coding: utf-8 -*-
"""Tests stub models"""

from datetime import datetime

import six
from simplemodels.fields import SimpleField, DocumentField, IntegerField, DateTimeField, BooleanField, CharField, \
    ListField
from simplemodels.models import Document


class MailboxItem(Document):
    subject = CharField(default='')
    body = SimpleField(default='')
    type = SimpleField(choices=["SUGGESTION", "MAIL"],
                       max_length=10,
                       default='MAIL')
    # received_at = SimpleField(default=timezone.now)
    received_at = DateTimeField(default=datetime.now)
    is_read = BooleanField(default=False)

    def __init__(self, data=None, **kwargs):
        if data is None:
            data = {}
        super(MailboxItem, self).__init__(data, **kwargs)
        if 'received_at' not in data and not self.received_at:
            self.received_at = datetime.now()

    def __repr__(self):
        return six.u("<{}({}): {}>".format(
            self.__class__.__name__, self.type, self.subject))

    def __unicode__(self):
        return six.u("<{}({}): {}>".format(
            self.__class__.__name__, self.type, self.subject))


class Address(Document):
    street = SimpleField()
    zip = IntegerField()


class Person(Document):
    name = SimpleField(required=True)
    address = DocumentField(model=Address)
    phones = ListField(int)


class Comment(Document):
    body = CharField()
    author = DocumentField(Person)
    created = DateTimeField(default=datetime.now)
    favorite_by = ListField(of=Person)


class Post(Document):
    title = CharField()
    author = DocumentField(Person)
    comments = ListField(of=Comment)
    tags = ListField(of=str)
