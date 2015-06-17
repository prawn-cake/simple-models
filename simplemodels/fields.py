# -*- coding: utf-8 -*-
""" Fields for DictEmbedded model """

from simplemodels import PYTHON_VERSION

from simplemodels.exceptions import ValidationError
import six
from decimal import Decimal, InvalidOperation

__all__ = ['SimpleField', 'IntegerField', 'FloatField', 'DecimalField',
           'CharField', 'BooleanField']


class SimpleField(object):

    """Class-field with descriptor for DictEmbeddedDocument"""

    def __init__(self, default=None, required=False, choices=None,
                 validator=None, error_text='', name=None, **kwargs):
        """
        :param name: optional name
        :param default: default value
        :param required: is field required
        :param choices: choices list. See utils.Choices
        :param validator: callable object to validate a value
        :param error_text: return with validation error, which helps to debug
        :param kwargs: for future options
        """

        self._name = None           # will be set by holder
        self._holder_name = None    # will be set by holder
        self._optional_name = name

        self.required = required
        # TODO: support choices validation
        self.choices = choices
        self.validator = validator
        # TODO: validate default value
        self.default = default() if callable(default) else default
        self.error_text = error_text

    def get_name(self):
        return self._optional_name or self._name

    def validate(self, value):
        """Helper method to validate field.

        :param value:
        :return:
        """
        from simplemodels.models import DictEmbeddedDocument

        if self.validator is None:
            return value

        try:
            is_document = False
            try:
                # Handle an error with issubclass(lambda function)
                is_document = issubclass(
                    self.validator, DictEmbeddedDocument)
            except TypeError:
                pass

            if is_document:
                validated_val = self.validator(**value)
            else:
                validated_val = self.validator(value)

        # InvalidOperation for decimal, TypeError
        except (ValueError, InvalidOperation, TypeError):
            raise ValidationError("Wrong value '{}' for the field `{}`. {}"
                                  "".format(value, self, self.error_text))
        else:
            return validated_val

    def has_default(self):
        return self.default is not None

    def __get__(self, instance, owner):
        return instance.__dict__.get(self.get_name(), self.default)

    def __set__(self, instance, value):
        value = self.validate(value)
        instance.__dict__[self.get_name()] = value

    def __repr__(self):
        return six.u("{}.{}".format(self._holder_name, self.get_name()))

    def __unicode__(self):
        return six.u("{}.{}".format(self._holder_name, self.get_name()))


class IntegerField(SimpleField):
    def __init__(self, **kwargs):
        kwargs['validator'] = int
        super(IntegerField, self).__init__(**kwargs)


class FloatField(SimpleField):
    def __init__(self, **kwargs):
        kwargs['validator'] = float
        super(FloatField, self).__init__(**kwargs)


class DecimalField(SimpleField):
    def __init__(self, **kwargs):
        kwargs['validator'] = Decimal
        super(DecimalField, self).__init__(**kwargs)


class CharField(SimpleField):
    def __init__(self, is_unicode=False, **kwargs):
        if PYTHON_VERSION == 2:
            kwargs['validator'] = unicode if is_unicode else str
        else:
            kwargs['validator'] = str
        super(CharField, self).__init__(**kwargs)


class BooleanField(SimpleField):
    def __init__(self, **kwargs):
        kwargs['validator'] = bool
        super(BooleanField, self).__init__(**kwargs)


class DocumentField(SimpleField):
    """Embedded document field"""

    def __init__(self, model, **kwargs):
        kwargs['validator'] = model
        super(DocumentField, self).__init__(**kwargs)