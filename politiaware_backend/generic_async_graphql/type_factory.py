"""
Dynamic Strawberry ObjectType and Payload factory for generic_async_graphql.
"""

from typing import Any, Dict, List, Optional, Tuple, Type, Union
import dataclasses
import datetime
from decimal import Decimal
import strawberry
from asgiref.sync import sync_to_async
from django.db import models

from .model_loader import get_model_fields, get_primary_key_field

# Type registries to prevent duplicate class registrations in Strawberry schema
_STRAWBERRY_TYPE_REGISTRY: Dict[str, Any] = {}
_PAYLOAD_TYPE_REGISTRY: Dict[str, Any] = {}
_PAGINATED_TYPE_REGISTRY: Dict[str, Any] = {}


@strawberry.type
class DeletePayload:
    """Standardized payload for delete mutations in Strawberry."""
    success: bool
    errors: Optional[List[str]] = None
    id: Optional[strawberry.ID] = None


def django_field_to_python_type(field_obj: models.Field) -> Tuple[Type, bool]:
    """
    Maps a Django model field to a corresponding Python/Strawberry type and nullability flag.
    Returns: (python_type, is_nullable)
    """
    is_nullable = getattr(field_obj, "null", False) or getattr(field_obj, "blank", False)

    if isinstance(field_obj, (models.AutoField, models.BigAutoField, models.SmallAutoField)):
        return strawberry.ID, False
    elif isinstance(field_obj, (models.IntegerField, models.SmallIntegerField, models.BigIntegerField, models.PositiveIntegerField)):
        return int, is_nullable
    elif isinstance(field_obj, (models.FloatField,)):
        return float, is_nullable
    elif isinstance(field_obj, (models.DecimalField,)):
        return Decimal, is_nullable
    elif isinstance(field_obj, (models.BooleanField, models.NullBooleanField)):
        return bool, is_nullable
    elif isinstance(field_obj, (models.DateField,)):
        return datetime.date, is_nullable
    elif isinstance(field_obj, (models.DateTimeField,)):
        return datetime.datetime, is_nullable
    elif isinstance(field_obj, (models.ForeignKey, models.OneToOneField)):
        # Represent foreign key id on the flat model type
        return strawberry.ID, is_nullable
    elif isinstance(field_obj, (models.CharField, models.TextField, models.EmailField, models.SlugField)):
        return str, is_nullable
    return str, is_nullable


def make_relation_resolver(col: str):
    """
    Creates an async resolver for ForeignKey and OneToOneField relationships.
    1. If foreign key id is None, returns None immediately without any DB query.
    2. If related object is already in Django fields_cache (e.g. from select_related), returns it immediately.
    3. Otherwise, safely loads the related object in a threadpool via sync_to_async to prevent
       SynchronousOnlyOperation in async GraphQL execution.
    """
    async def resolve_relation(root: strawberry.Parent[Any]) -> Any:
        if root is None:
            return None
        if isinstance(root, dict):
            return root.get(col)

        if isinstance(root, models.Model):
            fk_attname = f"{col}_id"
            if hasattr(root, fk_attname) and getattr(root, fk_attname) is None:
                return None
            fields_cache = getattr(getattr(root, "_state", None), "fields_cache", {})
            if col in fields_cache:
                return fields_cache[col]
            try:
                return await sync_to_async(getattr, thread_sensitive=True)(root, col)
            except (models.ObjectDoesNotExist, AttributeError):
                return None

        val = getattr(root, col, None)
        if callable(val):
            return None
        return val

    return resolve_relation


def make_relation_id_resolver(col: str):
    """
    Creates an async resolver for relationship IDs when max depth is reached.
    Extracts the ID directly from the foreign key attribute (e.g. <col>_id) without DB query.
    """
    async def resolve_id(root: strawberry.Parent[Any]) -> Any:
        if root is None:
            return None
        if isinstance(root, dict):
            val = root.get(f"{col}_id") or root.get(col)
            return str(val) if val is not None else None

        if isinstance(root, models.Model):
            fk_attname = f"{col}_id"
            if hasattr(root, fk_attname):
                val = getattr(root, fk_attname)
                return str(val) if val is not None else None
            fields_cache = getattr(getattr(root, "_state", None), "fields_cache", {})
            if col in fields_cache:
                rel = fields_cache[col]
                return str(rel.pk) if rel else None
            try:
                rel = await sync_to_async(getattr, thread_sensitive=True)(root, col)
                return str(rel.pk) if rel else None
            except Exception:
                return None

        val = getattr(root, f"{col}_id", None) or getattr(root, col, None)
        if callable(val):
            return None
        return str(val) if val is not None else None

    return resolve_id


def get_or_create_strawberry_type(
    model_cls: Type[models.Model],
    return_cols: Union[str, List[str]] = "__all__",
    type_name: Optional[str] = None,
    depth: int = 2,
    visited: Optional[set] = None
) -> Any:
    """
    Dynamically generates and caches a Strawberry ObjectType representing a Django model,
    including nested ObjectTypes for ForeignKey and OneToOneField relationships.
    """
    base_name = type_name or f"Async_{model_cls._meta.app_label}_{model_cls.__name__}Type"
    cache_key = f"{base_name}_{hash(tuple(sorted(return_cols)) if isinstance(return_cols, list) else return_cols)}_d{depth}"

    if cache_key in _STRAWBERRY_TYPE_REGISTRY:
        return _STRAWBERRY_TYPE_REGISTRY[cache_key]

    if base_name in _STRAWBERRY_TYPE_REGISTRY:
        return _STRAWBERRY_TYPE_REGISTRY[base_name]

    current_visited = (visited or set()) | {model_cls}

    all_fields = get_model_fields(model_cls)
    if return_cols == "__all__":
        cols = list(all_fields.keys())
    else:
        cols = list(return_cols)
        pk_name = get_primary_key_field(model_cls)
        if pk_name not in cols and "id" not in cols:
            cols.append(pk_name)

    annotations: Dict[str, Any] = {}
    class_attrs: Dict[str, Any] = {}

    for col in cols:
        fobj = all_fields.get(col)
        if not fobj:
            continue

        if isinstance(fobj, (models.ForeignKey, models.OneToOneField)):
            related_model = getattr(fobj, "related_model", None) or getattr(fobj.remote_field, "model", None)
            if isinstance(related_model, str):
                from django.apps import apps
                related_model = apps.get_model(related_model)

            if depth > 0 and related_model and related_model not in current_visited:
                rel_type = get_or_create_strawberry_type(
                    related_model,
                    depth=depth - 1,
                    visited=current_visited
                )
                annotations[col] = Optional[rel_type]
                class_attrs[col] = strawberry.field(resolver=make_relation_resolver(col))
            else:
                annotations[col] = Optional[strawberry.ID]
                class_attrs[col] = strawberry.field(resolver=make_relation_id_resolver(col))
        else:
            py_type, is_null = django_field_to_python_type(fobj)
            if is_null:
                annotations[col] = Optional[py_type]
                class_attrs[col] = None
            else:
                annotations[col] = py_type

    class_attrs["__annotations__"] = annotations

    dynamic_cls = type(base_name, (), class_attrs)
    strawberry_decorated = strawberry.type(dynamic_cls, description=f"Asynchronous GraphQL Type for {model_cls.__name__}")

    _STRAWBERRY_TYPE_REGISTRY[cache_key] = strawberry_decorated
    _STRAWBERRY_TYPE_REGISTRY[base_name] = strawberry_decorated
    return strawberry_decorated


def get_or_create_paginated_type(
    model_cls: Type[models.Model],
    item_type: Any,
    type_name: Optional[str] = None
) -> Any:
    """
    Creates and caches a standardized paginated response type:
      total: Int
      offset: Int
      limit: Int
      data: [ItemType]
    """
    name = type_name or f"Async_{model_cls._meta.app_label}_{model_cls.__name__}PaginatedType"
    if name in _PAGINATED_TYPE_REGISTRY:
        return _PAGINATED_TYPE_REGISTRY[name]

    annotations = {
        "total": int,
        "offset": int,
        "limit": int,
        "data": List[item_type],
    }

    attrs = {
        "__annotations__": annotations,
        "total": 0,
        "offset": 0,
        "limit": 10,
        "data": dataclasses.field(default_factory=list),
    }

    dynamic_cls = type(name, (), attrs)
    strawberry_decorated = strawberry.type(
        dynamic_cls,
        description=f"Paginated response for {model_cls.__name__} records"
    )

    _PAGINATED_TYPE_REGISTRY[name] = strawberry_decorated
    return strawberry_decorated


def get_or_create_payload_type(
    model_cls: Type[models.Model],
    data_type: Any,
    payload_name: Optional[str] = None
) -> Any:
    """
    Creates and caches a standardized mutation response payload:
      success: Boolean
      errors: [String]
      data: ItemType
    """
    name = payload_name or f"Async_{model_cls._meta.app_label}_{model_cls.__name__}Payload"
    if name in _PAYLOAD_TYPE_REGISTRY:
        return _PAYLOAD_TYPE_REGISTRY[name]

    annotations = {
        "success": bool,
        "errors": Optional[List[str]],
        "data": Optional[data_type],
    }

    attrs = {
        "__annotations__": annotations,
        "success": True,
        "errors": None,
        "data": None,
    }

    dynamic_cls = type(name, (), attrs)
    strawberry_decorated = strawberry.type(
        dynamic_cls,
        description=f"Mutation response payload for {model_cls.__name__}"
    )

    _PAYLOAD_TYPE_REGISTRY[name] = strawberry_decorated
    return strawberry_decorated

