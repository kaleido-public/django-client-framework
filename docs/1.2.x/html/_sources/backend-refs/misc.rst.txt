Context
================

    This is a dictionary containing:

    .. code:: py

        {
            "version": str,
            "locale": str,
            "request": Request,
            "view": APIView
        }


    ``version``, ``locale``
        Defaults to ``None``. If there's a path parameter named
        ``version`` or ``locale``, then they receives the value of that.

    ``request``
        The DRF ``Request`` object.

    ``view``
        The DRF ``View`` object.


