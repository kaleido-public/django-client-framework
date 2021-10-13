from logging import getLogger
from typing import Any, Dict, Generic, List, Type, TypeVar, cast

from django.core.exceptions import FieldDoesNotExist
from django.db.models.fields import Field as DjangoField
from django.db.models.fields.related import ForeignKey
from django.utils.functional import cached_property
from ipromise.overrides import overrides
from rest_framework.fields import Field as DRFField
from rest_framework.serializers import BaseSerializer
from rest_framework.serializers import ModelSerializer as DRFModelSerializer
from rest_framework.serializers import PrimaryKeyRelatedField
from rest_framework.utils.model_meta import RelationInfo
from rest_framework.validators import UniqueValidator

from django_client_framework.exceptions import ValidationError

from ..models import DCFModel
from .serializer import DCFSerializer

LOG = getLogger(__name__)


def get_model_field(model, key, default=None):
    try:
        return model._meta.get_field(key)
    except FieldDoesNotExist:
        return default


def register_serializer_field(for_model_field: Type[DjangoField]):
    def make_decorator(serializer_field: Type[DRFField]):
        ModelSerializer.additional_serializer_field_mapping[
            for_model_field
        ] = serializer_field
        return serializer_field

    return make_decorator


T = TypeVar("T", bound=DCFModel)


class UniqueID(UniqueValidator):
    def __call__(self, value, serializer_field):
        try:
            return super().__call__(value, serializer_field)
        except ValidationError:
            raise ValidationError(
                f"A resource with the ID {value} already exists.", "exists"
            )


class DCFModelSerializer(DCFSerializer[T], DRFModelSerializer, Generic[T]):
    additional_serializer_field_mapping: Dict[Type[DjangoField], Type[DRFField]] = {}

    @cached_property
    def serializer_field_mapping(self):
        mapping = cast(Any, super().serializer_field_mapping)
        mapping.update(self.additional_serializer_field_mapping)
        return mapping

    @overrides(DRFModelSerializer)
    def get_default_field_names(self, declared_fields, model_info):
        """
        Return the default list of field names that will be used if the
        `Meta.fields` option is not specified.
        """

        def append_id(field_name: str, relation_info: RelationInfo):
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
        """Adds support for Meta.required_fields."""
        extra_kwargs = super().get_extra_kwargs()
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
                    "validators": [UniqueID(queryset=self.Meta.model.objects.all())],
                }
            )

        return extra_kwargs

    @overrides(DRFModelSerializer)
    def build_field(self, field_name, info, model_class, nested_depth):
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
    def is_valid(self, raise_exception=False):
        return all(
            [
                super().is_valid(raise_exception),
                self.__check_undefined_fields(raise_exception),
                self.__check_readonly_fields(raise_exception),
            ]
        )

    def __check_undefined_fields(self, raise_exception):
        """Enforces that each field passing through the Serializer must be
        declared in the Meta.fields, for added Security."""
        valid_fields = self.fields.keys()
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

    def __check_readonly_fields(self, raise_exception):
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


ModelSerializer = DCFModelSerializer


class GenerateJsonSchemaDecorator:
    for_model_read: Dict[Type[DCFModel], List[Type[DCFSerializer]]] = {}
    for_model_write: Dict[Type[DCFModel], List[Type[DCFSerializer]]] = {}

    def __call__(self, for_model):
        def decorator(serializer_class):
            self.for_model_read.setdefault(for_model, [])
            self.for_model_read[for_model].append(serializer_class)
            return serializer_class

        return decorator

    def write(self, for_model):
        def decorator(serializer_class):
            self.for_model_write.setdefault(for_model, [])
            self.for_model_write[for_model].append(serializer_class)
            return serializer_class

        return decorator

    def get_models(self):
        return [*self.for_model_read.keys(), *self.for_model_write.keys()]


generate_jsonschema = GenerateJsonSchemaDecorator()


def check_integrity():
    from django_client_framework.api import BaseModelAPI

    generate_jsonschema_for_models = {
        **generate_jsonschema.for_model_read,
        **generate_jsonschema.for_model_write,
    }
    for model in BaseModelAPI.models:
        if (
            model not in generate_jsonschema_for_models
            or not generate_jsonschema_for_models[model]
        ):
            LOG.warn(
                f"{model} is a registered api model but does not have a generated json schema"
            )

    for model in generate_jsonschema_for_models:
        if model not in BaseModelAPI.models:
            raise NotImplementedError(
                f"{model} has a generated json schema but is not a registered api model"
            )

    for serializer_cls in ModelSerializer.__subclasses__():
        model = serializer_cls.Meta.model
        for field_name in getattr(serializer_cls.Meta, "fields", []):
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

        for field_name in getattr(serializer_cls.Meta, "exclude", []):
            if not get_model_field(model, field_name):
                raise NotImplementedError(
                    f"'{field_name}' in {serializer_cls.__name__}.Meta.exclude is not a field."
                )
