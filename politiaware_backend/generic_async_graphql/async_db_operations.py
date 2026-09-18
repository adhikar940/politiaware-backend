"""
Asynchronous Database Operations Service Layer for generic_async_graphql.
Performs all database read operations natively asynchronously (using Django ORM async APIs
like aget(), acount(), aexists(), and async-iterable querysets with select_related / prefetch_related).
For write operations, delegates to sync_db_operations wrapped thread-sensitively in sync_to_async.
"""

from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union
from asgiref.sync import sync_to_async
from django.db import models
from django.db.models import Q

from .sync_db_operations import (
    sync_create_record,
    sync_update_record,
    sync_partial_update_record,
    sync_delete_record,
    assign_model_fields,
    get_clean_exclude_fields
)
from politiaware_backend.valkey_cache import (
    is_cache_enabled,
    build_list_cache_key,
    aget_cached_list,
    aset_cached_list,
    ainvalidate_model
)




# ---------------------------------------------------------------------------
# QUERY PARSING & RELATIONS INTROSPECTION
# ---------------------------------------------------------------------------

def parse_nested_filters(
    filters_dict: Dict[str, Any],
    field_name_map: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Parses top-down nested filter dictionaries into Django ORM filter kwargs.
    Example:
      {"abbreviation": {"icontains": "BSP"}} -> {"abbreviation__icontains": "BSP"}
      {"party": {"partyname": {"icontains": "Congress"}}} -> {"party__partyname__icontains": "Congress"}
    """
    field_name_map = field_name_map or {}
    orm_kwargs: Dict[str, Any] = {}

    def _traverse(data: Dict[str, Any], prefix: str = ""):
        for k, v in data.items():
            if v is None:
                continue

            current_key = f"{prefix}__{k}" if prefix else k
            mapped_key = field_name_map.get(current_key, current_key)

            if isinstance(v, dict):
                is_operator_dict = any(op in ("exact", "iexact", "contains", "icontains",
                                              "startswith", "istartswith", "endswith", "iendswith",
                                              "in", "gt", "gte", "lt", "lte", "range",
                                              "year", "month", "day", "isnull", "regex", "iregex")
                                       for op in v.keys())
                if is_operator_dict:
                    for op, val in v.items():
                        if val is not None:
                            if op == "exact":
                                orm_kwargs[mapped_key] = val
                            else:
                                orm_kwargs[f"{mapped_key}__{op}"] = val
                else:
                    _traverse(v, prefix=mapped_key)
            else:
                orm_kwargs[mapped_key] = v

    _traverse(filters_dict)
    return orm_kwargs


def extract_relation_paths_from_info(
    model_cls: Type[models.Model],
    info: Any,
    subfield: str = "data",
    max_depth: int = 3
) -> List[str]:
    """
    Extracts valid single-valued relation paths (ForeignKeys and OneToOneFields)
    requested in the GraphQL query under `subfield` (default: 'data') to optimize
    ORM query execution via select_related.
    """
    if not info or not hasattr(info, "selected_fields") or not info.selected_fields:
        return []

    def _find_target_selections(fields):
        for f in fields:
            if f.name == subfield:
                return f.selections
            if f.selections:
                found = _find_target_selections(f.selections)
                if found:
                    return found
        return []

    data_selections = _find_target_selections(info.selected_fields)
    if not data_selections:
        return []

    select_related_paths: List[str] = []

    def _walk(curr_model: Type[models.Model], selections: List[Any], prefix: str = "", depth: int = max_depth):
        if depth <= 0 or not selections:
            return

        for sel in selections:
            field_name = sel.name
            try:
                fobj = curr_model._meta.get_field(field_name)
            except Exception:
                continue

            if isinstance(fobj, (models.ForeignKey, models.OneToOneField)):
                path = f"{prefix}__{field_name}" if prefix else field_name
                select_related_paths.append(path)
                rel_model = getattr(fobj, "related_model", None) or getattr(fobj.remote_field, "model", None)
                if isinstance(rel_model, str):
                    from django.apps import apps
                    try:
                        rel_model = apps.get_model(rel_model)
                    except LookupError:
                        rel_model = None

                if rel_model and sel.selections:
                    _walk(rel_model, sel.selections, prefix=path, depth=depth - 1)

    _walk(model_cls, data_selections)
    return select_related_paths


# ---------------------------------------------------------------------------
# ASYNCHRONOUS READ OPERATIONS (ALL QUERIES ASYNC)
# ---------------------------------------------------------------------------

async def async_fetch_list(
    model_cls: Type[models.Model],
    filters_data: Optional[Dict[str, Any]] = None,
    search_term: Optional[str] = None,
    search_fields: Optional[List[str]] = None,
    order_by: Optional[Union[str, List[str]]] = None,
    offset: int = 0,
    limit: int = 10,
    custom_queryset_hook: Optional[Callable] = None,
    field_name_map: Optional[Dict[str, str]] = None,
    info: Optional[Any] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Asynchronously queries, filters, searches, orders, and paginates a model queryset.
    Optimizes relational lookups with select_related based on GraphQL field selection.
    Returns:
      {"total": int, "offset": int, "limit": int, "data": list}
    """
    # 0. Check Valkey cache if enabled
    cache_active = is_cache_enabled()
    payload_key = None
    meta_key = None
    tracking_set_key = None
    metadata = None

    if cache_active:
        select_paths = extract_relation_paths_from_info(model_cls, info) if info else None
        payload_key, meta_key, tracking_set_key, metadata = build_list_cache_key(
            model_cls=model_cls,
            filters_data=filters_data,
            search_term=search_term,
            search_fields=search_fields,
            order_by=order_by,
            offset=offset,
            limit=limit,
            select_paths=select_paths,
        )
        cached_res = await aget_cached_list(payload_key)
        if cached_res is not None:
            return cached_res

    qs = model_cls.objects.all()

    # 1. Custom get_queryset hook if defined
    if custom_queryset_hook:
        qs = custom_queryset_hook(qs, info, **kwargs)

    # 2. Top-down nested filters
    if filters_data and isinstance(filters_data, dict):
        orm_filters = parse_nested_filters(filters_data, field_name_map)
        if orm_filters:
            qs = qs.filter(**orm_filters)

    # 3. Text search
    if search_term and search_fields:
        search_query = Q()
        for sf in search_fields:
            search_query |= Q(**{f"{sf}__icontains": search_term})
        qs = qs.filter(search_query)

    # 4. Ordering
    if order_by:
        if isinstance(order_by, str):
            order_by = [order_by]
        qs = qs.order_by(*order_by)

    # 5. Total count asynchronously via Django async ORM
    total = await qs.acount()

    # 6. Optimize relations via select_related from GraphQL selection set
    if info:
        select_paths = extract_relation_paths_from_info(model_cls, info)
        if select_paths:
            qs = qs.select_related(*select_paths)

    # 7. Slicing and async evaluation into list using async iterator
    sliced_qs = qs[offset:offset + limit]
    items = [item async for item in sliced_qs]

    result = {
        "total": total,
        "offset": offset,
        "limit": limit,
        "data": items,
    }

    # 8. Store in Valkey cache if enabled
    if cache_active and payload_key and meta_key and tracking_set_key and metadata:
        await aset_cached_list(
            payload_key=payload_key,
            meta_key=meta_key,
            tracking_set_key=tracking_set_key,
            result_dict=result,
            metadata=metadata,
        )

    return result



async def async_get_record(
    model_cls: Type[models.Model],
    pk_val: Any,
    pk_field_name: str = "id",
    select_paths: Optional[List[str]] = None,
    prefetch_paths: Optional[List[str]] = None,
    info: Optional[Any] = None
) -> Tuple[Optional[models.Model], Optional[str]]:
    """
    Asynchronously fetches a single model instance using Django's async aget().
    Returns: (instance, error_message)
    """
    qs = model_cls.objects.all()

    if info:
        extracted = extract_relation_paths_from_info(model_cls, info)
        if extracted:
            select_paths = list(set((select_paths or []) + extracted))

    if select_paths:
        qs = qs.select_related(*select_paths)
    if prefetch_paths:
        qs = qs.prefetch_related(*prefetch_paths)

    try:
        instance = await qs.aget(**{pk_field_name: pk_val})
        return instance, None
    except model_cls.DoesNotExist:
        return None, f"{model_cls.__name__} with {pk_field_name}='{pk_val}' does not exist."
    except Exception as e:
        return None, str(e)


async def async_count_records(
    model_cls: Type[models.Model],
    filters_data: Optional[Dict[str, Any]] = None,
    field_name_map: Optional[Dict[str, str]] = None,
    custom_queryset_hook: Optional[Callable] = None,
    info: Optional[Any] = None,
    **kwargs
) -> int:
    """
    Asynchronously counts records matching optional filters using qs.acount().
    """
    qs = model_cls.objects.all()
    if custom_queryset_hook:
        qs = custom_queryset_hook(qs, info, **kwargs)
    if filters_data and isinstance(filters_data, dict):
        orm_filters = parse_nested_filters(filters_data, field_name_map)
        if orm_filters:
            qs = qs.filter(**orm_filters)
    return await qs.acount()


async def async_check_exists(
    model_cls: Type[models.Model],
    filters_data: Optional[Dict[str, Any]] = None,
    field_name_map: Optional[Dict[str, str]] = None,
    custom_queryset_hook: Optional[Callable] = None,
    info: Optional[Any] = None,
    **kwargs
) -> bool:
    """
    Asynchronously checks if records matching filters exist using qs.aexists().
    """
    qs = model_cls.objects.all()
    if custom_queryset_hook:
        qs = custom_queryset_hook(qs, info, **kwargs)
    if filters_data and isinstance(filters_data, dict):
        orm_filters = parse_nested_filters(filters_data, field_name_map)
        if orm_filters:
            qs = qs.filter(**orm_filters)
    return await qs.aexists()


# ---------------------------------------------------------------------------
# ASYNC BRIDGES FOR SYNCHRONOUS MUTATIONS (THREAD-SENSITIVE)
# ---------------------------------------------------------------------------

async def async_create_record(
    model_cls: Type[models.Model],
    input_data: Dict[str, Any],
    create_cols: List[str],
    required_cols: Optional[List[str]] = None,
    before_save: Optional[Callable] = None,
    after_save: Optional[Callable] = None,
    info: Optional[Any] = None
) -> Tuple[Optional[models.Model], Optional[List[str]]]:
    """
    Asynchronously executes sync_create_record inside a thread-sensitive worker.
    Invalidates Valkey cache for model_cls upon successful creation.
    """
    inst, errs = await sync_to_async(sync_create_record, thread_sensitive=True)(
        model_cls=model_cls,
        input_data=input_data,
        create_cols=create_cols,
        required_cols=required_cols,
        before_save=before_save,
        after_save=after_save,
        info=info
    )
    if inst is not None and not errs and is_cache_enabled():
        await ainvalidate_model(model_cls)
    return inst, errs


async def async_update_record(
    model_cls: Type[models.Model],
    pk_val: Any,
    input_data: Dict[str, Any],
    update_cols: List[str],
    pk_field_name: str = "id",
    before_save: Optional[Callable] = None,
    after_save: Optional[Callable] = None,
    info: Optional[Any] = None
) -> Tuple[Optional[models.Model], Optional[List[str]]]:
    """
    Asynchronously executes sync_update_record inside a thread-sensitive worker.
    Invalidates Valkey cache for model_cls upon successful update.
    """
    inst, errs = await sync_to_async(sync_update_record, thread_sensitive=True)(
        model_cls=model_cls,
        pk_val=pk_val,
        input_data=input_data,
        update_cols=update_cols,
        pk_field_name=pk_field_name,
        before_save=before_save,
        after_save=after_save,
        info=info
    )
    if inst is not None and not errs and is_cache_enabled():
        await ainvalidate_model(model_cls)
    return inst, errs


async def async_partial_update_record(
    model_cls: Type[models.Model],
    pk_val: Any,
    input_data: Dict[str, Any],
    update_cols: List[str],
    pk_field_name: str = "id",
    before_save: Optional[Callable] = None,
    after_save: Optional[Callable] = None,
    info: Optional[Any] = None
) -> Tuple[Optional[models.Model], Optional[List[str]]]:
    """
    Asynchronously executes sync_partial_update_record inside a thread-sensitive worker.
    Invalidates Valkey cache for model_cls upon successful partial update.
    """
    inst, errs = await sync_to_async(sync_partial_update_record, thread_sensitive=True)(
        model_cls=model_cls,
        pk_val=pk_val,
        input_data=input_data,
        update_cols=update_cols,
        pk_field_name=pk_field_name,
        before_save=before_save,
        after_save=after_save,
        info=info
    )
    if inst is not None and not errs and is_cache_enabled():
        await ainvalidate_model(model_cls)
    return inst, errs


async def async_delete_record(
    model_cls: Type[models.Model],
    pk_val: Any,
    pk_field_name: str = "id",
    before_delete: Optional[Callable] = None,
    after_delete: Optional[Callable] = None,
    info: Optional[Any] = None
) -> Tuple[Optional[Any], bool, Optional[List[str]]]:
    """
    Asynchronously executes sync_delete_record inside a thread-sensitive worker.
    Invalidates Valkey cache for model_cls upon successful deletion.
    """
    deleted_id, success, errs = await sync_to_async(sync_delete_record, thread_sensitive=True)(
        model_cls=model_cls,
        pk_val=pk_val,
        pk_field_name=pk_field_name,
        before_delete=before_delete,
        after_delete=after_delete,
        info=info
    )
    if success and is_cache_enabled():
        await ainvalidate_model(model_cls)
    return deleted_id, success, errs


