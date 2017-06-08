# -*- coding: utf-8 -*-

__all__ = [
    'ValidationError',
    'FieldRequiredError',
    'TypeIsNotSupported',
    'DefaultValueError',
    'DocumentError'
    'ImmutableFieldError',
    'ModelValidationError'
]


class ValidationError(Exception):
    """ Custom exception class. Useful for validation methods """

    def __str__(self):
        if hasattr(self, 'message'):
            return self.message
        return super(ValidationError, self).__str__()


class ModelNotFoundError(ValidationError):
    """Raises when DocumentField has wrong model assignment"""
    pass


class ModelValidationError(ValidationError):
    """User-defined exception. Raised when model validation is failed"""
    pass


class FieldError(ValidationError):
    """Field specific exception"""
    pass


class FieldRequiredError(FieldError):
    """ Raised when required field is not found """
    pass


class DocumentError(ValidationError):
    """Document-specific error"""
    pass


class ImmutableFieldError(FieldError):
    """Raised when try to set certain immutable field in a document"""
    pass
