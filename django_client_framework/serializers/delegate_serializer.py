from __future__ import annotations

from logging import getLogger
from typing import Any, Dict, Optional, Tuple, Type

from django.utils.functional import cached_property

from django_client_framework.models.abstract.serializable import D

from .. import exceptions as e
from .serializer import DCFSerializer, T

LOG = getLogger(__name__)


class DelegateSerializer(DCFSerializer[T, D]):
    """
    Any subclass can provide read, create, update delegate serializers dynamically.
    """

    def __init__(
        self,
        instance: Optional[T] = None,
        data: Optional[D] = None,
        *,
        context: Dict[str, Any] = {},
        **kwargs: Any,
    ) -> None:
        self.is_read = self.is_create = self.is_update = False
        self.serializer_kwargs = kwargs
        self.instance = instance
        self.initial_data = data
        self.serializer_context = context

        if data is not None and instance is not None:
            self.is_update = True
        if data is not None and instance is None:
            self.is_create = True
        if data is None and instance is not None:
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

    def delete_obj(self):
        return self.delegate.delete_obj()

    def get_delegate(self, raise_exception: bool = False) -> DCFSerializer[T, D]:
        delegate = None

        if self.is_update:
            assert self.instance is not None
            if prevalcls := self.get_update_prevalidation_class():
                prevalins = prevalcls(
                    data=self.initial_data,
                    instance=self.instance,
                    context=self.serializer_context,
                    partial=True,
                    **self.serializer_kwargs,
                )
                prevalins.is_valid(raise_exception)
                prevalidated_data = prevalins.validated_data
            else:
                prevalidated_data = None

            delegatecls, is_partial = self.get_update_delegate_class(
                self.instance,
                initial_data=self.initial_data,
                prevalidated_data=prevalidated_data,
            )

            delegate = delegatecls(
                instance=self.instance,
                data=self.initial_data,
                context=self.serializer_context,
                partial=is_partial,
                **self.serializer_kwargs,
            )

        elif self.is_create:
            if prevalcls := self.get_create_prevalidation_class():
                prevalins = prevalcls(
                    data=self.initial_data,
                    instance=self.instance,
                    context=self.serializer_context,
                    partial=False,
                    **self.serializer_kwargs,
                )
                prevalins.is_valid(raise_exception)
                prevalidated_data = prevalins.validated_data
            else:
                prevalidated_data = None

            delegate_class = self.get_create_delegate_class(
                initial_data=self.initial_data,
                prevalidated_data=prevalidated_data,
            )
            delegate = delegate_class(
                instance=self.instance,
                data=self.initial_data,
                context=self.serializer_context,
                **self.serializer_kwargs,
            )

        elif self.is_read:
            delegate = self.read_delegate

        assert delegate is not None
        return delegate

    @cached_property
    def delegate(self) -> DCFSerializer[T, D]:
        if ret := self.get_delegate():
            return ret
        else:
            raise NotImplementedError("Unable to decide delegate")

    def __getattr__(self, name):
        # be careful, when you want to access fields in self.read_delegate you might
        # accidentally land here
        if name in self.__dict__:
            return self.__dict__[name]
        else:
            return getattr(self.delegate, name)

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
    ) -> Tuple[Type[DCFSerializer[T, D]], bool]:
        raise NotImplementedError(
            f"{self.__class__} must implement .get_update_delegate_class()"
        )

    def get_read_delegate_class(self) -> Type[DCFSerializer[T, D]]:
        raise NotImplementedError(
            f"{self.__class__} must implement .get_read_delegate_class()"
        )

    def get_create_prevalidation_class(self):
        return None

    def get_update_prevalidation_class(self):
        return None

    @cached_property
    def data(self):
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
