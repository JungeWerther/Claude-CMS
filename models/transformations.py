"""
Transformation utilities for converting between SQLAlchemy and Pydantic models.
"""

from typing import Type

from pydantic import BaseModel
from sqlalchemy.orm import DeclarativeBase


def sqlalchemy_to_pydantic[T: BaseModel](
    sqlalchemy_obj: DeclarativeBase, pydantic_model: Type[T]
) -> T:
    """
    Convert a SQLAlchemy model instance to a Pydantic model instance.

    Args:
        sqlalchemy_obj: The SQLAlchemy model instance to convert
        pydantic_model: The target Pydantic model class

    Returns:
        An instance of the Pydantic model

    Example:
        >>> user_orm = UserORM(id=1, name="John")
        >>> user_pydantic = sqlalchemy_to_pydantic(user_orm, User)
    """
    return pydantic_model.model_validate(sqlalchemy_obj)


def pydantic_to_sqlalchemy[T: DeclarativeBase](
    pydantic_obj: BaseModel,
    sqlalchemy_model: Type[T],
    exclude_unset: bool = False,
    exclude_none: bool = False,
) -> T:
    """
    Convert a Pydantic model instance to a SQLAlchemy model instance.

    Args:
        pydantic_obj: The Pydantic model instance to convert
        sqlalchemy_model: The target SQLAlchemy model class
        exclude_unset: Whether to exclude fields that were not explicitly set
        exclude_none: Whether to exclude fields with None values

    Returns:
        An instance of the SQLAlchemy model

    Example:
        >>> user_pydantic = User(id=1, name="John")
        >>> user_orm = pydantic_to_sqlalchemy(user_pydantic, UserORM)
    """
    data = pydantic_obj.model_dump(
        exclude_unset=exclude_unset, exclude_none=exclude_none
    )
    return sqlalchemy_model(**data)


__all__ = [
    "sqlalchemy_to_pydantic",
    "pydantic_to_sqlalchemy",
]
