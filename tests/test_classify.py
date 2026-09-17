import pytest

from dmc import classify as c
from dmc.classify import Classification, classify, classify_by_metadata, parse_yavg, refine_with_grain
from dmc.profiles import SourceClass


def test_bluray_rip_is_bluray(bluray_rip):
    r = classify_by_metadata(bluray_rip)
    assert r.source is SourceClass.BLURAY
    assert "1920x1080" in r.reason


def test_dvd_rip_is_dvd(dvd_rip):
    assert classify_by_metadata(dvd_rip).source is SourceClass.DVD


def test_low_bitrate_dvd_leans_grainy(old_dvd_rip):
    r = classify_by_metadata(old_dvd_rip)
    assert r.source is SourceClass.DVD_GRAINY
    assert r.confidence < 0.8


def test_phone_video_is_phone(phone):
    r = classify_by_metadata(phone)
    assert r.source is SourceClass.PHONE
    assert r.confidence == 1.0


def test_hd_mp4_without_phone_markers_is_low_confidence_phone(phone_json):
    phone_json["format"]["tags"] = {}
    phone_json["streams"][0]["side_data_list"] = []
    phone_json["streams"][0]["avg_frame_rate"] = "24000/1001"
    from dmc.probe import parse_ffprobe
    r = classify_by_metadata(parse_ffprobe(phone_json))
    assert r.source is SourceClass.PHONE
    assert r.confidence < 1.0


def test_pal_dvd_geometry(dvd_rip_json):
    dvd_rip_json["streams"][0].update(height=576, avg_frame_rate="25/1")
    from dmc.probe import parse_ffprobe
    assert classify_by_metadata(parse_ffprobe(dvd_rip_json)).source is SourceClass.DVD


def test_already_encoded_output_still_classifies_by_geometry(encoded_output):
    """samples/expected files are HEVC at DVD size; they should read as DVD-ish, not unknown."""
    assert classify_by_metadata(encoded_output).source in {SourceClass.DVD, SourceClass.DVD_GRAINY}


def test_unknown_geometry(dvd_rip_json):
    dvd_rip_json["streams"][0].update(width=640, height=360, codec_name="h264")
    from dmc.probe import parse_ffprobe
    assert classify_by_metadata(parse_ffprobe(dvd_rip_json)).source is SourceClass.UNKNOWN


def test_parse_yavg_extracts_values():
    text = "frame:0 pts:1\nlavfi.signalstats.YAVG=3.250000\nfoo\nlavfi.signalstats.YAVG=4.75"
    assert parse_yavg(text) == [3.25, 4.75]


def test_refine_splits_dvd_on_threshold():
    base = Classification(SourceClass.DVD, "sd")
    assert refine_with_grain(base, 9.0, threshold=6.0).source is SourceClass.DVD_GRAINY
    assert refine_with_grain(base, 2.0, threshold=6.0).source is SourceClass.DVD
    assert refine_with_grain(base, 2.0).grain_score == 2.0


def test_refine_leaves_bluray_alone_and_keeps_score():
    base = Classification(SourceClass.BLURAY, "hd")
    out = refine_with_grain(base, 40.0)
    assert out.source is SourceClass.BLURAY
    assert out.grain_score == 40.0


def test_refine_without_score_keeps_metadata_decision(old_dvd_rip):
    base = classify_by_metadata(old_dvd_rip)
    assert refine_with_grain(base, None).source is base.source


def test_classify_measures_grain_only_for_sd(monkeypatch, dvd_rip, bluray_rip):
    calls = []
    monkeypatch.setattr(c, "grain_score", lambda path, dur: calls.append(path) or 12.0)
    assert classify(dvd_rip).source is SourceClass.DVD_GRAINY
    assert classify(bluray_rip).source is SourceClass.BLURAY
    assert calls == [dvd_rip.path]


def test_classify_can_skip_grain(monkeypatch, dvd_rip):
    monkeypatch.setattr(c, "grain_score", lambda *a: pytest.fail("should not measure"))
    assert classify(dvd_rip, measure_grain=False).source is SourceClass.DVD


def test_grain_score_returns_none_without_ffmpeg(monkeypatch, tmp_path):
    monkeypatch.setattr(c, "_ffmpeg_path", lambda: None)
    assert c.grain_score(tmp_path / "x.mkv", 100.0) is None
