# -*- coding: utf-8 -*-
""" Fields for DictEmbedded model """

from core.exceptions import SimpleFieldValidationError


class SimpleField(object):

    """Class-field with descriptor for DictEmbeddedDocument"""

    def __init__(self, default=None, required=False, choices=None,
                 link_cls=None, **kwargs):
        # TODO: problem here - can't to user weakref dict -- possible memory leaks
        self.data = {}  # instance values storage

        # set by SimpleEmbeddedMeta
        self._name = None
        self.default = default
        self.required = required

        # TODO: support choices validation
        self.choices = choices

        # TODO: support list of link_cls
        self.link_cls = link_cls

    def __get__(self, instance, owner):
        return self.data.get(id(instance), self.default)

    def __set__(self, instance, value):
        self.validate_link_cls(self.link_cls, value)
        self.data[id(instance)] = value

    def __delete__(self, instance):
        del self.data[id(instance)]

    @classmethod
    def validate_link_cls(cls, link_cls, value):
        from core.models import DictEmbeddedDocument

        if link_cls:
            if isinstance(link_cls, list):
                # link_cls can equals to '[Bids]' for example
                # that means list for Bids classes
                if not isinstance(value, list) and value is not None:
                    raise SimpleFieldValidationError(
                        "Wrong list value instance, should be list of "
                        "'{}'".format(link_cls.__name__)
                    )
                elif value is None:
                    pass
                else:
                    for v in value:
                        cls.validate_link_cls(link_cls[0], v)
            elif issubclass(link_cls, DictEmbeddedDocument):
                if not isinstance(value, link_cls) and value is not None:
                    raise SimpleFieldValidationError(
                        "Wrong value instance, should be '{}'".format(
                            link_cls.__name__
                        ))
            else:
                raise SimpleFieldValidationError(
                    "Unexpected 'link_cls' value: {}".format(link_cls)
                )

    def validate(self):
        # check required
        field_val = self.data.get(id(self))
        if self.required and not field_val:
            raise SimpleFieldValidationError(
                "Field '{}' is required".format(self._name)
            )

        # check cls
        if self.link_cls and not isinstance(field_val, self.link_cls):
            raise SimpleFieldValidationError(
                "Field '{}' value not equal to '{}' instance".format(
                    self._name, self.link_cls.__name__)
            )

        return True
