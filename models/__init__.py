"""
Models module with metaclass-enforced parity between SQLAlchemy and Pydantic models.
"""

from typing import Any, Dict, Type

from pydantic import BaseModel
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""

    pass


# Registry to track model pairs
_sqlalchemy_models: Dict[str, Type] = {}
_pydantic_models: Dict[str, Type[BaseModel]] = {}


class ValidatedPydanticMeta(type(BaseModel)):
    """
    Metaclass for Pydantic models that ensures a corresponding SQLAlchemy model exists.
    """

    def __new__(cls, name: str, bases: tuple, namespace: dict, **kwargs):
        cls = super().__new__(cls, name, bases, namespace, **kwargs)

        # Skip validation for BaseModel itself and abstract classes
        if name == "BaseModel" or namespace.get("__abstract__", False):
            return cls

        # Register the Pydantic model
        _pydantic_models[name] = cls

        # Check if corresponding SQLAlchemy model exists
        if name not in _sqlalchemy_models:
            raise AssertionError(
                f"Pydantic model '{name}' has no corresponding SQLAlchemy model. "
                f"Create a SQLAlchemy model with the same name first."
            )

        return cls


class ValidatedSQLAlchemyMeta(type(Base)):
    """
    Metaclass for SQLAlchemy models that registers them for Pydantic validation.
    """

    def __new__(cls, name: str, bases: tuple, namespace: dict, **kwargs):
        cls = super().__new__(cls, name, bases, namespace, **kwargs)

        # Skip registration for Base itself and abstract classes
        if name == "Base" or namespace.get("__abstract__", False):
            return cls

        # Register the SQLAlchemy model
        _sqlalchemy_models[name] = cls

        return cls


class ValidatedBase(Base, metaclass=ValidatedSQLAlchemyMeta):
    """
    Base class for SQLAlchemy models with validation tracking.
    """

    __abstract__ = True


class ValidatedPydanticModel(BaseModel, metaclass=ValidatedPydanticMeta):
    """
    Base class for Pydantic models with validation that ensures
    a corresponding SQLAlchemy model exists.
    """

    __abstract__ = True

    class Config:
        from_attributes = True


def get_model_registry():
    """
    Returns the current state of model registries.
    Useful for debugging and verification.
    """
    return {
        "sqlalchemy_models": list(_sqlalchemy_models.keys()),
        "pydantic_models": list(_pydantic_models.keys()),
    }


__all__ = [
    "Base",
    "ValidatedBase",
    "ValidatedPydanticModel",
    "get_model_registry",
]
