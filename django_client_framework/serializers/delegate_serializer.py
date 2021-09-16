from __future__ import annotations

from logging import getLogger
from typing import Any, Generic, Tuple, Type, TypeVar, overload

from django.db.models.base import Model
from django.utils.functional import cached_property

from django_client_framework import exceptions as e

from .serializer import Serializer

LOG = getLogger(__name__)

T = TypeVar("T", bound=Model)


class DelegateSerializer(Generic[T], Serializer[T]):
    """
    Any subclass can provide read, create, update delegate serializers dynamically.
    """

    @overload
    def __init__(self, *, instance: T, data: Any):
        ...

    @overload
    def __init__(self, *, instance: T):
        ...

    @overload
    def __init__(self, *, data: Any):
        ...

    def __init__(self, *, instance: T = None, data: Any = None, **kwargs):
        self.__delegate = None
        self.is_read = self.is_create = self.is_update = False
        self.kwargs = kwargs
        self.instance = instance
        self.initial_data = data
        if data is not None and instance is not None:
            self.is_update = True
        if data is not None and instance is None:
            self.is_create = True
        if data is None and instance is not None:
            self.is_read = True

        self.read_delegate = self.get_read_delegate_class(instance)(instance=instance)

    def get_delegate(self, raise_exception: bool = False) -> Serializer[T]:
        delegate = None

        if self.is_update:
            if prevalcls := self.get_update_prevalidation_class():
                prevalins = prevalcls(
                    data=self.initial_data, instance=self.instance, partial=True
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

            self.kwargs.update(dict(partial=is_partial))
            delegate = delegatecls(
                instance=self.instance, data=self.initial_data, **self.kwargs
            )

        elif self.is_create:
            if prevalcls := self.get_create_prevalidation_class():
                prevalins = prevalcls(
                    data=self.initial_data, instance=self.instance, partial=False
                )
                prevalins.is_valid(raise_exception)
                prevalidated_data = prevalins.validated_data
            else:
                prevalidated_data = None

            delegate = self.get_create_delegate_class(
                initial_data=self.initial_data,
                prevalidated_data=prevalidated_data,
            )(instance=self.instance, data=self.initial_data, **self.kwargs)

        elif self.is_read:
            delegate = self.read_delegate

        assert delegate is not None
        return delegate

    @cached_property
    def delegate(self) -> Serializer[T]:
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
        self, initial_data, prevalidated_data
    ) -> Type[Serializer]:
        raise NotImplementedError(
            f"{self.__class__} must implement .get_create_delegate_class()"
        )

    def get_update_delegate_class(
        self, instance, initial_data, prevalidated_data
    ) -> Tuple[Type[Serializer], bool]:
        raise NotImplementedError(
            f"{self.__class__} must implement .get_update_delegate_class()"
        )

    def get_read_delegate_class(self, instance) -> Type[Serializer]:
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
