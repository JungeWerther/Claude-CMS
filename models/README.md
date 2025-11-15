# Models Module

This module provides a validated model system that ensures parity between SQLAlchemy ORM models and Pydantic models.

## Features

- **Metaclass Validation**: Automatically ensures that for each Pydantic model, there exists a corresponding SQLAlchemy model with the same name
- **Transformation Utilities**: Helper functions to convert between SQLAlchemy and Pydantic models
- **Type Safety**: Full type hints for better IDE support and type checking

## Installation

Dependencies are managed in `pyproject.toml`:
- `sqlalchemy>=2.0.0`
- `pydantic>=2.0.0`

Install with:
```bash
uv sync
```

## Usage

### Defining Models

**Important**: Always define the SQLAlchemy model BEFORE the Pydantic model with the same name.

```python
from models import ValidatedBase, ValidatedPydanticModel
from sqlalchemy import Column, Integer, String
from pydantic import Field

# 1. Define SQLAlchemy model first
class User(ValidatedBase):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True)

# 2. Define Pydantic model with the same name
class User(ValidatedPydanticModel):
    id: int = Field(default=None)
    name: str = Field(..., max_length=100)
    email: str
```

### What Happens If You Don't Follow the Rules?

If you try to create a Pydantic model without a corresponding SQLAlchemy model:

```python
# This will raise AssertionError!
class Comment(ValidatedPydanticModel):
    id: int
    text: str

# AssertionError: Pydantic model 'Comment' has no corresponding SQLAlchemy model.
```

### Transformation Utilities

```python
from models.transformations import (
    sqlalchemy_to_pydantic,
    pydantic_to_sqlalchemy,
    sqlalchemy_list_to_pydantic,
    update_sqlalchemy_from_pydantic,
)

# Convert SQLAlchemy to Pydantic
user_orm = session.query(User).first()
user_pydantic = sqlalchemy_to_pydantic(user_orm, User)

# Convert Pydantic to SQLAlchemy
user_data = User(id=1, name="John", email="john@example.com")
user_orm = pydantic_to_sqlalchemy(user_data, User)

# Convert list of SQLAlchemy objects
users_orm = session.query(User).all()
users_pydantic = sqlalchemy_list_to_pydantic(users_orm, User)

# Update SQLAlchemy object from Pydantic
user_update = User(name="Jane")
updated_user = update_sqlalchemy_from_pydantic(user_orm, user_update)
```

### Database Setup

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base

# Create SQLite database
engine = create_engine('sqlite:///database.db', echo=True)

# Create all tables
Base.metadata.create_all(engine)

# Create session
Session = sessionmaker(bind=engine)
session = Session()
```

## Model Registry

You can inspect registered models:

```python
from models import get_model_registry

registry = get_model_registry()
print(registry['sqlalchemy_models'])  # ['User', 'Post', ...]
print(registry['pydantic_models'])    # ['User', 'Post', ...]
```

## Architecture

### Metaclasses

- **ValidatedSQLAlchemyMeta**: Registers SQLAlchemy models in a global registry
- **ValidatedPydanticMeta**: Validates that a corresponding SQLAlchemy model exists when a Pydantic model is defined

### Base Classes

- **ValidatedBase**: Extends SQLAlchemy's `DeclarativeBase` with validation tracking
- **ValidatedPydanticModel**: Extends Pydantic's `BaseModel` with validation that ensures SQLAlchemy model exists

### Why This Design?

This design enforces the pattern where:
1. Your database schema (SQLAlchemy) is the source of truth
2. Your API/validation layer (Pydantic) mirrors the schema
3. You can't accidentally create validation models without corresponding database models
4. Refactoring is safer - renaming a Pydantic model without renaming the SQLAlchemy model will fail immediately

## Example

See `models/example.py` for a complete example with User and Post models.
