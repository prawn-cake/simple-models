# -*- coding: utf-8 -*-
""" Fields for DictEmbedded model """


class SimpleField(object):

    """Class-field with descriptor for DictEmbeddedDocument"""

    def __init__(self, default=None, required=False, choices=None, _type=None,
                 **kwargs):

        """

        :param default: default value
        :param required: is field required
        :param choices: choices list. See utils.Choices
        :param _type: type validation
        :param kwargs: for future options
        """
        self._name = None
        # For future static typing
        self.type = _type

        self.default = default
        self.required = required

        # TODO: support choices validation
        self.choices = choices

    def __get__(self, instance, owner):
        return instance.__dict__.get(self._name, self.default)

    def __set__(self, instance, value):
        from simplemodels.validators import get_validator
        value = get_validator(self.type).validate(value)
        instance.__dict__[self._name] = value

    def __repr__(self):
        return unicode("<{}: {}>".format(self.__class__.__name__, self._name))

    def __unicode__(self):
        return unicode("<{}: {}>".format(self.__class__.__name__, self._name))