"""
Dynamic Query Generator for generic_async_graphql.
Builds async list and extra query fields for Strawberry GraphQL,
delegating database fetching to the db_operations service layer.
"""

from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union
from dataclasses import asdict
import strawberry
from django.db import models

from .model_loader import get_django_model
from .type_factory import get_or_create_strawberry_type, get_or_create_paginated_type
from .filter_factory import get_or_create_model_filter_type
from .db_operations import async_fetch_list


def _format_query_name(model_name: str, prefix: str = "", suffix: str = "") -> str:
    """Formats a model name into a camelCase GraphQL query name (e.g. allLokSabhaMPs, allPartys, allDistricts)."""
    clean_name = model_name[0].upper() + model_name[1:] if model_name else ""
    if suffix.lower() == "s" and clean_name.lower().endswith("s"):
        suffix = ""
    if prefix:
        return f"{prefix}{clean_name}{suffix}"
    return f"{model_name[0].lower()}{model_name[1:]}{suffix}"


def create_async_list_field(
    model_cls: Type[models.Model],
    paginated_type: Any,
    filter_type: Any,
    field_name_map: Dict[str, str],
    search_fields: List[str],
    custom_queryset_hook: Optional[Callable] = None,
    description: Optional[str] = None
) -> Any:
    """
    Creates an async Strawberry field with top-down filters, search, ordering, and pagination.
    Delegates all DB operations to db_operations.async_fetch_list.
    """
    async def resolver(
        info: strawberry.Info,
        filters: Optional[filter_type] = None,
        search: Optional[str] = None,
        order_by: Optional[List[str]] = None,
        offset: int = 0,
        limit: int = 10
    ) -> paginated_type:
        # Convert Strawberry input dataclass to dictionary
        filters_dict = asdict(filters) if filters is not None else None

        res_dict = await async_fetch_list(
            model_cls=model_cls,
            filters_data=filters_dict,
            search_term=search,
            search_fields=search_fields,
            order_by=order_by,
            offset=offset,
            limit=limit,
            custom_queryset_hook=custom_queryset_hook,
            field_name_map=field_name_map,
            info=info
        )
        return paginated_type(**res_dict)

    # Attach annotations so Strawberry reflection inspects arguments properly
    resolver.__annotations__ = {
        "info": strawberry.Info,
        "filters": Optional[filter_type],
        "search": Optional[str],
        "order_by": Optional[List[str]],
        "offset": int,
        "limit": int,
        "return": paginated_type,
    }

    return strawberry.field(
        resolver,
        description=description or f"List, filter, and paginate {model_cls.__name__} records (asynchronous)"
    )


def build_model_queries(
    model_name: str,
    normalized_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Builds all query fields for a single model (list, extra) using Strawberry.
    Returns: { query_field_name: strawberry.field }
    """
    queries_dict = {}
    model_cls = normalized_config["model_cls"]
    queries_cfg = normalized_config.get("queries") or {}

    list_cfg = queries_cfg.get("list")
    if list_cfg and list_cfg.get("enabled", True):
        return_cols = list_cfg.get("return_cols", "__all__")
        custom_type = list_cfg.get("type")
        item_type = custom_type if custom_type else get_or_create_strawberry_type(model_cls, return_cols=return_cols)
        paginated_type = get_or_create_paginated_type(model_cls, item_type)

        query_name = list_cfg.get("name") or _format_query_name(model_cls.__name__, prefix="all", suffix="s")

        filter_fields = list_cfg.get("filter_fields") or {}
        filter_depth = list_cfg.get("filter_depth", 3)
        filter_type = get_or_create_model_filter_type(model_cls, filter_fields, max_depth=filter_depth)

        field_name_map = {fname.replace("__", "_"): fname for fname in filter_fields.keys()}
        search_fields = list_cfg.get("search_fields") or []
        get_qs_hook = list_cfg.get("get_queryset")
        custom_resolver = list_cfg.get("resolver")

        if custom_resolver:
            # Wrap custom resolver as strawberry field
            field_def = strawberry.field(custom_resolver, description=f"Custom list query for {model_cls.__name__}")
        else:
            field_def = create_async_list_field(
                model_cls=model_cls,
                paginated_type=paginated_type,
                filter_type=filter_type,
                field_name_map=field_name_map,
                search_fields=search_fields,
                custom_queryset_hook=get_qs_hook
            )

        queries_dict[query_name] = field_def

    # Model-level Extra Queries
    extra_cfg = queries_cfg.get("extra") or {}
    for extra_name, extra_val in extra_cfg.items():
        if isinstance(extra_val, dict):
            extra_res = extra_val.get("resolver")
            if extra_res:
                queries_dict[extra_name] = strawberry.field(extra_res)
        elif callable(extra_val):
            queries_dict[extra_name] = strawberry.field(extra_val)

    return queries_dict

