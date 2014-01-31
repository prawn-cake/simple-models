# -*- coding: utf-8 -*-


class SimpleFieldValidationError(Exception):

    """ Custom exception class"""

    def __unicode__(self):
        return unicode(self.message)