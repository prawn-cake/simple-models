# -*- coding: utf-8 -*-
from decimal import Decimal
from unittest import TestCase
from datetime import datetime
from simplemodels import PYTHON_VERSION
from simplemodels.exceptions import ValidationError, ValidationRequiredError
from simplemodels.fields import SimpleField, IntegerField, BooleanField, \
    CharField, DecimalField, FloatField, DocumentField
from simplemodels.models import AttributeDict, DictEmbeddedDocument
from simplemodels.utils import Choices
import six


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
        return six.u("<{}({}): {}>".format(
            self.__class__.__name__, self.type, self.subject))

    def __unicode__(self):
        return six.u("<{}({}): {}>".format(
            self.__class__.__name__, self.type, self.subject))


class Address(DictEmbeddedDocument):
    street = SimpleField()


class Person(DictEmbeddedDocument):
    name = SimpleField(required=True)
    address = SimpleField(validator=Address)


#### End of test model classes ###


class AttributeDictTest(TestCase):
    def test_dict(self):

        ad = AttributeDict()
        ad._id = 1
        self.assertEqual(ad['_id'], 1)
        self.assertEqual(ad._id, 1)
        self.assertEqual(getattr(ad, '_id'), 1)

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
            contentBid = SimpleField(default=Money())

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
            l = SimpleField(default=list)

        a = A()
        self.assertEqual(a.f, 10)
        self.assertEqual(a.l, [])

    def test_simple_field_required(self):
        class TestDictDocument(DictEmbeddedDocument):
            xsi_type = SimpleField(required=True)

        self.assertRaises(ValidationRequiredError, TestDictDocument)
        self.assertRaises(
            ValidationRequiredError, TestDictDocument, xsi_type='')
        self.assertRaises(
            ValidationRequiredError, TestDictDocument, xsi_type=None)
        self.assertTrue(TestDictDocument(xsi_type='html'))

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

        document = DocumentWithProperty(a=1, b=2)

        self.assertEqual(document.c, '12')

    def test_get_instance_method(self):
        """ get_instance method should guarantee that object contains exactly
        same fields as described


        """
        class TestModel(DictEmbeddedDocument):
            a = SimpleField()
            b = SimpleField()

        source_data = {'a': 1, 'b': 2, 'c': 3, 'd': 4}
        obj = TestModel(**source_data)
        self.assertEqual(len(obj), len(TestModel._fields))
        for field_name in obj.keys():
            self.assertIn(field_name, TestModel._fields)

    def test_field_type(self):
        class PostAddress(DictEmbeddedDocument):
            street = SimpleField(validator=str)

        class User(DictEmbeddedDocument):
            id = SimpleField(validator=int)
            name = SimpleField(required=True, default='TestName')
            address = SimpleField(validator=PostAddress)

        a = User(id='1', name='Maks', address=PostAddress(street=999))
        self.assertIsInstance(a, User)
        self.assertIsInstance(a.address, PostAddress)
        self.assertEqual(a.id, 1)
        self.assertEqual(a.address.street, '999')

        a = User(
            id='1', name='Maks',
            address={'street': 999, 'city': 'Saint-Petersburg'}
        )
        self.assertIsInstance(a, User)
        self.assertIsInstance(a.address, PostAddress)
        self.assertEqual(a.id, 1)
        self.assertEqual(a.address.street, '999')
        # city is not declared as an Address field
        self.assertRaises(KeyError, getattr, a.address, 'city')

        # Expect a ValidationError: wrong 'address' format is passed
        self.assertRaises(
            ValidationError, User,
            id='1', name='Maks', address=[('street', 999), ]
        )

    def test_model_with_validator(self):
        class Timestamp(DictEmbeddedDocument):
            hour = SimpleField(validator=int)
            minute = SimpleField(validator=int)

        class Moment(DictEmbeddedDocument):
            start_date = SimpleField(
                validator=lambda value: datetime.strptime(
                    value, '%Y-%m-%dT%H:%M:%SZ'))
            count = SimpleField(validator=int)
            timestamp = SimpleField(validator=Timestamp)
            ts = SimpleField(validator=Timestamp)

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

    def test_model_optional_name(self):
        class RateModel(DictEmbeddedDocument):
            InterestRate = SimpleField(validator=float, name='Interest Rate')

        data = {"Interest Rate": "1.01"}
        my_model = RateModel(**data)
        self.assertEqual(len(my_model), 1)
        self.assertEqual(my_model.InterestRate, 1.01)

        my_model = RateModel(**data)
        self.assertEqual(len(my_model), 1)
        self.assertEqual(my_model.InterestRate, 1.01)
        self.assertEqual(my_model['Interest Rate'], 1.01)

    def test_model_optional_name_required(self):
        class RateModel(DictEmbeddedDocument):
            InterestRate = SimpleField(validator=float,
                                       name='Interest Rate',
                                       required=True)
        data = {"Interest Rate": "1.01"}
        my_model = RateModel(**data)
        self.assertEqual(my_model['Interest Rate'], 1.01)
        self.assertRaises(ValidationRequiredError, RateModel)


class ValidationTest(TestCase):
    def test_raise_validation_error(self):
        street = 'Pagoda street'
        self.assertRaises(ValidationError, Person, address=street)


class TypedFieldsTest(TestCase):
    def setUp(self):
        class SubDocument(DictEmbeddedDocument):
            int_field = IntegerField()

        self.subdocument = SubDocument

        class Model(DictEmbeddedDocument):
            int_field = IntegerField()
            float_field = FloatField()
            decimal_field = DecimalField()
            bool_field = BooleanField()
            char_field = CharField()
            uchar_field = CharField(is_unicode=True)
            doc_field = DocumentField(model=SubDocument)

        self.model = Model

    def test_int(self):
        instance = self.model(int_field='1')
        self.assertIsInstance(instance.int_field, int)
        self.assertEqual(instance.int_field, 1)
        self.assertRaises(ValidationError, self.model, int_field='a')

    def test_float(self):
        instance = self.model(float_field='1')
        self.assertIsInstance(instance.float_field, float)
        self.assertEqual(instance.float_field, 1.0)
        self.assertRaises(ValidationError, self.model, float_field='a')

    def test_decimal(self):
        instance = self.model(decimal_field=1.0)
        self.assertIsInstance(instance.decimal_field, Decimal)
        self.assertEqual(instance.decimal_field, Decimal('1.0'))
        self.assertRaises(ValidationError, self.model, decimal_field='a')

    def test_bool(self):
        for val in (1, True, 'abc'):
            instance = self.model(bool_field=val)
            self.assertIsInstance(instance.bool_field, bool)
            self.assertEqual(instance.bool_field, True)

        for val in ('', 0, None, False):
            instance = self.model(bool_field=val)
            self.assertIsInstance(instance.bool_field, bool)
            self.assertEqual(instance.bool_field, False)

    def test_char(self):
        if PYTHON_VERSION == 2:
            instance = self.model(char_field='abc')
            self.assertIsInstance(instance.char_field, str)
            self.assertEqual(instance.char_field, 'abc')

            instance = self.model(uchar_field='abc')
            self.assertIsInstance(instance.uchar_field, unicode)
            self.assertEqual(instance.uchar_field, u'abc')

            instance = self.model(uchar_field=1.0)
            self.assertIsInstance(instance.uchar_field, unicode)
            self.assertEqual(instance.uchar_field, u'1.0')

    def test_doc(self):
        instance = self.model(doc_field={'int_field': '1'})
        self.assertIsInstance(instance.doc_field, self.subdocument)
        self.assertEqual(instance.doc_field, {'int_field': 1})