# -*- coding: utf-8 -*-
import six
from simplemodels.exceptions import ValidationRequiredError, \
    ImmutableDocumentError
from simplemodels.fields import SimpleField, DocumentField


__all__ = ['Document', 'ImmutableDocument']


class AttributeDict(dict):

    """Dict wrapper with access to keys via attributes"""

    def __getattr__(self, name):
        # do not affect magic methods like __deepcopy__
        if name.startswith('__') and name.endswith('__'):
            return super(AttributeDict, self).__getattr__(self, name)

        try:
            return self[name]
        except KeyError:
            raise AttributeError("Attribute '{}' doesn't exist".format(name))

    def __setattr__(self, key, value):
        super(AttributeDict, self).__setattr__(key, value)
        self[key] = value


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
        _required_fields = []

        # Inspect subclass to save SimpleFields and require field names
        for field_name, obj in dct.items():
            if issubclass(type(obj), SimpleField):
                # set SimpleField text name as a private `_name` attribute
                obj._name = field_name
                obj._holder_name = name  # class holder name

                _fields[obj.name] = obj
                if obj.required:
                    _required_fields.append(obj.name)

        dct['_fields'] = _fields
        dct['_required_fields'] = tuple(_required_fields)

        cls = super(DocumentMeta, mcs).__new__(mcs, name, parents, dct)
        return cls


@six.add_metaclass(DocumentMeta)
class Document(AttributeDict):

    """ Main class to represent structured dict-like document """

    # TODO: implement some kind of class Meta:
    ALLOW_EXTRA_FIELDS = False
    IGNORE_NONE_ON_INIT = False

    def __init__(self, **kwargs):
        kwargs = self._clean_kwargs(kwargs)

        # dict init
        prepared_fields = self._prepare_fields(**kwargs)
        super(Document, self).__init__(**prepared_fields)

    def _prepare_fields(self, **kwargs):
        """Do field validations and set defaults

        :param kwargs: init parameters
        :return: :raise RequiredValidationError:
        """
        errors_list = []

        # Do some validations
        for field_name, field_obj in self._fields.items():

            # Get field value or set default
            default_val = getattr(field_obj, 'default')
            field_val = kwargs.get(
                field_name,
                default_val() if callable(default_val) else default_val)

            # Validate required fields
            self._validate_required(
                name=field_name, value=field_val, errors=errors_list)

            # Ignore None field values from the initial structure
            if self.IGNORE_NONE_ON_INIT and field_val is None:
                continue

            if errors_list:
                raise ValidationRequiredError(str(errors_list))

            # Build model structure
            if field_name in kwargs:
                field_obj.__set_value__(self, field_val)
                kwargs[field_name] = field_obj.__get__(self, field_name)
            elif issubclass(type(field_obj), DocumentField):
                # build empty nested document
                field_obj.__set_value__(self, {})
                kwargs[field_name] = field_obj.__get__(self, field_name)
            else:
                field_obj.__set_value__(self, field_val)
                kwargs[field_name] = field_obj.__get__(self, field_name)

        return kwargs

    @classmethod
    def _validate_required(cls, name, value, errors):
        if name in getattr(cls, '_required_fields', []):
            if value is None or value == '':
                errors.append("Field '{}' is required for {}".format(
                    name, cls.__name__))
        return True

    @classmethod
    def _clean_kwargs(cls, kwargs):
        fields = getattr(cls, '_fields', {})
        if cls.ALLOW_EXTRA_FIELDS:  # put everything extra in the document
            return {k: v for k, v in kwargs.items()}
        else:
            return {k: v for k, v in kwargs.items() if k in fields}


class ImmutableDocument(Document):
    """Read only document. Useful"""

    def __setattr__(self, key, value):
        raise ImmutableDocumentError(
            'Set operation is not allowed for {}'.format(
                self.__class__.__name__))

    def __setitem__(self, key, value):
        return setattr(self, key, value)
