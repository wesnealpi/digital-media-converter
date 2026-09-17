import pytest

from dmc.profiles import PROFILES, SourceClass, profile_for


def test_every_encodable_class_has_a_profile():
    for cls in SourceClass:
        if cls is SourceClass.UNKNOWN:
            continue
        assert profile_for(cls).source is cls


def test_unknown_has_no_profile():
    with pytest.raises(ValueError):
        profile_for(SourceClass.UNKNOWN)


@pytest.mark.parametrize("cls,rf,great", [
    (SourceClass.BLURAY, 25, 21),
    (SourceClass.DVD, 20, 16),
    (SourceClass.DVD_GRAINY, 22, 18),
])
def test_rf_values_match_wes_notes(cls, rf, great):
    """From the 'Medium' block in the 2021 notes: BluRay 25 (24-27) / 21 great, DVD 20 (18-22) / 16 great."""
    p = PROFILES[cls]
    assert p.rf == rf
    assert p.rf_great == great
    assert p.rf_range[0] <= p.rf <= p.rf_range[1]
    assert p.rf_great < p.rf


def test_shared_settings_are_identical_across_profiles():
    ref = PROFILES[SourceClass.BLURAY]
    for p in PROFILES.values():
        assert (p.container, p.encoder, p.encoder_preset, p.encoder_tune, p.encopts) == \
               ("av_mkv", "x265_10bit", "medium", "fastdecode", "ref=4:bframes=8:rc-lookahead=60:subme=7:aq-mode=3")
        assert (p.audio_encoder, p.audio_bitrate, p.audio_mixdown, p.audio_lang) == (ref.audio_encoder, 160, "stereo", "eng")


def test_dvd_profiles_denoise_and_deinterlace_but_bluray_does_not():
    assert PROFILES[SourceClass.BLURAY].denoise is None
    assert PROFILES[SourceClass.BLURAY].deinterlace is False
    assert PROFILES[SourceClass.DVD].denoise.preset == "ultralight"
    assert PROFILES[SourceClass.DVD].denoise.tune == "none"
    assert PROFILES[SourceClass.DVD].deinterlace is True
    assert PROFILES[SourceClass.DVD_GRAINY].denoise.tune == "film"


def test_great_and_with_rf_return_new_profiles():
    p = PROFILES[SourceClass.DVD]
    assert p.great.rf == 16 and p.rf == 20
    assert p.with_rf(12).rf == 12
    assert p.with_rf(12).denoise == p.denoise
