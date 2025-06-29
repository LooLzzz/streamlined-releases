import subprocess
from logging import getLogger
from typing import Literal, Optional

import git

from ..settings import app_settings

logger = getLogger(__name__)

__all__ = [
    "bump_version",
    "generate_gitcliff_changelog_file",
    "get_gitcliff_bumped_version",
    "get_gitcliff_changelog_diff",
    "set_git_safe_directory",
    "upsert_branch",
]


def get_gitcliff_changelog_diff(
    bump: bool = True,
    unreleased: bool = True,
    strip: Optional[Literal['header', 'footer', 'all']] = None,
    prepend: bool = False,
    to_file: bool = False,
):
    args = ['git-cliff']

    if bump:
        args.append('--bump')

    if unreleased:
        args.append('--unreleased')

    if strip:
        args.extend(['--strip', strip])

    if prepend:
        args.extend(['--prepend', app_settings.changelog_filepath.as_posix()])

    if to_file:
        args.extend(['--output', app_settings.changelog_filepath.as_posix()])

    try:
        res = subprocess.run(
            # cwd=app_settings.github.workspace,
            args=args,
            check=True,
            capture_output=True,
            text=True,
        )

        return res.stdout.strip()

    except subprocess.CalledProcessError as exc:
        logger.error('Failed to generate changelog')
        logger.error('stdout: %s', exc.stdout)
        logger.error('stderr: %s', exc.stderr)
        raise


def generate_gitcliff_changelog_file():
    cmd = ['git-cliff', '--bump']

    if not app_settings.changelog_filepath.exists():
        # create a new changelog file
        cmd.extend([
            '-o', app_settings.changelog_filepath.as_posix(),
        ])
    else:
        # append to the existing changelog file
        cmd.extend([
            '--unreleased',
            '--prepend', app_settings.changelog_filepath.as_posix(),
        ])

    try:
        res = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
        )
        return res.stdout.strip()

    except subprocess.CalledProcessError as exc:
        logger.error('Failed to get bumped version from git cliff')
        logger.error('stdout: %s', exc.stdout)
        logger.error('stderr: %s', exc.stderr)
        raise


def get_gitcliff_bumped_version():
    try:
        res = subprocess.run(
            # cwd=app_settings.github.workspace,
            args=['git-cliff', '--bumped-version'],
            check=True,
            capture_output=True,
            text=True,
        )
        return res.stdout.strip()

    except subprocess.CalledProcessError as exc:
        logger.error('Failed to get bumped version from git cliff')
        logger.error('stdout: %s', exc.stdout)
        logger.error('stderr: %s', exc.stderr)
        raise


def upsert_branch(branch_name: str, base_ref: str):
    repo = git.Repo(app_settings.github.workspace)

    try:
        # Try to get the branch, catch IndexError if it doesn't exist
        _branch = repo.branches[branch_name]

    except IndexError:
        # If it doesn't exist, create it from the base ref
        logger.info("Creating branch '%s' from base ref '%s'", branch_name, base_ref)
        repo.git.checkout(base_ref, b=branch_name)
        repo.git.push('origin', '-u', branch_name)

    return branch_name


def set_git_safe_directory(dir: str):
    subprocess.run(
        args=['git', 'config', '--global', '--add', 'safe.directory', dir],
        check=True,
        capture_output=True,
        text=True,
    )


def bump_version(version: str,
                 target_ref: str,
                 do_commit: bool = True,
                 commit_changelog: bool = True,
                 commit_force: bool = False):
    """Bump the version in the current branch using `uv version`"""

    # checkout the target branch
    repo = git.Repo(app_settings.github.workspace)
    repo.git.checkout(target_ref)

    try:
        # do the bump
        res = subprocess.run(
            cwd=app_settings.github.workspace,
            args=[
                'uv', 'version', '--frozen', '--short', version,
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        semver = res.stdout.strip()
        logger.info("Bumped version to '%s'", semver)
    except subprocess.CalledProcessError as exc:
        logger.error('Failed to bump version using `uv version`')
        logger.error('stdout: %s', exc.stdout)
        logger.error('stderr: %s', exc.stderr)
        raise

    if do_commit:
        if commit_changelog:
            # generate the changelog
            logger.info('Generating changelog for version %s', version)
            generate_gitcliff_changelog_file()

        # commit changes if working tree is dirty
        if not repo.is_dirty():
            logger.info('No changes to commit, working tree is clean.')

        else:
            # commit the changes
            files_to_commit = [
                'pyproject.toml',
                # 'uv.lock',
                app_settings.changelog_filepath.as_posix(),
            ]
            logger.info('Committing changes to %s', files_to_commit)
            repo.git.add(*files_to_commit)

            actor = git.Actor(app_settings.bump_commit_actor.name, app_settings.bump_commit_actor.email)
            repo.index.commit(
                message=f'chore(release): Bumped version to {version}',
                author=actor,
                committer=actor,
            )

            # push to origin
            origin = repo.remote(name='origin')
            origin.push(
                refspec=f'{target_ref}:{target_ref}',
                force=commit_force,
            )
