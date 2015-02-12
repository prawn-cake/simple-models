# -*- coding: utf-8 -*-
from datetime import datetime
from simplemodels.exceptions import ValidationError, ValidationTypeIsNotSupported
from simplemodels.models import DictEmbeddedDocument
import abc


class AbstractValidator(object):

    """ Abstract validator """

    __metaclass__ = abc.ABCMeta

    @classmethod
    @abc.abstractmethod
    def validate(cls, value, **kwargs):
        """Validate method

        :param value:
        :raise NotImplementedError:
        """
        raise NotImplementedError()


class TypeValidator(AbstractValidator):
    TYPE = None

    @classmethod
    def using(cls, value):
        """Method enable to override TYPE attribute.

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
    def validate(cls, value, **kwargs):
        if cls.TYPE is None:
            # Do not apply validation for None value
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
    def validate(cls, value, **kwargs):
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


# FIXME: DEPRECATED --> use validator callable function instead
class DatetimeValidator(TypeValidator):
    DT_TEMPLATES = {
        'json': '%Y-%m-%dT%H:%M:%SZ',
        'iso8601': '%Y-%m-%dT%H:%M:%S',
        'iso_date': '%Y-%m-%d',
        'iso_time': '%H:%M:%S'
    }

    @classmethod
    def validate(cls, value, **kwargs):
        """Validate datetime
        Default format is json aware datetime format (iso8601).
        For example: 2009-04-01T23:51:23Z

        :param value: datetime string
        :param kwargs:
        :return: :raise ValidationError:
        """
        _format = kwargs.get('format') or '%Y-%m-%dT%H:%M:%SZ'
        dt_template = kwargs.get('dt_template')
        if dt_template:
            _format = cls._get_template_format(dt_template)
        try:
            value = datetime.strptime(value, _format)
        except ValueError as err:
            raise ValidationError(err)
        return value

    @classmethod
    def _get_template_format(cls, template_name):
        return cls.DT_TEMPLATES.get(template_name, cls.DT_TEMPLATES['json'])


# TODO: add datetime validator
VALIDATORS_MAP = {
    None: NullValidator,
    int: IntValidator,
    str: StringValidator,
    dict: DictValidator,
    'int': IntValidator,
    'str': StringValidator,
    'dict': DictValidator,
    'datetime': DatetimeValidator,
    DictEmbeddedDocument: DictEmbeddedDocumentValidator
}


def get_validator(type_cls):
    if type_cls in VALIDATORS_MAP:
        return VALIDATORS_MAP[type_cls]

    # determine parent class
    if type_cls.__bases__[-1] == DictEmbeddedDocument:
        # Execute .using() to cast object class explicitly
        return VALIDATORS_MAP[DictEmbeddedDocument].using(type_cls)

    raise ValidationTypeIsNotSupported(
        "Validation type '{}' is not supported".format(type_cls))