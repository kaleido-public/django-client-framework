from .access_controlled import AccessControlled
from .model import DCFModel, DjangoModel
from .rate_limited import RateLimited
from .searchable import Searchable
from .serializable import Serializable
from .user import DCFAbstractUser, get_dcf_user_model, get_user_model


def check_integrity() -> None:
    from . import access_controlled, serializable, user

    access_controlled.check_integrity()
    serializable.check_integrity()
    user.check_integrity()
