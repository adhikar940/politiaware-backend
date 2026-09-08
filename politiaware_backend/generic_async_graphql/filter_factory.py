"""
Dynamic Top-Down Filter Input Generator for generic_async_graphql.
Builds typed GraphQL filter inputs for primitive scalars and nested relationships.
"""

from typing import Any, Dict, List, Optional, Type
import datetime

try:
    import strawberry
    HAS_STRAWBERRY = True
    STRAWBERRY_ID = strawberry.ID
    _strawberry_input_dec = strawberry.input
    _strawberry_field = strawberry.field
except ImportError:
    strawberry = None
    HAS_STRAWBERRY = False
    STRAWBERRY_ID = str
    _strawberry_input_dec = lambda c, *args, **kwargs: c
    _strawberry_field = lambda *args, **kwargs: kwargs.get("default", None)

from django.db import models

from politiaware_backend.generic_async_graphql.model_loader import get_field_by_name, get_model_fields

_FILTER_TYPE_REGISTRY: Dict[str, Any] = {}


@_strawberry_input_dec(description="String field filter operators")
class StringFilterInput:
    exact: Optional[str] = None
    iexact: Optional[str] = None
    contains: Optional[str] = None
    icontains: Optional[str] = None
    startswith: Optional[str] = None
    endswith: Optional[str] = None
    in_: Optional[List[str]] = _strawberry_field(default=None, name="in")
    isnull: Optional[bool] = None


@_strawberry_input_dec(description="Integer field filter operators")
class IntFilterInput:
    exact: Optional[int] = None
    gt: Optional[int] = None
    gte: Optional[int] = None
    lt: Optional[int] = None
    lte: Optional[int] = None
    in_: Optional[List[int]] = _strawberry_field(default=None, name="in")
    range: Optional[List[int]] = None
    isnull: Optional[bool] = None


@_strawberry_input_dec(description="ID field filter operators")
class IdFilterInput:
    exact: Optional[STRAWBERRY_ID] = None
    in_: Optional[List[STRAWBERRY_ID]] = _strawberry_field(default=None, name="in")
    gt: Optional[STRAWBERRY_ID] = None
    gte: Optional[STRAWBERRY_ID] = None
    lt: Optional[STRAWBERRY_ID] = None
    lte: Optional[STRAWBERRY_ID] = None
    isnull: Optional[bool] = None


@_strawberry_input_dec(description="Float / Decimal field filter operators")
class FloatFilterInput:
    exact: Optional[float] = None
    gt: Optional[float] = None
    gte: Optional[float] = None
    lt: Optional[float] = None
    lte: Optional[float] = None
    range: Optional[List[float]] = None
    isnull: Optional[bool] = None


@_strawberry_input_dec(description="Date field filter operators")
class DateFilterInput:
    exact: Optional[datetime.date] = None
    gt: Optional[datetime.date] = None
    gte: Optional[datetime.date] = None
    lt: Optional[datetime.date] = None
    lte: Optional[datetime.date] = None
    year: Optional[int] = None
    month: Optional[int] = None
    day: Optional[int] = None
    range: Optional[List[datetime.date]] = None
    isnull: Optional[bool] = None


@_strawberry_input_dec(description="DateTime field filter operators")
class DateTimeFilterInput:
    exact: Optional[datetime.datetime] = None
    gt: Optional[datetime.datetime] = None
    gte: Optional[datetime.datetime] = None
    lt: Optional[datetime.datetime] = None
    lte: Optional[datetime.datetime] = None
    year: Optional[int] = None
    month: Optional[int] = None
    day: Optional[int] = None
    range: Optional[List[datetime.datetime]] = None
    isnull: Optional[bool] = None


@_strawberry_input_dec(description="Boolean field filter operators")
class BooleanFilterInput:
    exact: Optional[bool] = None
    isnull: Optional[bool] = None


def get_filter_type_for_field(field_obj: models.Field) -> Optional[Any]:
    """Maps a Django model field to its corresponding Strawberry Filter Input class."""
    if isinstance(field_obj, (models.AutoField, models.BigAutoField, models.SmallAutoField)):
        return IdFilterInput
    elif isinstance(field_obj, (models.IntegerField, models.SmallIntegerField, models.BigIntegerField, models.PositiveIntegerField)):
        return IntFilterInput
    elif isinstance(field_obj, (models.FloatField, models.DecimalField)):
        return FloatFilterInput
    elif isinstance(field_obj, (models.DateField,)):
        return DateFilterInput
    elif isinstance(field_obj, (models.DateTimeField,)):
        return DateTimeFilterInput
    elif isinstance(field_obj, (models.BooleanField, models.NullBooleanField)):
        return BooleanFilterInput
    elif isinstance(field_obj, (models.CharField, models.TextField, models.EmailField, models.SlugField)):
        return StringFilterInput
    return StringFilterInput


def get_or_create_model_filter_type(
    model_cls: Type[models.Model],
    filter_fields: Dict[str, List[str]],
    max_depth: int = 3,
    current_depth: int = 1
) -> Any:
    """
    Dynamically generates a Strawberry input type for a Django model's top-down filters.
    Supports nested relationship traversals up to max_depth.
    """
    cache_key = f"AsyncFilter_{model_cls._meta.app_label}_{model_cls.__name__}_depth{current_depth}"
    if cache_key in _FILTER_TYPE_REGISTRY:
        return _FILTER_TYPE_REGISTRY[cache_key]

    annotations: Dict[str, Any] = {}
    class_attrs: Dict[str, Any] = {}

    all_fields = get_model_fields(model_cls)

    for fname, lookups in filter_fields.items():
        clean_name = fname.replace("__", "_")

        # Check if field is direct field or nested relation
        if fname in all_fields:
            fobj = all_fields[fname]
            if isinstance(fobj, (models.ForeignKey, models.OneToOneField)):
                # If relationship and within depth, build nested filter input
                if current_depth < max_depth and fobj.related_model:
                    nested_fields = {
                        rf.name: ["exact", "icontains", "in", "isnull"]
                        for rf in fobj.related_model._meta.get_fields()
                        if hasattr(rf, "name") and not getattr(rf, "auto_created", False)
                    }
                    nested_filter_type = get_or_create_model_filter_type(
                        fobj.related_model,
                        nested_fields,
                        max_depth=max_depth,
                        current_depth=current_depth + 1
                    )
                    annotations[clean_name] = Optional[nested_filter_type]
                    class_attrs[clean_name] = None
                else:
                    annotations[clean_name] = Optional[IdFilterInput]
                    class_attrs[clean_name] = None
            else:
                filter_input_cls = get_filter_type_for_field(fobj)
                if filter_input_cls:
                    annotations[clean_name] = Optional[filter_input_cls]
                    class_attrs[clean_name] = None
        else:
            # Traversed path e.g. "party__abbreviation"
            fobj = get_field_by_name(model_cls, fname)
            if fobj:
                filter_input_cls = get_filter_type_for_field(fobj)
                if filter_input_cls:
                    annotations[clean_name] = Optional[filter_input_cls]
                    class_attrs[clean_name] = None

    class_attrs["__annotations__"] = annotations

    dynamic_filter_cls = type(cache_key, (), class_attrs)
    strawberry_decorated = _strawberry_input_dec(
        dynamic_filter_cls,
        description=f"Top-down structured filters for {model_cls.__name__}"
    )

    _FILTER_TYPE_REGISTRY[cache_key] = strawberry_decorated
    return strawberry_decorated
