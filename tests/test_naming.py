import pytest

from dmc.naming import MovieName, clean_title, parse_stem


@pytest.mark.parametrize("stem,title,year,imdb", [
    ("Spider-Man (2002) {imdb-tt0145487}", "Spider-Man", 2002, "tt0145487"),
    ("Vegas Vacation (1997) {imdb-tt0120434}", "Vegas Vacation", 1997, "tt0120434"),
    # real file in samples/expected is missing the closing brace
    ("Top Gun Maverick (2022) {imdb-tt1745960", "Top Gun Maverick", 2022, "tt1745960"),
    ("Dave (1993)", "Dave", 1993, None),
    ("Total Recall", "Total Recall", None, None),
    ("Vegas Vacation_t00", "Vegas Vacation", None, None),
    ("Men In Black T00-1", "Men In Black", None, None),
    ("A Knight's Tale (2001) {imdb-tt0183790}", "A Knight's Tale", 2001, "tt0183790"),
])
def test_parse_stem(stem, title, year, imdb):
    assert parse_stem(stem) == MovieName(title, year, imdb)


def test_filename_round_trip():
    n = MovieName("Top Gun Maverick", 2022, "tt1745960")
    assert n.filename() == "Top Gun Maverick (2022) {imdb-tt1745960}.mkv"
    assert parse_stem(n.filename()[:-4]) == n


def test_filename_without_optional_parts():
    assert MovieName("Dave").filename() == "Dave.mkv"
    assert MovieName("Dave", 1993).filename(".mp4") == "Dave (1993).mp4"


def test_clean_title_strips_windows_reserved_characters():
    assert clean_title('Who: Am I? <Test> "x"/y\\z|.') == "Who Am I Test xyz"
    assert clean_title("  Double   space  ") == "Double space"
