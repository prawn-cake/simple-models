# -*- coding: utf-8 -*-
from simplemodels.exceptions import SimpleFieldValidationError
from simplemodels.fields import SimpleField


class AttributeDict(dict):

    """Dict wrapper with access to keys via attributes"""

    def __getattr__(self, item):
        # not override system methods like __deepcopy__
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

        _fields = []
        _required_fields = []

        for obj_name, obj in dct.items():
            if isinstance(obj, SimpleField):
                _fields.append(obj_name)
                if obj.required:
                    _required_fields.append(obj_name)

                # reflect name for field
                if isinstance(obj, SimpleField):
                    obj._name = obj_name

        dct['_fields'] = tuple(_fields)
        dct['_required_fields'] = tuple(_required_fields)

        return super(SimpleEmbeddedMeta, mcs).__new__(mcs, name, parents, dct)


class DictEmbeddedDocument(AttributeDict):

    """ Alternative implementation of EmbeddedDocument for mongoengine. """

    __metaclass__ = SimpleEmbeddedMeta

    def __init__(self, **kwargs):
        super(DictEmbeddedDocument, self).__init__(**kwargs)
        for field_name in self._fields:
            if field_name in kwargs:
                setattr(self, field_name, kwargs[field_name])
            else:
                # very tricky here -- look at descriptor SimpleField
                # this trick need for init default structure representation like
                # Document() -> {'field_1': <value OR default value>, ...}
                setattr(self, field_name, getattr(self, field_name))

        cls = type(self)
        for field_name in cls._required_fields:
            # field_obj = type(getattr(obj, field_name)).__dict__[field_name]
            # field_obj.validate()
            if not getattr(self, field_name):
                raise SimpleFieldValidationError(
                    "Field '{}' is required for {}".format(
                        field_name, cls.__name__)
                )

    @classmethod
    def get_instance(cls, **kwargs):
        """Return instance with exactly the same fields as described,
        filter not described keys.

        :param kwargs:
        :return: cls instance
        """
        return cls(**{k: v for k, v in kwargs.items() if k in cls._fields})