simple-models
=============
Simple models - structured dict-like models which is useful for many tasks

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
        address = SimpleField(link_cls=Address)


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

Nothing special here

    pip install simple-models


Full documentation
==================

http://simple-models.readthedocs.org/en/latest/


Bug tracker
===========

For all questions, suggestions, bugs let me know here, please: https://github.com/prawn-cake/simple-models/issues


License
=======

MIT - http://opensource.org/licenses/MIT
