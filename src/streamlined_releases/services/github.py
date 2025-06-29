import re
from logging import getLogger

from ..settings import app_settings

logger = getLogger(__name__)

__all__ = [
    "create_pull_request",
    "is_rc_commit",
    "set_github_action_output",
]


def set_github_action_output(**kwargs):
    with app_settings.github.output.open('a') as fp:
        for k, v in kwargs.items():
            fp.write(f'{k}={v}')


def create_pull_request(head_ref: str, base_ref: str, title: str, body: str = None, **kwargs):
    gh = app_settings.github.get_client()
    repo = gh.get_repo(app_settings.github.repository)

    logger.info("Creating pull request '%s' from '%s' to '%s'", title, head_ref, base_ref)
    pr = repo.create_pull(
        base=base_ref,
        head=head_ref,
        title=title,
        body=body,
        **kwargs,
    )
    logger.info('Pull request (#%s) created: "%s"', pr.number, pr.html_url)
    return pr


def is_rc_commit(sha: str):
    gh = app_settings.github.get_client()
    repo = gh.get_repo(app_settings.github.repository)

    commit = repo.get_commit(sha)
    prs = commit.get_pulls()
    rc_branch_template = re.compile(r'^rc/(?P<version>.+)-(?P<ref>.+)$')

    for pr in prs:
        if pr.merged:
            if rc_branch_template.match(pr.head.ref):
                return True

    return False
