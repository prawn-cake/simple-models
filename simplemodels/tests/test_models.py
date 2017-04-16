# -*- coding: utf-8 -*-
import json
import time
from datetime import datetime
from unittest import TestCase

from simplemodels.exceptions import ValidationError, FieldRequiredError, \
    DefaultValueError, ImmutableDocumentError, ModelValidationError
from simplemodels.fields import SimpleField, IntegerField, CharField, \
    DocumentField, FloatField, BooleanField, ListField
from simplemodels.models import AttributeDict, Document, ImmutableDocument, \
    registry


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

    def test_nested_dict_access_via_attributes(self):
        # Test nested attributes on create (on get in fact)
        d = AttributeDict(a=1, nested=dict(b=2, nested_2=dict(c=3)))
        self.assertEqual(d.a, 1)
        self.assertEqual(d.nested.b, 2)
        self.assertEqual(d.nested.nested_2.c, 3)
        self.assertEqual(d, {'a': 1, 'nested': {'b': 2, 'nested_2': {'c': 3}}})

        # Test nested attributes on set
        d_2 = AttributeDict()
        d_2.a = 1
        d_2.nested = dict(b=2)
        d_2.nested.nested_2 = dict(c=3)
        self.assertEqual(d_2.a, 1)
        self.assertEqual(d_2.nested.b, 2)
        self.assertEqual(d_2.nested.nested_2.c, 3)
        self.assertEqual(
            d_2, {'a': 1, 'nested': {'b': 2, 'nested_2': {'c': 3}}})


class DocumentTest(TestCase):

    def test_document(self):
        class Money(Document):

            """Nested"""

            xsi_type = SimpleField('Money')
            microAmount = SimpleField()

        class BidEmbedded(Document):
            xsi_type = CharField(default='BidEmbedded')
            contentBid = DocumentField(model=Money)

        bid = BidEmbedded()

        self.assertIsInstance(bid, dict)
        self.assertIsInstance(bid._fields, dict)
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
        class A(Document):
            f = SimpleField(default=10)
            l = SimpleField(default=list)

        a = A()
        self.assertEqual(a.f, 10)
        self.assertEqual(a.l, [])

    def test_simple_field_required(self):
        class TestDocument(Document):
            xsi_type = SimpleField(required=True)

        with self.assertRaises(FieldRequiredError) as err:
            doc = TestDocument()
            self.assertIsNone(doc)
            self.assertIn('Field xsi_type is required', str(err))

        self.assertRaises(
            FieldRequiredError, TestDocument, dict(xsi_type=''))
        self.assertRaises(
            FieldRequiredError, TestDocument, dict(xsi_type=None))
        self.assertTrue(TestDocument(dict(xsi_type='html')))

    def test_default_values_with_several_instances(self):
        from simplemodels.tests.stub_models import MailboxItem

        td = MailboxItem()
        td_2 = MailboxItem(dict(is_read=True))

        self.assertFalse(td.is_read)
        self.assertTrue(td_2.is_read)

        td.is_read = True
        td_2.is_read = False
        self.assertTrue(td.is_read)
        self.assertTrue(td['is_read'])
        self.assertFalse(td_2.is_read)

    def test_default_values_init(self):
        class Message(Document):
            ts = SimpleField(default=datetime.now)

        # Expect that default value will differ at 1 sec
        msg_1 = Message()
        time.sleep(1)
        msg_2 = Message()
        self.assertEqual((msg_2.ts - msg_1.ts).seconds, 1)

    def test_wrong_default_callable(self):
        def get_id():
            return 'Not int'

        with self.assertRaises(ValidationError):
            class Message(Document):
                id = IntegerField(default=get_id)
            msg = Message()
            self.assertIsNone(msg)

    def test_getting_classname(self):
        from simplemodels.tests.stub_models import Address

        self.assertEqual(Address.__name__, 'Address')

    def test_property_getter(self):
        class DocumentWithProperty(Document):
            a = SimpleField()
            b = SimpleField()

            @property
            def c(self):
                return str(self.a) + str(self.b)

        document = DocumentWithProperty(dict(a=1, b=2))

        self.assertEqual(document.c, '12')

    def test_fields_container(self):
        """ get_instance method should guarantee that object contains exactly
        same fields as described


        """
        class TestModel(Document):
            a = SimpleField()
            b = SimpleField()

        source_data = {'a': 1, 'b': 2, 'c': 3, 'd': 4}
        obj = TestModel(**source_data)
        self.assertEqual(len(obj), len(TestModel._fields))
        for field_name in obj.keys():
            self.assertIn(field_name, TestModel._fields)

    def test_field_type(self):
        class PostAddress(Document):
            street = CharField()

        class User(Document):
            id = SimpleField(validators=[int])
            name = SimpleField(required=True, default='TestName')
            address = DocumentField(model=PostAddress)

        a = User(dict(id='1', name='Maks', address=PostAddress(dict(street=999))))
        self.assertIsInstance(a, User)
        self.assertIsInstance(a.address, PostAddress)
        self.assertEqual(a.id, 1)
        self.assertEqual(a.address.street, '999')

        a = User(
            dict(
                id='1', name='Maks',
                address={'street': 999, 'city': 'Saint-Petersburg'}
            )
        )
        self.assertIsInstance(a, User)
        self.assertIsInstance(a.address, PostAddress)
        self.assertEqual(a.id, 1)
        self.assertEqual(a.address.street, '999')
        # city is not declared as an Address field
        self.assertRaises(AttributeError, getattr, a.address, 'city')

        # Expect a ValidationError: wrong 'address' format is passed
        self.assertRaises(
            ValidationError, User,
            dict(id='1', name='Maks', address=[('street', 999), ])
        )

    def test_model_with_validator(self):
        class Timestamp(Document):
            hour = SimpleField(validators=[int])
            minute = SimpleField(validators=[int])

        class Moment(Document):
            start_date = SimpleField(
                validators=[lambda value: datetime.strptime(
                    value, '%Y-%m-%dT%H:%M:%SZ')])
            count = SimpleField(validators=[int])
            timestamp = DocumentField(model=Timestamp)
            ts = DocumentField(model=Timestamp)

        moment = Moment(
            dict(
                start_date='2009-04-01T23:51:23Z',
                count='1',
                timestamp=dict(hour=10, minute=59),
                ts=Timestamp(hour=10, minute=59)
            )
        )
        self.assertIsInstance(moment.start_date, datetime)
        self.assertIsInstance(moment.count, int)
        self.assertIsInstance(moment.timestamp, Timestamp)
        self.assertIsInstance(moment.ts, Timestamp)

        self.assertRaises(ValidationError, Moment, dict(count='a'))

    def test_model_verbose_name(self):
        class RateModel(Document):
            InterestRate = FloatField(name='Interest Rate')

        data = {"Interest Rate": "1.01"}
        my_model = RateModel(data)
        self.assertEqual(len(my_model), 1)
        self.assertEqual(my_model.InterestRate, 1.01)

        my_model = RateModel(data)
        self.assertEqual(len(my_model), 1)
        self.assertEqual(my_model.InterestRate, 1.01)
        self.assertEqual(my_model['Interest Rate'], 1.01)

    def test_model_verbose_name_required(self):
        class RateModel(Document):
            InterestRate = FloatField(name='Interest Rate', required=True)
        data = {"Interest Rate": "1.01"}
        my_model = RateModel(data)
        self.assertEqual(my_model['Interest Rate'], 1.01)
        self.assertRaises(FieldRequiredError, RateModel)

    def test_allow_extra_fields_attribute(self):
        """ Create document with ALLOW_EXTRA_FIELDS = True and expect that all
         extra fields will be stored, otherwise will be filtered

        """

        class LogMessage(Document):

            class Meta:
                ALLOW_EXTRA_FIELDS = True

            timestamp = CharField()
            app_name = CharField()
            text = CharField(max_length=500)

        msg = LogMessage(
            dict(
                timestamp=datetime.now(),
                app_name='Logger',
                text='test log message',
                level='DEBUG'  # extra field isn't described in the document
            )
        )
        self.assertEqual(msg.level, 'DEBUG')

    def test_choices_option(self):
        class LogMessage(Document):
            level = CharField(choices=['INFO', 'DEBUG', 'ERROR'])
            text = CharField(max_length=500)

        with self.assertRaises(ValidationError):
            # Put wrong log level
            message = LogMessage(dict(level='FATAL', text='Test log message'))
            self.assertIsNone(message)

        message = LogMessage(dict(level='DEBUG', text='Test log message'))
        self.assertTrue(message)

        with self.assertRaises(ValueError) as err:
            class Message(Document):
                tag = CharField(choices='INFO, DEBUG')
            self.assertIn('Wrong choices data type', str(err))

    def test_mutable_default_values(self):
        class Post(Document):
            tags = SimpleField(default=['news'])
        p = Post()
        self.assertEqual(p.tags, ['news'])
        p.tags.append('sport')
        self.assertEqual(p.tags, ['news', 'sport'])
        p2 = Post()
        self.assertEqual(p2.tags, ['news'])

    def test_inheritance(self):
        class Message(Document):
            text = CharField(required=True)

        class UserMessage(Message):
            user_id = IntegerField()

        msg = UserMessage(dict(text='message text'))
        self.assertIn('text', msg)
        self.assertIn('user_id', msg)

        msg = UserMessage(dict(text='user message text'))
        self.assertEqual(msg.user_id, None)
        self.assertEqual(msg.text, 'user message text')

    def test_multiple_inheritance(self):
        class AuthMixin(Document):
            username = CharField(required=True)

        class UserMixin(Document):
            id = IntegerField()

        class User(AuthMixin, UserMixin):
            full_name = CharField()

        user = User(dict(username='John'))
        self.assertEqual(user.username, 'John')
        self.assertEqual(user.id, None)
        self.assertEqual(user.full_name, '')

        class BankAccountMixin(Document):
            account_id = IntegerField()
            bank_name = CharField(default='Golden sink')

        class MyUser(User, BankAccountMixin):
            id = FloatField(required=True)

        # expect that inherited username field is still required
        with self.assertRaises(FieldRequiredError) as err:
            my_user = MyUser(dict(id=1))
            self.assertIsNone(my_user)
            self.assertIn('Field username is required', str(err))

        # Check that id value was overridden and coerced to float
        my_user = MyUser(dict(id=1, username='Max'))
        self.assertIsInstance(my_user.id, float)

        # Check fields existence
        self.assertEqual(my_user.full_name, '')
        self.assertEqual(my_user.account_id, None)
        self.assertEqual(my_user.bank_name, 'Golden sink')
        self.assertEqual(my_user, {'id': 1.0,
                                   'full_name': '',
                                   'username': 'Max',
                                   'account_id': None,
                                   'bank_name': 'Golden sink'})

    def test_post_model_validation(self):
        class User(Document):
            name = CharField()
            password = CharField(required=True)
            is_admin = BooleanField(default=False)

            @staticmethod
            def validate_password(document, value):
                if document.is_admin and len(value) < 10:
                    raise ModelValidationError(
                        'Admin password is too short (< 10 characters)')
                return value

        with self.assertRaises(ModelValidationError) as err:
            user = User(dict(name='Mikko', password='123', is_admin=True))
            self.assertIn('Admin password is too short', str(err))
            self.assertIsNone(user)

        user = User(dict(name='Mikko', password='1234567890', is_admin=True))
        self.assertIsInstance(user, User)

    def test_model_with_self_field(self):
        class User(Document):

            class Meta:
                ALLOW_EXTRA_FIELDS = True

            name = CharField()
            self = CharField()
            cls = CharField()
            User_ = CharField()

        class Company(Document):
            name = CharField()

        data = {
            'name': 'John Smith',
            'self': 'Handsome',
            'cls': 'So fresh, So clean clean',
            'unused': 'foo/bar',
            'User_': 'X'
        }

        user = User(data)
        self.assertIsInstance(user, User)
        self.assertEqual(user, data)
        company = Company(data)
        self.assertIsInstance(company, Company)

    def test_instance_check(self):
        class User(Document):
            id = IntegerField()
            name = CharField()

        user = User(id=1, name='John')
        self.assertTrue(isinstance(user, User))
        self.assertFalse(isinstance({'id': 1, 'name': 'John'}, User))

    def test_fail_create_model_with_non_dict_input(self):
        class User(Document):
            id = IntegerField()
            name = CharField()

        with self.assertRaises(ModelValidationError):
            User('this must be a dict')


class DocumentMetaOptionsTest(TestCase):

    def test_nested_meta(self):
        class Message(Document):
            text = SimpleField()

            class Meta:
                ALLOW_EXTRA_FIELDS = False
                OMIT_MISSED_FIELDS = True

        msg = Message()
        self.assertEqual(msg._meta.OMIT_MISSED_FIELDS, True)
        self.assertEqual(msg._meta.ALLOW_EXTRA_FIELDS, False)

    def test_nested_meta_with_inheritance(self):
        class Message(Document):
            text = SimpleField()

            class Meta:
                ALLOW_EXTRA_FIELDS = False
                OMIT_MISSED_FIELDS = True

        class LogMessage(Message):
            logfile = CharField()

            class Meta:
                OMIT_MISSED_FIELDS = False

        # Expect that Message meta options will be inherited
        log_msg = LogMessage()
        self.assertEqual(log_msg._meta.OMIT_MISSED_FIELDS, False)
        self.assertEqual(log_msg._meta.ALLOW_EXTRA_FIELDS, False)

    def test_omit_missed_fields_attribute(self):
        class Message(Document):
            text = CharField(max_length=120)

        msg = Message()
        self.assertEqual(msg, {'text': ''})

        class MessageWithoutNone(Document):

            class Meta:
                OMIT_MISSED_FIELDS = True

            text = CharField()

        msg = MessageWithoutNone()
        self.assertEqual(msg, {})
        self.assertEqual(msg.text, None)

        msg.text = None
        self.assertEqual(msg, {'text': ''})
        self.assertEqual(msg.text, '')

    def test_omit_missed_fields_attribute_with_defaults(self):
        class User(Document):
            name = CharField(max_length=120)
            role = CharField(default='admin')

            class Meta:
                OMIT_MISSED_FIELDS = True

        user = User()
        self.assertEqual(user, {'role': 'admin'})
        self.assertEqual(user.role, 'admin')

    def test_omit_missed_fields_with_required(self):
        class User(Document):
            name = CharField(required=True)
            role = CharField()

            class Meta:
                OMIT_MISSED_FIELDS = True

        with self.assertRaises(ValidationError):
            user = User()
            self.assertIsNone(user)

        user = User(dict(name='Mr.Robot'))
        self.assertEqual(user, {'name': 'Mr.Robot'})


class ValidationTest(TestCase):

    def test_raise_validation_error(self):
        from simplemodels.tests.stub_models import Person

        with self.assertRaises(ValidationError):
            p = Person(address='Pagoda street')
            self.assertIsNone(p)

    def test_validation_with_default_values(self):
        # Expect an error on class initialization step
        with self.assertRaises(DefaultValueError):
            class A(Document):
                id = IntegerField(default='a')

        # Accepted case: string to int will be forced
        class B(Document):
            id = IntegerField(default='1')

        b = B()
        self.assertEqual(b.id, 1)

        # Unicode case
        # with self.assertRaises(ValidationDefaultError):
        #     class C(Document):
        #         name = CharField(default=u'\x80')


class ImmutableDocumentTest(TestCase):

    def test_immutable_document(self):
        class User(ImmutableDocument):
            id = IntegerField(default=1)
            name = CharField(default='John')

        user = User()
        self.assertEqual(user.id, 1)
        with self.assertRaises(ImmutableDocumentError):
            user.name = 'Jorge'

        with self.assertRaises(ImmutableDocumentError):
            setattr(user, 'name', 'Jorge')

        with self.assertRaises(ImmutableDocumentError):
            user['name'] = 'Jorge'

    def test_immutable_nested_document(self):
        class MetaInfo(ImmutableDocument):
            id = CharField(default='unknown')
            login = CharField(default='guest')

        class User(Document):
            name = CharField()
            meta = DocumentField(model=MetaInfo)

        user = User()

        # Check init params
        self.assertEqual(user.meta.login, 'guest')

        # Try to set immutable nested doc field, expect error
        with self.assertRaises(ImmutableDocumentError):
            user.meta.login = 'admin'

        # Try to set mutable top-level name field
        user.name = 'Jorge'
        self.assertEqual(user.name, 'Jorge')


class JsonValidationTest(TestCase):

    def setUp(self):
        class Address(Document):
            city = CharField(default='St.Petersburg')

        class User(Document):
            id = IntegerField(default=0)
            name = CharField(default='John')
            height = FloatField(default=165.5)
            # salary = DecimalField(default=10000)
            address = DocumentField(model=Address)
            is_married = BooleanField(default=False)
            social_networks = ListField(of=str,
                                        default=['facebook.com', 'google.com'])

        self.user_cls = User
        self.user = User()

    def test_json_dumps(self):
        # Serialize document to json
        serialized = json.dumps(self.user)
        self.assertIsInstance(serialized, str)

        # Deserialize
        deserialized = json.loads(serialized)
        self.assertIsInstance(deserialized, dict)

        user = self.user_cls(**deserialized)
        self.assertEqual(user.id, 0)
        self.assertEqual(user.name, 'John')
        self.assertEqual(user.height, 165.5)
        self.assertEqual(user.address.city, 'St.Petersburg')
        self.assertEqual(user.is_married, False)
        self.assertEqual(user.social_networks, ['facebook.com', 'google.com'])

    def test_none_val_for_not_required_fields(self):
        """Expect that if field is not required None value is accepted

        """

        class Post(Document):
            owner_id = IntegerField(required=False)

        post_1 = Post()
        self.assertIsNone(post_1.owner_id)
        json_data = json.dumps(post_1)
        post_2 = Post(**json.loads(json_data))
        self.assertIsNone(post_2.owner_id)

        post_3 = Post(owner_id=None)
        self.assertIsNone(post_3.owner_id)


class RegistryTest(TestCase):

    def test_registry(self):
        class User(Document):
            pass

        self.assertIn('User', registry)
        self.assertIs(registry['User'], User)
