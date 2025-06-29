from logging import getLogger

from ..settings import app_settings

logger = getLogger(__name__)

__all__ = [
    "on_pull_request_merged",
]


def on_pull_request_merged():
    ...
