# -*- coding: utf-8 -*-
from unittest import TestCase
from datetime import datetime
from simplemodels.exceptions import SimpleFieldValidationError
from simplemodels.fields import SimpleField
from simplemodels.models import AttributeDict, DictEmbeddedDocument
from simplemodels.utils import Choices


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
        class A(DictEmbeddedDocument):
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

    def test_getting_classname(self):
        self.assertEqual(Address.__name__, 'Address')

    def test_property_getter(self):
        class DocumentWithProperty(DictEmbeddedDocument):
            a = SimpleField()
            b = SimpleField()

            @property
            def c(self):
                return str(self.a) + str(self.b)

        document = DocumentWithProperty.get_instance(a=1, b=2)

        self.assertEqual(document.c, '12')

    def test_get_instance_method(self):
        """ get_instance method should guarantee that object contains exactly
        same fields as described


        """
        class TestModel(DictEmbeddedDocument):
            a = SimpleField()
            b = SimpleField()

        source_data = {'a': 1, 'b': 2, 'c': 3, 'd': 4}
        obj = TestModel.get_instance(**source_data)
        self.assertEqual(len(obj), len(TestModel._fields))
        for field_name in obj.keys():
            field_name in TestModel._fields


class Address(DictEmbeddedDocument):
    street = SimpleField()


class Person(DictEmbeddedDocument):
    name = SimpleField(required=True)
    address = SimpleField(link_cls=Address)


class ValidationTest(TestCase):
    def test_raise_validation_error(self):
        street = 'Pagoda street'
        self.assertRaises(
            SimpleFieldValidationError,
            Person.get_instance, address=street
        )

    def test_linking_cls(self):
        street = 'Pagoda street'
        person = Person.get_instance(
            address=Address.get_instance(street=street,),
            name='Max'
        )
        self.assertEqual(person.address.street, street)

    def test_auto_create_linking_cls_nested_object(self):
        """If passed correct structure expect that document validate and create
        instance of link_cls class automatically

        """
        street = 'Pagoda street'
        address_dict = {'street': street}
        self.assertRaises(
            SimpleFieldValidationError,
            Person.get_instance, address={'wrong address param': 'test'}
        )
        person = Person.get_instance(address=address_dict, name='Max')
        self.assertIsInstance(person, Person)
        self.assertIsInstance(person.address, Address)
        self.assertEqual(person.address.street, address_dict['street'])