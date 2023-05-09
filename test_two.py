
import pytest

from bot.database.schema import Language
from bot.database import localdatabase as db
from bot.booknames.parse import parse_bible_citation



@pytest.fixture
def language() -> Language:
    return db.get_language(code='S')


def test_get_books(language):
    assert len(db.get_books(language.id)) == 66


def test_search(language):
    print(parse_bible_citation('sal 1:1', language.id))


