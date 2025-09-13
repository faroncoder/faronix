# repo.tpl.py  — AUTO-GENERATED service layer for {{ model }}
from typing import Any, Dict, Iterable
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from ..models import {{ model }}
from .webhook_wrapper import Webhooks

class {{ model }}Repo:
    """Single place for all DB logic for {{ model }}."""
    webhooks = Webhooks(
        base_url={{ (webhooks.base_url if webhooks and webhooks.base_url else None)|pyrepr }},
        headers={{ (webhooks.headers if webhooks and webhooks.headers else None)|pyrepr }},
        routes={{ (webhooks.events if webhooks and webhooks.events else None)|pyrepr }},
    )

    @staticmethod
    def qs():
        return {{ model }}.objects.all()

    @staticmethod
    def get(pk: int) -> {{ model }}:
        return {{ model }}.objects.get(pk=pk)

    @staticmethod
    @transaction.atomic
    def create(data: Dict[str, Any]) -> {{ model }}:
        obj = {{ model }}.objects.create(**data)
        {{ model }}Repo.webhooks.emit("created", {"id": obj.pk})
        return obj

    @staticmethod
    @transaction.atomic
    def bulk_create(rows: Iterable[Dict[str, Any]]) -> int:
        objs = [{{ model }}(**row) for row in rows]
        {{ model }}.objects.bulk_create(objs)
        # optional aggregate webhook:
        {{ model }}Repo.webhooks.emit("created", {"count": len(objs)})
        return len(objs)

    @staticmethod
    @transaction.atomic
    def update(pk: int, data: Dict[str, Any]) -> {{ model }}:
        obj = {{ model }}.objects.select_for_update().get(pk=pk)
        for k, v in data.items():
            setattr(obj, k, v)
        obj.save()
        {{ model }}Repo.webhooks.emit("updated", {"id": obj.pk})
        return obj

    @staticmethod
    @transaction.atomic
    def delete(pk: int) -> None:
        {{ model }}.objects.filter(pk=pk).delete()
        {{ model }}Repo.webhooks.emit("deleted", {"id": pk})
