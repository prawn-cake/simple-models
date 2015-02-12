# -*- coding: utf-8 -*-
from unittest import TestCase
from datetime import datetime
from simplemodels.exceptions import ValidationError
from simplemodels.fields import SimpleField
from simplemodels.models import AttributeDict, DictEmbeddedDocument
from simplemodels.utils import Choices
from simplemodels.validators import get_validator


### Test model classes ###


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


class Address(DictEmbeddedDocument):
    street = SimpleField()


class Person(DictEmbeddedDocument):
    name = SimpleField(required=True)
    address = SimpleField(type=Address)


#### End of test model classes ###


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
        self.assertIsInstance(bid._fields, dict)
        self.assertIsInstance(bid._required_fields, tuple)
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

        self.assertRaises(ValidationError, TestDictDocument)

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

    def test_field_type(self):
        class PostAddress(DictEmbeddedDocument):
            street = SimpleField(type=str)

        class ModelA(DictEmbeddedDocument):
            id = SimpleField(type=int)
            name = SimpleField(required=True, default='TestName')
            address = SimpleField(type=PostAddress)

        a = ModelA.get_instance(
            id='1',
            name='Maks',
            address=PostAddress.get_instance(street=999)
        )
        self.assertIsInstance(a, ModelA)
        self.assertIsInstance(a.address, PostAddress)
        self.assertEqual(a.id, 1)
        self.assertEqual(a.address.street, '999')

        a = ModelA.get_instance(
            id='1', name='Maks',
            address={'street': 999, 'city': 'Saint-Petersburg'}
        )
        self.assertIsInstance(a, ModelA)
        self.assertIsInstance(a.address, PostAddress)
        self.assertEqual(a.id, 1)
        self.assertEqual(a.address.street, '999')
        # city is not declared as an Address field
        self.assertRaises(KeyError, getattr, a.address, 'city')

        # Expect a ValidationError: wrong 'address' format is passed
        self.assertRaises(
            ValidationError, ModelA.get_instance,
            id='1', name='Maks', address=[('street', 999), ]
        )

    def test_new_constructor(self):
        class PostAddress(DictEmbeddedDocument):
            street = SimpleField(type=str)

        address_1 = PostAddress(street='Pobeda street', apartments='32')
        address_2 = PostAddress.get_instance(
            street='Pobeda street', apartments='32')
        self.assertEqual(address_1, address_2)

    def test_model_with_validator(self):
        class Timestamp(DictEmbeddedDocument):
            hour = SimpleField(validator=int)
            minute = SimpleField(validator=int)

        class Moment(DictEmbeddedDocument):
            start_date = SimpleField(
                validator=lambda value: datetime.strptime(
                    value, '%Y-%m-%dT%H:%M:%SZ'))
            count = SimpleField(validator=int)
            timestamp = SimpleField(validator=Timestamp.from_dict)
            ts = SimpleField(validator=Timestamp.from_dict)

        moment = Moment(
            start_date='2009-04-01T23:51:23Z',
            count='1',
            timestamp=dict(hour=10, minute=59),
            ts=Timestamp(hour=10, minute=59)
        )
        self.assertIsInstance(moment.start_date, datetime)
        self.assertIsInstance(moment.count, int)
        self.assertIsInstance(moment.timestamp, Timestamp)
        self.assertIsInstance(moment.ts, Timestamp)

        self.assertRaises(ValidationError, Moment, count='a')


class ValidationTest(TestCase):
    def test_raise_validation_error(self):
        street = 'Pagoda street'
        self.assertRaises(
            ValidationError,
            Person.get_instance, address=street
        )


class ValidatorsTest(TestCase):
    def test_null_validator(self):
        value = 10
        value = get_validator(None).validate(value)
        # expect validator nothing to do and return value as-is
        self.assertEqual(value, 10)

    def test_str_validator(self):
        value = 10
        value = get_validator(str).validate(value)
        # expect converted to str value
        self.assertEqual(value, '10')

    def test_int_validator(self):
        value = 10
        value = get_validator(int).validate(value)
        self.assertEqual(value, 10)
        # Expect an error
        value = 'aa'
        self.assertRaises(ValidationError, get_validator(int).validate, value)

    def test_dict_embedded_document_validator(self):
        class DocumentA(DictEmbeddedDocument):
            title = SimpleField()
            number = SimpleField()

        class DocumentB(DictEmbeddedDocument):
            title = SimpleField()
            number = SimpleField()

        value = DocumentA.get_instance(title='document1', number=1)
        value = get_validator(DictEmbeddedDocument).using(
            DocumentA).validate(value)
        self.assertIsInstance(value, DocumentA)
        self.assertEqual(value.title, 'document1')
        self.assertEqual(value.number, 1)

        value = dict(title='document1', number=1)
        value = get_validator(DictEmbeddedDocument).using(
            DocumentB).validate(value)
        self.assertIsInstance(value, DocumentB)
        self.assertEqual(value.title, 'document1')
        self.assertEqual(value.number, 1)

        self.assertRaises(
            ValidationError, get_validator(DictEmbeddedDocument).validate,
            ['invalid parameter']
        )

    def test_datetime_validator(self):
        # FIXME: DEPRECATED
        json_value = '2009-04-01T23:51:23Z'
        iso8601_value = '2009-04-01T23:51:23'
        iso_date_value = '2009-04-01'
        iso_time_value = '23:51:23'
        custom_c_value = 'Tue Aug 16 21:30:00 1988'

        validator = get_validator('datetime')

        # test default format
        self.assertIsInstance(validator.validate(json_value), datetime)

        # test templates
        self.assertIsInstance(
            validator.validate(json_value, dt_template='json'),
            datetime)

        self.assertIsInstance(
            validator.validate(iso8601_value, dt_template='iso8601'),
            datetime)

        self.assertIsInstance(
            validator.validate(iso_date_value, dt_template='iso_date'),
            datetime)

        self.assertIsInstance(
            validator.validate(iso_time_value, dt_template='iso_time'),
            datetime)

        # test custom format
        self.assertIsInstance(
            validator.validate(custom_c_value, format='%c'),
            datetime)