"""
awslimitchecker/utils.py

The latest version of this package is available at:
<https://github.com/jantman/awslimitchecker>

##############################################################################
Copyright 2015-2018 Jason Antman <jason@jasonantman.com>

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
import logging
from copy import deepcopy
import botocore.vendored.requests as requests
from awslimitchecker.version import _VERSION_TUP, _VERSION

logger = logging.getLogger(__name__)


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
    :type separator: str
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


def paginate_dict(function_ref, *argv, **kwargs):
    """
    Paginate through a query that returns a dict result, and return the
    combined result.

    Note that this function requires some special kwargs to be passed in:

    * __alc_marker_path__ - The dictionary path to the Marker for the next
      result set. If this path does not exist, the raw result will be returned.
    * __alc_data_path__ - The dictionary path to the list containing the query
      results. This will be updated with the results of subsequent queries.
    * __alc_marker_param__ - The parameter name to pass to ``function_ref``
      with the marker value.

    These paths should be lists, in a form usable by
    :py:func:`~._get_dict_value_by_path`.

    :param function_ref: the function to call
    :type function_ref: ``function``
    :param argv: the parameters to pass to the function
    :type argv: tuple
    :param kwargs: keyword arguments to pass to the function
    :type kwargs: dict
    """
    if 'alc_marker_path' not in kwargs:
        raise Exception("alc_marker_path must be specified for queries "
                        "that return a dict.")
    if 'alc_data_path' not in kwargs:
        raise Exception("alc_data_path must be specified for queries "
                        "that return a dict.")
    if 'alc_marker_param' not in kwargs:
        raise Exception("alc_marker_param must be specified for queries "
                        "that return a dict.")

    marker_path = kwargs['alc_marker_path']
    data_path = kwargs['alc_data_path']
    marker_param = kwargs['alc_marker_param']

    # strip off "^alc_" args
    pass_kwargs = {}
    for k, v in kwargs.items():
        if not k.startswith('alc_'):
            pass_kwargs[k] = v

    # first function call
    result = function_ref(*argv, **pass_kwargs)

    # check for marker, return if not present
    marker = _get_dict_value_by_path(result, marker_path)
    if marker is None:
        return result
    logger.debug("Found marker (%s) in result; iterating for more results",
                 marker_path)
    # iterate results
    results = []
    results.extend(_get_dict_value_by_path(result, data_path))
    while marker is not None:
        logger.debug("Querying %s with %s=%s", function_ref, marker_param,
                     marker)
        pass_kwargs[marker_param] = marker
        result = function_ref(*argv, **pass_kwargs)
        data = _get_dict_value_by_path(result, data_path)
        results.extend(data)
        marker = _get_dict_value_by_path(result, marker_path)
    # drop the full results into the last result response
    res = _set_dict_value_by_path(result, results, data_path)
    return res


def _get_dict_value_by_path(d, path):
    """
    Given a dict (``d``) and a list specifying the hierarchical path to a key
    in that dict (``path``), return the value at that path or None if it does
    not exist.

    :param d: the dict to search in
    :type d: dict
    :param path: the path to the key in the dict
    :type path: list
    """
    tmp_path = deepcopy(path)
    try:
        while len(tmp_path) > 0:
            k = tmp_path.pop(0)
            d = d[k]
        return d
    except:
        return None


def _set_dict_value_by_path(d, val, path):
    """
    Given a dict (``d``), a value (``val``),  and a list specifying the
    hierarchical path to a key in that dict (``path``), set the value in ``d``
    at ``path`` to ``val``.

    :param d: the dict to search in
    :type d: dict
    :param path: the path to the key in the dict
    :type path: list
    :raises: TypeError if the path is too short
    :returns: the modified dict
    """
    tmp_path = deepcopy(path)
    tmp_d = deepcopy(d)
    result = tmp_d
    while len(tmp_path) > 0:
        if len(tmp_path) == 1:
            result[tmp_path[0]] = val
            break
        k = tmp_path.pop(0)
        result = result[k]
    return tmp_d


def _get_latest_version():
    """
    Attempt to retrieve the latest awslimitchecker version from PyPI, timing
    out after 4 seconds. If the version can be retrieved and is greater than
    the currently running version, return it as a string. If the version cannot
    be retrieved or is not greater than the currently running version, return
    None.

    This function MUST not ever raise an exception.

    :return: latest version from PyPI, if newer than current version
    :rtype: `str` or `None`
    """
    try:
        r = requests.get(
            'https://pypi.org/pypi/awslimitchecker/json',
            timeout=4.0, headers={
                'User-Agent': 'github.com/jantman/awslimitchecker '
                              '%s' % _VERSION
            }
        )
        j = r.json()
        latest = tuple([
            int(i) for i in j['info']['version'].split('.')[0:3]
        ])
        if latest > _VERSION_TUP:
            return j['info']['version']
    except Exception:
        logger.debug('Error getting latest version from PyPI', exc_info=True)
    return None
