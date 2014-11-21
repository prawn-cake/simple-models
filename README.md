simple-models
=============
Simple models - structured dict-like models which is useful for many tasks

Notes
======
From version 0.2.0 the following functionality is not supported:

 **link_cls** SimpleField attribute was replaced with universal type validation


    class Address(DictEmbeddedDocument):
        ...



    class Person(DictEmbeddedDocument):
        name = SimpleField(required=True)
        address = SimpleField(link_cls=Address)


    # starts from 0.2.0 universal type validation should be used instead
    class Person(DictEmbeddedDocument):
        name = SimpleField(required=True)
        address = SimpleField(_type=Address)

Quick start
===========

Convenient way to declare your structured data

    from simplemodels.fields import SimpleField
    from simplemodels.models import DictEmbeddedDocument


    class Address(DictEmbeddedDocument):
        city = SimpleField(default='Saint-Petersburg')
        street = SimpleField(required=True)


    class Person(DictEmbeddedDocument):
        name = SimpleField(required=True)
        address = SimpleField(_type=Address)  # object typing


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
[![Documentation Status](https://readthedocs.org/projects/simple-models/badge/?version=latest)](https://readthedocs.org/projects/simple-models/?badge=latest)


Bug tracker
===========

For all questions, suggestions, bugs let me know here, please: https://github.com/prawn-cake/simple-models/issues


License
=======

MIT - http://opensource.org/licenses/MIT
