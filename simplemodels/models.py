# -*- coding: utf-8 -*-
import copy
import inspect
import weakref
from abc import ABCMeta
from collections import MutableMapping

import six

from simplemodels.exceptions import ModelValidationError, DocumentError
from simplemodels.fields import ExtraField, SimpleField

__all__ = ['Document', 'ImmutableDocument']

registry = weakref.WeakValueDictionary()


class DocumentMeta(ABCMeta):
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
        _meta = {}

        # Document inheritance implementation
        for parent_cls in parents:
            # Copy parent fields
            parent_fields = getattr(parent_cls, '_fields', {})
            _fields.update(parent_fields)

            # Copy parent meta options
            parent_meta = getattr(parent_cls, '_meta', {})
            _meta.update(parent_meta)

        # Inspect subclass to save SimpleFields and require field names
        for field_name, obj in dct.items():
            if issubclass(type(obj), SimpleField):
                # set SimpleField text name as a private `_name` attribute
                obj._name = field_name
                obj._holder_name = name  # class holder name
                _fields[obj.name] = obj

            elif all([field_name == 'Meta', inspect.isclass(obj)]):
                _meta.update(obj.__dict__)

        dct['_fields'] = _fields
        dct['_parents'] = tuple(parents)
        dct['_meta'] = _meta

        cls = super(DocumentMeta, mcs).__new__(mcs, name, parents, dct)
        registry[name] = cls
        return cls


@six.add_metaclass(DocumentMeta)
class Document(MutableMapping):
    """ Main class to represent structured dict-like document """

    class Meta:
        # make a model 'schemaless'
        ALLOW_EXTRA_FIELDS = False

        # if field is not passed to the constructor, exclude it from structure
        OMIT_MISSED_FIELDS = False

        # TODO: it might make sense to add option to raise an error if unknown
        # field is given for the document

    def __init__(self, data=None, **kwargs):
        if data is None:
            data = {}

        if self._meta['ALLOW_EXTRA_FIELDS']:
            self._fields = copy.deepcopy(self._fields)

        if not isinstance(data, MutableMapping):
            raise ModelValidationError(
                "Data must be instance of mapping, but got '%s'!" %
                type(data))

        data = copy.deepcopy(data)
        data = self._clean_data(data)

        self._prepare_fields(data, **kwargs)
        self._post_init_validation()

    def __getitem__(self, name):
        return getattr(self, name)

    def __setitem__(self, name, value):
        setattr(self, name, value)

    def __delitem__(self, name):
        delattr(self, name)

    def __iter__(self):
        """Iterator over available field names of the Document.

        Fields, which values are `None` will be returned only
        in case `OMIT_MISSED_FIELDS` meta variable is `False`.
        """
        for field_name in self._fields:
            if self.get(field_name) is not None or not self._meta['OMIT_MISSED_FIELDS']:
                yield field_name

    def __len__(self):
        return len(self._fields)

    def as_dict(self):
        return {
            field_name: self._fields[field_name].to_python(value)
            for field_name, value in self.items()
        }

    def _prepare_fields(self, data, **kwargs):
        """Do field validations and set defaults

        :param data: init parameters
        :return:
        """

        # It validates values on set, check fields.SimpleField#__set_value__
        for field_name, field_obj in self._fields.items():
            field_val = data.get(field_name, field_obj.default)

            # Build model structure
            if field_name in data:
                # remove field from data, so at the end
                # only extra fields would left.
                data.pop(field_name)

                # set presented field
                field_obj.__set_value__(self, field_val, **kwargs)
            else:
                # field is not presented in the given init parameters
                if field_val is None and self._meta['OMIT_MISSED_FIELDS']:
                    # Run validation even on skipped fields to validate
                    # 'required' and other attributes
                    field_obj.validate(field_val)
                    continue
                field_obj.__set_value__(self, field_val, **kwargs)

        # Create extra fields if any were not filtered by `_clean_data` method.
        # ALLOW_EXTRA_FIELDS has an effect here
        for key, value in data.items():
            # py3 will raise an AttributeError without explicitly given 'None'
            # as a 3rd parameter
            if getattr(self, key, None):
                raise DocumentError(
                    "Can't add extra field '%s.%s' because document already has "
                    "entity with the same name" % (self.__class__.__name__, key))
            field_obj = ExtraField()
            field_obj._name = key
            field_obj._holder_name = self.__class__.__name__
            self._fields[key] = field_obj

            field_obj.__set_value__(self, value, **kwargs)
        return data

    @classmethod
    def _clean_data(cls, kwargs):
        """Clean with excluding extra fields if the model has
        ALLOW_EXTRA_FIELDS meta flag on

        :param kwargs: dict
        :return: cleaned kwargs
        """
        fields = getattr(cls, '_fields', {})

        # put everything extra in the document
        if cls._meta['ALLOW_EXTRA_FIELDS']:
            return kwargs
        else:
            return {k: v for k, v in kwargs.items() if k in fields}

    def _post_init_validation(self):
        """Validate model after init with validate_%s extra methods
        """
        internals = dir(self)
        # NOTE: this can be done in the DocumentMeta
        for field_name, field_obj in self._fields.items():
            method_name = 'validate_%s' % field_name
            if method_name in internals:
                validation_method = getattr(self, method_name)
                if inspect.isfunction(validation_method):
                    # NOTE: probably need to pass immutable copy of the object
                    validation_method(self, self[field_name])
                else:
                    raise ModelValidationError(
                        '%s (%r) is not a function' %
                        (method_name, validation_method,))

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, dict(self))


class ImmutableDocument(Document):
    """Read only document. Useful for validation purposes only"""

    def __setattr__(self, key, value):
        raise DocumentError(
            '{} is immutable. Set operation is not allowed.'.format(self))

    def __setitem__(self, key, value):
        return setattr(self, key, value)
