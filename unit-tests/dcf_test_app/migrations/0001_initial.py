# Generated by Django 3.2.11 on 2022-01-21 06:28

import uuid

import django.db.models.deletion
from django.db import migrations, models

import django_client_framework.models.abstract.model
import django_client_framework.models.abstract.rate_limited
import django_client_framework.models.abstract.serializable


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Brand",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        unique=True,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("name", models.CharField(max_length=100, null=True, unique=True)),
                ("priority", models.IntegerField(default=1)),
            ],
            options={
                "abstract": False,
            },
            bases=(
                models.Model,
                django_client_framework.models.abstract.serializable.Serializable,
                django_client_framework.models.abstract.model.__implements__,
                django_client_framework.models.abstract.model.IDCFModel,
            ),
        ),
        migrations.CreateModel(
            name="ThrottledModel",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        unique=True,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            bases=(
                models.Model,
                django_client_framework.models.abstract.serializable.Serializable,
                django_client_framework.models.abstract.model.__implements__,
                django_client_framework.models.abstract.model.IDCFModel,
                django_client_framework.models.abstract.rate_limited.RateLimited,
            ),
        ),
        migrations.CreateModel(
            name="Product",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        unique=True,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("barcode", models.CharField(blank=True, default="", max_length=255)),
                ("priority", models.IntegerField(default=1)),
                (
                    "brand",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="products",
                        to="dcf_test_app.brand",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=(
                models.Model,
                django_client_framework.models.abstract.serializable.Serializable,
                django_client_framework.models.abstract.model.__implements__,
                django_client_framework.models.abstract.model.IDCFModel,
            ),
        ),
    ]
