from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings

__all__ = [
    "Settings",
    "app_settings",
]


class Inputs(BaseSettings):
    model_config = {
        'env_prefix': 'INPUT_',
        'populate_by_name': True,
    }

    my_number: Optional[int] = None


class Settings(BaseSettings):
    github_output: Path
    inputs: Inputs = Field(default_factory=Inputs)

    # @field_validator('github_output', mode='after')
    # @classmethod
    # def resolve_github_path(cls, value: Path):
    #     return value.resolve().absolute()


app_settings = Settings()
