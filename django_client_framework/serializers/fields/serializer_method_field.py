from rest_framework import serializers as s
from rest_framework.fields import Field


class TypedSerializerMethodField(s.SerializerMethodField):
    def __init__(self, type: Field, *args, **kwargs):
        self.type = type
        super().__init__(*args, **kwargs)
