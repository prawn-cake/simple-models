# -*- coding: utf-8 -*-
""" Fields for DictEmbedded model """
from simplemodels.exceptions import ValidationError
import six


class SimpleField(object):

    """Class-field with descriptor for DictEmbeddedDocument"""

    def __init__(self, default=None, required=False, choices=None, type=None,
                 validator=None, error_text='', **kwargs):
        """

        :param default: default value
        :param required: is field required
        :param choices: choices list. See utils.Choices
        :param type: type validation
        :param validator: enhanced type validation with callable object
        :param error_text: return with validation error, helps to debug
        :param kwargs: for future options
        """

        self._name = None
        self._holder_name = None

        # For future static typing
        # FIXME: Remove type, use only callable validator instead
        self.type = type

        self.default = default() if callable(default) else default

        self.required = required

        # TODO: support choices validation
        self.choices = choices

        self.validator = validator

        self.error_text = error_text

        # FIXME: DEPRECATED validators, in future use only one callable validator
        # Get built-in validator if not provided
        if validator is None or not callable(validator):
            from simplemodels.validators import get_validator
            self.validator = get_validator(self.type)

    def validate(self, value):
        """Helper method to validate field.
        It could be done with 2 ways:
            - built-in validator with validator.validate(value) method
            - provided by user custom callable method to validate

        :param value:
        :return:
        """
        if value is None:
            return value

        # Check for built-in validators
        if hasattr(self.validator, 'validate'):
            return self.validator.validate(value)
        else:
            try:
                return self.validator(value)
            except ValueError:
                raise ValidationError("Wrong value '{}' for field `{}`. {}"
                                      "".format(value, self, self.error_text))

    def has_default(self):
        return self.default is not None

    def __get__(self, instance, owner):
        return instance.__dict__.get(self._name, self.default)

    def __set__(self, instance, value):
        value = self.validate(value)
        instance.__dict__[self._name] = value

    def __repr__(self):
        return six.u("{}.{}".format(self._holder_name, self._name))

    def __unicode__(self):
        return six.u("{}.{}".format(self._holder_name, self._name))