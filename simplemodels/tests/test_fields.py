# -*- coding: utf-8 -*-
import hashlib
import unittest
from collections import OrderedDict
from decimal import Decimal, InvalidOperation

import six

from simplemodels import PYTHON_VERSION
from simplemodels.exceptions import FieldError, FieldRequiredError, ImmutableFieldError, ModelNotFoundError, \
    ValidationError
from simplemodels.fields import BooleanField, CharField, DecimalField, DictField, DocumentField, FloatField, \
    IntegerField, ListField, SimpleField
from simplemodels.models import Document


class FieldsTest(unittest.TestCase):

    def setUp(self):
        class SubDocument(Document):
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
        instance = self.model(dict(int_field='1'))
        self.assertIsInstance(instance.int_field, int)
        self.assertEqual(instance.int_field, 1)
        self.assertRaises(ValueError, self.model, dict(int_field='a'))

    def test_float(self):
        instance = self.model(dict(float_field='1'))
        self.assertIsInstance(instance.float_field, float)
        self.assertEqual(instance.float_field, 1.0)
        self.assertRaises(ValueError, self.model, dict(float_field='a'))

    def test_decimal(self):
        instance = self.model(dict(decimal_field=1.0))
        self.assertIsInstance(instance.decimal_field, Decimal)
        self.assertEqual(instance.decimal_field, Decimal('1.0'))
        self.assertRaises(InvalidOperation, self.model, dict(decimal_field='a'))

    def test_bool(self):
        for val in (1, True, 'abc'):
            instance = self.model(dict(bool_field=val))
            self.assertIsInstance(instance.bool_field, bool)
            self.assertEqual(instance.bool_field, True)

        for val in ('', 0, False):
            instance = self.model(dict(bool_field=val))
            self.assertIsInstance(instance.bool_field, bool)
            self.assertEqual(instance.bool_field, False)

        for val in (None, ):
            instance = self.model(dict(bool_field=val))
            self.assertNotIsInstance(instance.bool_field, bool)
            self.assertEqual(instance.bool_field, None)

    @unittest.skipIf(PYTHON_VERSION > 2, 'only py2 test')
    def test_char(self):
        instance = self.model(dict(char_field='abc'))
        self.assertIsInstance(instance.char_field, unicode)
        self.assertEqual(instance.char_field, 'abc')

        instance = self.model(dict(uchar_field='abc'))
        self.assertIsInstance(instance.uchar_field, unicode)
        self.assertEqual(instance.uchar_field, u'abc')

        instance = self.model(dict(uchar_field=1.0))
        self.assertIsInstance(instance.uchar_field, unicode)
        self.assertEqual(instance.uchar_field, u'1.0')

    def test_char_field_max_length(self):
        class User(Document):
            username = CharField(max_length=20)

        with self.assertRaises(ValidationError) as err:
            user = User(dict(username='a' * 21))
            self.assertIsNone(user)
            self.assertIn('Max length is exceeded', err)

    def test_char_field_unicode(self):
        class User(Document):
            name = CharField(required=True)

        user_1 = User(dict(name='John'))
        user_2 = User(dict(name=six.u('宝, 褒, 苞')))
        if PYTHON_VERSION == 2:
            self.assertIsInstance(user_1.name, unicode)
            self.assertIsInstance(user_2.name, unicode)
            self.assertEqual(user_2.name, six.u('宝, 褒, 苞'))
        else:
            self.assertIsInstance(user_1.name, str)

    def test_char_field_unicode_false(self):
        class User(Document):
            name = CharField(is_unicode=False)

        user = User(dict(name='John'))
        if PYTHON_VERSION == 2:
            self.assertFalse(isinstance(user.name, unicode))
        self.assertIsInstance(user.name, str)

    def test_char_field_none(self):
        class User(Document):
            name = CharField()

        user_1 = User(name=None)
        self.assertEqual(user_1.name, None)

        user_2 = User()
        self.assertEqual(user_2.name, None)
        user_2.name = None
        self.assertEqual(user_2.name, None)

    def test_doc(self):
        instance = self.model(dict(doc_field={'int_field': '1'}))
        self.assertIsInstance(instance.doc_field, self.subdocument)
        self.assertEqual(instance.doc_field, {'int_field': 1})

    def test_empty_nested(self):
        instance = self.model()
        self.assertIsNone(instance.doc_field.int_field)

    def test_immutable_field(self):
        class User(Document):
            name = CharField()
            system_id = IntegerField(immutable=True)

        user = User(dict(system_id=0))
        self.assertEqual(user.system_id, 0)

        with self.assertRaises(ImmutableFieldError) as err:
            user.system_id = 1
            self.assertEqual(user.system_id, 0)
            self.assertIn('User.system_id field is immutable', err)

    def test_documents_list_field(self):
        class User(Document):
            name = CharField()

        class Post(Document):
            text = CharField()
            viewed = SimpleField(
                coerce_=lambda items, **kw: [User(item, **kw) for item in items or []])

        post = Post(dict(text='abc', viewed=[{'name': 'John'}]))
        self.assertIsInstance(post, Post)
        self.assertIsInstance(post.viewed, list)

        for user in post.viewed:
            self.assertIsInstance(user, User)

    def test_dict_field(self):
        class User(Document):
            attrs = DictField(required=True)

            def get_attr_x(self):
                if 'x' in self.attrs:
                    return self.attrs['x']
                return None

            def set_attr_x(self, val):
                self.attrs['x'] = val

        error_values = (1, ['test'], {True, 2, 'x'}, (None, 23, False), None)
        for val in error_values:
            with self.assertRaises(ValidationError):
                user = User(attrs=val)
                self.assertIsNone(user)

        correct_values = ({'a': 1}, dict(a=None, b=False))
        for val in correct_values:
            user = User(dict(attrs=val))
            self.assertEqual(user.attrs, val)

        # Test __setitem__ and __getitem__ field methods
        user = User(dict(attrs={}))
        self.assertEqual(user.get_attr_x(), None)

        user.set_attr_x(1)
        self.assertEqual(user.get_attr_x(), 1)

    def test_dict_field_with_custom_dict_cls(self):
        # Check dict_cls parameter, must be always Mapping type
        with self.assertRaises(ValueError) as err:
            class FailedDoc(Document):
                attrs = DictField(dict_cls=list)
            failed = FailedDoc()
            self.assertIsNone(failed)
            self.assertIn('Wrong dict_cls parameter', str(err))

        class User(Document):
            attrs = DictField(required=True, dict_cls=OrderedDict)
        user = User(dict(attrs=[('b', 1), ('a', 2)]))
        self.assertIsInstance(user.attrs, OrderedDict)
        self.assertEqual(list(user.attrs.values()), [1, 2])


class FieldsAttributesTest(unittest.TestCase):

    def setUp(self):
        # fmt: fields cls, test value, extra init kwargs
        self.fields = [
            (SimpleField, ['my_field', 2, {'x': 1}, {1, 1, 2}], {}),
            (CharField, 'my_field', {}),
            (IntegerField, 101, {}),
            (FloatField, 999.998, {}),
            (BooleanField, True, {}),
            (ListField, [1, 2.0], {'of': float}),
            (DecimalField, Decimal('47'), {}),
            (DictField, {'answer': 42}, {}),
            # (DocumentField, {'name': 'Maks'}, {'model': User})
        ]

    def test_required(self):
        for field_cls, test_value, kwargs in self.fields:

            class MyDocument(Document):
                test_field = field_cls(required=True, **kwargs)

            # Test correct document creation
            doc = MyDocument(dict(test_field=test_value))
            self.assertIsInstance(doc, MyDocument)
            self.assertEqual(doc.test_field, test_value)

            # Test required error case
            if issubclass(field_cls, ListField):
                doc = MyDocument()
                self.assertEqual(doc, {'test_field': []})
            else:
                with self.assertRaises(FieldRequiredError) as err:
                    doc = MyDocument()
                    self.assertIsNone(doc)
                    self.assertIn('Field test_field is required', str(err))

    def test_default(self):
        for field_cls, test_value, kwargs in self.fields:
            class MyDocument(Document):
                test_field = field_cls(default=test_value, **kwargs)

            doc = MyDocument()
            self.assertEqual(doc.test_field, test_value)

    def test_choices(self):
        for field_cls, test_value, kwargs in self.fields:
            class MyDocument(Document):
                test_field = field_cls(default=test_value, **kwargs)

            doc = MyDocument()
            self.assertEqual(doc.test_field, test_value)


class DocumentFieldTest(unittest.TestCase):

    def test_str_model_lookup(self):
        class Address(Document):
            street = CharField()

        class User(Document):
            address = DocumentField(model='Address')

        user = User({'address': {'street': 'Morison street'}})
        self.assertEqual(user.address.street, 'Morison street')

    def test_str_model_lookup_error(self):
        with self.assertRaises(ModelNotFoundError) as err:
            class User(Document):
                address = DocumentField(model='Address1')

            self.assertIn("Model 'Address1' does not exist", err)


class ListFieldTest(unittest.TestCase):

    def test_base(self):
        class Post(Document):
            text = CharField()
            tags = ListField(of=float)

        # Test wrong tags type, must be list of items
        with self.assertRaises(ValueError):
            post = Post(dict(text='test', tags='Tags'))
            self.assertIsNone(post)

        # Test wrong list item type, int is not accepted for Post
        with self.assertRaises(ValueError):
            post = Post(dict(text='test', tags=['a', 1, Decimal(1)]))
            self.assertIsNone(post)

        post = Post(dict(text='text'))
        self.assertEqual(post.tags, [])

        post = Post(dict(text='test', tags=[2, 1.0]))
        self.assertIsInstance(post, Post)
        self.assertEqual(post.tags, [2.0, 1.0])

        post.tags.append(3)
        self.assertEqual(post.tags, [2.0, 1.0, 3.0])
        self.assertEqual(post.tags[:], [2.0, 1.0, 3.0])
        self.assertEqual(post.tags[-1], 3.0)

    def test_assign_list_value(self):
        class Post(Document):
            text = CharField()
            tags = ListField(of=float)

        post = Post(text='test', tags=[2, 1.0])
        # NOTE: it's ok cuz float(Decimal('1.1')) works fine
        post.tags = [Decimal('1.1')]
        self.assertEqual(post.tags, [1.1])

        with self.assertRaises(ValueError):
            post.tags = ['string value']

        post.tags.append(123)
        self.assertEqual(post.tags, [1.1, 123])

        # TODO: this should be uncommented as it shows the actual problem.
        # with self.assertRaises(ValidationError):
        #     post.tags.append('abc')

    def test_collection_methods(self):
        class Comment(Document):
            text = CharField()

        class Post(Document):
            text = CharField()
            comments = ListField(of=Comment)

        post = Post({'text': 'my post',
                            'comments': [
                                {'text': 'Comment #1'},
                                {'text': 'Comment #2'}]
                            })
        self.assertEqual(len(post.comments), 2)
        self.assertEqual(len(post.comments[:]), 2)

        self.assertEqual(post.comments[0].text, 'Comment #1')

        self.assertEqual(post.comments[1:], [{'text': 'Comment #2'}])
        self.assertEqual(post.comments[1:], [Comment({'text': 'Comment #2'})])

        self.assertTrue({'text': 'Comment #2'} in post.comments)
        self.assertTrue(Comment({'text': 'Comment #2'}) in post.comments)

        post.comments.append(dict(text='This is the last'))
        self.assertEqual(post.comments[-1], {'text': 'This is the last'})
        self.assertEqual(post.comments[-1], Comment({'text': 'This is the last'}))

        self.assertTrue({'text': 'This is the last'} in post.comments)
        self.assertTrue(Comment({'text': 'This is the last'}) in post.comments)

    def test_sorting(self):
        class Student(Document):
            name = CharField()
            courses = ListField(of=int)

        student = Student({'name': 'foobar', 'courses': [4, 2, 1]})
        student.courses.append(3)
        student.courses.insert(0, 5)

        self.assertEqual(student.courses, [5, 4, 2, 1, 3])
        student.courses.sort()
        self.assertEqual(student.courses, [1, 2, 3, 4, 5])
        student.courses.sort(reverse=True)
        self.assertEqual(student.courses, [5, 4, 3, 2, 1])

    def test_defaults(self):
        class Post(Document):
            text = CharField()
            tags = ListField(of=str, default=['news'])

        p1 = Post()
        p1.tags.append('sport')
        self.assertEqual(p1.tags, ['news', 'sport'])
        p2 = Post()
        self.assertEqual(p2.tags, ['news'])

    def test_default_empty(self):
        class Post(Document):
            text = CharField()
            tags = ListField(of=str, required=True)

        p = Post({})
        self.assertEqual(p.tags, [])
        self.assertEqual(p, {'text': None, 'tags': []})

    def test_list_field_of_documents(self):
        class Comment(Document):
            body = CharField()

        class User(Document):
            name = CharField()
            comments = ListField(of=Comment)

        comments = [
            {'body': 'comment #1'},
            {'body': 'seconds comment'},
            {'body': 'one more comment'},
        ]
        user = User({
            'name': 'John Smith',
            'comments': comments
        })

        user.comments.append({'body': 'Last comment'})
        user.comments.insert(0, Comment({'body': 'The very first comment'}))

        self.assertIsInstance(user, User)
        self.assertEqual(user.comments, [{'body': 'The very first comment'}] + comments + [{'body': 'Last comment'}])
        for comment in user.comments:
            self.assertTrue(comment.body)
            self.assertIsInstance(comment, Comment)

        comment = Comment(dict(body='test comment'))
        user = User(dict(name='John Smith', comments=[comment]))
        self.assertIsInstance(user, User)
        self.assertEqual(user.comments, [{'body': 'test comment'}])

    def test_override_validators(self):
        """Overriding 'validators' is not allowed for ListField, the proper
        interface is to use 'of' parameter

        """

        sha256 = lambda x: hashlib.sha256(x.encode('utf-8')).hexdigest()

        class Post(Document):
            id = IntegerField()
            comments = ListField(of=sha256, validators=[str])

        post = Post({'id': 1, 'comments': ['comment1', 'comment2']})
        for comment in post.comments:
            self.assertEqual(len(comment), 64)

        with self.assertRaises(Exception):
            post.comments.append(100500)

    def test_multiple_instances(self):
        class Post(Document):
            text = CharField()
            tags = ListField(of=str, required=True)

        post1 = Post(dict(text='Post #1', tags=None)) # if the field is `required`, should not it fail here?
        post2 = Post(dict(text='Post #2', tags=[]))
        post3 = Post(dict(text='Post #2', tags=['python', 'Ruby', 'Java Script']))

        post1.tags.append('Java')
        post2.tags.extend(['C++', 'Go'])
        post3.tags.pop()
        post3.tags[1] = 'bash'

        self.assertEqual(post1.tags, ['Java'])
        self.assertEqual(post2.tags, ['C++', 'Go'])
        self.assertEqual(post3.tags, ['python', 'bash'])

    def test_append(self):
        class Post(Document):
            tags = ListField(of=int)

        post = Post()
        with self.assertRaises(ValueError):
            post.tags.append("foobar")

    def test_list_of_self(self):
        class User(Document):
            friends = ListField(of='User')

        user_foo = User()
        user_bar = User(dict(friends=[user_foo]))
        self.assertEqual(user_foo.friends, [])
        self.assertEqual(user_foo.friends, [])
        # check access two times
        self.assertEqual(user_bar.friends[0], user_foo)
        self.assertEqual(user_bar.friends[0], user_foo)

        # TODO: this should raise RecursionLimit exception, but as we're
        # TODO: adding a copy of an object it doesn't.
        # TODO: Do we care?
        user_foo.friends.append(user_bar)
        print(user_foo)


class ValidatorsTest(unittest.TestCase):

    def test_fail_validators_as_non_list(self):

        with self.assertRaises(FieldError) as err:
            class User(Document):
                name = CharField(validators=str)

            self.assertIn('validators must be list, tuple or set', str(err))

    def test_validator_raises_validation_error(self):
        def validate_password(value):
            if len(value) < 10:
                raise ValidationError('Password is too short')
            return value

        class User(Document):
            name = CharField()
            password = CharField(validators=[validate_password])

        with self.assertRaises(ValidationError) as err:
            user = User({'name': 'John', 'password': 'qwerty'})
            self.assertIsNone(user)
            self.assertIn('ValidationError: Password is too short', str(err))
