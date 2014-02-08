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
        address = SimpleField(link_cls=Address)


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
    SimpleFieldValidationError: Field 'name' is required for Person


    # or another example with wrong nested structure
    >>> person = Person(name='Max', address='St.Petersburg, Nevskii prospect 10')
    Traceback (most recent call last):
      File "<console>", line 1, in <module>
      ***
    SimpleFieldValidationError: Wrong value instance, should be 'Address'


    # correct behaviour
    >>> person = Person(name='Max', address=Address.get_instance(street='Nevskii prospect 10'))
    >>> person
    {'name': 'Max', 'address': {'city': 'Saint-Petersburg', 'street': 'Nevskii prospect 10'}}


Simple field
############

There is only one field type - SimpleField.
You can store any value here. No need to distinguish type of values now.

.. autoclass:: simplemodels.models.SimpleField
    :members:
    :private-members:
    :special-members:
