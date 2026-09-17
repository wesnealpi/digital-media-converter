"""Plex movie file names: ``Title (Year) {imdb-ttNNNNNNN}.mkv``.

See https://support.plex.tv/articles/naming-and-organizing-your-movie-media-files/
The IMDb tag is optional but is what makes Plex matching exact, so the
pipeline keeps it whenever the source name or a lookup provides one.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_INVALID = re.compile(r'[<>:"/\\|?*]')
_NAME_RE = re.compile(
    r"^(?P<title>.+?)\s*"
    r"(?:\((?P<year>\d{4})\))?\s*"
    r"(?:\{imdb-(?P<imdb>tt\d{7,8})\}?)?\s*$"
)
_IMDB_ANYWHERE = re.compile(r"(tt\d{7,8})")
_MAKEMKV_SUFFIX = re.compile(r"[_\s-]*t\d{2}(?:[-_]\d+)?$", re.IGNORECASE)


@dataclass(frozen=True)
class MovieName:
    title: str
    year: int | None = None
    imdb_id: str | None = None

    def filename(self, ext: str = ".mkv") -> str:
        parts = [clean_title(self.title)]
        if self.year:
            parts.append(f"({self.year})")
        if self.imdb_id:
            parts.append(f"{{imdb-{self.imdb_id}}}")
        return " ".join(parts) + ext


def clean_title(title: str) -> str:
    title = _INVALID.sub("", title).strip().rstrip(".")
    return re.sub(r"\s+", " ", title)


def parse_stem(stem: str) -> MovieName:
    """Parse a file stem back into its parts.

    Tolerates the malformed tag ``{imdb-tt1745960`` (missing closing brace)
    seen in real output, and strips MakeMKV's ``_t00`` title suffix.
    """
    stem = _MAKEMKV_SUFFIX.sub("", stem.strip())
    m = _NAME_RE.match(stem)
    if not m:
        return MovieName(clean_title(stem))
    title = m.group("title")
    year = int(m.group("year")) if m.group("year") else None
    imdb = m.group("imdb")
    if imdb is None:
        found = _IMDB_ANYWHERE.search(stem)
        imdb = found.group(1) if found else None
        if found:
            title = stem[: found.start()].replace("{imdb-", "").strip()
            ym = re.search(r"\((\d{4})\)\s*$", title)
            if ym:
                year = int(ym.group(1))
                title = title[: ym.start()].strip()
    return MovieName(clean_title(title), year, imdb)
