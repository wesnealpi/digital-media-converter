from fractions import Fraction
from pathlib import Path

import pytest

from dmc.probe import parse_ffprobe, ProbeError


def test_parses_video_geometry_and_rate(dvd_rip):
    v = dvd_rip.video
    assert (v.codec, v.width, v.height) == ("mpeg2video", 720, 480)
    assert v.frame_rate == Fraction(30000, 1001)
    assert v.fps == pytest.approx(29.97, abs=0.01)
    assert v.field_order == "tt"
    assert v.interlaced_flag is True


def test_progressive_is_not_flagged_interlaced(bluray_rip):
    assert bluray_rip.video.interlaced_flag is False


def test_container_is_first_name_only(bluray_rip, phone):
    assert bluray_rip.container == "matroska"
    assert phone.container == "mov"


def test_format_level_numbers(bluray_rip):
    assert bluray_rip.duration_s == pytest.approx(7814.5)
    assert bluray_rip.size_bytes == 28_500_000_000
    assert bluray_rip.bit_rate == 29_180_000


def test_audio_and_subtitle_streams(dvd_rip):
    assert [a.language for a in dvd_rip.audio] == ["eng", "fre"]
    assert dvd_rip.audio[0].channels == 6
    assert dvd_rip.audio[0].bit_rate == 448000
    assert [s.language for s in dvd_rip.subtitles] == ["eng", "spa"]


def test_forced_subtitle_disposition(bluray_rip):
    assert [s.forced for s in bluray_rip.subtitles] == [False, True]


def test_rotation_from_side_data(phone):
    assert phone.video.rotation == 270


def test_tags_are_lowercased(phone):
    assert phone.tags["com.apple.quicktime.make"] == "Apple"


def test_path_argument_wins_over_format_filename(dvd_rip_json):
    info = parse_ffprobe(dvd_rip_json, Path("C:/x/other.mkv"))
    assert info.path == Path("C:/x/other.mkv")


def test_missing_video_stream_raises():
    with pytest.raises(ProbeError):
        parse_ffprobe({"format": {}, "streams": [{"codec_type": "audio", "codec_name": "aac"}]})


def test_attached_picture_is_not_the_video_stream(dvd_rip_json):
    cover = {"index": 9, "codec_type": "video", "codec_name": "mjpeg", "width": 600, "height": 900,
             "disposition": {"attached_pic": 1}}
    dvd_rip_json["streams"].insert(0, cover)
    assert parse_ffprobe(dvd_rip_json).video.codec == "mpeg2video"


def test_zero_or_missing_frame_rate_does_not_crash(dvd_rip_json):
    dvd_rip_json["streams"][0]["avg_frame_rate"] = "0/0"
    dvd_rip_json["streams"][0]["r_frame_rate"] = "N/A"
    assert parse_ffprobe(dvd_rip_json).video.fps == 0.0
