# -*- coding: utf-8 -*-
import six
import inspect
from simplemodels.exceptions import ImmutableDocumentError, \
    ModelValidationError
from simplemodels.fields import SimpleField, DocumentField


__all__ = ['Document', 'ImmutableDocument']


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
        return cls


@six.add_metaclass(DocumentMeta)
class Document(AttributeDict):

    """ Main class to represent structured dict-like document """

    class Meta:
        ALLOW_EXTRA_FIELDS = False

        # if field is not passed to the constructor, exclude it from structure
        OMIT_MISSED_FIELDS = False

    def __init__(self, **kwargs):
        kwargs = self._clean_kwargs(kwargs)

        # dict init
        prepared_fields = self._prepare_fields(**kwargs)
        super(Document, self).__init__(**prepared_fields)
        self._post_init_validation()

    def _prepare_fields(self, **kwargs):
        """Do field validations and set defaults

        :param kwargs: init parameters
        :return: :raise RequiredValidationError:
        """

        # It validates values on set, see
        # simplemodels.fields.SimpleField#__set_value__
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
                    continue
                val = field_obj.__set_value__(self, field_val)
                kwargs[field_name] = val

        return kwargs

    @classmethod
    def _clean_kwargs(cls, kwargs):
        fields = getattr(cls, '_fields', {})

        # put everything extra in the document
        if cls._meta.ALLOW_EXTRA_FIELDS:
            kwargs = {k: v for k, v in kwargs.items()}
        else:
            kwargs = {k: v for k, v in kwargs.items() if k in fields}

        return kwargs

    def _post_init_validation(self):
        """Validate model after init
        """
        internals = dir(self)
        # NOTE: this can be done in the DocumentMeta
        for field_name, field_obj in self._fields.items():
            method_name = 'validate_%s' % field_name
            if method_name in internals:
                method = getattr(self, method_name)
                if inspect.isfunction(method):
                    # NOTE: probably need to pass immutable copy of the object
                    method(self, self[field_name])
                else:
                    raise ModelValidationError(
                        '%s (%r) is not a function' % (method_name, method, ))


class ImmutableDocument(Document):
    """Read only document. Useful"""

    def __setattr__(self, key, value):
        raise ImmutableDocumentError(
            'Set operation is not allowed for {}'.format(
                self.__class__.__name__))

    def __setitem__(self, key, value):
        return setattr(self, key, value)
