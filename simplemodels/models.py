# -*- coding: utf-8 -*-
from simplemodels.exceptions import ValidationRequiredError
from simplemodels.fields import SimpleField
import six

__all__ = ['DictEmbeddedDocument']


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
        for field_name, obj in dct.items():
            if isinstance(obj, SimpleField):
                # set SimpleField text name as a private `_name` attribute
                obj._name = field_name
                obj._holder_name = name  # class holder name

                _fields[obj.get_name()] = obj
                if obj.required:
                    _required_fields.append(obj.get_name())

        dct['_fields'] = _fields
        dct['_required_fields'] = tuple(_required_fields)

        return super(SimpleEmbeddedMeta, mcs).__new__(mcs, name, parents, dct)


@six.add_metaclass(SimpleEmbeddedMeta)
class DictEmbeddedDocument(AttributeDict):

    """ Main class to represent structured dict-like document """

    def __init__(self, **kwargs):
        kwargs = self._clean_kwargs(kwargs)
        prepared_fields = self._prepare_fields(**kwargs)
        super(DictEmbeddedDocument, self).__init__(**prepared_fields)

        # Initialize prepared field values to self.__dict__
        for name, value in prepared_fields.items():
            self.__dict__[name] = value

    def _prepare_fields(self, **kwargs):
        """Do field validations and set defaults

        :param kwargs: init parameters
        :return: :raise RequiredValidationError:
        """
        cls = self.__class__
        required_fields_errors = []

        # Do some validations
        for field_name, field_obj in self._fields.items():

            # Get field value or set default
            field_val = kwargs.get(field_name, getattr(field_obj, 'default'))

            # Validate required fields
            cls._validate_require(
                field_name, field_val, required_fields_errors)

            # Build model structure
            if field_name in kwargs:
                kwargs[field_name] = field_obj.validate(field_val)
            else:
                kwargs[field_name] = field_val

        if required_fields_errors:
            raise ValidationRequiredError(str(required_fields_errors))

        return kwargs

    @classmethod
    def _validate_require(cls, name, value, errors):
        if name in getattr(cls, '_required_fields', []):
            if value is None or value == '':
                errors.append("Field '{}' is required for {}".format(
                    name, cls.__name__))
        return True

    @classmethod
    def _clean_kwargs(cls, kwargs):
        fields = getattr(cls, '_fields', {})
        return {k: v for k, v in kwargs.items() if k in fields}

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
        """Create model instance from dict or from another model for nested
        fields

        :param kwargs:
        :return:
        """
        return cls(**cls._clean_kwargs(kwargs))


# TODO: implement searchable and filterable collection for embedded documents, think about it