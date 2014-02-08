# -*- coding: utf-8 -*-


class SimpleFieldValidationError(Exception):

    """ Custom exception class. Useful for validation methods"""

    def __unicode__(self):
        return unicode(self.message)