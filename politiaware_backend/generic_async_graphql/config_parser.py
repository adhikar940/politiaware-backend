"""
Configuration normalization, smart defaults injection, and callable resolution for generic_async_graphql.
"""

import importlib
from typing import Any, Dict, List, Optional, Type
from django.db import models

from politiaware_backend.generic_async_graphql.model_loader import get_editable_fields, get_model_fields


def resolve_callable(func_or_path: Any) -> Any:
    """
    Resolves a callable or an import path string (e.g. 'app.module.func').
    Returns the resolved callable or None.
    """
    if func_or_path is None:
        return None
    if callable(func_or_path):
        return func_or_path
    if isinstance(func_or_path, str):
        if "." in func_or_path:
            mod_name, attr_name = func_or_path.rsplit(".", 1)
            try:
                mod = importlib.import_module(mod_name)
                return getattr(mod, attr_name)
            except (ImportError, AttributeError) as exc:
                raise ImportError(f"Could not resolve callable from path '{func_or_path}': {exc}") from exc
        raise ValueError(f"Invalid callable path format: '{func_or_path}'. Expected 'module.callable_name'.")
    return func_or_path


def get_default_lookups_for_field(field_obj: models.Field) -> List[str]:
    """Returns default filter lookup operators for a given Django model field."""
    if isinstance(field_obj, (models.CharField, models.TextField, models.EmailField, models.SlugField)):
        return ["exact", "iexact", "contains", "icontains", "startswith", "endswith", "in", "isnull"]
    elif isinstance(field_obj, (models.IntegerField, models.SmallIntegerField, models.BigIntegerField, models.PositiveIntegerField)):
        return ["exact", "gt", "gte", "lt", "lte", "in", "range", "isnull"]
    elif isinstance(field_obj, (models.AutoField, models.BigAutoField)):
        return ["exact", "in", "gt", "gte", "lt", "lte", "isnull"]
    elif isinstance(field_obj, (models.FloatField, models.DecimalField)):
        return ["exact", "gt", "gte", "lt", "lte", "range", "isnull"]
    elif isinstance(field_obj, (models.DateField, models.DateTimeField)):
        return ["exact", "gt", "gte", "lt", "lte", "range", "year", "month", "day", "isnull"]
    elif isinstance(field_obj, (models.BooleanField, models.NullBooleanField)):
        return ["exact", "isnull"]
    elif isinstance(field_obj, (models.ForeignKey, models.OneToOneField)):
        return ["exact", "in", "isnull"]
    return ["exact", "isnull"]


def build_default_queries_config(model_cls: Type[models.Model]) -> Dict[str, Any]:
    """Generates default queries configuration for a model."""
    model_fields = get_model_fields(model_cls)
    filter_fields = {}
    search_fields = []

    for fname, fobj in model_fields.items():
        filter_fields[fname] = get_default_lookups_for_field(fobj)
        if isinstance(fobj, (models.CharField, models.TextField)):
            search_fields.append(fname)

    return {
        "list": {
            "enabled": True,
            "return_cols": "__all__",
            "filter_fields": filter_fields,
            "search_fields": search_fields,
            "ordering_fields": "__all__",
            "pagination": True
        },
        "extra": {}
    }


def build_default_mutations_config(model_cls: Type[models.Model]) -> Dict[str, Any]:
    """Generates default mutations configuration for a model."""
    editable_cols = get_editable_fields(model_cls)
    return {
        "create": {
            "enabled": True,
            "create_cols": editable_cols,
            "return_cols": "__all__"
        },
        "update": {
            "enabled": True,
            "pk": "id",
            "update_cols": editable_cols,
            "return_cols": "__all__"
        },
        "delete": {
            "enabled": True,
            "pk": "id",
            "return_cols": ["id"]
        },
        "extra": {}
    }


def normalize_model_config(
    model_identifier: str,
    raw_config: Optional[Dict[str, Any]],
    model_cls: Type[models.Model]
) -> Dict[str, Any]:
    """
    Normalizes model configuration.
    If raw_config is empty or None: injects smart defaults (list + CRUD mutations).
    If raw_config is specified: strictly applies whitelist and configures only specified operations.
    """
    raw_config = raw_config or {}

    has_queries_section = "queries" in raw_config
    has_mutations_section = "mutations" in raw_config

    if not has_queries_section and not has_mutations_section:
        # Empty config e.g. "Party": {} -> Generate list query + CRUD mutations
        return {
            "model_cls": model_cls,
            "app_label": model_cls._meta.app_label,
            "queries": build_default_queries_config(model_cls),
            "mutations": build_default_mutations_config(model_cls),
        }

    # Explicit configuration: Build queries strictly
    queries_cfg = {}
    if has_queries_section:
        raw_queries = raw_config.get("queries") or {}
        if "list" in raw_queries:
            raw_list = raw_queries["list"]
            if isinstance(raw_list, dict):
                queries_cfg["list"] = {
                    "enabled": raw_list.get("enabled", True),
                    "name": raw_list.get("name"),
                    "return_cols": raw_list.get("return_cols", "__all__"),
                    "filter_fields": raw_list.get("filter_fields") or {},
                    "filter_depth": raw_list.get("filter_depth", 3),
                    "search_fields": raw_list.get("search_fields") or [],
                    "ordering_fields": raw_list.get("ordering_fields", "__all__"),
                    "pagination": raw_list.get("pagination", True),
                    "resolver": resolve_callable(raw_list.get("resolver")),
                    "get_queryset": resolve_callable(raw_list.get("get_queryset")),
                }
            elif raw_list is True:
                queries_cfg["list"] = build_default_queries_config(model_cls)["list"]

        if "extra" in raw_queries:
            extra_queries = {}
            for eq_name, eq_val in (raw_queries.get("extra") or {}).items():
                if isinstance(eq_val, dict):
                    extra_queries[eq_name] = {
                        "type": eq_val.get("type"),
                        "args": eq_val.get("args") or {},
                        "resolver": resolve_callable(eq_val.get("resolver")),
                    }
                else:
                    extra_queries[eq_name] = eq_val
            queries_cfg["extra"] = extra_queries

    # Explicit configuration: Build mutations strictly
    mutations_cfg = {}
    if has_mutations_section:
        raw_muts = raw_config.get("mutations") or {}
        for action in ("create", "update", "delete"):
            if action in raw_muts:
                cfg_val = raw_muts[action]
                if isinstance(cfg_val, dict):
                    mutations_cfg[action] = {
                        "enabled": cfg_val.get("enabled", True),
                        "name": cfg_val.get("name"),
                        "pk": cfg_val.get("pk", "id"),
                        "create_cols": cfg_val.get("create_cols", get_editable_fields(model_cls)),
                        "update_cols": cfg_val.get("update_cols", get_editable_fields(model_cls)),
                        "return_cols": cfg_val.get("return_cols", "__all__"),
                        "required_cols": cfg_val.get("required_cols"),
                        "before_save": resolve_callable(cfg_val.get("before_save")),
                        "after_save": resolve_callable(cfg_val.get("after_save")),
                        "before_delete": resolve_callable(cfg_val.get("before_delete")),
                        "after_delete": resolve_callable(cfg_val.get("after_delete")),
                        "custom_mutate": resolve_callable(cfg_val.get("mutate")),
                    }
                elif cfg_val is True:
                    mutations_cfg[action] = build_default_mutations_config(model_cls)[action]

        if "extra" in raw_muts:
            extra_muts = {}
            for em_name, em_val in (raw_muts.get("extra") or {}).items():
                if isinstance(em_val, dict):
                    extra_muts[em_name] = {
                        "mutate": resolve_callable(em_val.get("mutate")),
                        "type": em_val.get("type"),
                        "input": em_val.get("input"),
                    }
                else:
                    extra_muts[em_name] = em_val
            mutations_cfg["extra"] = extra_muts

    return {
        "model_cls": model_cls,
        "app_label": model_cls._meta.app_label,
        "queries": queries_cfg,
        "mutations": mutations_cfg,
    }
