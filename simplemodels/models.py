# -*- coding: utf-8 -*-
from simplemodels.exceptions import RequiredValidationError
from simplemodels.fields import SimpleField


class AttributeDict(dict):

    """Dict wrapper with access to keys via attributes"""

    def __getattr__(self, item):
        # do not override system methods like __deepcopy__
        if item.startswith('__') and item.endswith('__'):
            return super(AttributeDict, self).__getattr__(self, item)

        return self[item]

    def __setattr__(self, key, value):
        super(AttributeDict, self).__setattr__(key, value)
        self[key] = value


class SimpleEmbeddedMeta(type):

    """ Metaclass for collecting fields info """

    def __new__(mcs, name, parents, dct):
        """

        :param name: class name
        :param parents: class parents
        :param dct: dict: includes class attributes, class methods,
        static methods, etc
        :return: new class
        """

        _fields = {}
        _required_fields = []

        # Inspect subclass to save SimpleFields and require field names
        for item_name, obj in dct.items():
            if isinstance(obj, SimpleField):
                _fields[item_name] = obj
                if obj.required:
                    _required_fields.append(item_name)

                # set SimpleField text name as a private `_name` attribute
                if isinstance(obj, SimpleField):
                    obj._name = item_name

        dct['_fields'] = _fields
        dct['_required_fields'] = tuple(_required_fields)

        return super(SimpleEmbeddedMeta, mcs).__new__(mcs, name, parents, dct)


class DictEmbeddedDocument(AttributeDict):

    """ Main class to represent structured dict-like document """

    __metaclass__ = SimpleEmbeddedMeta

    def __init__(self, **kwargs):
        super(DictEmbeddedDocument, self).__init__(**kwargs)
        validated_fields = self._validate_fields(**kwargs)

        # Initialize validated fields
        for name, value in validated_fields.items():
            setattr(self, name, value)

    def _validate_fields(self, **kwargs):
        """Do field validations

        :param kwargs:
        :return: :raise RequiredValidationError:
        """
        cls = type(self)
        required_fields_errors = []

        from simplemodels.validators import get_validator

        # Do some validations
        for field_name, obj in self._fields.items():
            field_value = getattr(self, field_name)

            # Validate requires
            cls._validate_require(
                field_name, field_value, required_fields_errors)

            # Validate or throw ValidationError
            if field_name in kwargs:
                value = get_validator(obj.type).validate(kwargs[field_name])
                kwargs[field_name] = value
                # validated_fields[field_name] = value
            else:
                kwargs[field_name] = field_value

        if required_fields_errors:
            raise RequiredValidationError(str(required_fields_errors))

        return kwargs

    @classmethod
    def _validate_require(cls, name, value, errors):
        if name in getattr(cls, '_required_fields', []):
            if not value:
                errors.append("Field '{}' is required for {}".format(
                    name, cls.__name__))
        return True

    @classmethod
    def get_instance(cls, **kwargs):
        """Get class instance with fields according to model declaration

        :param kwargs: key-value field parameters
        :return: class instance
        """
        return cls(**{k: v for k, v in kwargs.items()
                      if k in getattr(cls, '_fields', [])})