# -*- coding: utf-8 -*-
"""Tests stub models"""

from datetime import datetime
import six
from simplemodels.fields import SimpleField
from simplemodels.models import Document


class MailboxItem(Document):
    subject = SimpleField(default='')
    body = SimpleField(default='')
    type = SimpleField(choices=["SUGGESTION", "MAIL"],
                       max_length=10,
                       default='MAIL')
    # received_at = SimpleField(default=timezone.now)
    received_at = SimpleField(default='')
    is_read = SimpleField(default=False)

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


class Person(Document):
    name = SimpleField(required=True)
    address = SimpleField(validators=[Address])
