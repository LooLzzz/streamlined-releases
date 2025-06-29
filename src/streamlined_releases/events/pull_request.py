import re
from logging import getLogger

from github import GithubException

from ..services import get_gitcliff_changelog_diff
from ..settings import app_settings

logger = getLogger(__name__)

__all__ = [
    "on_pull_request_merged",
]


def on_pull_request_merged(version: str):
    """ 
    Create a new release from head_ref, if it doesn't already exist.

    Note:
      Checking for release existence is relevant because each PR merge from an RC branch will trigger this event.
      Usually when a PR is merged into the `dev` branch a new release should be created.
      On `stg` and `main` this won't do anything, as the release will already exist.
    """

    gh = app_settings.github.get_client()
    repo = gh.get_repo(app_settings.github.repository)
    release = None

    try:
        release = repo.get_release(version)
        logger.info("Release '%s' already exists, skipping creation", version)
    except GithubException as exc:
        if exc.status != 404:
            raise

    if release is None:
        logger.info('Generating changelog diff for release body')
        body = get_gitcliff_changelog_diff(
            bump=True,
            unreleased=True,
            strip='header',
        )

        logger.info("Creating release '%s' from '%s'", version, app_settings.github.head_ref)
        release = repo.create_git_tag_and_release(
            tag=version,
            tag_message=version,
            release_name=version,
            release_message=body,
            object=app_settings.github.sha,
            type='commit',
        )

    return release
