"""HandBrake encoding profiles, one per source class.

Every number here comes from Wes's "Movie Encoding 2021" notes (docs/) and is
summarised in docs/encoding-profiles.md. Change a value here only with a
matching ADR or a note in that document.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum


class SourceClass(StrEnum):
    BLURAY = "bluray"
    DVD = "dvd"
    DVD_GRAINY = "dvd_grainy"
    PHONE = "phone"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Denoise:
    """HandBrake NLMeans denoise preset and tune, or ``None`` for no filter."""
    preset: str  # ultralight, light, medium, strong
    tune: str = "none"  # none, film, grain, highmotion, animation


@dataclass(frozen=True)
class Profile:
    name: str
    source: SourceClass
    rf: float                      # x265 constant-quality value (lower = better)
    rf_great: float                # the value Wes uses when the movie deserves it
    rf_range: tuple[float, float]  # the band seen to work in the notes
    denoise: Denoise | None
    deinterlace: bool              # comb-detect + decomb; only acts on combed frames
    notes: str = ""

    # Shared settings; the same for every profile
    container: str = "av_mkv"
    encoder: str = "x265_10bit"
    encoder_preset: str = "medium"
    encoder_tune: str = "fastdecode"
    encopts: str = "ref=4:bframes=8:rc-lookahead=60:subme=7:aq-mode=3"
    audio_lang: str = "eng"
    audio_encoder: str = "av_aac"
    audio_bitrate: int = 160
    audio_mixdown: str = "stereo"
    all_subtitles: bool = True
    foreign_audio_scan_burn: bool = True

    def with_rf(self, rf: float) -> "Profile":
        return replace(self, rf=rf)

    @property
    def great(self) -> "Profile":
        """The same profile at the 'great quality' RF Wes reserves for favourites."""
        return replace(self, rf=self.rf_great)


PROFILES: dict[SourceClass, Profile] = {
    SourceClass.BLURAY: Profile(
        name="bluray",
        source=SourceClass.BLURAY,
        rf=25, rf_great=21, rf_range=(24, 27),
        denoise=None,
        deinterlace=False,
        notes="Modern HD sources. 26 medium 'looks great'; 24 for the pretty ones. "
              "Washed-out or low-light films (Endgame, Captain Marvel, Arrival) want RF 20 or lower.",
    ),
    SourceClass.DVD: Profile(
        name="dvd",
        source=SourceClass.DVD,
        rf=20, rf_great=16, rf_range=(18, 22),
        denoise=Denoise("ultralight", "none"),
        deinterlace=True,
        notes="Good-quality DVDs. Men In Black, A Knight's Tale, Capaldi Doctor Who at 18-20 with NLMeans Ultralight/None.",
    ),
    SourceClass.DVD_GRAINY: Profile(
        name="dvd_grainy",
        source=SourceClass.DVD_GRAINY,
        rf=22, rf_great=18, rf_range=(20, 24),
        denoise=Denoise("light", "film"),
        deinterlace=True,
        notes="Old or poorly encoded DVDs. NLMeans Light or Ultralight with tune film; "
              "TMNT at 22-24. Unsharp caused edge distortion and is not used.",
    ),
    SourceClass.PHONE: Profile(
        name="phone",
        source=SourceClass.PHONE,
        rf=25, rf_great=21, rf_range=(23, 27),
        denoise=None,
        deinterlace=False,
        notes="Progressive high-bitrate phone video; treated like Blu-ray. Not yet tuned against a real sample.",
    ),
}


def profile_for(source: SourceClass) -> Profile:
    try:
        return PROFILES[source]
    except KeyError:
        raise ValueError(f"no encoding profile for source class {source!r}") from None
