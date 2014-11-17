Simple models
#############

.. contents::


Description
###########

Simple models allow to make structured dict-like (json serializable) models for your application.

Main goals
-----------

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
        address = SimpleField(_type=Address)
        insurance_number = SimpleField(_type=int)  # object typing


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
    >>> person = Person(name='Max', address=Address.get_instance(street='Nevskii prospect 10'), insurance_number='111')
    >>> person
    {'name': 'Max', 'address': {'city': 'Saint-Petersburg', 'street': 'Nevskii prospect 10'}, insurance_number=111}


    class Address(DictEmbeddedDocument):
        city = SimpleField(required=True)
        street = SimpleField()


    # This example will raise an ValidationError !
    >>> person = Person(name='Max', address={'town': 'Saint-Petersburg'})

    # But if pass correct structure, then all will be ok
    >>> person = Person(name='Max', address={'city': 'Saint-Petersburg'})
    >>> isinstance(person.address, Address)
    True


Fields type validation
----------------------

From version 0.2.0 fields type validation is supported. See test examples below.


.. code-block:: python

    from simplemodels.fields import SimpleField
    from simplemodels.models import DictEmbeddedDocument

    class PostAddress(DictEmbeddedDocument):
        street = SimpleField(_type=str)

    class Person(DictEmbeddedDocument):
        id = SimpleField(_type=int)
        name = SimpleField(required=True, default='TestName')
        address = SimpleField(_type=PostAddress)

    person_1 = Person.get_instance(
        id='1', name='Maks', address=PostAddress.get_instance(street=999)
    )

    person_2 = Person.get_instance(
        id='2', name='John', address=dict(street=999)
    )

    # NOTE: take a look at 'id' and 'address.street'. All values will be caster according to '_type' parameter
    self.assertIsInstance(person_1, Person)
    self.assertEqual(person_1.id, 1)
    self.assertEqual(person_1.address.street, '999')  # type casting will be applied

    self.assertEqual(person_2.address.street, '999')  # type casting will be applied for dict value as well


Simple field
############

There is only one field type - SimpleField.
You can store any value here. There is way to validate type of field with '_type' parameter

.. autoclass:: simplemodels.fields.SimpleField
    :members:
    :private-members:
    :special-members:
