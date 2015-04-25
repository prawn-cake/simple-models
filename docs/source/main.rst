Simple models
#############

.. contents::


Description
###########

Simple models allow to make structured dict-like (json serializable) models for your application.

Main goals
----------

* Make declarative structures based on dict -- easy to understand, convenient to support;
* Implement structured data models with low coupling -- use anywhere;
* Should be able to validate structured data -- more expected behaviour for tons of code;
* Simplified code which contains big nested structures especially for API integration;
* Convenient way to use in IDE -- auto-complete using attributes instead dict keys;



Basics
######

Simple example
--------------

.. code-block:: python

    from simplemodels.fields import SimpleField
    from simplemodels.models import DictEmbeddedDocument


    class Address(DictEmbeddedDocument):
        city = SimpleField(default='Saint-Petersburg')
        street = SimpleField()


    class Person(DictEmbeddedDocument):
        name = SimpleField(required=True)
        address = SimpleField(type=Address)
        insurance_number = SimpleField(type=int)  # object typing


    address = Address(street='Nevskii prospect 10')


    # pure dict structure for any compatibility
    >>> address
    {'city': 'Saint-Petersburg', 'street': 'Nevskii prospect 10'}


    # dict subclass, nothing special
    >>> address.items()
    [('city', 'Saint-Petersburg'), ('street', 'Nevskii prospect 10')]


    # validation is supported
    >>> person = Person()
    Traceback (most recent call last):
      File "<console>", line 1, in <module>
      ***
    ValidationError: Field 'name' is required for Person


    # or another example with wrong nested structure
    >>> person = Person(name='Max', address='St.Petersburg, Nevskii prospect 10')
    Traceback (most recent call last):
      File "<console>", line 1, in <module>
      ***
    ValidationError: Wrong value instance, should be 'Address'


    # correct behaviour
    >>> person = Person(name='Max', address=Address(street='Nevskii prospect 10'), insurance_number='111')
    >>> person
    {'name': 'Max', 'address': {'city': 'Saint-Petersburg', 'street': 'Nevskii prospect 10'}, 'insurance_number': 111}


    class Address(DictEmbeddedDocument):
        city = SimpleField(required=True)
        street = SimpleField()


    # This example will raise an ValidationError !
    >>> person = Person(name='Max', address={'town': 'Saint-Petersburg'})

    # But if pass correct structure, then all will be ok
    >>> person = Person(name='Max', address={'city': 'Saint-Petersburg'})
    >>> isinstance(person.address, Address)
    True


Simple field
############

There is only one field type - SimpleField which stores any value.
You can add require or/and validation for it

.. autoclass:: simplemodels.fields.SimpleField
    :members:
    :private-members:
    :special-members:


Fields type validation and validators
-------------------------------------

From version 0.2.0 fields type validation is supported. See test examples below.

From version 0.2.1:
 * old validation ways with `type` are **DEPRECATED**. Use `validator` instead (see below)
 * `DictEmbeddedDocument.get_instance` method is **DEPRECATED**, use direct constructor instead

.. code-block:: python

    from simplemodels.fields import SimpleField
    from simplemodels.models import DictEmbeddedDocument

    class PostAddress(DictEmbeddedDocument):
        street = SimpleField(type=str)

    class Person(DictEmbeddedDocument):
        id = SimpleField(type=int)
        name = SimpleField(required=True, default='TestName')
        address = SimpleField(type=PostAddress)

    person_1 = Person(id='1', name='Maks', address=PostAddress(street=999))

    person_2 = Person(id='2', name='John', address=dict(street=999))

    # NOTE: take a look at `id` and `address.street`. All values will be casted to selected `type`
    self.assertIsInstance(person_1, Person)
    self.assertEqual(person_1.id, 1)
    self.assertEqual(person_1.address.street, '999')  # type casting will be applied

    self.assertEqual(person_2.address.street, '999')  # type casting will be applied for dict value as well


New field validation (starts from 0.2.1)
----------------------------------------

New `validator` attribute has been added to SimpleField:

* It must be callable
* Use method `from_dict` for related `DictEmbeddedDocument` models


.. code-block:: python

    class PostAddress(DictEmbeddedDocument):
        city = SimpleField(validator=str)  # same behaviour as previous
        delivery_date = SimpleField(       # advanced validator for datetime or whatever
            validator=lambda value: datetime.strptime(
                value, '%Y-%m-%dT%H:%M:%SZ'))

    class Package(DictEmbeddedDocument):
        id = SimpleField(validator=int)
        address = SimpleField(validator=PostAddress.from_dict)  # validate address


Optional field name (starts from 0.2.4)
---------------------------------------

Feature enables to use optional field name with custom characters.

.. code-block:: python

    class MyModel(DictEmbeddedDocument):
        InterestRate = SimpleField(validator=float,
                                   name='Interest Rate',
                                   required=True)
        ...


This will match a message like

.. code-block:: python

    {
        "Country": "Germany",
        "Currency": "EUR",
        "GDP": "34,388",
        "Inflation": "2.2",
        "Interest Rate": "1.01",
        "Population": "80,767,000"
    }