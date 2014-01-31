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

        for k, v in dct.items():
            if isinstance(v, SimpleField):
                _fields.append(k)
                if v.required:
                    _required_fields.append(k)

                # reflect name for field
                if isinstance(v, SimpleField):
                    v._name = k

        dct['_fields'] = tuple(_fields)
        dct['_required_fields'] = tuple(_required_fields)

        return super(SimpleEmbeddedMeta, mcs).__new__(mcs, name, parents, dct)


class DictEmbeddedDocument(AttributeDict):

    """ Alternative implementation of EmbeddedDocument for mongoengine. """

    __metaclass__ = SimpleEmbeddedMeta

    def __new__(cls, *args, **kwargs):
        obj = super(DictEmbeddedDocument, cls).__new__(cls, *args)

        # init default fields
        for f_name in cls._fields:
            if f_name in kwargs:
                setattr(obj, f_name, kwargs[f_name])
            else:
                setattr(obj, f_name, getattr(cls, f_name, None))

        # check required
        for rf_name in cls._required_fields:
            if not getattr(obj, rf_name):
                raise SimpleFieldValidationError(
                    "Field '{}' is required for {}".format(
                        rf_name, obj.__class__.__name__)
                )
        return obj

    @classmethod
    def get_instance(cls, **kwargs):
        return cls(**kwargs)