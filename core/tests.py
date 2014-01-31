# -*- coding: utf-8 -*-
from unittest import TestCase
from datetime import datetime
from core.exceptions import SimpleFieldValidationError
from core.fields import SimpleField
from core.models import AttributeDict, DictEmbeddedDocument
from core.utils import Choices


class AttributeDictTest(TestCase):
    def test_dict(self):

        ad = AttributeDict()
        ad._id = 1
        self.assertEqual(ad['_id'], 1)

    def test_system_methods(self):
        from copy import deepcopy

        attr_d = AttributeDict(a=1)
        ad_copy = deepcopy(attr_d)
        self.assertTrue(ad_copy)


class DictEmbeddedDocumentTest(TestCase):
    def test_document(self):
        class Money(DictEmbeddedDocument):

            """Nested"""

            xsi_type = SimpleField('Money')
            microAmount = SimpleField()

        class BidEmbedded(DictEmbeddedDocument):
            xsi_type = SimpleField('BidEmbedded')
            # xsi_type = fields.StringField(default='BidEmbedded')
            contentBid = SimpleField(Money())

        bid = BidEmbedded()

        self.assertIsInstance(bid, dict)
        self.assertEqual(
            sorted(bid._fields), sorted(('xsi_type', 'contentBid'))
        )

        self.assertEqual(
            bid,
            {
                'xsi_type': 'BidEmbedded',
                'contentBid': {'xsi_type': 'Money', 'microAmount': None}
            }
        )

    def test_simple_field_default(self):
        class A(object):
            f = SimpleField(default=10)

        a = A()
        self.assertEqual(a.f, 10)

    def test_simple_field_required(self):
        class TestDictDocument(DictEmbeddedDocument):
            xsi_type = SimpleField(required=True)

        self.assertRaises(SimpleFieldValidationError, TestDictDocument)

    def test_default_values_with_several_instances(self):
        td = MailboxItem()
        td_2 = MailboxItem(is_read=True)

        self.assertFalse(td.is_read)
        self.assertTrue(td_2.is_read)

        td.is_read = True
        td_2.is_read = False
        self.assertTrue(td.is_read)
        self.assertFalse(td_2.is_read)


class ValidationTest(TestCase):
    def test_base(self):
        class Address(DictEmbeddedDocument):
            street = SimpleField()

        class Person(DictEmbeddedDocument):
            name = SimpleField()
            address = SimpleField(link_cls=Address)

        # person = Person.get_instance(address='Pagoda street')
        street = 'Pagoda street'
        self.assertRaises(
            SimpleFieldValidationError,
            Person.get_instance, address=street
        )

        person = Person.get_instance(
            address=Address.get_instance(street=street)
        )
        self.assertEqual(person.address.street, street)


class MailboxItem(DictEmbeddedDocument):
    TYPES = Choices(
        ("SG", "SUGGESTION", "Suggestion"),
        ("ML", "MAIL", "Mail")
    )

    subject = SimpleField(default='')
    body = SimpleField(default='')
    type = SimpleField(choices=TYPES, max_length=10, default=TYPES.MAIL)
    # received_at = SimpleField(default=timezone.now)
    received_at = SimpleField(default='')
    is_read = SimpleField(default=False)

    def __init__(self, **kwargs):
        super(MailboxItem, self).__init__(**kwargs)
        if not 'received_at' in kwargs and not self.received_at:
            self.received_at = datetime.now()

    def __repr__(self):
        return unicode("<{}({}): {}>".format(
            self.__class__.__name__, self.type, self.subject))

    def __unicode__(self):
        return unicode("<{}({}): {}>".format(
            self.__class__.__name__, self.type, self.subject))