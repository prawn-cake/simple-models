simple-models
=============
[![Build Status](https://travis-ci.org/prawn-cake/simple-models.svg?branch=master)](https://travis-ci.org/prawn-cake/simple-models)
[![Documentation Status](https://readthedocs.org/projects/simple-models/badge/?version=latest)](https://readthedocs.org/projects/simple-models/?badge=latest)
[![Coverage Status](https://coveralls.io/repos/prawn-cake/simple-models/badge.svg)](https://coveralls.io/r/prawn-cake/simple-models)

Simple models - structured dict-like models which is useful for many tasks


Quick start
===========

Convenient way to declare your structured data

    from simplemodels.fields import SimpleField
    from simplemodels.models import DictEmbeddedDocument


    class Address(DictEmbeddedDocument):
        city = SimpleField(default='Saint-Petersburg')
        street = SimpleField(required=True, validator=str)


    class Person(DictEmbeddedDocument):
        name = SimpleField(required=True)
        address = SimpleField(validator=Address.from_dict)  # related model validation
        date_of_birth = SimpleField(
            validator=lambda value: datetime.strptime(value, '%Y-%m-%d')))


    address = Address(street='Nevskii prospect 10')

    >>> address
    {'city': 'Saint-Petersburg', 'street': 'Nevskii prospect 10'}

    >>> address.city
    'Saint-Petersburg'

    >>> import json
    >>> json.dumps(address)
    '{"city": "Saint-Petersburg", "street": "Nevskii prospect 10"}'



Installation
============

    pip install simple-models


Full documentation
==================
http://simple-models.readthedocs.org/


Bug tracker
===========

For all questions, suggestions, bugs let me know here, please: https://github.com/prawn-cake/simple-models/issues


License
=======

MIT - http://opensource.org/licenses/MIT
