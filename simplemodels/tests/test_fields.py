# -*- coding: utf-8 -*-
from decimal import Decimal
from unittest import TestCase
import six

from simplemodels import PYTHON_VERSION
from simplemodels.exceptions import ValidationError, ImmutableFieldError
from simplemodels.fields import IntegerField, FloatField, DecimalField, \
    BooleanField, CharField, DocumentField, ListField
from simplemodels.models import DictEmbeddedDocument, Document


class TypedFieldsTest(TestCase):
    def setUp(self):
        class SubDocument(DictEmbeddedDocument):
            int_field = IntegerField()

        self.subdocument = SubDocument

        class Model(Document):
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
            self.assertIsInstance(instance.char_field, unicode)
            self.assertEqual(instance.char_field, 'abc')

            instance = self.model(uchar_field='abc')
            self.assertIsInstance(instance.uchar_field, unicode)
            self.assertEqual(instance.uchar_field, u'abc')

            instance = self.model(uchar_field=1.0)
            self.assertIsInstance(instance.uchar_field, unicode)
            self.assertEqual(instance.uchar_field, u'1.0')

    def test_char_field_max_length(self):
        class User(Document):
            username = CharField(max_length=20)

        with self.assertRaises(ValidationError) as err:
            user = User(username='a' * 21)
            self.assertIsNone(user)
            self.assertIn('Max length is exceeded', err)

    def test_char_field_unicode(self):
        class User(Document):
            name = CharField(required=True)

        user_1 = User(name='John')
        user_2 = User(name=six.u('宝, 褒, 苞'))
        if PYTHON_VERSION == 2:
            self.assertIsInstance(user_1.name, unicode)
            self.assertIsInstance(user_2.name, unicode)
            self.assertEqual(user_2.name, six.u('宝, 褒, 苞'))
        else:
            self.assertIsInstance(user_1.name, str)

    def test_char_field_unicode_false(self):
        class User(Document):
            name = CharField(is_unicode=False)

        user = User(name='John')
        if PYTHON_VERSION == 2:
            self.assertFalse(isinstance(user.name, unicode))
        self.assertIsInstance(user.name, str)

    def test_doc(self):
        instance = self.model(doc_field={'int_field': '1'})
        self.assertIsInstance(instance.doc_field, self.subdocument)
        self.assertEqual(instance.doc_field, {'int_field': 1})

    def test_empty_nested(self):
        instance = self.model()
        self.assertIsNone(instance.doc_field.int_field)

    def test_immutable_field(self):
        class User(Document):
            name = CharField()
            system_id = IntegerField(immutable=True)

        user = User(system_id=0)
        self.assertEqual(user.system_id, 0)

        with self.assertRaises(ImmutableFieldError) as err:
            user.system_id = 1
            self.assertEqual(user.system_id, 0)
            self.assertIn('User.system_id field is immutable', err)

    def test_list_field(self):
        class Post(Document):
            text = CharField()
            tags = ListField(item_types=[str, float])

        # Test wrong tags type, must be list of items
        with self.assertRaises(ValidationError):
            post = Post(text='test', tags='Tags')
            self.assertIsNone(post)

        # Test wrong list item type, int is not accepted for Post
        with self.assertRaises(ValidationError):
            post = Post(text='test', tags=['a', 1, Decimal(1)])
            self.assertIsNone(post)

        post = Post(text='test', tags=['a', 1.0])
        self.assertTrue(post)

        # Test setter validation
        with self.assertRaises(ValidationError):
            post.tags = [Decimal(1)]
            # NOTE: This doesn't work
            # post.tags.append(123)

    def test_list_field_defaults(self):
        class Post(Document):
            text = CharField()
            tags = ListField(item_types=[str], default=['news'])

        p1 = Post()
        p1.tags.append('sport')
        self.assertEqual(p1.tags, ['news', 'sport'])
        p2 = Post()
        self.assertEqual(p2.tags, ['news'])
