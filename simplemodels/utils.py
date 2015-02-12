# -*- coding: utf-8 -*-


class Choices(object):

    """ Useful class for choices. """

    def __init__(self, *choices):
        self._choices = []
        self._choice_dict = {}

        for choice in choices:
            if isinstance(choice, (list, tuple)):
                if len(choice) == 2:
                    choice = (choice[0], choice[1], choice[1])

                elif len(choice) != 3:
                    raise ValueError(
                        "Choices can't handle a list/tuple of length {0}, only\
                        2 or 3".format(choice))
            else:
                choice = (choice, choice, choice)

            self._choices.append((choice[0], choice[2]))
            self._choice_dict[choice[1]] = choice[0]

    def __getattr__(self, attname):  # pragma: no cover
        try:
            return self._choice_dict[attname]
        except KeyError:
            raise AttributeError(attname)

    def __iter__(self):  # pragma: no cover
        return iter(self._choices)

    def __getitem__(self, index):  # pragma: no cover
        return self._choices[index]

    def __delitem__(self, index):  # pragma: no cover
        del self._choices[index]

    def __setitem__(self, index, value):  # pragma: no cover
        self._choices[index] = value

    def __repr__(self):  # pragma: no cover
        return "{0}({1})".format(
            self.__class__.__name__,
            self._choices
        )

    def __len__(self):  # pragma: no cover
        return len(self._choices)


class BuiltinWrapper(object):

    """Class-wrapper for built-in models for use it with weakref """

    def __init__(self, value, name=None):
        self._value = value
        self._name = name or 'undefined'

    @property
    def value(self):
        return self._value