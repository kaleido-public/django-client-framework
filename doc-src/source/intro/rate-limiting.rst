API Rate Limiting
=======================

Each `Model` is a resource, and each `create`, `read`, `update`, `delete` is an
`action`. The API rate limit is set on a per-resource, per-action, and per-ip
address basis.

If not specified, the default limit is 60 requests per minute for all resource
actions from any IP. If the limit is exceeded, the response is ``429 Too Many
Requets``.

.. code-block:: py

    class Product(DCFModel, RateLimited):

        class RateLimitManager:
            def get_rate_limit(self, instance, action, user, version, context) -> str:
                # user is the current user identified by the API token, or None
                if user:
                    # assuming there's a staff group
                    is_staff = user.groups.filter(id=default_groups.staffs.id).exists()
                    if is_staff:
                        return "120/min"
                return "60/min"

        def get_ratelimitmanager(self):
            return RateLimitManager()

To set the default limit:

.. code-block:: py

    from django_client_framework.api import rate_limit
    rate_limit.default = "120/min"
