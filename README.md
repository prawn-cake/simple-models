simple-models
=============
[![Build Status](https://travis-ci.org/prawn-cake/simple-models.svg?branch=master)](https://travis-ci.org/prawn-cake/simple-models)
[![Documentation Status](https://readthedocs.org/projects/simple-models/badge/?version=latest)](https://readthedocs.org/projects/simple-models/?badge=latest)
[![Coverage Status](https://coveralls.io/repos/prawn-cake/simple-models/badge.svg?branch=master&service=github)](https://coveralls.io/github/prawn-cake/simple-models?branch=master)

Simple models - it is:

* Define API messages as models, in declarative way;
* Validate API messages with familiar form-like way;
* Work with data flexibly with dict-like structures;


Install
=======

    pip install simple-models


Quick start
===========

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


    person = Person(name='John', address=Address(street='6th Avenue'))
    
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


Fields
======
* `SimpleField`     -- generic field (useful in cases when other fields are not)
* `IntegerField`    -- integer field
* `FloatField`      -- float field
* `DecimalField`    -- decimal field
* `CharField`       -- char field (python2/3 portable)
* `BooleanField`    -- boolean field
* `ListField`       -- list of items field *(new from v0.3.2)*


CharField
---------
CharField is a field with default unicode validator (for Python 2), all input strings will be transformed to unicode by default

Example (for python 2):

    class User(Document):
        name = CharField()
        
    >>> user = User(name='John')
    >>> isinstance(user.name, unicode)
    >>> True
    
To disable this behaviour **(not recommended)**, pass `is_unicode=False` field parameter:
    
    class User(Document):
        name = CharField(is_unicode=False)
    
    >>> user = User(name='John')
    >>> isinstance(user.name, unicode), isinstance(user.name, str) 
    >>> False, True

            
ListField
---------
Allows you to define list of items

Example:

    class Post(Document):
        text = CharField()
        tags = ListField(item_types=[str], default=['news'])

**NOTE:** mutable default values are protected (deep copied) and works as expected 


Documentation
=============
http://simple-models.readthedocs.org/ (TO BE UPDATED)


Bug tracker
===========

Warm welcome to suggestions and concerns

https://github.com/prawn-cake/simple-models/issues


License
=======

MIT - http://opensource.org/licenses/MIT
