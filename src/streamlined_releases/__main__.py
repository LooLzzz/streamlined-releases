import re
from logging import getLogger

from .events import on_pull_request_merged, on_push
from .services import is_rc_commit, set_git_safe_directory
from .settings import app_settings
from .utils import setup_logging

logger = getLogger(__name__)


def main():
    setup_logging()

    logger.info('-- Streamlined Releases --')
    logger.debug(
        'Streamlined Releases started with settings: %s',
        app_settings.model_dump_json(indent=2, exclude_none=True),
    )

    logger.debug("Setting '*' as safe directory in git config")
    set_git_safe_directory('*')

    match app_settings.github.event_name:
        case 'push' if app_settings.github.actor == app_settings.bump_commit_actor.name:
            logger.info('Skipping push event from the bump commit actor: %s', app_settings.bump_commit_actor.name)

        case 'push' if app_settings.github.ref_name not in app_settings.release_branches:
            logger.info("Skipping push event from non-release branch '%s'", app_settings.github.ref_name)

        case 'push' if is_rc_commit(app_settings.github.sha):
            logger.info(
                "Skipping push event from rc merge commit '%s' on branch '%s'",
                app_settings.github.sha, app_settings.github.ref_name,
            )

        case 'push':
            # means a push to a release branch
            on_push()

        case 'pull_request' if all((app_settings.github.event_action == 'closed',
                                    app_settings.github.pull_request_merged is True)):
            head_ref: str = app_settings.github.head_ref
            rc_branch_template = re.compile(r'rc/(?P<version>.+)-(?P<ref>.+)$')

            if m := rc_branch_template.match(head_ref):
                # means the PR was merged to the ref branch
                version = m.group('version')
                on_pull_request_merged(version)

            else:
                logger.info(
                    "Skipping pull request event: head ref '%s' does not match the expected rc branch pattern",
                    head_ref,
                )

        case _:
            logger.info(
                "Nothing to do, skipping event: %s %s",
                app_settings.github.event_name,
                f'({v})' if (v := app_settings.github.event_action) else '',
            )


if __name__ == '__main__':
    main()
