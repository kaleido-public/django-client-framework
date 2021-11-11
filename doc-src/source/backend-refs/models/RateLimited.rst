.. _RateLimited:

`class` RateLimited `extends AbstractDCFModel`
==========================================================

    .. code:: py

        from django_client_framework.models import RateLimited

    This base model class provides customization to the api rate limit.

`class` RateManager
---------------------------------

    A nested class in `RateLimited`_.

`method` get_rate `(self, queryset, user, action, version, context) -> str`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Parameters
        ``queryset``
            The current resource being accessed.

        ``user``
            The current authenticated user. Same as ``context["request"].user``.

        ``action``
            One of ``read``, ``write``, ``create``, ``delete``

        ``version``
            The ``<version:str>`` url path parameter of the current route, or ``"default"``.

        ``context``
            See `Context`_.

    Returns
        A string in the format of `number/period`, where the `number` is how
        many times the request is allowed, and the `period` is one of ``day``,
        ``min``, ``sec``.
        Examples: ``"3600/day"``, ``"60/min"``, ``"1/sec"``

`method` get_record_key `(self, queryset, user, ipid, action, version, context) -> str`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Parameters
        ``ipid``
            A string that uniquely identifies the IP address of the current
            user. This is not necessarily the IP address.

    Returns
        A key used to identify the same request. Each time a request is
        processed, a timestamp is recorded with the key. When the next request
        of the same key comes in, the timestamp is checked against the allowed
        frequency.

        By default, returns ``hash([queryset.model, user, ip, action])``.

