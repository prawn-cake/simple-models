# simple-models
[![Build Status](https://travis-ci.org/prawn-cake/simple-models.svg?branch=master)](https://travis-ci.org/prawn-cake/simple-models)
[![Documentation Status](https://readthedocs.org/projects/simple-models/badge/?version=latest)](https://readthedocs.org/projects/simple-models/?badge=latest)
[![Coverage Status](https://coveralls.io/repos/prawn-cake/simple-models/badge.svg?branch=master&service=github)](https://coveralls.io/github/prawn-cake/simple-models?branch=master)
![PythonVersions](https://www.dropbox.com/s/ck0nc28ttga2pw9/python-2.7_3.4-blue.svg?dl=1)

Simple models is a library allows to create validated dictionaries to increase predictability in your application.

Use cases:

* Restrict API messages interactions, bring request and response to predictable data format
* Any messages validation, very similar with well-known form features (django forms, wtforms, etc)
* Work with data flexibly with dict-like structures;


## Install

    pip install simple-models


## Quick start

**Important:** starting from v0.5.0 the only recommended and safe way to initialize a model is via `MyModel.create({'field_1': 'val_1', ...})` method 

Describe your document model, use suitable fields or nested documents 

    from datetime import datetime
    from simplemodels.fields import IntegerField, CharField, DocumentField, SimpleField
    from simplemodels.models import Document


    class Address(Document):
        city = CharField(default='Saint-Petersburg')
        street = CharField(required=True)


    class Person(Document):
        id = IntegerField(default=0)            # supports default values with validation
        name = CharField(required=True)         # raise exception if not passed
        address = DocumentField(model=Address)  # nested model validation
        date_of_birth = SimpleField(            # field with custom validator
            validators=[lambda value: datetime.strptime(value, '%Y-%m-%d')])


    person = Person.create({'name': 'John', 'address': {'street': '6th Avenue'}})
    
    >>> person
    {'address': {'city': 'Saint-Petersburg', 'street': '6th Avenue'},
     'date_of_birth': None,
     'id': 0,
     'name': 'John'}
    
    >>> person.address
    {'city': 'Saint-Petersburg', 'street': '6th Avenue'}

    >>> person.address.city
    'Saint-Petersburg'

    >>> import json
    >>> json.dumps(person)
    '{"date_of_birth": null, "id": 0, "address": {"city": "Saint-Petersburg", "street": "6th Avenue"}, "name": "John"}'

## Fields
* `SimpleField`     -- generic field (useful in cases when other fields are not)
* `IntegerField`    -- integer field
* `FloatField`      -- float field
* `DecimalField`    -- decimal field
* `CharField`       -- char field (python2/3 portable)
* `BooleanField`    -- boolean field
* `ListField`       -- list of items field *(new from v0.3.2)*
* `DocumentField`   -- nested-document field
* `DictField`       -- dictionary-specific field


#### CharField

CharField is a field with default unicode validator (for Python 2), all input strings will be transformed to unicode by default

Example (for python 2):

    class User(Document):
        name = CharField()
        
    >>> user = User.create({'name': 'John'})
    >>> isinstance(user.name, unicode)
    >>> True
    
To disable this behaviour **(not recommended)**, pass `is_unicode=False` field parameter:
    
    class User(Document):
        name = CharField(is_unicode=False)
    
    >>> user = User.create({'name': 'John'})
    >>> isinstance(user.name, unicode), isinstance(user.name, str) 
    >>> False, True

#### DocumentField

Allows to define nested structures for being validated

There are 3 forms to assign a nested model to its' parent

    #1. Different models with proper definition order. Keep in mind to define nested model before main one
    
    class Address(Document):
        street = CharField()

    class User(Document):
        address = DocumentField(model=Address)
    
    
    #2. Nested modelling - good for keeping "incapsulation"
    
    class User(Document):
        class _Address(Document):
            street = CharField()
        address = DocumentField(model=_Address)
        
    
    #3. Lazy model assignment with name. Model evaluation happens on validation step, it nicely solves ordering restriction in #1 
    ...
    
    class User(Document):
        address = DocumentField(model='Address')
    

#### ListField

Enables to validate list of items

Example:

    class Post(Document):
        text = CharField()
        tags = ListField(of=str, default=['news'])

**NOTE:** mutable default values are protected (deep copied) and works as expected 

**NOTE:** `ListField` always has `default=[]` value

#### DictField

This type of field enables to be more specific rather than just using `SimpleField` and also allows to use custom dict implementation, default is `dict` 

Example:

    class User(Document):
        attrs = DictField(required=True, dict_cls=OrderedDict)
        
    user = User.create({'attrs': [('b', 1), ('a', 2)]})


### Meta

*Meta* is a nested structure to define some extra document options

Example:

    class User(Document):
        name = CharField()
        role = CharField()

        class Meta:
            ALLOW_EXTRA_FIELDS = False
            OMIT_MISSED_FIELDS = True
            
#### Meta options

* `ALLOW_EXTRA_FIELDS` - accept to put extra fields not defined with schema
    
        >>> user = User.create(dict(name='Maksim', role='Admin', id=47))
        >>> user
        {'name': 'Maksim', 'role': 'Admin', 'id': 47}

* `OMIT_MISSED_FIELDS` - by default document instance structure is built with schema-defined keys even if it's not passed ( *default* or *None* will be set for absent).
    This options allows to omit missed fields from document
        
        >>> user = User.create({'name': 'Maksim'})
        >>> user
        
        # Without option
        {'name': 'Maksim', 'role': None}
        
        # With option
        {'name': 'Maksim'}

## Validators

Validator is always a callable object which gets data as an argument, validates it and returns validated data or raises `ValidationError`.

Example of validators: `str`, `set`, `lambda value: datetime.strptime(value, '%Y-%m-%d')`, etc

Validators can be used as a chain for the field, e.g
    
    import hashlib
    
    class User(Document):
        username = CharField()
        password = CharField(validators=[str, lambda x: hashlib.sha256(x).hexdigest()])


### Post-init model validation

Helps to validate your fields when it depends on the other fields

For example let's validate length of admin password if the user is.

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
            
**NOTE:** validation method must be static, have `validate_{field_name}` format and get 2 parameters: *document* and *value*             


### Inheritance

`Document` model supports inheritance. 
Sometimes it turns out very handy to define base message class and define subclasses inherited from the base one

    class BaseMessage(Document):
        method_name = CharField(required=True)    
        params = DictField(required=True)
        
        
    class HttpRpcMessage(BaseMessage):
        url = CharField(required=True)
    
    
    class RabbitRpcMessage(BaseMessage):
        amqp_headers = DictField(required=True)
    
        

## Run tests

    tox

**NOTE:** In some cases it requires to downgrade your *virtualenv* to *12.0.2* to run it with python 3. 

Related issues: 

* [python-future issue](https://github.com/PythonCharmers/python-future/issues/148)
* [import error issue](http://stackoverflow.com/questions/32861935/passing-python3-to-virtualenvwrapper-throws-up-importerror)



## Bug tracker

Warm welcome to suggestions and concerns

https://github.com/prawn-cake/simple-models/issues


## License

MIT - http://opensource.org/licenses/MIT
