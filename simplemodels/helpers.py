# -*- coding: utf-8 -*-


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
