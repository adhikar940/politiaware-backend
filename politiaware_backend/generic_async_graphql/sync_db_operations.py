"""
Synchronous Database Operations Service Layer for generic_async_graphql.
Encapsulates all blocking Django ORM write operations (create, update, partial update, delete)
inside thread-safe, atomic transactions with full model validation and lifecycle hooks.
These operations are always maintained strictly synchronous.
"""

from typing import Any, Callable, Dict, List, Optional, Tuple, Type
from django.core.exceptions import ValidationError
from django.db import models, transaction

from .model_loader import get_field_by_name


def assign_model_fields(instance: models.Model, data_dict: Dict[str, Any], allowed_cols: List[str]):
    """
    Safely assigns dictionary values to a Django model instance,
    handling ForeignKeys (assigning _id) and direct attributes.
    """
    for col, val in data_dict.items():
        if col not in allowed_cols:
            continue
        field_obj = get_field_by_name(instance.__class__, col)

        if isinstance(field_obj, (models.ForeignKey, models.OneToOneField)):
            if isinstance(val, (int, str)) or val is None:
                setattr(instance, f"{field_obj.name}_id", val)
            else:
                setattr(instance, field_obj.name, val)
        else:
            setattr(instance, col, val)


def get_clean_exclude_fields(
    model_cls: Type[models.Model],
    input_data: Dict[str, Any],
    required_cols: Optional[List[str]] = None
) -> List[str]:
    """
    Determines which fields to exclude from full_clean validation if not provided in input_data.
    Excludes nullable/optional unsupplied fields.
    """
    required_cols = required_cols or []
    exclude = []
    for field in model_cls._meta.get_fields():
        if not hasattr(field, "name") or field.name in input_data or field.name in required_cols:
            continue
        if getattr(field, "null", False) or getattr(field, "blank", False) or getattr(field, "has_default", lambda: False)():
            exclude.append(field.name)
    return exclude


# ---------------------------------------------------------------------------
# SYNCHRONOUS WRITE OPERATIONS (ALWAYS SYNC)
# ---------------------------------------------------------------------------

def sync_create_record(
    model_cls: Type[models.Model],
    input_data: Dict[str, Any],
    create_cols: List[str],
    required_cols: Optional[List[str]] = None,
    before_save: Optional[Callable] = None,
    after_save: Optional[Callable] = None,
    info: Optional[Any] = None
) -> Tuple[Optional[models.Model], Optional[List[str]]]:
    """
    Synchronously creates a new model record inside an atomic transaction.
    Returns: (instance, errors)
    """
    required_cols = required_cols or []

    try:
        with transaction.atomic():
            instance = model_cls()
            assign_model_fields(instance, input_data, create_cols)

            if before_save:
                before_save(instance, info, input_data)

            exclude_fields = get_clean_exclude_fields(model_cls, input_data, required_cols)
            instance.full_clean(exclude=exclude_fields if exclude_fields else None)
            instance.save()

            if after_save:
                after_save(instance, info)
            return instance, None
    except ValidationError as ve:
        errors = []
        if hasattr(ve, "message_dict"):
            for f, msgs in ve.message_dict.items():
                errors.extend([f"{f}: {m}" for m in msgs])
        else:
            errors = list(ve.messages)
        return None, errors
    except Exception as e:
        return None, [str(e)]


def sync_update_record(
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
    Synchronously updates an existing model record inside an atomic transaction.
    Returns: (instance, errors)
    """
    try:
        with transaction.atomic():
            try:
                instance = model_cls.objects.get(**{pk_field_name: pk_val})
            except model_cls.DoesNotExist:
                raise ValueError(f"{model_cls.__name__} with {pk_field_name}='{pk_val}' does not exist.")

            assign_model_fields(instance, input_data, update_cols)

            if before_save:
                before_save(instance, info, input_data)

            exclude_fields = get_clean_exclude_fields(model_cls, input_data, [])
            instance.full_clean(exclude=exclude_fields if exclude_fields else None)
            instance.save()

            if after_save:
                after_save(instance, info)
            return instance, None
    except ValidationError as ve:
        errors = []
        if hasattr(ve, "message_dict"):
            for f, msgs in ve.message_dict.items():
                errors.extend([f"{f}: {m}" for m in msgs])
        else:
            errors = list(ve.messages)
        return None, errors
    except Exception as e:
        return None, [str(e)]


def sync_partial_update_record(
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
    Synchronously applies a partial update (PATCH) to an existing model record,
    modifying and validating only explicitly provided non-None fields.
    Returns: (instance, errors)
    """
    try:
        with transaction.atomic():
            try:
                instance = model_cls.objects.get(**{pk_field_name: pk_val})
            except model_cls.DoesNotExist:
                raise ValueError(f"{model_cls.__name__} with {pk_field_name}='{pk_val}' does not exist.")

            # Filter only fields provided in input_data that are allowed in update_cols
            partial_data = {k: v for k, v in input_data.items() if v is not None and k in update_cols}
            assign_model_fields(instance, partial_data, list(partial_data.keys()))

            if before_save:
                before_save(instance, info, partial_data)

            # Exclude fields not supplied in partial_data from validation
            provided_fields = set(partial_data.keys())
            exclude_fields = [
                f.name for f in model_cls._meta.get_fields()
                if hasattr(f, "name") and f.name not in provided_fields
            ]
            instance.full_clean(exclude=exclude_fields if exclude_fields else None)
            instance.save()

            if after_save:
                after_save(instance, info)
            return instance, None
    except ValidationError as ve:
        errors = []
        if hasattr(ve, "message_dict"):
            for f, msgs in ve.message_dict.items():
                errors.extend([f"{f}: {m}" for m in msgs])
        else:
            errors = list(ve.messages)
        return None, errors
    except Exception as e:
        return None, [str(e)]


def sync_delete_record(
    model_cls: Type[models.Model],
    pk_val: Any,
    pk_field_name: str = "id",
    before_delete: Optional[Callable] = None,
    after_delete: Optional[Callable] = None,
    info: Optional[Any] = None
) -> Tuple[Optional[Any], bool, Optional[List[str]]]:
    """
    Synchronously deletes a model record inside an atomic transaction.
    Returns: (deleted_id, success, errors)
    """
    try:
        with transaction.atomic():
            try:
                instance = model_cls.objects.get(**{pk_field_name: pk_val})
            except model_cls.DoesNotExist:
                raise ValueError(f"{model_cls.__name__} with {pk_field_name}='{pk_val}' does not exist.")

            if before_delete:
                before_delete(instance, info)

            instance.delete()

            if after_delete:
                after_delete(pk_val, info)
            return pk_val, True, None
    except Exception as e:
        return pk_val, False, [str(e)]

