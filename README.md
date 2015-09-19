simple-models
=============
[![Build Status](https://travis-ci.org/prawn-cake/simple-models.svg?branch=master)](https://travis-ci.org/prawn-cake/simple-models)
[![Documentation Status](https://readthedocs.org/projects/simple-models/badge/?version=latest)](https://readthedocs.org/projects/simple-models/?badge=latest)
[![Coverage Status](https://coveralls.io/repos/prawn-cake/simple-models/badge.svg)](https://coveralls.io/r/prawn-cake/simple-models)

Simple models - dict-like models to structure your data in declarative way


Quick start
===========

Describe your models with specific or custom fields. 

"Link" your models to apply advanced validation with nested documents

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



Installation
============

    pip install simple-models


Documentation
=============
http://simple-models.readthedocs.org/


Bug tracker
===========

Warm welcome to suggestions and concerns

https://github.com/prawn-cake/simple-models/issues


License
=======

MIT - http://opensource.org/licenses/MIT
