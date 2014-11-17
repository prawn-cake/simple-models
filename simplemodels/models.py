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

        for obj_name, obj in dct.items():
            if isinstance(obj, SimpleField):
                _fields[obj_name] = obj
                if obj.required:
                    _required_fields.append(obj_name)

                # reflect name for field
                if isinstance(obj, SimpleField):
                    obj._name = obj_name

        dct['_fields'] = _fields
        dct['_required_fields'] = tuple(_required_fields)

        return super(SimpleEmbeddedMeta, mcs).__new__(mcs, name, parents, dct)


class DictEmbeddedDocument(AttributeDict):

    """ Alternative implementation of EmbeddedDocument for mongoengine. """

    __metaclass__ = SimpleEmbeddedMeta

    def __init__(self, **kwargs):
        super(DictEmbeddedDocument, self).__init__(**kwargs)
        cls = type(self)
        errors = []

        for field_name, obj in self._fields.items():
            if field_name in kwargs:
                from simplemodels.validators import get_validator
                value = get_validator(obj.type).validate(kwargs[field_name])
                setattr(self, field_name, value)
            else:
                # very tricky here -- look at descriptor SimpleField
                # this trick need for init default structure representation like
                # Document() -> {'field_1': <value OR default value>, ...}
                setattr(self, field_name, getattr(self, field_name))

            # Check for require
            if field_name in cls._required_fields:
                if not getattr(self, field_name):
                    errors.append(
                        "Field '{}' is required for {}".format(
                            field_name, cls.__name__)
                    )

        if errors:
            raise RequiredValidationError(str(errors))

    @classmethod
    def get_instance(cls, **kwargs):
        """Return instance with exactly the same fields as described,
        filter not described keys.

        :param kwargs:
        :return: cls instance
        """
        return cls(**{k: v for k, v in kwargs.items() if k in cls._fields})