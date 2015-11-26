# -*- coding: utf-8 -*-
"""Validator helpers"""
from simplemodels.exceptions import ValidationError


def is_instance(class_or_type_or_tuple):
    """Is instance validation wrapper

    :param class_or_type_or_tuple: __builtin__.isinstance second parameter
    :return: :raise ValidationError:

    Example:
        class Message(Document):
            ts = SimpleField(default=datetime.now,
                             validators=[is_instance(datetime)])
    """

    def wrapper(value):
        if not isinstance(value, class_or_type_or_tuple):
            raise ValidationError('Wrong type {}, must be {}'.format(
                type(value), class_or_type_or_tuple))
        return value
    return wrapper


def is_document(value):
    """Check if value is a simplemodels.models.Document instance

    :param value: some value
    :return: bool
    """
    from simplemodels.models import Document

    try:
        # Handle an error with issubclass(lambda function)
        return issubclass(value, Document)
    except TypeError:
        return False
