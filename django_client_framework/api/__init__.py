from typing import Type, TypeVar

from django_client_framework.models.abstract.serializable import (
    ISerializable,
    Serializable,
)

from .base_model_api import BaseModelAPI
from .model_collection_api import ModelCollectionAPI
from .model_object_api import ModelObjectAPI
from .related_model_api import RelatedModelAPI

T = TypeVar("T", bound="Type[ISerializable]")


def register_api_model(model_class: T) -> T:
    BaseModelAPI.models.append(model_class)
    return model_class


def check_integrity() -> None:
    for model in BaseModelAPI.models:
        if not issubclass(model, Serializable):
            raise TypeError(f"model {model} must inherit Serializable")
