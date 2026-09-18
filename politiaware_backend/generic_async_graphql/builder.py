"""
Schema Builder orchestrator for generic_async_graphql.
Iterates over GRAPHQL_CONF, generates all async queries & mutations,
and returns a compiled Strawberry Schema.
"""

from typing import Any, Dict, List, Optional, Tuple, Type
import strawberry

from .model_loader import get_django_model
from .config_parser import normalize_model_config, resolve_callable
from .query_factory import build_model_queries
from .mutation_factory import build_model_mutations


def generate_generic_async_types(
    graphql_conf: Dict[str, Any]
) -> Tuple[Any, Optional[Any]]:
    """
    Parses GRAPHQL_CONF and dynamically creates Strawberry Query and Mutation classes.
    Returns: (QueryClass, MutationClass)
    """
    query_fields: Dict[str, Any] = {}
    mutation_fields: Dict[str, Any] = {}

    extra_query_classes: List[Any] = []
    extra_mutation_classes: List[Any] = []

    from .type_factory import get_or_create_strawberry_type

    normalized_models: List[Tuple[str, Dict[str, Any]]] = []

    for key, val in graphql_conf.items():
        if key == "__extra_queries__":
            if isinstance(val, (list, tuple)):
                for q_item in val:
                    resolved = resolve_callable(q_item)
                    if resolved and isinstance(resolved, type):
                        extra_query_classes.append(resolved)
            continue

        if key == "__extra_mutations__":
            if isinstance(val, (list, tuple)):
                for m_item in val:
                    resolved = resolve_callable(m_item)
                    if resolved and isinstance(resolved, type):
                        extra_mutation_classes.append(resolved)
            continue

        model_name = key
        raw_config = val or {}

        try:
            model_cls = get_django_model(
                model_identifier=model_name,
                app_label=raw_config.get("app_label") if isinstance(raw_config, dict) else None
            )
        except Exception as exc:
            raise LookupError(f"Could not load model for config key '{model_name}': {exc}") from exc

        normalized_config = normalize_model_config(
            model_identifier=model_name,
            raw_config=raw_config,
            model_cls=model_cls
        )

        # Pre-initialize top-level model types so all models have complete definitions with relationships
        list_cfg = normalized_config.get("queries", {}).get("list", {})
        return_cols = list_cfg.get("return_cols", "__all__") if list_cfg else "__all__"
        get_or_create_strawberry_type(model_cls, return_cols=return_cols, depth=2)

        normalized_models.append((model_name, normalized_config))

    for model_name, normalized_config in normalized_models:
        # 1. Build queries
        model_queries = build_model_queries(model_name, normalized_config)
        for q_name, q_field in model_queries.items():
            query_fields[q_name] = q_field

        # 2. Build mutations
        model_mutations = build_model_mutations(model_name, normalized_config)
        for m_name, m_field in model_mutations.items():
            mutation_fields[m_name] = m_field

    # Fallback dummy field if query is completely empty
    if not query_fields and not extra_query_classes:
        @strawberry.field
        def _health_check() -> str:
            return "OK"
        query_fields["_health_check"] = _health_check

    query_bases = tuple(extra_query_classes) if extra_query_classes else ()
    QueryCls = type("Query", query_bases, query_fields)
    StrawberryQuery = strawberry.type(QueryCls)

    if mutation_fields or extra_mutation_classes:
        mutation_bases = tuple(extra_mutation_classes) if extra_mutation_classes else ()
        MutationCls = type("Mutation", mutation_bases, mutation_fields)
        StrawberryMutation = strawberry.type(MutationCls)
    else:
        StrawberryMutation = None

    return StrawberryQuery, StrawberryMutation


def generate_generic_async_graphql(
    graphql_conf: Dict[str, Any],
    extensions: Optional[List[Any]] = None
) -> strawberry.Schema:
    """
    Main entry point for generic_async_graphql.
    Parses GRAPHQL_CONF, dynamically creates Query & Mutation types,
    and returns a compiled Strawberry Schema.

    Usage:
        schema = generate_generic_async_graphql(GRAPHQL_CONF)
    """
    Query, Mutation = generate_generic_async_types(graphql_conf)
    return strawberry.Schema(
        query=Query,
        mutation=Mutation,
        extensions=extensions or []
    )

