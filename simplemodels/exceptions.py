# -*- coding: utf-8 -*-
import six


__all__ = [
    'ValidationError',
    'FieldRequiredError',
    'TypeIsNotSupported',
    'DefaultValueError',
    'ImmutableDocumentError',
    'ImmutableFieldError'
]


class ValidationError(Exception):
    """ Custom exception class. Useful for validation methods """

    def __unicode__(self):
        return six.u(self.message)


class FieldRequiredError(ValidationError):
    """ Raised when required field is not found """
    pass


class TypeIsNotSupported(ValidationError):
    pass


class DefaultValueError(ValidationError):
    """Raised when default value is wrong"""
    pass


class ImmutableDocumentError(ValidationError):
    """Raised when try to set any field in the immutable document"""
    pass


class ImmutableFieldError(ValidationError):
    """Raised when try to set certain immutable field in a document"""
    pass
