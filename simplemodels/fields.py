# -*- coding: utf-8 -*-
import copy
import warnings
from collections import Mapping, MutableSequence
from datetime import datetime
from decimal import Decimal

import six

from simplemodels import PYTHON_VERSION
from simplemodels.exceptions import FieldError, FieldRequiredError, ImmutableFieldError, \
    ModelNotFoundError, ValidationError
from simplemodels.utils import is_document

__all__ = ['SimpleField', 'IntegerField', 'FloatField', 'DecimalField',
           'CharField', 'BooleanField', 'DateTimeField', 'ListField',
           'DocumentField', 'DictField']


class SimpleField(object):
    """Basic field. It stores values as is by default."""

    MUTABLE_TYPES = (list, dict, set, bytearray)
    CHOICES_TYPES = (tuple, list, set)

    def __init__(self, default=None, required=False, choices=None, name=None,
                 validators=None, immutable=False, **kwargs):
        """
        :param name: field name, it's set in the DocumentMeta
        :param default: default value
        :param required: is field required
        :param choices: choices list.
        :param validators: list of callable objects - validators
        :param immutable: immutable field type
        :param kwargs: for future options
        """

        self._name = None  # set by object holder (Document)
        self._holder_name = None  # set by object holder (Document)
        self._verbose_name = kwargs.get('verbose_name', name)

        self.required = required
        if choices and not isinstance(choices, SimpleField.CHOICES_TYPES):
            raise ValueError(
                'Wrong choices data type {}, '
                'must be (tuple, list, set)'.format(type(choices)))
        self.choices = choices

        # NOTE: new feature - chain of validators
        self.validators = validators or []
        if not isinstance(self.validators, (list, tuple, set)):
            raise FieldError('validators must be list, tuple or set, '
                             '%r is given' % validators)

        self._add_validator(self._validate_required)
        self._add_validator(self._validate_choices)

        # Set default value
        self._set_default_value(default)

        self._immutable = immutable

    def _set_default_value(self, value):
        """Set default value, handle mutable default parameters,
        delegate set callable default value to Document

        :param value: default value
        """
        # Make a deep copy for mutable default values by setting it as a
        # callable lambda function
        if isinstance(value, SimpleField.MUTABLE_TYPES):
            self._default = lambda: copy.deepcopy(value)
        else:
            self._default = value

    def _typecast(self, value, func=None, **kwargs):
        """
        Cast given value to the field type.
        """
        if func and value is not None:
            return func(value, **kwargs)
        return value

    def to_python(self, value):
        return value

    @property
    def name(self):
        return self._verbose_name or self._name

    @property
    def default(self):
        return self._default() if callable(self._default) else self._default

    def _extract_value(self, value):
        """Extract value helper.
        This method looks dummy, but in some cases we need to extract value
        from the structure, e.g NestedPath

        :param value: any value
        :return: extracted value
        """
        return value

    def _validate_required(self, value):
        """
        Default validator for checking required value.

        :param value: value to validate.
        """
        if self.required:
            if value is None:
                raise FieldRequiredError(
                    "Field '%(name)s' is required: {%(name)r: %(value)r}"
                    % {'name': self.name, 'value': value})
            elif value == '':
                raise FieldRequiredError(
                    "Field '%(name)s' is empty: {%(name)r: %(value)r}"
                    % {'name': self.name, 'value': value})
        return True

    def _validate_choices(self, value):
        """
        Default validator for checking value within given choices.

        :param value: value to validate.
        """
        # Check choices if passed
        if self.choices:
            if value not in self.choices:
                raise ValidationError(
                    'Value {} is restricted by choices: {}'.format(
                        value, self.choices))
        return True

    def validate(self, value):
        """
        Method for validating a field.

        It runs several levels of validation:
          * validate required values
          * run main validators chain
          * run choices validation if applied

        :param value: value to validate
        """
        value = self._extract_value(value=value)

        # Run validators chain
        for validate in self.validators:
            if not validate(value):
                raise ValidationError(
                    "Value '{value}' of the `{name}` field haven't passed validation '{validate}'".format(
                        value=value, name=self.name, validate=validate)
                )

    def _add_validator(self, validator):
        """
        Helper method to add a validator to validation chain.

        :param validator: callable
        """
        if not callable(validator):
            raise FieldError(
                "Validator '%r' for field '%r' is not callable!" %
                (validator, self))

        if validator not in self.validators:
            self.validators.append(validator)

    def __get__(self, instance, owner):
        """Descriptor getter

        :param instance: simplemodels.models.Document instance
        :param owner: simplemodels.models.DocumentMeta
        :return: field value
        """
        return instance.__dict__.get(self.name)

    def __set_value__(self, instance, value, **kwargs):
        """Common value setter to use it from __set__ descriptor and from
        simplemodels.models.Document init

        IMPORTANT: THIS METHOD MUST RETURN A VALUE BECAUSE IT IS USED BY
        A DOCUMENT ON PREPARE DOCUMENT STEP

        :param instance: simplemodels.models.Document instance
        :param value: field value
        """
        value = self._typecast(value, **kwargs)
        self.validate(value)
        instance.__dict__[self.name] = value
        return value

    def __set__(self, instance, value):
        """Descriptor setter

        :param instance: simplemodels.models.Document instance
        :param value: field value
        :raise ImmutableFieldError:
        """
        if self._immutable:
            raise ImmutableFieldError('{!r} field is immutable'.format(self))
        self.__set_value__(instance, value)

    def __repr__(self):
        if self._holder_name and self.name:
            return six.u("{}.{}".format(self._holder_name, self.name))
        else:
            return self.__class__.__name__

    def __unicode__(self):
        return self.__repr__()


class ExtraField(SimpleField):
    """
    Class for creating fields from extra values.

    If Model has `ALLOW_EXTRA_FIELDS` meta flag configured,
    all extra fields would be created using this class.
    """


class IntegerField(SimpleField):

    def _typecast(self, value, **kwargs):
        return super(IntegerField, self)._typecast(value, int, **{})


class FloatField(SimpleField):

    def _typecast(self, value, **kwargs):
        return super(FloatField, self)._typecast(value, float, **{})


class DecimalField(SimpleField):

    def _typecast(self, value, **kwargs):
        return super(DecimalField, self)._typecast(value, Decimal, **{})


class CharField(SimpleField):

    def _typecast(self, value, **kwargs):
        return super(CharField, self)._typecast(value, self._caster, **{})

    def __init__(self, is_unicode=True, max_length=None, **kwargs):
        if PYTHON_VERSION == 2:
            self._caster = unicode if is_unicode else str
        else:
            self._caster = str

        super(CharField, self).__init__(**kwargs)

        # Add max length validator
        self._max_length = max_length
        if self._max_length is not None:
            self._add_validator(self.validate_max_length)

    def validate_max_length(self, value):
        if value and len(value) > self._max_length:
            raise ValidationError(
                'Max length is exceeded ({} < {}) for the '
                'field {!r}'.format(len(value), self._max_length, self))
        return True


class BooleanField(SimpleField):

    def _typecast(self, value, **kwargs):
        return super(BooleanField, self)._typecast(value, bool, **{})


class DateTimeField(SimpleField):
    DATE_FORMAT = '%Y-%m-%dT%H:%M:%SZ'

    def __init__(self, date_fmt=None, **kwargs):
        self._date_fmt = date_fmt or self.DATE_FORMAT
        super(DateTimeField, self).__init__(**kwargs)

    def _typecast(self, value, **kwargs):
        if isinstance(value, six.string_types):
            func = lambda val: datetime.strptime(val, self._date_fmt)
        elif isinstance(value, (int, float)):
            func = datetime.fromtimestamp
        elif isinstance(value, datetime) or value is None:
            func = None
        else:
            raise ValueError("Incorrect type '{type}' for '{name}' field!".format(
                type=type(value).__name__, name=self.name
            ))

        return super(DateTimeField, self)._typecast(value, func, **{})

    def to_python(self, value):
        if value is not None:
            return value.strftime(self._date_fmt)


class DocumentField(SimpleField):
    """Embedded document field.

    Usage:

        class Website(Document):
            url = CharField()

        class User(Document)
            website = DocumentField(model=Website)  # or model='Website'
    """

    def __init__(self, model, **kwargs):
        self._model = model
        super(DocumentField, self).__init__(**kwargs)

    def _typecast(self, value, **kwargs):
        if isinstance(self._model, str):
            from simplemodels.models import registry
            model = registry.get(self._model)
            if not model:
                raise ModelNotFoundError(
                    "Model '%s' does not exist" %
                    self._model)
        else:
            model = self._model

        return super(DocumentField, self)._typecast(
            value or {}, model, **kwargs)

    def to_python(self, value):
        return value.as_dict()


class ListType(MutableSequence):
    """
    Special sequence class which is instantiated for `ListField`.

    When you add a `ListField` and create an instance of it,
    original field descriptor is saved in `<SomeDocument>._fields`,
    and you field attribute is replaces with instance of `ListType`.
    """

    def __init__(self, value, of, **kwargs):
        if not isinstance(value, MutableSequence):
            raise ValueError('Value %r is not a sequence' % value)

        self._of = of
        self._raw_value = value
        self._kwargs = kwargs
        # if `of` is string - postpone type casting
        self._list = None if isinstance(self._of, str) else self.list

    @property
    def list(self):
        if hasattr(self, '_raw_value'):
            if isinstance(self._of, str):
                from simplemodels.models import registry
                self._of = registry.get(self._of)
                if not self._of:
                    raise ModelNotFoundError(
                        "Model '%s' does not exist" % self._of)

            if is_document(self._of):
                self._list = [self._of(data, **self._kwargs)
                              for data in self._raw_value]
            else:
                self._list = [self._of(data) for data in self._raw_value]
            delattr(self, '_raw_value')

        return self._list

    def __len__(self):
        return len(self.list)

    def __getitem__(self, index):
        return self.list[index]

    def __setitem__(self, index, value):
        self.list[index] = value

    def __delitem__(self, index):
        del self.list[index]

    def __eq__(self, other):
        return self.list == other

    def __ne__(self, other):
        return self.list != other

    def __str__(self):
        return self.list.__str__()

    def __repr__(self):
        return self.list.__repr__()

    def sort(self, key=None, reverse=False):
        self._list = sorted(self.list, key=key, reverse=reverse)

    def insert(self, index, value):
        from simplemodels.models import Document

        if isinstance(value, (Document, ListField)):
            value = self._of(data=value, **self._kwargs)
        else:
            value = self._of(value)
        self.list.insert(index, value)


class ListField(SimpleField):
    """ List of items field"""

    def __init__(self, of, **kwargs):
        """

        :param of: callable: single validator,
                   e.g: 'str', 'lambda x: str(x).upper()'
        :param kwargs:
        """

        self._of = of

        # NOTE: forbid to have external validators for the ListField
        if 'validators' in kwargs:
            warnings.warn(
                "%s shouldn't have 'validators' parameter, use 'of' instead"
                % self.__class__.__name__)
            kwargs.pop('validators')

        super(ListField, self).__init__(**kwargs)

    def _typecast(self, value, **kwargs):
        return ListType(value=value or [], of=self._of, **kwargs)

    def to_python(self, value):
        if hasattr(self._of, 'as_dict'):
            return [item.as_dict() for item in value]
        return [item for item in value]


class DictField(SimpleField):
    """ Dictionary field. Useful when you want to be more specific than just
    using SimpleField"""

    def __init__(self, dict_cls=dict, **kwargs):
        if not issubclass(dict_cls, Mapping):
            raise ValueError("Wrong dict_cls parameter '%r'. "
                             "Must be Mapping" % dict_cls)
        self._dict_cls = dict_cls
        super(DictField, self).__init__(**kwargs)

    def _typecast(self, value, **kwargs):
        return super(DictField, self)._typecast(value, self._dict_cls, **{})
