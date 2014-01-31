# -*- coding: utf-8 -*-
from core.exceptions import SimpleFieldValidationError
from core.fields import SimpleField


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

    """ Metaclass for collecting info about fields """

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

        for name, obj in dct.items():
            if isinstance(obj, SimpleField):
                _fields.append(name)
                if obj.required:
                    _required_fields.append(name)

                # reflect name for field
                if isinstance(obj, SimpleField):
                    obj._name = name

        dct['_fields'] = tuple(_fields)
        dct['_required_fields'] = tuple(_required_fields)

        return super(SimpleEmbeddedMeta, mcs).__new__(mcs, name, parents, dct)


class DictEmbeddedDocument(AttributeDict):

    """ Alternative implementation of EmbeddedDocument for mongoengine. """

    __metaclass__ = SimpleEmbeddedMeta

    def __new__(cls, *args, **kwargs):
        obj = super(DictEmbeddedDocument, cls).__new__(cls, *args)

        # init default fields
        for field_name in cls._fields:
            if field_name in kwargs:
                setattr(obj, field_name, kwargs[field_name])
            else:
                setattr(obj, field_name, getattr(cls, field_name, None))

        # check required
        for field_name in cls._required_fields:
            # field_obj = type(getattr(obj, field_name)).__dict__[field_name]
            # field_obj.validate()
            if not getattr(obj, field_name):
                raise SimpleFieldValidationError(
                    "Field '{}' is required for {}".format(
                        field_name, obj.__class__.__name__)
                )
        return obj

    @classmethod
    def get_instance(cls, **kwargs):
        return cls(**kwargs)