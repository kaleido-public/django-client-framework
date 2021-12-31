from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING, Any, TypeVar, cast

from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.search import SearchQuery
from django.db import models as m
from django.db.models import Model as DjangoModel
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from ..search_feature import SearchFeature
from .model import DCFModel, IDCFModel

if TYPE_CHECKING:
    from django.db.models import Model


LOG = getLogger(__name__)


T = TypeVar("T", bound="DCFModel", covariant=True)


class ISearchable(IDCFModel[DCFModel]):
    pass


class Searchable(DjangoModel, ISearchable):
    class Meta:
        abstract = True

    search_feature = GenericRelation(SearchFeature)  # type: ignore

    def get_text_feature(self) -> str:
        raise NotImplementedError()

    def _get_text_feature(self):
        # Need to reset @cached_property otherwise auto-update won't work
        self._meta: Any
        new_self: Any = self._meta.model.objects.get(pk=self.id)
        text = new_self.get_text_feature()
        if type(text) is not str:
            raise TypeError(
                f".get_text_feature() must return a str, instead of {type(text)}"
            )
        return text

    @classmethod
    def filter_by_text_search(cls, search_text, queryset=None):
        if queryset is None:
            queryset = cls.objects.all()

        search_text = search_text.strip()

        if not search_text:
            raise ValueError(
                "search_text cannot be empty string or only contain spaces."
            )

        pk_set = set(
            SearchFeature.objects.filter(
                content_type=ContentType.objects.get_for_model(cast(Model, cls))
            )
            .filter(
                m.Q(search_vector=SearchQuery(search_text))
                | m.Q(text_feature__icontains=search_text)
            )
            .values_list("object_id", flat=True)
        )
        return queryset.filter(pk__in=pk_set)

    def get_or_create_searchfeature(self):
        assert isinstance(self, DjangoModel)
        return SearchFeature.objects.get_or_create(
            content_type=ContentType.objects.get_for_model(self),
            object_id=self.id,
            defaults={"text_feature": self._get_text_feature()},
        )

    def update_or_create_searchfeature(self):
        return SearchFeature.objects.update_or_create(
            content_type=ContentType.objects.get_for_model(self.as_model()),
            object_id=self.id,
            defaults={"text_feature": self._get_text_feature()},
        )

    @classmethod
    def update_all_search_feature(cls):
        for instance in cls.objects.all():
            cast(Searchable, instance).update_or_create_searchfeature()


@receiver(post_save)
def update_searchfeature_on_change(sender, instance, **kwargs):
    """
    When a Searchable object is created or updated, we need to update its related
    SearchFeature in order to update the search index.
    """
    if isinstance(instance, Searchable):
        LOG.debug(f"{sender=} {instance=}")
        instance.update_or_create_searchfeature()


@receiver(post_delete)
def delete_searchfeature_on_delete(sender, instance, **kwargs):
    if isinstance(instance, Searchable):
        LOG.debug(f"{sender=} {instance=}")
        instance.search_feature.all().delete()  # type: ignore
