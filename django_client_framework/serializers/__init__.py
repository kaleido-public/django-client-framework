from rest_framework.fields import *
from rest_framework.serializers import *

from .delegate_serializer import DelegateSerializer
from .fields import *
from .model_serializer import DCFModelSerializer, generate_jsonschema
from .serializer import (
    DCFSerializer,
    DCFSerializerMeta,
    SerializerContext,
    DCFSerializerScope,
)


def check_integrity() -> None:
    from . import model_serializer

    model_serializer.check_integrity()
    for base in [DCFSerializer, DCFModelSerializer]:
        for serializer_cls in base.__subclasses__():
            if meta_cls := getattr(serializer_cls, "Meta"):
                if not issubclass(meta_cls, DCFSerializerMeta):
                    raise NotImplementedError(
                        f"Make sure {meta_cls} inherits DCFSerializerMeta."
                    )
            else:
                raise NotImplementedError(
                    f"Make sure {serializer_cls}.Meta is defined and inherits DCFSerializerMeta."
                )
