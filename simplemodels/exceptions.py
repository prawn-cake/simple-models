# -*- coding: utf-8 -*-
import six


__all__ = [
    'ValidationError',
    'ValidationRequiredError',
    'ValidationTypeIsNotSupported'
]


class ValidationError(Exception):
    """ Custom exception class. Useful for validation methods """

    def __unicode__(self):
        return six.u(self.message)


class ValidationRequiredError(ValidationError):
    """ Raised when required field is not found """

    pass


class ValidationTypeIsNotSupported(ValidationError):
    pass