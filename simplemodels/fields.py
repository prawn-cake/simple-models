# -*- coding: utf-8 -*-
""" Fields for DictEmbedded model """

from decimal import Decimal, InvalidOperation
import warnings

import six

from simplemodels import PYTHON_VERSION
from simplemodels.exceptions import ValidationError, ValidationDefaultError, \
    ImmutableFieldError


__all__ = ['SimpleField', 'IntegerField', 'FloatField', 'DecimalField',
           'CharField', 'BooleanField']


class SimpleField(object):

    """Class-field with descriptor for DictEmbeddedDocument"""

    def __init__(self, default=None, required=False, choices=None, name=None,
                 validator=None, validators=None, error_text='',
                 immutable=False, **kwargs):
        """
        :param name: optional name
        :param default: default value
        :param required: is field required
        :param choices: choices list.
        :param validator: callable object to validate a value. DEPRECATED
        :param validators: list of callable objects - validators
        :param error_text: user-defined error text in case of errors
        :param immutable: immutable field type
        :param kwargs: for future options
        """

        self._name = None           # set by object holder (Document)
        self._holder_name = None    # set by object holder (Document)
        self._verbose_name = kwargs.get('verbose_name', name)

        self.required = required
        if choices and not isinstance(choices, (tuple, list, set)):
            raise ValueError(
                'Wrong choices data type {}, '
                'must be (tuple, list, set)'.format(type(choices)))
        self.choices = choices
        self.validator = validator

        # NOTE: new feature - chain of validators
        self.validators = validators or []

        self.default = default() if callable(default) else default
        self._value = default() if callable(default) else default

        self.error_text = error_text

        # validate default value
        if self.default:
            self.default = self.validate(value=self.default,
                                         err=ValidationDefaultError)

        self._immutable = immutable

        # for backward compatibility
        if self.validator:
            warnings.warn('Use `validators` parameter instead of `validator`')
            self.validators.append(self.validator)
    
    @property
    def name(self):
        return self._verbose_name or self._name
    
    def validate(self, value, err=ValidationError):
        """Helper method to validate field.

        :param value: value to validate
        :return:
        """
        from simplemodels.models import Document

        if not self.validators:
            return value

        def is_document(validator):
            try:
                # Handle an error with issubclass(lambda function)
                return issubclass(validator, Document)
            except TypeError:
                return False

        for validator in self.validators:
            try:
                if is_document(validator):
                    # use document as a validator for nested documents
                    doc_cls = validator
                    value = doc_cls(**value)
                else:
                    value = validator(value)

            # InvalidOperation for decimal, TypeError
            except InvalidOperation:
                raise err("Invalid decimal operation for '{!r}' for the field "
                          "`{!r}`. {}".format(value, self, self.error_text))
            except (ValueError, TypeError):
                raise err("Wrong value '{!r}' for the field `{!r}`. "
                          "{}".format(value, self, self.error_text))

        if self.choices:
            if value not in self.choices:
                raise ValueError(
                    'Value {} is restricted by choices: {}'.format(
                        value, self.choices))
        return value

    @classmethod
    def _validate_choices(cls, value, choices):
        if value not in choices:
            pass

    def has_default(self):
        return self.default is not None

    @staticmethod
    def _add_default_validator(validator, kwargs):
        """Helper method for subclasses

        :param validator:
        """
        kwargs.setdefault('validators', [])

        if validator not in kwargs['validators']:
            kwargs['validators'].append(validator)
        return kwargs

    def __get__(self, instance, owner):
        return instance.__dict__.get(self.name, self.default)

    def __set__(self, instance, value):
        if self._immutable:
            raise ImmutableFieldError('{!r} field is immutable'.format(self))
        value = self.validate(value)
        instance.__dict__[self.name] = value

    def __repr__(self):
        return six.u("{}.{}".format(self._holder_name, self.name))

    def __unicode__(self):
        return six.u("{}.{}".format(self._holder_name, self.name))


class IntegerField(SimpleField):
    def __init__(self, **kwargs):
        self._add_default_validator(int, kwargs)
        super(IntegerField, self).__init__(**kwargs)


class FloatField(SimpleField):
    def __init__(self, **kwargs):
        self._add_default_validator(float, kwargs)
        super(FloatField, self).__init__(**kwargs)


class DecimalField(SimpleField):
    def __init__(self, **kwargs):
        self._add_default_validator(Decimal, kwargs)
        super(DecimalField, self).__init__(**kwargs)


class CharField(SimpleField):
    def __init__(self, is_unicode=True, max_length=None, **kwargs):
        if PYTHON_VERSION == 2:
            validator = unicode if is_unicode else str
        else:
            validator = str

        self._add_default_validator(validator, kwargs)

        # Add max length validator
        if max_length:
            self.max_length = max_length
            self._add_default_validator(
                validator=self._validate_max_length,
                kwargs=kwargs)

        super(CharField, self).__init__(**kwargs)

    def _validate_max_length(self, value):
        if len(value) > self.max_length:
            raise ValidationError(
                'Max length is exceeded ({} < {}) for the field {!r}'.format(
                    len(value), self.max_length, self))


class BooleanField(SimpleField):
    def __init__(self, **kwargs):
        self._add_default_validator(bool, kwargs)
        super(BooleanField, self).__init__(**kwargs)


class DocumentField(SimpleField):
    """Embedded document field"""

    def __init__(self, model, **kwargs):
        self._add_default_validator(model, kwargs)
        super(DocumentField, self).__init__(**kwargs)
