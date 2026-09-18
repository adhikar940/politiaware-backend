"""
Dynamic Strawberry InputType Factory for generic_async_graphql.
Builds typed input types for create and update mutations.
"""

from typing import Any, Dict, List, Optional, Type
import strawberry
from django.db import models

from .model_loader import get_model_fields, get_required_fields
from .type_factory import django_field_to_python_type

_INPUT_TYPE_REGISTRY: Dict[str, Any] = {}


def get_or_create_input_type(
    model_cls: Type[models.Model],
    allowed_cols: List[str],
    is_update: bool = False,
    required_cols: Optional[List[str]] = None,
    input_name: Optional[str] = None
) -> Any:
    """
    Dynamically generates and caches a Strawberry InputType for create/update mutations.
    """
    action_str = "Update" if is_update else "Create"
    name = input_name or f"Async_{model_cls._meta.app_label}_{model_cls.__name__}{action_str}Input"

    if name in _INPUT_TYPE_REGISTRY:
        return _INPUT_TYPE_REGISTRY[name]

    all_fields = get_model_fields(model_cls)
    strictly_required = [] if is_update else (required_cols if required_cols is not None else get_required_fields(model_cls, allowed_cols))

    annotations: Dict[str, Any] = {}
    class_attrs: Dict[str, Any] = {}

    for col in allowed_cols:
        fobj = all_fields.get(col)
        if not fobj:
            continue

        py_type, _ = django_field_to_python_type(fobj)

        if col in strictly_required:
            annotations[col] = py_type
        else:
            annotations[col] = Optional[py_type]
            class_attrs[col] = None

    class_attrs["__annotations__"] = annotations

    dynamic_cls = type(name, (), class_attrs)
    strawberry_decorated = strawberry.input(
        dynamic_cls,
        description=f"Input arguments for {action_str.lower()} {model_cls.__name__}"
    )

    _INPUT_TYPE_REGISTRY[name] = strawberry_decorated
    return strawberry_decorated

