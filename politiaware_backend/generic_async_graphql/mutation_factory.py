"""
Dynamic Mutation Generator for generic_async_graphql.
Builds async create, update, delete, and extra mutation fields for Strawberry GraphQL,
delegating database transactions to the db_operations service layer.
"""

from typing import Any, Callable, Dict, List, Optional, Tuple, Type
from dataclasses import asdict
import strawberry
from django.db import models

from .type_factory import (
    DeletePayload,
    get_or_create_payload_type,
    get_or_create_strawberry_type
)
from .input_factory import get_or_create_input_type
from .async_db_operations import (
    async_create_record,
    async_update_record,
    async_partial_update_record,
    async_delete_record
)


def _format_mutation_name(model_name: str, action: str) -> str:
    """Formats mutation name e.g. createLokSabha, updateLokSabha, deleteLokSabha."""
    clean_name = model_name[0].upper() + model_name[1:] if model_name else ""
    return f"{action.lower()}{clean_name}"


def create_async_create_field(
    model_cls: Type[models.Model],
    create_cols: List[str],
    return_cols: Any,
    required_cols: Optional[List[str]] = None,
    before_save: Optional[Callable] = None,
    after_save: Optional[Callable] = None,
    custom_mutate: Optional[Callable] = None
) -> Any:
    """Creates a Strawberry create mutation field delegating to db_operations.async_create_record."""
    item_type = get_or_create_strawberry_type(model_cls, return_cols=return_cols)
    payload_type = get_or_create_payload_type(model_cls, item_type)
    input_type = get_or_create_input_type(model_cls, create_cols, is_update=False, required_cols=required_cols)

    async def resolver(info: strawberry.Info, input: input_type) -> payload_type:
        if custom_mutate:
            return await custom_mutate(info, input=input)

        raw_dict = asdict(input) if input is not None else {}
        input_data = {k: v for k, v in raw_dict.items() if v is not None}
        instance, errors = await async_create_record(
            model_cls=model_cls,
            input_data=input_data,
            create_cols=create_cols,
            required_cols=required_cols,
            before_save=before_save,
            after_save=after_save,
            info=info
        )

        if errors:
            return payload_type(success=False, errors=errors, data=None)
        return payload_type(success=True, errors=None, data=instance)

    resolver.__annotations__ = {
        "info": strawberry.Info,
        "input": input_type,
        "return": payload_type,
    }

    return strawberry.field(
        resolver,
        description=f"Creates a new {model_cls.__name__} record asynchronously"
    )


def create_async_update_field(
    model_cls: Type[models.Model],
    update_cols: List[str],
    return_cols: Any,
    pk_field_name: str = "id",
    before_save: Optional[Callable] = None,
    after_save: Optional[Callable] = None,
    custom_mutate: Optional[Callable] = None
) -> Any:
    """Creates a Strawberry update mutation field delegating to db_operations.async_update_record."""
    item_type = get_or_create_strawberry_type(model_cls, return_cols=return_cols)
    payload_type = get_or_create_payload_type(model_cls, item_type)
    input_type = get_or_create_input_type(model_cls, update_cols, is_update=True)

    async def resolver(info: strawberry.Info, id: strawberry.ID, input: input_type) -> payload_type:
        if custom_mutate:
            return await custom_mutate(info, id=id, input=input)

        raw_dict = asdict(input) if input is not None else {}
        # Only update explicitly provided non-None fields
        input_data = {k: v for k, v in raw_dict.items() if v is not None}

        instance, errors = await async_update_record(
            model_cls=model_cls,
            pk_val=id,
            input_data=input_data,
            update_cols=update_cols,
            pk_field_name=pk_field_name,
            before_save=before_save,
            after_save=after_save,
            info=info
        )

        if errors:
            return payload_type(success=False, errors=errors, data=None)
        return payload_type(success=True, errors=None, data=instance)

    resolver.__annotations__ = {
        "info": strawberry.Info,
        "id": strawberry.ID,
        "input": input_type,
        "return": payload_type,
    }

    return strawberry.field(
        resolver,
        description=f"Updates an existing {model_cls.__name__} record asynchronously"
    )


def create_async_partial_update_field(
    model_cls: Type[models.Model],
    update_cols: List[str],
    return_cols: Any,
    pk_field_name: str = "id",
    before_save: Optional[Callable] = None,
    after_save: Optional[Callable] = None,
    custom_mutate: Optional[Callable] = None
) -> Any:
    """Creates a Strawberry partial update mutation field delegating to async_partial_update_record."""
    item_type = get_or_create_strawberry_type(model_cls, return_cols=return_cols)
    payload_type = get_or_create_payload_type(model_cls, item_type)
    input_type = get_or_create_input_type(model_cls, update_cols, is_update=True)

    async def resolver(info: strawberry.Info, id: strawberry.ID, input: input_type) -> payload_type:
        if custom_mutate:
            return await custom_mutate(info, id=id, input=input)

        raw_dict = asdict(input) if input is not None else {}
        input_data = {k: v for k, v in raw_dict.items() if v is not None}

        instance, errors = await async_partial_update_record(
            model_cls=model_cls,
            pk_val=id,
            input_data=input_data,
            update_cols=update_cols,
            pk_field_name=pk_field_name,
            before_save=before_save,
            after_save=after_save,
            info=info
        )

        if errors:
            return payload_type(success=False, errors=errors, data=None)
        return payload_type(success=True, errors=None, data=instance)

    resolver.__annotations__ = {
        "info": strawberry.Info,
        "id": strawberry.ID,
        "input": input_type,
        "return": payload_type,
    }

    return strawberry.field(
        resolver,
        description=f"Partially updates an existing {model_cls.__name__} record asynchronously"
    )


def create_async_delete_field(
    model_cls: Type[models.Model],
    pk_field_name: str = "id",
    before_delete: Optional[Callable] = None,
    after_delete: Optional[Callable] = None,
    custom_mutate: Optional[Callable] = None
) -> Any:
    """Creates a Strawberry delete mutation field delegating to db_operations.async_delete_record."""
    async def resolver(info: strawberry.Info, id: strawberry.ID) -> DeletePayload:
        if custom_mutate:
            return await custom_mutate(info, id=id)

        del_id, success, errors = await async_delete_record(
            model_cls=model_cls,
            pk_val=id,
            pk_field_name=pk_field_name,
            before_delete=before_delete,
            after_delete=after_delete,
            info=info
        )

        return DeletePayload(
            success=success,
            errors=errors,
            id=str(del_id) if del_id is not None else None
        )

    resolver.__annotations__ = {
        "info": strawberry.Info,
        "id": strawberry.ID,
        "return": DeletePayload,
    }

    return strawberry.field(
        resolver,
        description=f"Deletes a {model_cls.__name__} record asynchronously"
    )


def build_model_mutations(
    model_name: str,
    normalized_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Builds all mutation fields for a single model (create, update, delete, extra).
    Returns: { mutation_field_name: strawberry.field }
    """
    mutations_dict = {}
    model_cls = normalized_config["model_cls"]
    mutations_cfg = normalized_config.get("mutations") or {}

    # 1. Create Mutation
    create_cfg = mutations_cfg.get("create")
    if create_cfg and create_cfg.get("enabled", True):
        name = create_cfg.get("name") or _format_mutation_name(model_cls.__name__, "create")
        mutations_dict[name] = create_async_create_field(
            model_cls=model_cls,
            create_cols=create_cfg.get("create_cols", []),
            return_cols=create_cfg.get("return_cols", "__all__"),
            required_cols=create_cfg.get("required_cols"),
            before_save=create_cfg.get("before_save"),
            after_save=create_cfg.get("after_save"),
            custom_mutate=create_cfg.get("custom_mutate"),
        )

    # 2. Update Mutation
    update_cfg = mutations_cfg.get("update")
    if update_cfg and update_cfg.get("enabled", True):
        name = update_cfg.get("name") or _format_mutation_name(model_cls.__name__, "update")
        mutations_dict[name] = create_async_update_field(
            model_cls=model_cls,
            update_cols=update_cfg.get("update_cols", []),
            return_cols=update_cfg.get("return_cols", "__all__"),
            pk_field_name=update_cfg.get("pk", "id"),
            before_save=update_cfg.get("before_save"),
            after_save=update_cfg.get("after_save"),
            custom_mutate=update_cfg.get("custom_mutate"),
        )

    # 3. Partial Update Mutation (Optional)
    partial_update_cfg = mutations_cfg.get("partial_update")
    if partial_update_cfg and partial_update_cfg.get("enabled", True):
        name = partial_update_cfg.get("name") or _format_mutation_name(model_cls.__name__, "partialUpdate")
        mutations_dict[name] = create_async_partial_update_field(
            model_cls=model_cls,
            update_cols=partial_update_cfg.get("update_cols", []),
            return_cols=partial_update_cfg.get("return_cols", "__all__"),
            pk_field_name=partial_update_cfg.get("pk", "id"),
            before_save=partial_update_cfg.get("before_save"),
            after_save=partial_update_cfg.get("after_save"),
            custom_mutate=partial_update_cfg.get("custom_mutate"),
        )

    # 4. Delete Mutation
    delete_cfg = mutations_cfg.get("delete")
    if delete_cfg and delete_cfg.get("enabled", True):
        name = delete_cfg.get("name") or _format_mutation_name(model_cls.__name__, "delete")
        mutations_dict[name] = create_async_delete_field(
            model_cls=model_cls,
            pk_field_name=delete_cfg.get("pk", "id"),
            before_delete=delete_cfg.get("before_delete"),
            after_delete=delete_cfg.get("after_delete"),
            custom_mutate=delete_cfg.get("custom_mutate"),
        )

    # 4. Extra Mutations
    extra_cfg = mutations_cfg.get("extra") or {}
    for extra_name, extra_val in extra_cfg.items():
        if isinstance(extra_val, dict):
            extra_mutate = extra_val.get("mutate")
            if extra_mutate:
                mutations_dict[extra_name] = strawberry.field(extra_mutate)
        elif callable(extra_val):
            mutations_dict[extra_name] = strawberry.field(extra_val)

    return mutations_dict

