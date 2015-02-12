# -*- coding: utf-8 -*-
from simplemodels.exceptions import RequiredValidationError
from simplemodels.fields import SimpleField


class AttributeDict(dict):

    """Dict wrapper with access to keys via attributes"""

    def __getattr__(self, item):
        # do not affect magic methods like __deepcopy__
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
                    obj._holder_name = name  # class holder name

        dct['_fields'] = _fields
        dct['_required_fields'] = tuple(_required_fields)

        return super(SimpleEmbeddedMeta, mcs).__new__(mcs, name, parents, dct)


class DictEmbeddedDocument(AttributeDict):

    """ Main class to represent structured dict-like document """

    __metaclass__ = SimpleEmbeddedMeta

    def __init__(self, **kwargs):
        kwargs = self._clean_kwargs(kwargs)
        super(DictEmbeddedDocument, self).__init__(**kwargs)
        prepared_fields = self._prepare_fields(**kwargs)

        # Initialize prepared fields
        for name, value in prepared_fields.items():
            setattr(self, name, value)

    def _prepare_fields(self, **kwargs):
        """Do field validations

        :param kwargs:
        :return: :raise RequiredValidationError:
        """
        cls = type(self)
        required_fields_errors = []

        # Do some validations
        for field_name, obj in self._fields.items():
            field_value = getattr(self, field_name)

            # Validate requires
            cls._validate_require(
                field_name, field_value, required_fields_errors)

            # Build model structure
            if field_name not in kwargs:
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
    def _clean_kwargs(cls, kwargs):
        return {
            k: v for k, v in kwargs.items()
            if k in getattr(cls, '_fields', [])
        }

    @classmethod
    def get_instance(cls, **kwargs):
        """Get class instance with fields according to model declaration

        :param kwargs: key-value field parameters
        :return: class instance
        """
        # FIXME: remove this method
        return cls(**cls._clean_kwargs(kwargs))

    @classmethod
    def from_dict(cls, kwargs):
        return cls(**cls._clean_kwargs(kwargs))