"""
awslimitchecker/utils.py

The latest version of this package is available at:
<https://github.com/jantman/awslimitchecker>

##############################################################################
Copyright 2015 Jason Antman <jason@jasonantman.com> <http://www.jasonantman.com>

    This file is part of awslimitchecker, also known as awslimitchecker.

    awslimitchecker is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    awslimitchecker is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with awslimitchecker.  If not, see <http://www.gnu.org/licenses/>.

The Copyright and Authors attributions contained herein may not be removed or
otherwise altered, except to add the Author attribution of a contributor to
this work. (Additional Terms pursuant to Section 7b of the AGPL v3)
##############################################################################
While not legally required, I sincerely request that anyone who finds
bugs please submit them at <https://github.com/jantman/awslimitchecker> or
to me via email, and that you send any contributions or improvements
either as a pull request on GitHub, or to me via email.
##############################################################################

AUTHORS:
Jason Antman <jason@jasonantman.com> <http://www.jasonantman.com>
##############################################################################
"""

import argparse


class StoreKeyValuePair(argparse.Action):
    """
    Store key=value options in a dict as {'key': 'value'}.

    Supports specifying the option multiple times, but NOT with ``nargs``.

    See :py:class:`~argparse.Action`.
    """

    def __init__(self, option_strings, dest, nargs=None, const=None,
                 default=None, type=None, choices=None, required=False,
                 help=None, metavar=None):
        super(StoreKeyValuePair, self).__init__(option_strings, dest, nargs,
                                                const, default, type, choices,
                                                required, help, metavar)
        self.default = {}

    def __call__(self, parser, namespace, values, option_string=None):
        if '=' not in values:
            raise argparse.ArgumentError(self, 'must be in the form key=value')
        n, v = values.split('=')
        # handle quotes for values with spaces
        n = n.strip('"\'')
        getattr(namespace, self.dest)[n] = v


def dict2cols(d, spaces=2, separator=' '):
    """
    Take a dict of string keys and string values, and return a string with
    them formatted as two columns separated by at least ``spaces`` number of
    ``separator`` characters.

    :param d: dict of string keys, string values
    :type d: dict
    :param spaces: number of spaces to separate columns by
    :type spaces: int
    :param separator: character to fill in between columns
    :type separator: string
    """
    if len(d) == 0:
        return ''
    s = ''
    maxlen = max([len(k) for k in d.keys()])
    fmt_str = '{k:' + separator + '<' + str(maxlen + spaces) + '}{v}\n'
    for k in sorted(d.keys()):
        s += fmt_str.format(
            k=k,
            v=d[k],
        )
    return s
