# -*- coding: utf-8 -*-
from collections import Mapping
import copy
from decimal import Decimal, InvalidOperation

import six

from simplemodels import PYTHON_VERSION
from simplemodels.exceptions import ValidationError, DefaultValueError, \
    ImmutableFieldError, FieldRequiredError
from simplemodels.utils import is_document


__all__ = ['SimpleField', 'IntegerField', 'FloatField', 'DecimalField',
           'CharField', 'BooleanField', 'ListField', 'DocumentField',
           'DictField']


class SimpleField(object):
    """Basic field. It stores values as is by default."""

    MUTABLE_TYPES = (list, dict, set, bytearray)
    CHOICES_TYPES = (tuple, list, set)

    def __init__(self, default=None, required=False, choices=None, name=None,
                 validators=None, error_text='', immutable=False, **kwargs):
        """
        :param name: optional name
        :param default: default value
        :param required: is field required
        :param choices: choices list.
        :param validators: list of callable objects - validators
        :param error_text: user-defined error text in case of errors
        :param immutable: immutable field type
        :param kwargs: for future options
        """

        self._name = None           # set by object holder (Document)
        self._holder_name = None    # set by object holder (Document)
        self._verbose_name = kwargs.get('verbose_name', name)

        self.required = required
        if choices and not isinstance(choices, SimpleField.CHOICES_TYPES):
            raise ValueError(
                'Wrong choices data type {}, '
                'must be (tuple, list, set)'.format(type(choices)))
        self.choices = choices

        # NOTE: new feature - chain of validators
        self.validators = validators or []
        self._value = None  # will be set by Document
        self.error_text = error_text

        # Set default value
        self._set_default_value(default)

        self._immutable = immutable

    def _set_default_value(self, value):
        """Set default value, handle mutable default parameters,
        delegate set callable default value to Document

        :param value: default value
        """
        # Make a deep copy for mutable default values by setting it as a
        # callable lambda function, see the code below
        if isinstance(value, SimpleField.MUTABLE_TYPES):
            self.default = lambda: copy.deepcopy(value)
        else:
            self.default = value

        # Validate and set default value
        if value is not None:
            if callable(self.default):
                self.validate(value=self.default(), err=DefaultValueError)
            else:
                self.default = self.validate(value=self.default,
                                             err=DefaultValueError)

    @property
    def name(self):
        return self._verbose_name or self._name

    def _run_validators(self, value, err=ValidationError):
        """Run validators chain and return validated (cleaned) value

        :param value: field value
        :param err: error to raise in case of validation errors
        :return: value :raise err:
        """
        for validator in self.validators:
            try:
                if is_document(validator):
                    # use document as a validator for nested documents
                    doc_cls = validator
                    value = doc_cls(**value)
                else:
                    value = validator(value)

                if value is None:
                    raise ValidationError(
                        'validator {!r} returned None value'.format(validator))

            # InvalidOperation for decimal, TypeError
            except InvalidOperation:
                raise err("Invalid decimal operation for '{!r}' for the field "
                          "`{!r}`. {}".format(value, self, self.error_text))
            except (ValueError, TypeError):
                # Accept None value for non-required fields
                if not self.required and value is None:
                    return value

                raise err("Wrong value '{!r}' for the field `{!r}`. "
                          "{}".format(value, self, self.error_text))
        return value

    def _validate_required(self, value):
        if self.required:
            if value is None or value == '':
                raise FieldRequiredError('Field %s is required' % self.name)

    def _pre_validate(self, value, err=ValidationError):
        """One of the validation chain method.

        :param value: simplemodels.exceptions.ValidationError: class
        :param err:
        :return:
        """
        return value

    def validate(self, value, err=ValidationError):
        """Main field validation method.

        It runs several levels of validation:
          * required attribute validation
          * pre-validation
          * validator chain
          * choices validation if applied

        :param value: value to validate
        :param err: simplemodels.exceptions.ValidationError: class
        :return: validated value
        """
        # Validate required
        self._validate_required(value=value)

        # Skip validation if no validators
        if not self.validators:
            return value

        # Run validators chain
        value = self._pre_validate(value=value, err=err)
        value = self._run_validators(value=value, err=err)

        # Check choices if passed
        if self.choices:
            if value not in self.choices:
                raise ValidationError(
                    'Value {} is restricted by choices: {}'.format(
                        value, self.choices))
        return value

    @staticmethod
    def _add_default_validator(validator, kwargs):
        """Helper method to add default validator used in subclasses

        :param kwargs: dict: field init key-value arguments
        :param validator: callable
        """
        kwargs.setdefault('validators', [])

        if validator not in kwargs['validators']:
            kwargs['validators'].append(validator)
        return kwargs

    def __get__(self, instance, owner):
        """Descriptor getter

        :param instance: simplemodels.models.Document instance
        :param owner: simplemodels.models.DocumentMeta
        :return: field value
        """
        return instance.__dict__.get(self.name)

    def __set_value__(self, instance, value):
        """Common value setter to use it from __set__ descriptor and from
        simplemodels.models.Document init

        :param instance: simplemodels.models.Document instance
        :param value: field value
        """
        value = self.validate(value)
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
            def validate_max_length(value):
                if len(value) > max_length:
                    raise ValidationError(
                        'Max length is exceeded ({} < {}) for the '
                        'field {!r}'.format(len(value), self.max_length, self))
                return value

            self.max_length = max_length
            self._add_default_validator(
                validator=validate_max_length,
                kwargs=kwargs)

        super(CharField, self).__init__(**kwargs)

    def __set_value__(self, instance, value):
        """Override method. Forbid to store None for CharField, because it
        result to conflicts like str(None) --> 'None'

        """
        if value is None:
            value = ''
        return super(CharField, self).__set_value__(instance, value)


class BooleanField(SimpleField):
    def __init__(self, **kwargs):
        self._add_default_validator(bool, kwargs)
        super(BooleanField, self).__init__(**kwargs)


class DocumentField(SimpleField):
    """Embedded document field.

    Usage:

        class Website(Document):
            url = CharField()

        class User(Document)
            website = DocumentField(model=Website)
    """

    def __init__(self, model, **kwargs):
        self._add_default_validator(model, kwargs)
        super(DocumentField, self).__init__(**kwargs)


class ListField(SimpleField):
    """ List of items field"""

    def __init__(self, item_types, **kwargs):
        if not isinstance(item_types, (list, set, tuple)):
            raise ValueError(
                'Wrong item_types data format, must be list, '
                'set or tuple, given {}'.format(type(item_types)))
        self._add_default_validator(list, kwargs)

        # list of possible item instances, for example: [str, int, float]
        # NOTE: unicode value will be accepted for `str` type
        self._item_types = []

        # Item type must be callable
        errors = []
        for t in item_types:
            if callable(t):
                self._item_types.append(t)
            else:
                errors.append('{} item type must be callable'.format(t))

        if errors:
            raise ValueError('\n'.join(errors))

        super(ListField, self).__init__(**kwargs)

    def _pre_validate(self, value, err=ValidationError):
        """Custom list field validate method

        :param value: values list, save value name for interface compatibility
        :param err: Exception class
        :return: :raise err:
        """

        items_list = value
        if not isinstance(items_list, list):
            raise err('Wrong values type {}, must be a list'.format(
                type(items_list)))

        errors = []
        types = tuple(self._item_types)
        for item in items_list:
            if not isinstance(item, types):
                # Unicode hook for python 2, accept unicode type as a str value
                if PYTHON_VERSION == 2 and str in types:
                    if isinstance(item, unicode):
                        continue
                errors.append(
                    'List value {} has wrong type ({}), must be one of '
                    '{}'.format(item, type(item).__name__, self._item_types))

        if errors:
            raise err('\n'.join(errors))
        return items_list


class DictField(SimpleField):
    """ Dictionary field. Useful when you want to be more specific than just
    using SimpleField"""

    def __init__(self, dict_cls=dict, **kwargs):
        if not issubclass(dict_cls, Mapping):
            raise ValueError("Wrong dict_cls parameter '%r'. "
                             "Must be Mapping" % dict_cls)
        self._add_default_validator(dict_cls, kwargs)
        super(DictField, self).__init__(**kwargs)

    def __getitem__(self, item):
        return self._value[item]

    def __setitem__(self, key, value):
        self._value[key] = value
