# simple-models
[![Build Status](https://travis-ci.org/prawn-cake/simple-models.svg?branch=master)](https://travis-ci.org/prawn-cake/simple-models)
[![Documentation Status](https://readthedocs.org/projects/simple-models/badge/?version=latest)](https://readthedocs.org/projects/simple-models/?badge=latest)
[![Coverage Status](https://coveralls.io/repos/prawn-cake/simple-models/badge.svg?branch=master&service=github)](https://coveralls.io/github/prawn-cake/simple-models?branch=master)
![PythonVersions](https://www.dropbox.com/s/ck0nc28ttga2pw9/python-2.7_3.4-blue.svg?dl=1)

Simple models is a library which allows you to create validated dictionaries to increase predictability in your application.

Use cases:

* Restrict API messages interactions, bring request and response to predictable data format.
* Any messages validation, very similar with well-known form features (django forms, wtforms, etc).
* Work with data flexibly with dict-like structures.


## Install

    pip install simple-models


## Quick start

Describe your document model, use suitable fields or nested documents:

    >>> from datetime import datetime
    >>> from simplemodels.fields import IntegerField, CharField, DocumentField, DateTimeField
    >>> from simplemodels.models import Document
    
    >>> class Address(Document):
    ...     city = CharField(default='Saint-Petersburg')
    ...     street = CharField(required=True)
    
    >>> class Person(Document):
    ...  id = IntegerField(default=0)            # supports default values
    ...  name = CharField(required=True)         # raise exception if not passed
    ...  address = DocumentField(model=Address)  # nested model validation
    ...  date_of_birth = DateTimeField(          # date time field with custom format
    ...             date_fmt='%Y-%m-%d')
    
    >>> person = Person({'name': 'John', 'address': {'street': '6th Avenue'}})
    >>> person
    Person({'date_of_birth': None, 'id': 0, 'address': Address({'city': u'Saint-Petersburg', 'street': u'6th Avenue'}), 'name': u'John'})
    
    >>> person.address
    Address({'city': u'Saint-Petersburg', 'street': u'6th Avenue'})

    >>> person.address.city
    u'Saint-Petersburg'

    >>> import json
    >>> json.dumps(person.as_dict())
    '{"date_of_birth": null, "id": 0, "address": {"city": "Saint-Petersburg", "street": "6th Avenue"}, "name": "John"}'

## Fields
* `SimpleField`     -- generic field (useful in cases when other fields are not)
* `IntegerField`    -- integer field
* `FloatField`      -- float field
* `DecimalField`    -- decimal field
* `CharField`       -- char field (python2/3 portable)
* `BooleanField`    -- boolean field
* `DateTimeField`   -- date time field
* `ListField`       -- list of items field
* `DocumentField`   -- nested-document field
* `DictField`       -- dictionary-specific field


#### CharField

CharField is a field with default unicode validator (for Python 2), all input strings will be transformed to unicode by default.

Example (for python 2):

    >>> class User(Document):
    ...  name = CharField()
        
    >>> user = User({'name': 'John'})
    >>> isinstance(user.name, unicode)
    True
    
To disable this behaviour **(not recommended)**, pass `is_unicode=False` field parameter:
    
    >>> class User(Document):
    ...  name = CharField(is_unicode=False)
    
    >>> user = User({'name': 'John'})
    >>> isinstance(user.name, unicode), isinstance(user.name, str) 
    (False, True)

#### DocumentField

Allows to define nested structures for being validated.

There are 3 forms to assign a nested model to its' parent:

1. Different models with proper definition order. Keep in mind to define nested model before main one
   
 
        class Address(Document):
            street = CharField()
    
        class User(Document):
            address = DocumentField(model=Address)
    
    
2. Nested modelling - good for keeping "incapsulation"

            
        class User(Document):
            class _Address(Document):
                street = CharField()
            address = DocumentField(model=_Address)
        
    
3. Lazy model assignment with name. Model evaluation happens on validation step, it nicely solves ordering restriction from `#1` 

    
        class User(Document):
            address = DocumentField(model='Address')
    

#### ListField

Field for mapping to the list of items of a given type. The type of element could be both builtin or custom Model.
You can expect the same behaviour as for standard `list` type:

Example:

    >>> from simplemodels.fields import ListField, CharField
    >>> from simplemodels.models import Document
    
    >>> class Comment(Document):
    ...    body = CharField()
        
    >>> class Post(Document):
    ...    text = CharField()
    ...    tags = ListField(of=str, default=['news'])
    ...    comments = ListField(of=Comment)
    
    >>> post = Post({'text':"Do you like cats?", 'comments':[Comment({'body': "Yes, they're so cute!"})]})
    >>> post.comments.append(dict(body="Elephant in the room..."))
    >>> post
    Post({'text': u'Do you like cats?', 'comments': [Comment({'body': u"Yes, they're so cute!"}), Comment({'body': u'Elephant in the room...'})], 'tags': ['news']})


**NOTE:** mutable default values are protected (deep copied) and works as expected.

**NOTE:** `ListField` always has `default=[]` value

#### DictField

This type of field enables to be more specific, rather than just using `SimpleField` and also allows to use custom dict implementation, default is `dict`.

Example:

    >>> from simplemodels.fields import DictField
    >>> from simplemodels.models import Document
    >>> from collections import OrderedDict
    
    >>> class UserAsDict(Document):
    ...    attrs = DictField(required=True, dict_cls=OrderedDict)
        
    >>> UserAsDict({'attrs': [('b', 1), ('a', 2)]}).as_dict()
    {'attrs': OrderedDict([('b', 1), ('a', 2)])}
    


### Meta

*Meta* is a nested structure to define some extra document options.

Example:

    >>> class UserWithMeta(Document):
    ...    name = CharField()
    ...    role = CharField()
    ...
    ...    class Meta:
    ...        ALLOW_EXTRA_FIELDS = True
    ...        OMIT_MISSED_FIELDS = True
            
#### Meta options

* `ALLOW_EXTRA_FIELDS` - accept to put extra fields not defined with schema
    
        >>> user = UserWithMeta(dict(name='Maksim', role='Admin', id=47))
        >>> user
        UserWithMeta({'role': u'Admin', 'name': u'Maksim', 'id': 47})
        

* `OMIT_MISSED_FIELDS` - this option lets us omit values with `None`:
        
        user = User({'name': 'Maksim'})
        user
        
        # Without option
        {'name': 'Maksim', 'role': None}
        
        # With option
        {'name': 'Maksim'}

## Validators

Validator is always a callable object which gets data as an argument and validates it. Validator must return `True`, otherwise it's considered failed.

Example of validators: `lambda v: v > 10`, `lambda v: 10 < len(v) < 100`, etc.

Validators can be used as a chain for the field, e.g
    
    import hashlib
    
    class User(Document):
        username = CharField()
        password = CharField(validators=[str, lambda x: hashlib.sha256(x).hexdigest()])


### Post-init model validation

Helps to validate your fields when it depends on the other fields

For example let's validate length of admin password if the user is.

    >>> from simplemodels.fields import CharField, BooleanField
    >>> from simplemodels.models import Document
    >>> from simplemodels.exceptions import ModelValidationError
    
    >>> class UserWithPassword(Document):
    ...    name = CharField()
    ...    password = CharField(required=True)
    ...    is_admin = BooleanField(default=False)
    ...
    ...    @staticmethod
    ...    def validate_password(document, value):
    ...        if document.is_admin and len(value) < 10:
    ...            raise ModelValidationError(
    ...                'Admin password is too short (< 10 characters)')
    ...        return value
    
    >>> UserWithPassword(dict(name='Normal user', password='foo', is_admin=False))
    UserWithPassword({'password': u'foo', 'is_admin': False, 'name': u'Normal user'})
    >>> UserWithPassword(dict(name='Admin user', password='foo', is_admin=True))
    Traceback (most recent call last):
      ...
    ModelValidationError: Admin password is too short (< 10 characters)
    
            
**NOTE:** validation method must be static, have `validate_{field_name}` format and get 2 parameters: *document* and *value*             


### Inheritance

`Document` model supports inheritance. 
Sometimes it turns out very handy to define base message class and define subclasses inherited from the base one:

    class BaseMessage(Document):
        method_name = CharField(required=True)    
        params = DictField(required=True)
        
        
    class HttpRpcMessage(BaseMessage):
        url = CharField(required=True)
    
    
    class RabbitRpcMessage(BaseMessage):
        amqp_headers = DictField(required=True)
    

### Immutable documents and fields

If you need to make your field or whole document immutable

#### Immutable field
    
    >>> from simplemodels.models import Document
    
    >>> class UserWithImmutableId(Document):
    ...    id = IntegerField(immutable=True)
    ...    name = CharField()
        
    >>> user = UserWithImmutableId({'name': 'John', 'id': 1})
    >>> user.name = 'Mark'
    >>> user
    UserWithImmutableId({'id': 1, 'name': u'Mark'})
    >>> user.id = 2
    Traceback (most recent call last):
      ...
    ImmutableFieldError: UserWithImmutableId.id field is immutable
    
#### Immutable document 

    >>> from simplemodels.fields import CharField, IntegerField
    >>> from simplemodels.models import ImmutableDocument
    
    >>> class ImmutableUser(ImmutableDocument):
    ...    id = IntegerField()
    ...    name = CharField()
        
    >>> user = ImmutableUser({'name': 'John', 'id': 1})
    >>> user.id = 2
    Traceback (most recent call last):
      ...
    DocumentError: ImmutableUser({'id': 1, 'name': u'John'}) is immutable. Set operation is not allowed.

## Run tests

    tox

**NOTE:** In some cases it requires to downgrade your *virtualenv* to *12.0.2* to run it with python 3. 

Related issues: 

* [python-future issue](https://github.com/PythonCharmers/python-future/issues/148)
* [import error issue](http://stackoverflow.com/questions/32861935/passing-python3-to-virtualenvwrapper-throws-up-importerror)



## Bug tracker

Warm welcome to suggestions and concerns

https://github.com/prawn-cake/simple-models/issues

## Contributors (without any specific order)
- [grundic](https://github.com/grundic)

## License

MIT - http://opensource.org/licenses/MIT
