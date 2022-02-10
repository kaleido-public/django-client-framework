from __future__ import annotations

from logging import getLogger
from typing import *
from uuid import UUID

from django.core.exceptions import FieldDoesNotExist
from django.db.models import Field as DjangoField
from django.db.models.base import Model
from django.db.models.fields import UUIDField as DjangoUUIDField
from django.db.models.fields.related import ForeignKey
from django.db.models.query import QuerySet
from django.utils.functional import cached_property
from ipromise.overrides import overrides
from rest_framework.fields import SerializerMethodField
from rest_framework.fields import UUIDField as DRFUUIDField
from rest_framework.serializers import BaseSerializer
from rest_framework.serializers import ModelSerializer as DRFModelSerializer
from rest_framework.serializers import PrimaryKeyRelatedField, empty
from rest_framework.utils.model_meta import RelationInfo
from rest_framework.validators import UniqueValidator

from django_client_framework.exceptions import ValidationError
from django_client_framework.models.abstract.model import __implements__
from django_client_framework.models.abstract.serializable import D
from django_client_framework.models.abstract.user import DCFAbstractUser

from .serializer import DCFSerializer, IDCFSerializer, T

if TYPE_CHECKING:
    pass

LOG = getLogger(__name__)

"""Summary of how DRF Serializers work internally:

    Serializers can be assigned with fields, and serializers are fields
    themselves, so you can use a Serializer as a field like this:

    class ExampleSerializer(Serializer):

        example = ExampleSerializer2(read_only=True)

    When calling .is_valid(), the following happens:

    1. .run_validation() on the current serializer is called
    2. Inside .run_validation(), .to_internal_value() is called
    3. For each field, .to_internal_value() recursively calls the field's .run_validation()
    4. .to_internal_value() returns the validated_data
    5. The serializer's .validate() is called with validated_data
    6. Finally, .run_validation() returns the validated_data
"""


def get_model_field(model: Type[Model], key: str) -> Optional[DjangoField]:
    try:
        return model._meta.get_field(key)
    except FieldDoesNotExist:
        return None


class UniqueID(UniqueValidator):
    def __call__(self, value: UUID, serializer_field: Any) -> Any:
        try:
            return super().__call__(value, serializer_field)
        except ValidationError:
            raise ValidationError(
                f"A resource with the ID {value} already exists.", "exists"
            )


class DCFUUIDField(DRFUUIDField):
    """The DRFUUIDField casts the UUID value back and forth to a str. However,
    in DRFModelSerializer, a ForeignKey of the UUID type is not casted. This
    leaves a inconsistency of type, and makes the code more complex. Therefore,
    we replace the DRFUUID field with our version that skips the type
    conversion. Now we get a UUID value from the .id field too."""

    def to_representation(self, value: UUID) -> UUID:  # type:ignore[override]
        return value

    def to_internal_value(self, data: UUID) -> UUID:  # type:ignore[override]
        return data


class IDCFModelSerializer(IDCFSerializer[T, D]):
    def to_modelserializer(self) -> DCFModelSerializer[T, D]:
        return cast(DCFModelSerializer[T, D], self)


class DCFModelSerializer(
    DRFModelSerializer, DCFSerializer, __implements__, IDCFModelSerializer[T, D]
):
    def __init__(
        self,
        instance: Optional[T] = None,
        data: Any = empty,
        many: bool = False,
        read_only: bool = False,
        partial: bool = False,
        source: Optional[str] = None,
        context: Any = {},
        prefer_cache: bool = False,
        locale: Optional[str] = None,
        request_user: Optional[DCFAbstractUser] = None,
    ) -> None:
        super().__init__(
            instance=instance,
            data=data,
            many=many,
            read_only=read_only,
            source=source,  # type: ignore
            partial=partial,
            context=context,
            prefer_cache=prefer_cache,
            locale=locale,
            request_user=request_user,
        )

    instance: Optional[T]
    data: D  # type: ignore

    type = SerializerMethodField()

    def get_type(self, instance: T) -> str:
        assert instance._meta.model_name is not None
        return instance._meta.model_name

    @cached_property
    def serializer_field_mapping(self) -> Any:  # type:ignore[override]
        mapping = cast(Any, super().serializer_field_mapping)
        mapping.update(
            {
                DjangoUUIDField: DCFUUIDField,  # This replaces all DRFUUID field with our DCFUUIDField
            }
        )
        return mapping

    @overrides(DRFModelSerializer)
    def get_default_field_names(
        self, declared_fields: Any, model_info: Any
    ) -> List[str]:
        """
        Return the default list of field names that will be used if the
        `Meta.fields` option is not specified.
        """

        def append_id(field_name: str, relation_info: RelationInfo) -> str:
            if isinstance(relation_info.model_field, ForeignKey):
                return field_name + "_id"
            else:
                return field_name

        return (
            [model_info.pk.name]
            + list(declared_fields)
            + list(model_info.fields)
            + [
                append_id(field_name, field)
                for field_name, field in model_info.forward_relations.items()
            ]
        )

    @overrides(DRFModelSerializer)
    def get_extra_kwargs(self) -> Dict[str, Any]:
        extra_kwargs = super().get_extra_kwargs()
        extra_kwargs = self.__read_meta_required_fields(extra_kwargs)
        extra_kwargs = self.__make_id_writable_for_create(extra_kwargs)
        return extra_kwargs

    def __read_meta_required_fields(
        self, extra_kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Adds support for Meta.required_fields."""
        extra_required = getattr(self.Meta, "required_fields", None)
        if extra_required is not None:
            if not isinstance(extra_required, (list, tuple)):
                raise TypeError(
                    "The `required_fields` option must be a list or tuple. "
                    "Got %s." % type(extra_required).__name__
                )
            for field_name in extra_required:
                kwargs = extra_kwargs.get(field_name, {})
                kwargs["required"] = True
                extra_kwargs[field_name] = kwargs
        return extra_kwargs

    def __make_id_writable_for_create(
        self, extra_kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Make the ID field also write-able for creating an UUID."""
        extra_kwargs.setdefault("id", {})
        if self.instance:  # Update
            extra_kwargs["id"].update({"read_only": True})
        else:  # Create
            extra_kwargs["id"].update(
                {
                    "read_only": False,
                    "required": False,
                    "allow_null": False,
                    "validators": [
                        UniqueID(queryset=QuerySet(model=self.Meta.model).all())
                    ],
                }
            )

        return extra_kwargs

    @overrides(DRFModelSerializer)
    def build_field(
        self, field_name: str, info: Any, model_class: Type[Model], nested_depth: int
    ) -> Any:
        suffix = "_id"
        if field_name.endswith(suffix):
            # now we checked {field_name} is {old_field_name}_id
            old_field_name = field_name[0 : -len(suffix)]
            if old_field_name in info.relations and isinstance(
                info.relations[old_field_name].model_field, ForeignKey
            ):
                _, ret_kwargs = super().build_field(
                    old_field_name, info, model_class, nested_depth
                )
                ret_kwargs.update({"source": old_field_name})
                return self.serializer_related_field, ret_kwargs
        return super().build_field(field_name, info, model_class, nested_depth)

    @overrides(BaseSerializer)
    def is_valid(self, raise_exception: bool = False) -> bool:
        return all(
            [
                super().is_valid(raise_exception),
                self.__check_undefined_fields(raise_exception),
                self.__check_readonly_fields(raise_exception),
            ]
        )

    def __check_undefined_fields(self, raise_exception: bool) -> bool:
        """Enforces that each field passing through the Serializer must be
        declared in the Meta.fields, for added Security."""
        valid_fields = list(self.fields.keys())
        input_fields = self.initial_data.keys()

        if extra_fields := list(set(input_fields) - set(valid_fields)):
            valid_fields = list(valid_fields)
            valid_fields.sort()
            extra_fields.sort()
            if raise_exception:
                raise ValidationError(
                    {
                        field: [f"Extra field. Valid fields are: {valid_fields}"]
                        for field in extra_fields
                    }
                )
            else:
                return False
        return True

    def __check_readonly_fields(self, raise_exception: bool) -> bool:
        """By default, any 'read_only' fields that are incorrectly included in
        the serializer input will be ignored. This method enforces that the
        error is more explicit by raising a ValidationError."""
        read_only_fields = set(
            [
                field_name
                for field_name, field_instance in self.fields.items()
                if field_instance.read_only
            ]
        )

        if invalid_fields := [
            key for key in self.initial_data if key in read_only_fields
        ]:
            if raise_exception:
                invalid_fields.sort()
                raise ValidationError(f"These fields are read-only: {invalid_fields}")
            else:
                return False
        return True


class GenerateJsonSchemaDecorator:
    for_model_read: Dict[Type[Model], List[Type[DCFSerializer]]] = {}
    for_model_write: Dict[Type[Model], List[Type[DCFSerializer]]] = {}

    def __call__(self, for_model: Type[Model]) -> Any:
        def decorator(serializer_class: Type[DCFSerializer]) -> Type[DCFSerializer]:
            self.for_model_read.setdefault(for_model, [])
            self.for_model_read[for_model].append(serializer_class)
            return serializer_class

        return decorator

    def write(self, for_model: Type[Model]) -> Any:
        def decorator(serializer_class: Type[DCFSerializer]) -> Type[DCFSerializer]:
            self.for_model_write.setdefault(for_model, [])
            self.for_model_write[for_model].append(serializer_class)
            return serializer_class

        return decorator

    def get_models(self) -> List[Type[Model]]:
        return [*self.for_model_read.keys(), *self.for_model_write.keys()]


generate_jsonschema = GenerateJsonSchemaDecorator()


def check_integrity() -> None:
    for serializer_cls in DCFModelSerializer.__subclasses__():
        model = serializer_cls.Meta.model
        if hasattr(serializer_cls.Meta, "exclude"):
            raise NotImplementedError(
                f"Using 'exclude' in {serializer_cls.__name__}.Meta is discouraged. Use 'fields' instead."
            )
        if not hasattr(serializer_cls.Meta, "fields"):
            raise NotImplementedError(
                f"You must add 'fields' in {serializer_cls.__name__}.Meta."
            )

        declared_fields = getattr(serializer_cls.Meta, "fields")
        for must_present in ["id", "type", "created_at"]:
            if must_present not in declared_fields:
                raise NotImplementedError(
                    f"You must add '{must_present}' to {serializer_cls.__name__}.Meta.fields: {serializer_cls.Meta.fields}"
                )
        for field_name in declared_fields:
            if field_name not in serializer_cls().fields:
                raise NotImplementedError(
                    f"{field_name} in {serializer_cls.__name__}.Meta.fields is not a field"
                )
            field = serializer_cls().fields[field_name]
            if (
                isinstance(field, PrimaryKeyRelatedField)
                and not field_name.endswith("_id")
                and get_model_field(model, field_name)
            ):
                raise NotImplementedError(
                    f"You must append '_id' to '{field_name}' in {serializer_cls.__name__}.Meta.fields."
                )
