import logging

from .utils import (
    BIBLE_BOOKALIAS_NUM,
    BIBLE_NUM_BOOKALIAS,
    list_of_lists,
    BIBLE_BOOKNAMES,
    safechars,
    parse_bible_pattern,
    parse_booknum,
    parse_chapter,
    parse_verses,
    seems_bible,
    BooknumNotFound,
    MultipleBooknumsFound,
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)

# https://stackoverflow.com/a/879937/9505959
class NoParsingFilter(logging.Filter):
    def filter(self, record):
        return not record.getMessage().startswith('parsing')


def create_logger(name):
    logger = logging.getLogger(__name__)
    logger.addFilter(NoParsingFilter())
    return logger