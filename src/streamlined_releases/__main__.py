from .settings import app_settings


def set_github_action_output(**kwargs):
    with app_settings.github_output.open('a') as fp:
        for k, v in kwargs.items():
            fp.write(f'{k}={v}')


def main():
    ...


if __name__ == '__main__':
    main()
