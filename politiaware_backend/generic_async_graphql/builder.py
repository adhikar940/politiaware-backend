"""
Schema Builder orchestrator for generic_async_graphql.
Iterates over GRAPHQL_CONF or TOML configuration, generates all async queries & mutations,
and returns a compiled Strawberry Schema.
"""

from typing import Any, Dict, List, Optional, Tuple, Type

try:
    import strawberry
    HAS_STRAWBERRY = True
    _strawberry_type_dec = strawberry.type
    _strawberry_field = strawberry.field
except ImportError:
    strawberry = None
    HAS_STRAWBERRY = False
    _strawberry_type_dec = lambda c, *args, **kwargs: c
    _strawberry_field = lambda f, *args, **kwargs: f

from politiaware_backend.generic_async_graphql.model_loader import get_django_model
from politiaware_backend.generic_async_graphql.config_parser import normalize_model_config, resolve_callable
from politiaware_backend.generic_async_graphql.query_factory import build_model_queries
from politiaware_backend.generic_async_graphql.mutation_factory import build_model_mutations

try:
    from politiaware_backend.conf.conf_loader import config
except ImportError:
    config = {}


def generate_generic_async_types(
    graphql_conf: Optional[Dict[str, Any]] = None
) -> Tuple[Any, Optional[Any]]:
    """
    Parses GRAPHQL_CONF or TOML [graphql.models] and dynamically creates Strawberry Query and Mutation classes.
    Returns: (QueryClass, MutationClass)
    """
    if graphql_conf is None:
        toml_models = config.get("graphql", {}).get("models", {}) if isinstance(config, dict) else {}
        graphql_conf = {k: {} for k in toml_models.keys()}

    query_fields: Dict[str, Any] = {}
    mutation_fields: Dict[str, Any] = {}

    extra_query_classes: List[Any] = []
    extra_mutation_classes: List[Any] = []

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
        def _health_check() -> str:
            return "OK"
        query_fields["_health_check"] = _strawberry_field(_health_check)

    query_bases = tuple(extra_query_classes) if extra_query_classes else ()
    QueryCls = type("Query", query_bases, query_fields)
    StrawberryQuery = _strawberry_type_dec(QueryCls)

    if mutation_fields or extra_mutation_classes:
        mutation_bases = tuple(extra_mutation_classes) if extra_mutation_classes else ()
        MutationCls = type("Mutation", mutation_bases, mutation_fields)
        StrawberryMutation = _strawberry_type_dec(MutationCls)
    else:
        StrawberryMutation = None

    return StrawberryQuery, StrawberryMutation


def generate_generic_async_graphql(
    graphql_conf: Optional[Dict[str, Any]] = None,
    extensions: Optional[List[Any]] = None
) -> Any:
    """
    Main entry point for generic_async_graphql.
    Parses GRAPHQL_CONF or TOML config, dynamically creates Query & Mutation types,
    and returns a compiled Strawberry Schema.

    Usage:
        schema = generate_generic_async_graphql()  # reads from TOML
        # OR
        schema = generate_generic_async_graphql(GRAPHQL_CONF)
    """
    if not HAS_STRAWBERRY:
        raise ImportError(
            "Strawberry GraphQL is not installed in the current environment. "
            "Please install it using: pip install 'strawberry-graphql[django]'"
        )

    Query, Mutation = generate_generic_async_types(graphql_conf)
    return strawberry.Schema(
        query=Query,
        mutation=Mutation,
        extensions=extensions or []
    )
