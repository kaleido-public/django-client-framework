from __future__ import annotations

from logging import getLogger
from typing import *

from django.utils.functional import cached_property

from django_client_framework.exceptions import ValidationError
from django_client_framework.models.abstract.serializable import D

from .. import exceptions as e
from .serializer import DCFSerializer, SerializerContext, T

LOG = getLogger(__name__)


class DelegateSerializer(DCFSerializer[T, D]):
    """
    Any subclass can provide read, create, update delegate serializers dynamically.
    """

    def __init__(
        self,
        instance: Optional[T] = None,
        data: Optional[D] = None,
        context: Optional[SerializerContext] = None,
        **kwargs: Any,
    ) -> None:
        self.is_read = self.is_create = self.is_update = False
        self.serializer_kwargs = kwargs
        self.instance = instance
        self.initial_data = data
        self.serializer_context = context

        if data is not None and instance is not None:
            self.is_update = True
        elif data is not None and instance is None:
            self.is_create = True
        elif data is None:
            self.is_read = True

        self.read_delegate = self.get_read_delegate_class()(
            instance=instance,
            context=context,
            **self.serializer_kwargs,
        )

    def update(self, instance: T, validated_data: Any) -> T:
        return self.delegate.update(instance, validated_data)

    def create(self, validated_data: T) -> T:
        return self.delegate.create(validated_data)

    def save(self, **kwargs: Any) -> T:
        return self.delegate.save(**kwargs)

    def delete(self, instance: T) -> None:
        return self.delegate.delete(instance)

    def create_obj(self) -> T:
        return self.delegate.create_obj()

    def update_obj(self) -> T:
        return self.delegate.update_obj()

    def delete_obj(self) -> None:
        return self.delegate.delete_obj()

    def get_save_prevalidation_serializer(
        self, initial_data: Any
    ) -> DCFSerializer | None:
        if self.is_update:
            assert self.instance is not None
            return self.get_update_prevalidation_serializer(
                instance=self.instance, initial_data=initial_data
            )
        elif self.is_create:
            return self.get_create_prevalidation_serializer(initial_data=initial_data)
        else:
            return None

    def get_update_prevalidation_serializer(
        self, instance: T, initial_data: Any
    ) -> DCFSerializer | None:
        sercls = self.get_save_prevalidation_class()
        if sercls is None:
            return None
        return sercls(data=initial_data, instance=instance)

    def get_create_prevalidation_serializer(
        self, initial_data: Any
    ) -> DCFSerializer | None:
        sercls = self.get_save_prevalidation_class()
        if sercls is None:
            return None
        return sercls(data=initial_data)

    def get_save_prevalidation_class(self) -> Type[DCFSerializer] | None:
        if self.is_update:
            assert self.instance is not None
            return self.get_update_prevalidation_class(instance=self.instance)
        elif self.is_create:
            return self.get_create_prevalidation_class()
        else:
            return None

    def get_update_prevalidation_class(self, instance: T) -> Type[DCFSerializer] | None:
        return None

    def get_create_prevalidation_class(self) -> Type[DCFSerializer] | None:
        return None

    def get_save_delegate_serializer(
        self, initial_data: Any, prevalidated_data: Any
    ) -> DCFSerializer:
        if self.is_update:
            assert self.instance is not None
            return self.get_update_delegate_serializer(
                instance=self.instance,
                initial_data=initial_data,
                prevalidated_data=prevalidated_data,
            )
        elif self.is_create:
            return self.get_create_delegate_serializer(
                initial_data=initial_data, prevalidated_data=prevalidated_data
            )
        else:
            raise NotImplementedError()

    def get_create_delegate_serializer(
        self,
        initial_data: Dict[str, Any],
        prevalidated_data: Optional[Dict[str, Any]],
    ) -> DCFSerializer[T, D]:
        return self.get_create_delegate_class(
            initial_data=initial_data, prevalidated_data=prevalidated_data
        )(
            **{  # type:ignore
                "instance": self.instance,
                "data": self.initial_data,
                "context": self.serializer_context,
                **self.serializer_kwargs,
            }
        )

    def get_update_delegate_serializer(
        self,
        instance: T,
        initial_data: Dict[str, Any],
        prevalidated_data: Optional[Dict[str, Any]],
    ) -> DCFSerializer[T, D]:
        cls = self.get_update_delegate_class(
            instance=instance,
            initial_data=initial_data,
            prevalidated_data=prevalidated_data,
        )
        return cls(
            **{  # type:ignore
                "instance": self.instance,
                "data": self.initial_data,
                "context": self.serializer_context,
                "partial": cls.Meta.partial_update,
                **self.serializer_kwargs,
            }
        )

    def get_save_delegate_class(self, prevalidated_data: Any) -> Type[DCFSerializer]:
        if self.is_update:
            assert self.instance is not None
            return self.get_update_delegate_class(
                instance=self.instance,
                initial_data=self.initial_data,
                prevalidated_data=prevalidated_data,
            )
        elif self.is_create:
            return self.get_create_delegate_class(
                initial_data=self.initial_data, prevalidated_data=prevalidated_data
            )
        else:
            raise NotImplementedError()

    def get_create_delegate_class(
        self,
        initial_data: Dict[str, Any],
        prevalidated_data: Optional[Dict[str, Any]],
    ) -> Type[DCFSerializer[T, D]]:
        raise NotImplementedError(
            f"{self.__class__} must implement .get_create_delegate_class()"
        )

    def get_update_delegate_class(
        self,
        instance: T,
        initial_data: Dict[str, Any],
        prevalidated_data: Optional[Dict[str, Any]],
    ) -> Type[DCFSerializer[T, D]]:
        raise NotImplementedError(
            f"{self.__class__} must implement .get_update_delegate_class()"
        )

    def get_delegate(self, raise_exception: bool = False) -> DCFSerializer[T, D]:
        delegate = None
        if prevalins := self.get_save_prevalidation_serializer(
            initial_data=self.initial_data
        ):
            prevalins.is_valid(raise_exception=True)
            prevalidated_data = prevalins.validated_data
        else:
            prevalidated_data = None
        if self.is_read:
            delegate = self.read_delegate
        else:
            delegate = self.get_save_delegate_serializer(
                initial_data=self.initial_data, prevalidated_data=prevalidated_data
            )
        assert delegate is not None
        return delegate

    @cached_property
    def delegate(self) -> DCFSerializer[T, D]:
        try:
            if ret := self.get_delegate():
                return ret
        except ValidationError as e:
            raise e
        except Exception as e:
            raise ValueError(
                f"An exception occurred when trying to determine the delegate: {e}\n"
                f"Current class: {self.__class__}.\n"
            )
        else:
            raise NotImplementedError("Unable to decide delegate")

    def __getattr__(self, name: str) -> Any:
        # be careful, when you want to access fields in self.read_delegate you might
        # accidentally land here
        if name in self.__dict__:
            return self.__dict__[name]
        else:
            return getattr(self.delegate, name)

    def get_read_delegate_class(self) -> Type[DCFSerializer[T, D]]:
        raise NotImplementedError(
            f"{self.__class__} must implement .get_read_delegate_class()"
        )

    @cached_property
    def data(self) -> D:  # type: ignore
        return self.read_delegate.data

    def to_representation(self, instance: T) -> D:
        return self.read_delegate.to_representation(instance)

    def is_valid(self, raise_exception: bool = False) -> bool:
        """
        Need to overwrite this method to handle our custom ValidationError class
        """
        try:
            # may throw from get_*_prevalidation_class()
            return self.delegate.is_valid(raise_exception)
        except e.ValidationError:
            if raise_exception:
                raise
            else:
                return False
