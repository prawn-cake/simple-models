# -*- coding: utf-8 -*-
""" Fields for DictEmbedded model """

from simplemodels.exceptions import ValidationError
from simplemodels.validators import VALIDATORS_MAP


class SimpleField(object):

    """Class-field with descriptor for DictEmbeddedDocument"""

    def __init__(self, default=None, required=False, choices=None,
                 link_cls=None, _type=None, **kwargs):

        """

        :param default: default value
        :param required: is field required
        :param choices: choices list. See utils.Choices
        :param link_cls: link to nested structure
        :param kwargs: for future options
        """
        self._name = None
        # For future static typing
        self.type = _type

        self.default = default
        self.required = required

        # TODO: support choices validation
        self.choices = choices

        self.link_cls = link_cls

    def __get__(self, instance, owner):
        return instance.__dict__.get(self._name, self.default)

    def __set__(self, instance, value):
        value = VALIDATORS_MAP[self.type].validate(value)
        instance.__dict__[self._name] = value

    @classmethod
    def validate_link_cls(cls, link_cls, value):
        from simplemodels.models import DictEmbeddedDocument

        if isinstance(link_cls, list):
            # link_cls can equals to '[Bids]' for example
            # that means list for Bids classes
            if not isinstance(value, list) and value is not None:
                raise ValidationError(
                    "Wrong list value instance, should be list of "
                    "'{}'".format(link_cls.__name__)
                )
            elif value is None:
                pass
            else:
                for v in list(value):
                    cls.validate_link_cls(link_cls[0], v)
        elif issubclass(link_cls, DictEmbeddedDocument):
            # Auto-create instance from dict if structure is correct
            if isinstance(value, dict):
                try:
                    value = link_cls.get_instance(**value)
                except ValidationError:
                    raise ValidationError(
                        "Passed wrond dict value {} for link_cls "
                        "'{}'".format(value, link_cls)
                    )
            elif not isinstance(value, link_cls) and value is not None:
                raise ValidationError(
                    "Wrong value instance '{}', should be '{}'".format(
                        value, link_cls.__name__
                    ))

        else:
            raise ValidationError(
                "Unexpected 'link_cls' value: {}".format(link_cls)
            )
        return value

    def __repr__(self):
        return unicode("<{}: {}>".format(self.__class__.__name__, self._name))

    def __unicode__(self):
        return unicode("<{}: {}>".format(self.__class__.__name__, self._name))