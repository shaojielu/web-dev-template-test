from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """Base schema class with ORM mode (from_attributes) enabled."""

    model_config = ConfigDict(from_attributes=True)
