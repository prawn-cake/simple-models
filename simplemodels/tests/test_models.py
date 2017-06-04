# -*- coding: utf-8 -*-
import json
import os
import os.path as op
import time
from datetime import datetime
from unittest import TestCase

from simplemodels.exceptions import FieldRequiredError, ImmutableDocumentError, \
    ModelValidationError, ValidationError
from simplemodels.fields import BooleanField, CharField, DateTimeField, \
    DocumentField, FloatField, IntegerField, ListField, SimpleField
from simplemodels.models import Document, ImmutableDocument, registry
from simplemodels.tests.stub_models import Address, Comment, Person, Post


CUR_DIR = op.abspath(op.dirname(__file__))
FIXTURES_DIR = op.join(CUR_DIR, 'fixtures')


def get_json_fixture(fixture_name):
    with open(op.join(FIXTURES_DIR, fixture_name)) as fd:
        return json.load(fd)


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

        self.assertIsInstance(bid.as_dict(), dict)
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

        class Message(Document):
            id = IntegerField(default=get_id)

        with self.assertRaises(ValueError):
            Message()

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
        class TestModel(Document):
            a = SimpleField()
            b = SimpleField()

        source_data = {'a': 1, 'b': 2, 'c': 3, 'd': 4}
        obj = TestModel(source_data)
        self.assertEqual(len(obj), len(TestModel._fields))
        for field_name in obj.keys():
            self.assertIn(field_name, TestModel._fields)

    def test_field_type(self):
        class PostAddress(Document):
            street = CharField()

        class User(Document):
            id = IntegerField()
            name = SimpleField(required=True, default='TestName')
            address = DocumentField(model=PostAddress)

        a = User(
            dict(
                id='1',
                name='Maks',
                address=PostAddress(
                    dict(
                        street=999))))
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
            hour = IntegerField()
            minute = IntegerField()

        class Moment(Document):
            start_date = DateTimeField()
            count = IntegerField()
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

        self.assertRaises(ValueError, Moment, dict(count='a'))

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
        self.assertEqual(user.full_name, None)

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
        self.assertEqual(my_user.full_name, None)
        self.assertEqual(my_user.account_id, None)
        self.assertEqual(my_user.bank_name, 'Golden sink')
        self.assertDictEqual(my_user.as_dict(), {'id': 1.0,
                                                 'full_name': None,
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

    def test_update_value(self):
        from simplemodels.tests.stub_models import Address

        address = Address(dict(street='foo'))
        self.assertEqual(address.street, 'foo')
        self.assertEqual(address['street'], 'foo')

        address.street = 'bar'
        self.assertEqual(address.street, 'bar')
        self.assertEqual(address['street'], 'bar')

        address['street'] = 'baz'
        self.assertEqual(address.street, 'baz')
        self.assertEqual(address['street'], 'baz')

    def test_key_with_special_symbols(self):
        class Foo(Document):
            bar = CharField(name='special-attribute with unexpected symbols!')

        foo = Foo({'special-attribute with unexpected symbols!': 'baz'})
        self.assertEqual(foo.bar, 'baz')
        self.assertEqual(
            foo['special-attribute with unexpected symbols!'], 'baz')
        self.assertEqual(
            getattr(
                foo,
                'special-attribute with unexpected symbols!'),
            'baz')

    def test_extra_attributes(self):
        class Foo(Document):

            class Meta:
                ALLOW_EXTRA_FIELDS = True

        data = {
            'hello': 'world',
            'special-attribute with unexpected symbols!': 'baz'}
        foo = Foo(data)

        self.assertEqual(foo.hello, 'world')
        self.assertEqual(foo['hello'], 'world')
        self.assertEqual(getattr(foo, 'hello'), 'world')

        self.assertEqual(
            foo['special-attribute with unexpected symbols!'], 'baz')
        self.assertEqual(
            getattr(
                foo,
                'special-attribute with unexpected symbols!'),
            'baz')
        self.assertDictEqual(foo.as_dict(), data)

        data1 = {'some name': {'another some name': [1, 3, 5]}}
        foo1 = Foo(data1)
        self.assertEqual(foo1['some name'], {'another some name': [1, 3, 5]})
        self.assertEqual(foo1['some name']['another some name'], [1, 3, 5])
        self.assertDictEqual(foo1.as_dict(), data1)

        data2 = {':x:': ':y:', 'foo1': foo1}
        foo2 = Foo(data2)
        self.assertEqual(foo2[':x:'], ':y:')
        self.assertEqual(foo2.foo1, foo1)
        self.assertEqual(foo2.foo1, foo1.as_dict())
        self.assertEqual(foo2.as_dict(), {':x:': ':y:', 'foo1': data1})

    def test_init_with_kwargs(self):
        class Base(Document):

            def __init__(self, data, password, **kwargs):
                self.password = password
                super(Base, self).__init__(data=data, password=password, **kwargs)

        class Tag(Base):
            value = CharField()

        class TagsContainer(Base):
            tags = ListField(of=Tag)

        class User(Base):
            name = CharField()
            tag = DocumentField(TagsContainer)

        user = User(password='secret',
                    data={'name': 'tu-ti-ta-ta',
                          'tag': {'tags': [dict(value='foo'), dict(value='bar')]}})
        self.assertEqual(user.password, 'secret')
        self.assertEqual(user.tag.tags[0].password, 'secret')
        user.tag.tags.append(Tag(dict(value='bar'), 'secret'))
        # # user.tag.tags.append(dict(value='bar'))  # THIS DOESN't WORK!!!
        self.assertEqual(user.tag.tags[1].password, 'secret')


class DocumentToPythonTest(TestCase):

    def setUp(self):
        self.address_empty = Address()
        self.address_1 = Address(dict(street="Park Boulevard", zip='4591'))
        self.address_2 = Address(dict(street="Freshour Circle", zip='3329'))
        self.address_3 = Address(dict(street="Edsel Road", zip=938))

        self.person_cara = Person(
            dict(name='Cara', address=self.address_1, phones=['12', 21, 22]))
        self.person_theodore = Person(
            dict(name='Theodore', address=self.address_2, phones=['44']))
        self.person_fausto = Person(
            dict(name='Fausto', address=self.address_2, phones=[]))
        self.person_julieta = Person(
            dict(name='Julieta', address=self.address_3))
        self.person_henry = Person(
            dict(name='Henry', address=self.address_3, phones=[8, 3, 12, 99]))

    def test_address_as_dict(self):
        self.assertDictEqual(
            self.address_empty.as_dict(), {'street': None, 'zip': None})
        self.assertDictEqual(
            self.address_1.as_dict(), dict(street="Park Boulevard", zip=4591))
        self.assertDictEqual(
            self.address_2.as_dict(), dict(street="Freshour Circle", zip=3329))
        self.assertDictEqual(
            self.address_3.as_dict(), dict(street="Edsel Road", zip=938))

    def test_person_as_dict(self):
        self.assertDictEqual(
            self.person_cara.as_dict(),
            dict(name='Cara',
                 address=dict(street="Park Boulevard", zip=4591),
                 phones=[12, 21, 22])
        )
        self.assertDictEqual(
            self.person_theodore.as_dict(),
            dict(
                name='Theodore',
                address=dict(
                    street="Freshour Circle",
                    zip=3329),
                phones=[44])
        )
        self.assertDictEqual(
            self.person_fausto.as_dict(),
            dict(
                name='Fausto',
                address=dict(
                    street="Freshour Circle",
                    zip=3329),
                phones=[])
        )
        self.assertDictEqual(
            self.person_julieta.as_dict(),
            dict(
                name='Julieta',
                address=dict(
                    street="Edsel Road",
                    zip=938),
                phones=[])
        )
        self.assertDictEqual(
            self.person_henry.as_dict(),
            dict(name='Henry',
                 address=dict(street="Edsel Road", zip=938),
                 phones=[8, 3, 12, 99])
        )

    def test_post_as_dict(self):
        first_comment = Comment(dict(
            body="I like this post!",
            author=self.person_julieta,
            created="2017-05-31T00:00:00Z",
            favorite_by=[self.person_fausto, self.person_cara]
        ))
        second_comment = Comment(dict(
            body="It could be better...",
            author=self.person_cara,
            created="2017-05-31T11:11:11Z",
            favorite_by=[]
        ))
        post = Post(dict(
            title='The Wiz',
            author=self.person_theodore,
            comments=[
                first_comment,
                second_comment,
                dict(
                    body="You think it's funny?!",
                    author=self.person_henry,
                    created="2017-05-31T22:22:22Z",
                    favorite_by=[self.person_henry]
                )
            ],
            tags=["foo", 'bar', u'baz']
        ))

        self.assertDictEqual(post.as_dict(), get_json_fixture('post_1.json'))

        del post.comments[2]
        post.comments.append(
            dict(
                body="What can I add more?",
                author=dict(
                    name='Timothy S Manning',
                    address=self.address_1,
                ),
                created="2017-05-31T12:34:56Z",
                favorite_by=[
                    dict(
                        name='Shannon',
                        address=dict(street="Red Hawk Road", zip=3015),
                        phones=[23233, 6566]
                    ),
                    dict(
                        name='Harold Jones',
                        address=dict(street="Still Pastures Drive", zip=4030),
                    )
                ]
            )
        )

        self.assertDictEqual(post.as_dict(), get_json_fixture('post_2.json'))


class DocumentMetaOptionsTest(TestCase):

    def test_nested_meta(self):
        class Message(Document):
            text = SimpleField()

            class Meta:
                ALLOW_EXTRA_FIELDS = False
                OMIT_MISSED_FIELDS = True

        msg = Message()
        self.assertEqual(msg._meta['OMIT_MISSED_FIELDS'], True)
        self.assertEqual(msg._meta['ALLOW_EXTRA_FIELDS'], False)

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
        self.assertEqual(log_msg._meta['OMIT_MISSED_FIELDS'], False)
        self.assertEqual(log_msg._meta['ALLOW_EXTRA_FIELDS'], False)

    def test_omit_missed_fields_attribute(self):
        class Message(Document):
            text = CharField(max_length=120)

        msg = Message()
        self.assertEqual(msg, {'text': None})

        class MessageWithoutNone(Document):

            class Meta:
                OMIT_MISSED_FIELDS = True

            text = CharField()

        msg = MessageWithoutNone()
        self.assertEqual(msg, {})
        self.assertEqual(msg.text, None)

        msg.text = None
        # TODO: this is very tricky: `OMIT_MISSED_FIELDS` should only care
        # about missed fields in original data or `None` should be also
        # treated as missed value?
        self.assertEqual(msg, {})
        self.assertEqual(msg.text, None)

        msg.text = 11**2
        self.assertEqual(msg, dict(text='121'))

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

        class A(Document):
            id = IntegerField(default='a')

        with self.assertRaises(ValueError):
            # Expect an error creating an instance of class
            A()

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
        serialized = json.dumps(dict(self.user.as_dict()))
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
        json_data = json.dumps(post_1.as_dict())
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
