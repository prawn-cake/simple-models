Simple models
#############

.. contents::


Description
###########

The library for defining message structures in declarative way.

It enables to get more predictable behaviour when you work with any sort of messages your application send and receive.

Along with it it increase robustness and stability of your code because of validation supporting.

Validation here is followed by bit different approach. Field is valid if it can be forced to a validator function type.


Main goals
##########

* Standardize complex API (json) messages in declarative way;
* Transparent dict to json transformation. Every time you might feel that you work with just dict;
* Validate input message parameters in the form-like style (not exactly, but similar);
* Supporting complex nested message structures for describing complex API messages;
* IDE auto-completion deeper than one dictionary key level;


Basics
######

Documents
---------
Document is a main holder object. So you could think about it as about dict subclass

There are several types of documents:

    * Document          -- dict-like document
    * ImmutableDocument -- all fields are immutable

Fields
------
Fields are document attributes. It's like "dict keys", but smarter

There are several types of documents:
    * SimpleField   -- basic field, can contain anything
    * IntegerField
    * FloatField
    * DecimalField
    * CharField
    * BooleanField
    * DocumentField -- nested document

Example
-------

.. code-block:: python

    from simplemodels.fields import SimpleField, CharField, DocumentField, IntegerField
    from simplemodels.models import Document


    class Address(Document):
        city = CharField(default='Saint-Petersburg')
        street = CharField()


    class Person(Document):
        name = CharField(required=True)
        address = DocumentField(type=Address)
        insurance_number = IntegerField()


    address = Address(street='Nevskii prospect 10')


    # pure dict structure for any compatibility
    >>> address
    {'city': 'Saint-Petersburg', 'street': 'Nevskii prospect 10'}


    # dict subclass, all is as expected
    >>> address.items()
    [('city', 'Saint-Petersburg'), ('street', 'Nevskii prospect 10')]


    # Create person without required `name` field: got an ValidationError
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


    class Address(Document):
        city = SimpleField(required=True)
        street = SimpleField()


    # This example will raise an ValidationError !
    >>> person = Person(name='Max', address={'town': 'Saint-Petersburg'})

    # But if pass correct structure, then all will be ok
    >>> person = Person(name='Max', address={'city': 'Saint-Petersburg'})
    >>> isinstance(person.address, Address)
    True


Custom field
------------
Let's define custom SHA1 field which will be convert given value to sha1

.. code-block:: python

    class SHA1Field(SimpleField):
        def __init__(self, **kwargs):
            def validate_sha1(value):
                from hashlib import sha1
                return sha1(value).hexdigest()

            self._add_default_validator(validate_sha1, kwargs)
            super(SHA1Field, self).__init__(**kwargs)

    class Message(Document):
        password = SHA1Field()

    >>> message = Message(password='qwerty')
    >>> message.password
    'b1b3773a05c0ed0176787a4f1574ff0075f7521e'


    # Same result without inheritance
    def validate_sha1(value):
        from hashlib import sha1
        return sha1(value).hexdigest()

    class Message(Document):
        password = SimpleField(validators=[validate_sha1])


Simple field
############

Basic field class. You can override it by yourself to create custom fields

.. autoclass:: simplemodels.fields.SimpleField
    :members:
    :special-members:

Validation
----------
Validation is a pipeline value processing. Value is considered valid if it can be forced to validator function.


Verbose field name
------------------

Feature enables to use verbose (optional) field name.

.. code-block:: python

    class CountryInfo(Document):
        Country = CharField()
        Currency = CharField()
        GDP = FloatField()
        Inflation = FloatField()
        InterestRate = FloatField(name='Interest Rate')  # space in the output name
        Population = IntegerField()


This will match a message like

.. code-block:: python

    {
        "Country": "Germany",
        "Currency": "EUR",
        "GDP": 34,388,
        "Inflation": 2.2,
        "Interest Rate": 1.01,
        "Population": 80767000
    }


Immutability
============

There are two types of immutability are supported:

* Document-level immutability

.. code-block:: python

    class User(ImmutableDocument):
        id = IntegerField(default=1)
        name = CharField(default='John')

* Field-level immutability

.. code-block:: python

    class User(Document):
        name = CharField()
        system_id = IntegerField(immutable=True)