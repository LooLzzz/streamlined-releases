import json
from functools import lru_cache
from pathlib import Path
from typing import Literal, NamedTuple, Optional

from github import Auth, Github
from pydantic import Field, computed_field, model_validator
from pydantic_settings import BaseSettings

__all__ = [
    "Settings",
    "app_settings",
]


class ActorTuple(NamedTuple):
    name: str
    email: str


class Inputs(BaseSettings):
    model_config = {'env_prefix': 'INPUT_'}

    git_username: Optional[str] = None
    git_email: Optional[str] = None
    bump_commit_message: Optional[str] = None
    changelog_filepath: Optional[Path] = None
    main_branch: Optional[str] = None
    staging_branch: Optional[str] = None
    dev_branch: Optional[str] = None

    @property
    def bump_commit_actor(self) -> Optional[ActorTuple]:
        if self.git_username and self.git_email:
            return ActorTuple(self.git_username, self.git_email)
        return None


class GithubEnv(BaseSettings):
    """taken from https://docs.github.com/en/actions/how-tos/writing-workflows/choosing-what-your-workflow-does/store-information-in-variables#default-environment-variables"""

    model_config = {'env_prefix': 'GITHUB_'}

    action_path: Optional[Path] = None
    action_repository: Optional[str] = None
    action: Optional[str] = None
    actor_id: Optional[str] = None
    actor: Optional[str] = None
    api_url: str = 'https://api.github.com'
    base_ref: Optional[str] = None
    env: Optional[Path] = None
    event_name: Optional[str] = None
    event_path: Optional[Path] = None
    graphql_url: str = 'https://api.github.com/graphql'
    head_ref: Optional[str] = None
    job: Optional[str] = None
    output: Optional[Path] = None
    path: Optional[Path] = None
    ref_name: Optional[str] = None
    ref_protected: Optional[str] = None
    ref_type: Optional[Literal['branch', 'tag']] = None
    ref: Optional[str] = None
    repository_id: Optional[str] = None
    repository_owner_id: Optional[str] = None
    repository_owner: Optional[str] = None
    repository: Optional[str] = None
    retention_days: Optional[int] = None
    run_attempt: Optional[int] = None
    run_id: Optional[str] = None
    run_number: Optional[int] = None
    server_url: str = 'https://github.com'
    sha: Optional[str] = None
    step_summary: Optional[Path] = None
    token: Optional[str] = None
    triggering_actor: Optional[str] = None
    workflow_ref: Optional[str] = None
    workflow_sha: Optional[str] = None
    workflow: Optional[str] = None
    workspace: Optional[Path] = None

    def __hash__(self):
        """Override hash to allow caching."""
        d = self.model_dump(exclude_none=True)
        return hash(tuple(sorted(d.items())))

    @computed_field
    @property
    def event_action(self) -> Optional[str]:
        return self.event_payload.get('action', None)

    @property
    def event_payload(self) -> dict:
        return json.loads(
            self.event_path.read_text()
            if self.event_path and self.event_path.exists()
            else '{}'
        )

    @property
    def pull_request_number(self) -> Optional[int]:
        pr_payload: dict = self.event_payload.get('pull_request', {})
        number = pr_payload.get('number', None)
        return int(number) if number is not None else None

    @property
    def pull_request_merged(self) -> Optional[bool]:
        pr_payload: dict = self.event_payload.get('pull_request', {})
        return pr_payload.get('merged', None)

    @lru_cache(maxsize=1)
    def get_client(self):
        if not self.token:
            raise ValueError('GitHub token is missing from environment variables.')

        return Github(
            base_url=self.api_url,
            auth=Auth.Token(self.token),
        )


class Settings(BaseSettings):
    model_config = {
        'populate_by_name': True,
        'validate_default': True,
    }

    runner_debug: bool = False
    changelog_filepath: Path = 'CHANGELOG.md'
    bump_commit_actor: ActorTuple = ('github-actions[bot]', 'github-actions[bot]@users.noreply.github.com')
    bump_commit_message: str = 'chore(release): Bumped version to {version}'

    main_branch: str = 'main'
    staging_branch: str = 'stg'
    dev_branch: str = 'dev'

    github: GithubEnv = Field(default_factory=GithubEnv)
    inputs: Inputs = Field(default_factory=Inputs)

    @model_validator(mode='after')
    def _apply_input_overrides(self):
        direct_overrides = [
            'bump_commit_actor',
            'bump_commit_message',
            'changelog_filepath',
            'dev_branch',
            'main_branch',
            'staging_branch',
        ]

        for field in direct_overrides:
            if field not in self.model_fields_set:
                if v := getattr(self.inputs, field, None):
                    setattr(self, field, v)

        return self

    @property
    def release_branches(self):
        return [
            self.main_branch,
            self.staging_branch,
            self.dev_branch,
        ]

    @property
    def log_level(self):
        return 'DEBUG' if self.runner_debug else 'INFO'


app_settings = Settings()
