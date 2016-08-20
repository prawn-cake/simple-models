# -*- coding: utf-8 -*-

import six
import inspect
import weakref
from simplemodels.exceptions import ImmutableDocumentError, \
    ModelValidationError
from simplemodels.fields import SimpleField, DocumentField


__all__ = ['Document', 'ImmutableDocument']


registry = weakref.WeakValueDictionary()


class AttributeDict(dict):

    """Dict wrapper with access to keys via attributes"""

    def __getattr__(self, name):
        # do not affect magic methods like __deepcopy__
        if name.startswith('__') and name.endswith('__'):
            return super(AttributeDict, self).__getattr__(self, name)

        try:
            val = self[name]
            if isinstance(val, dict) and not isinstance(val, AttributeDict):
                return AttributeDict(val)
            return val
        except KeyError:
            raise AttributeError("Attribute '{}' doesn't exist".format(name))

    def __setattr__(self, key, value):
        if isinstance(value, dict):
            value = AttributeDict(value)
        super(AttributeDict, self).__setattr__(key, value)
        self[key] = super(AttributeDict, self).__getattribute__(key)


class DocumentMeta(type):
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
        _meta = AttributeDict()

        # Document inheritance implementation
        for parent_cls in parents:
            # Copy parent fields
            parent_fields = getattr(parent_cls, '_fields', {})
            _fields.update(parent_fields)

            # Copy parent meta options
            parent_meta = getattr(parent_cls, '_meta', AttributeDict())
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

    def __instancecheck__(cls, instance):
        """Document instance check implementation.
        It allows to do `isinstance(my_instance, MyDocument)`

        :param instance: any data
        :return: bool
        """
        # Instance data must be a dict or Document
        cond = (isinstance(instance, dict),
                issubclass(type(instance), Document))
        if not any(cond):
            return False
        try:
            cls(**instance)
        except TypeError:
            return False
        return True


@six.add_metaclass(DocumentMeta)
class Document(AttributeDict):
    """ Main class to represent structured dict-like document """

    class Meta:
        # make a model 'schemaless'
        ALLOW_EXTRA_FIELDS = False

        # if field is not passed to the constructor, exclude it from structure
        OMIT_MISSED_FIELDS = False

        # TODO: it might make sense to add option to raise an error if unknown
        # field is given for the document

    def __init__(self, **kwargs):
        kwargs = self._unprotect_fields(kwargs)
        kwargs = self._clean_kwargs(kwargs)

        # dict init
        prepared_fields = self._prepare_fields(kwargs)
        super(Document, self).__init__(**prepared_fields)
        self._post_init_validation()

    def _prepare_fields(self, kwargs):
        """Do field validations and set defaults

        :param kwargs: init parameters
        :return: :raise RequiredValidationError:
        """

        # It validates values on set, check fields.SimpleField#__set_value__
        for field_name, field_obj in self._fields.items():

            # Get field value or set default
            default_val = getattr(field_obj, 'default')
            field_val = kwargs.get(field_name)
            if field_val is None:
                field_val = default_val() if callable(default_val) \
                    else default_val

            # Build model structure
            if field_name in kwargs:
                # set presented field
                val = field_obj.__set_value__(self, field_val)
                kwargs[field_name] = val
            elif issubclass(type(field_obj), DocumentField):
                # build empty nested document
                val = field_obj.__set_value__(self, {})
                kwargs[field_name] = val
            else:
                # field is not presented in the given init parameters
                if field_val is None and self._meta.OMIT_MISSED_FIELDS:
                    # Run validation even on skipped fields to validate
                    # 'required' and other attributes
                    field_obj.validate(field_val)
                    continue
                val = field_obj.__set_value__(self, field_val)
                kwargs[field_name] = val

        return kwargs

    @classmethod
    def _clean_kwargs(cls, kwargs):
        """Clean with excluding extra fields if the model has
        ALLOW_EXTRA_FIELDS meta flag on

        :param kwargs: dict
        :return: cleaned kwargs
        """
        fields = getattr(cls, '_fields', {})

        # put everything extra in the document
        if cls._meta.ALLOW_EXTRA_FIELDS:
            kwargs = {k: v for k, v in kwargs.items()}
        else:
            kwargs = {k: v for k, v in kwargs.items() if k in fields}

        return kwargs

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
                        (method_name, validation_method, ))

    @classmethod
    def _protect_fields(cls, kwargs):
        """Rename all of the fields with ModelName_field.
        This enables fields protection from 'self', 'cls' and other reserved
        keywords
        """
        return {'%s_%s' % (cls.__name__, k): v for k, v in kwargs.items()}

    @classmethod
    def _unprotect_fields(cls, kwargs):
        """Reverse of protect fields + backward compatible with old init style.

        """
        protect_prefix = '%s_' % cls.__name__
        unprotected = {}
        for k, v in kwargs.items():
            if k.startswith(protect_prefix):
                k = k.replace(protect_prefix, '')
                unprotected[k] = v

            # Do not override protected and decoded values
            if k not in unprotected:
                unprotected[k] = v
        return unprotected

    @classmethod
    def create(cls, kwargs):
        """Safe factory method to create a document

        :return: document instance
        """
        protected = cls._protect_fields(kwargs)
        return cls(**protected)


class ImmutableDocument(Document):
    """Read only document. Useful for validation purposes only"""

    def __setattr__(self, key, value):
        raise ImmutableDocumentError(
            '%r is immutable. Set operation is not allowed for {}'.format(
                self, self.__class__.__name__))

    def __setitem__(self, key, value):
        return setattr(self, key, value)
