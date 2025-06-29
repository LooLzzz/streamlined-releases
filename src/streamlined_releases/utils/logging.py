import logging
import traceback as tb
from logging import config as logging_config
from pathlib import Path

import yaml

from ..settings import app_settings

logger = logging.getLogger(__name__)
logger_set_up = False

LOG_CONFIG_FILEPATH = Path(__file__).parent.parent.parent.parent / 'logging.yaml'

__all__ = [
    "setup_logging",
]


def setup_logging(remove_existing_handlers: bool = False):
    global logger, logger_set_up

    if logger_set_up:
        logger.debug('Logging already set up, exiting early')
        return

    if remove_existing_handlers:
        root_logger = logging.getLogger()
        if root_logger.handlers:
            for handler in root_logger.handlers:
                root_logger.removeHandler(handler)

    if LOG_CONFIG_FILEPATH.exists():
        try:
            config = yaml.safe_load(LOG_CONFIG_FILEPATH.read_text())
            config['root']['level'] = app_settings.log_level
            logging_config.dictConfig(config)

        except Exception as e:
            tb.print_exc()
            print(f'Error while loading logging configuration file: {e!r}. Using default configs')
            logging.basicConfig(level=app_settings.log_level, force=True)

    else:
        tb.print_exc()
        print('Failed to load configuration file. Using default configs')
        logging.basicConfig(level=app_settings.log_level, force=True)

    logger_set_up = True
    logger = logging.getLogger(__name__)
    logger.info('Logging setup complete')
    logger.debug('Logging level set to %s', app_settings.log_level)
