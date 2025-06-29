import re
from logging import getLogger

import git

from ..services import (bump_version, create_pull_request, get_gitcliff_bumped_version, get_gitcliff_changelog_diff,
                        upsert_branch)
from ..settings import app_settings

logger = getLogger(__name__)

__all__ = [
    "on_push",
]


def on_push():
    gh = app_settings.github.get_client()
    gh_repo = gh.get_repo(app_settings.github.repository)
    bumped_version = get_gitcliff_bumped_version()
    rc_branch_name = f'rc/{bumped_version}-{app_settings.github.ref_name}'
    rc_branch_template = re.compile(rf'^rc/(?P<version>.+)-{app_settings.github.ref_name}$')

    logger.info("Bumped version: '%s'", bumped_version)

    pull_requests = gh_repo.get_pulls()
    rc_pr = None
    rc_pr_version = None

    for pr in pull_requests:
        if m := rc_branch_template.match(pr.head.ref):
            logger.info("Found active RC pull request (#%s) from '%s'", pr.number, pr.head.ref)
            rc_pr_version = m.group('version')
            rc_pr = pr
            break

    # validate the version in the pull request
    if rc_pr and rc_pr_version != bumped_version:
        logger.warning(
            "Version mismatch in RC pull request (#%s): expected '%s', found '%s'. Closing previous pull request",
            rc_pr.number, bumped_version, rc_pr_version
        )
        rc_pr.edit(state='closed')
        rc_pr = None

    logger.info('Generating changelog diff for pull request body')
    body = get_gitcliff_changelog_diff(
        bump=True,
        unreleased=True,
        strip='header',
        prepend=False,
    )

    # replace 'bumped_version' to 'rc_branch_name' in the comparison url as the bumped version tag is not yet created
    # i.e replace 'v1.0.0...v1.0.1' with 'v1.0.0...rc/v1.0.1-dev'
    body = body.replace(f'...{bumped_version}', f'...{rc_branch_name}')
    logger.debug('Pull request body:\n%s', body)

    if rc_pr is None:
        logger.info("No existing pull request found for branch '%s'", rc_branch_name)
        logger.info("Creating pull request for release candidate branch '%s'", rc_branch_name)

        # create the release candidate branch if it doesn't exist
        upsert_branch(
            branch_name=f'rc/{bumped_version}-{app_settings.github.ref_name}',
            base_ref=app_settings.github.ref_name,
        )

        # add bumped version to the branch
        bump_version(
            version=bumped_version,
            target_ref=rc_branch_name,
            do_commit=True,
        )

        # create the initial pull request
        rc_pr = create_pull_request(
            head_ref=rc_branch_name,
            base_ref=app_settings.github.ref_name,
            title=f'[Release Candidate] {bumped_version}-{app_settings.github.ref_name} 🚀',
            body=body,
        )

    else:
        logger.info("Pull request (#%s) already exists for branch '%s'", rc_pr.number, rc_branch_name)
        logger.info('Updating pull request (#%s) with new changes', rc_pr.number)

        # move branch head to the latest commit on the base branch
        repo = git.Repo(app_settings.github.workspace)
        repo.git.reset('--hard', rc_pr.head.sha)

        # add bumped version to the branch
        bump_version(
            version=bumped_version,
            target_ref=rc_branch_name,
            do_commit=True,
            commit_force=True,
        )

        # update the pull request with the new changes
        rc_pr.edit(
            title=f'[Release Candidate] {bumped_version}-{app_settings.github.ref_name} 🚀',
            body=body,
        )
