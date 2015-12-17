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
import time
import logging
from boto.exception import BotoServerError
from boto.resultset import ResultSet
from boto.ec2.autoscale.limits import AccountLimits
from copy import deepcopy

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


def invoke_with_throttling_retries(function_ref, *argv, **kwargs):
    """
    Invoke a Boto operation using an exponential backoff in the case of
    API request throttling.

    This is taken from:
    https://github.com/47lining/ansible-modules-core/blob/2d189f0d192717f83e3c6d37d3fe0988fc329b5a/cloud/amazon/cloudformation.py#L192
    see:
    https://github.com/ansible/ansible-modules-core/pull/224
    and
    https://github.com/ansible/ansible-modules-core/pull/569

    To use, transform:

        ``conn.action(args)``

    into:

        ``invoke_with_throttling_retries(conn.action, args)``

    :param function_ref: the function to call
    :type function_ref: function
    :param argv: the parameters to pass to the function
    :type argv: tuple
    :param kwargs: keyword arguments to pass to the function. Any arguments
      with names starting with ``alc_`` will be removed for internal use.
    :type kwargs: dict
    """
    IGNORE_CODE = 'Throttling'
    MAX_RETRIES = 5
    SLEEP_BASE_SECONDS = 2

    # strip off "^alc_" args
    pass_kwargs = {}
    for k, v in kwargs.items():
        if not k.startswith('alc_'):
            pass_kwargs[k] = v

    retries = 0
    while True:
        try:
            retval = function_ref(*argv, **pass_kwargs)
            return retval
        except BotoServerError as e:
            if e.code != IGNORE_CODE:
                raise e
            if retries == MAX_RETRIES:
                logger.error("Reached maximum number of retries; raising error")
                raise e
        stime = SLEEP_BASE_SECONDS * (2**retries)
        logger.info("Call of %s got throttled; sleeping %s seconds before "
                    "retrying", function_ref, stime)
        time.sleep(stime)
        retries += 1


def paginate_query(function_ref, *argv, **kwargs):
    """
    Invoke a Boto operation, automatically paginating through all responses.
    First, pass the function, args and kwargs to
    :py:func:`~.invoke_with_throttling_retries`.

    If kwargs['alc_no_paginate'] is True, return the result immediately.

    If ``function_ref`` returns a :py:class:`boto.resultset.ResultSet` object
    and its ``next_token`` attribute is not None, pass it through to
    :py:func:`~._paginate_resultset` and return the result.

    Else if ``function_ref`` returns a dict, pass it through to
    :py:func:`~._paginate_dict` and return the result.

    Else, return the result.

    :param function_ref: the function to call
    :type function_ref: function
    :param argv: the parameters to pass to the function
    :type argv: tuple
    :param kwargs: keyword arguments to pass to the function
      (:py:func:`~.invoke_with_throttling_retries`)
    :type kwargs: dict
    """
    paginate_dict_params = [
        'alc_marker_path', 'alc_data_path', 'alc_marker_param'
    ]
    result = invoke_with_throttling_retries(function_ref, *argv, **kwargs)
    if 'alc_no_paginate' in kwargs and kwargs['alc_no_paginate'] is True:
        logger.debug("explicitly not paginating query")
        return result
    if isinstance(result, ResultSet) and result.next_token is None:
        return result
    elif isinstance(result, ResultSet) and result.next_token is not None:
        return _paginate_resultset(result, function_ref, *argv, **kwargs)
    elif isinstance(result, AccountLimits):
        # cannot be paginated
        return result
    elif isinstance(result, dict):
        if set(paginate_dict_params).issubset(kwargs):
            return _paginate_dict(result, function_ref, *argv, **kwargs)
        else:
            logger.warning("Query returned a dict, but does not have "
                           "_paginate_dict params set; cannot paginate (" +
                           str(function_ref) + ")")
            return result
    logger.warning("Query result of type %s cannot be paginated", type(result))
    return result


def _paginate_dict(result, function_ref, *argv, **kwargs):
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

    All function calls are passed through
    :py:func:`~.invoke_with_throttling_retries`.

    :param result: the first result from the query
    :type result: dict
    :param function_ref: the function to call
    :type function_ref: function
    :param argv: the parameters to pass to the function
    :type argv: tuple
    :param kwargs: keyword arguments to pass to the function
      (:py:func:`~.invoke_with_throttling_retries`)
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
        func_kwargs = deepcopy(kwargs)
        func_kwargs[marker_param] = marker
        result = invoke_with_throttling_retries(
            function_ref, *argv, **func_kwargs)
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


def _paginate_resultset(result, function_ref, *argv, **kwargs):
    """
    Paginate through a query that returns a :py:class:`boto.resultset.ResultSet`
    object, and return the combined result.

    All function calls are passed through
    :py:func:`~.invoke_with_throttling_retries`.

    :param result: the first ResultSet from the query
    :type result: :py:class:`boto.resultset.ResultSet`
    :param function_ref: the function to call
    :type function_ref: function
    :param argv: the parameters to pass to the function
    :type argv: tuple
    :param kwargs: keyword arguments to pass to the function
      (:py:func:`~.invoke_with_throttling_retries`)
    :type kwargs: dict
    """
    logger.debug("Iterating all ResultSets for query of %s", function_ref)
    # we don't want any markers in the final result
    final_result = ResultSet()
    final_result.extend(result)
    while hasattr(result, 'next_token') and result.next_token is not None:
        logger.debug("Getting next response set; next_token=%s",
                     result.next_token)
        next_kwargs = deepcopy(kwargs)
        next_kwargs['next_token'] = result.next_token
        result = invoke_with_throttling_retries(
            function_ref, *argv, **next_kwargs)
        final_result.extend(result)
    return final_result


def boto_query_wrapper(function_ref, *argv, **kwargs):
    """
    Function to wrap all boto query method calls, for throttling and pagination.

    Calls :py:func:`~.paginate_query` and returns the result.

    :param function_ref: the function to call
    :type function_ref: function
    :param argv: the parameters to pass to the function
    :type argv: tuple
    :param kwargs: keyword arguments to pass to the function
      (:py:func:`~.paginate_query`)
    :type kwargs: dict
    :returns: return value of ``function_ref``
    """
    # wrap throttling in pagination
    result = paginate_query(function_ref, *argv, **kwargs)
    return result
