# -*- coding: utf-8 -*-
from simplemodels.exceptions import ValidationError
from simplemodels.models import DictEmbeddedDocument 


class AbstractValidator(object):

    """ Abstract validator """

    @classmethod
    def validate(cls, value):
        """Validate method

        :param value:
        :raise NotImplementedError:
        """
        raise NotImplementedError()


class TypeValidator(AbstractValidator):
    TYPE = None

    @classmethod
    def validate(cls, value):
        if cls.TYPE is None:  # for default NullValidator
            return value

        if isinstance(value, cls.TYPE):
            return value

        try:
            value = cls.TYPE(value)
        except ValueError as err:
            raise ValidationError(err)
        return value


class NullValidator(TypeValidator):

    """Default validator to validate nothing"""

    TYPE = None


class IntValidator(TypeValidator):
    TYPE = int


class StringValidator(TypeValidator):
    TYPE = str


class DictValidator(TypeValidator):
    TYPE = dict


class DictEmbeddedDocumentValidator(TypeValidator):
    TYPE = DictEmbeddedDocument

    @classmethod
    def validate(cls, value):
        """Validate DictEmbeddedDocument field.
        Passed value must be dict value

        :param value:
        :return: :raise ValidationError:
        """
        if isinstance(value, DictEmbeddedDocument):
            return value

        if not isinstance(value, dict):
            raise ValidationError('Passed non-dict value for {} field'
                                  ''.format(DictEmbeddedDocument.__name__))

        value = DictEmbeddedDocument.get_instance(**value)
        return value


VALIDATORS_MAP = {
    None: NullValidator,
    int: IntValidator,
    str: StringValidator,
    dict: DictValidator,
    DictEmbeddedDocument: DictEmbeddedDocumentValidator
}