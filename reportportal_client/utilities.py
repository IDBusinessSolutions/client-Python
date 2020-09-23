import six
from time import time
import datetime

from .errors import ResponseError, EntryCreatedError, OperationCompletionError


def _convert_string(value):
    """Support and convert strings in py2 and py3.

    :param value: input string
    :return value: convert string
    """
    if isinstance(value, six.text_type):
        # Don't try to encode 'unicode' in Python 2.
        return value
    return str(value)


def _dict_to_payload(dictionary):
    """Convert dict to list of dicts.

    :param dictionary: initial dict
    :return list: list of dicts
    """
    system = dictionary.pop("system", False)
    return [
        {"key": key, "value": _convert_string(value), "system": system}
        for key, value in sorted(dictionary.items())
    ]


def _get_id(response):
    """Get id from Response.

    :param response: Response object
    :return id: int value of id
    """
    try:
        return _get_data(response)["id"]
    except KeyError:
        raise EntryCreatedError(
            "No 'id' in response: {0}".format(response.text))


def _get_msg(response):
    """
    Get message from Response.

    :param response: Response object
    :return: data: json data
    """
    return _get_data(response)



def _get_data(response):
    """
    Get data from Response.

    :param response: Response object
    :return: json data
    """
    data = _get_json(response)
    error_messages = _get_messages(data)
    error_count = len(error_messages)

    if error_count == 1:
        raise ResponseError(error_messages[0])
    elif error_count > 1:
        raise ResponseError(
            "\n  - ".join(["Multiple errors:"] + error_messages))
    elif not response.ok:
        response.raise_for_status()
    elif not data:
        raise ResponseError("Empty response")
    else:
        return data


def _get_json(response):
    """
    Get json from Response.

    :param response: Response object
    :return: data: json object
    """
    try:
        if response.text:
            return response.json()
        else:
            return {}
    except ValueError as value_error:
        raise ResponseError(
            "Invalid response: {0}: {1}".format(value_error, response.text))


def _get_messages(data):
    """
    Get messages (ErrorCode) from Response.

    :param data: dict of datas
    :return list: Empty list or list of errors
    """
    error_messages = []
    for ret in data.get("responses", [data]):
        if "errorCode" in ret:
            error_messages.append(
                "{0}: {1}".format(ret["errorCode"], ret.get("message"))
            )

    return error_messages


def uri_join(*uri_parts):
    """Join uri parts.

    Avoiding usage of urlparse.urljoin and os.path.join
    as it does not clearly join parts.

    Args:
        *uri_parts: tuple of values for join, can contain back and forward
                    slashes (will be stripped up).

    Returns:
        An uri string.

    """
    return '/'.join(str(s).strip('/').strip('\\') for s in uri_parts)


def to_isoformat(date_time):
    if isinstance(date_time, str):
        date_time = datetime.datetime.strptime(date_time, '%Y-%m-%dT%H:%M:%S.%f')

    if isinstance(date_time, datetime.datetime):
        time_isoformat = date_time.isoformat()
    else:
        raise Exception("Time is not in datetime format")

    return time_isoformat