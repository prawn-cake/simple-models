# -*- coding: utf-8 -*-
from simplemodels.exceptions import ValidationError, ValidationTypeIsNotSupported
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
    def using(cls, value):
        """Override TYPE value.
        Usage:
            Validator.using(MyKlass).validate(value)

        :param value:
        :return:
        """
        setattr(cls, '__BACKUP_TYPE', cls.TYPE)
        setattr(cls, 'TYPE', value)
        return cls

    @classmethod
    def _clean_validate(cls):
        backup_type = getattr(cls, '__BACKUP_TYPE', None)
        if backup_type:
            setattr(cls, 'TYPE', backup_type)
        setattr(cls, '__BACKUP_TYPE', None)

    @classmethod
    def validate(cls, value):
        if cls.TYPE is None:  # for default NullValidator
            pass
        elif isinstance(value, cls.TYPE):
            pass
        else:
            try:
                value = cls.TYPE(value)
            except ValueError as err:
                raise ValidationError(err)
            finally:
                cls._clean_validate()
        cls._clean_validate()
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

        if not issubclass(cls.TYPE, DictEmbeddedDocument):
            raise ValidationError(
                'Class {} is not a subclass of {}'.format(
                    cls.TYPE.__name__, DictEmbeddedDocument.__name__))
        value = cls.TYPE.get_instance(**value)

        return value


VALIDATORS_MAP = {
    None: NullValidator,
    int: IntValidator,
    str: StringValidator,
    dict: DictValidator,
    DictEmbeddedDocument: DictEmbeddedDocumentValidator
}


def get_validator(_type):
    if _type in VALIDATORS_MAP:
        return VALIDATORS_MAP[_type]

    # determine parent class
    if _type.__bases__[-1] == DictEmbeddedDocument:
        # Execute .using() to cast object class explicitly
        return VALIDATORS_MAP[DictEmbeddedDocument].using(_type)

    raise ValidationTypeIsNotSupported(
        "Validation type '{}' is not supported".format(_type)
    )