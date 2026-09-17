from pathlib import Path

import pytest

from dmc.handbrake import build_command, parse_progress
from dmc.profiles import PROFILES, SourceClass


def _opt(cmd, flag):
    """Value following ``flag`` in argv."""
    return cmd[cmd.index(flag) + 1]


@pytest.fixture
def dvd_cmd():
    return build_command(Path("in/Vegas Vacation_t00.mkv"), Path("out/Vegas Vacation (1997).mkv"),
                         PROFILES[SourceClass.DVD], subtitle_count=2)


def test_io_and_container(dvd_cmd):
    assert dvd_cmd[0] == "HandBrakeCLI"
    assert _opt(dvd_cmd, "-i").endswith("Vegas Vacation_t00.mkv")
    assert _opt(dvd_cmd, "-o").endswith("Vegas Vacation (1997).mkv")
    assert _opt(dvd_cmd, "-f") == "av_mkv"


def test_video_settings_from_notes(dvd_cmd):
    assert _opt(dvd_cmd, "-e") == "x265_10bit"
    assert _opt(dvd_cmd, "--encoder-preset") == "medium"
    assert _opt(dvd_cmd, "--encoder-tune") == "fastdecode"
    assert _opt(dvd_cmd, "-x") == "ref=4:bframes=8:rc-lookahead=60:subme=7:aq-mode=3"
    assert _opt(dvd_cmd, "-q") == "20"
    assert "--vfr" in dvd_cmd


def test_audio_is_single_english_stereo_aac(dvd_cmd):
    assert _opt(dvd_cmd, "--audio-lang-list") == "eng"
    assert "--first-audio" in dvd_cmd
    assert _opt(dvd_cmd, "-E") == "av_aac"
    assert _opt(dvd_cmd, "-B") == "160"
    assert _opt(dvd_cmd, "--mixdown") == "stereo"
    assert "--audio-copy-mask" not in dvd_cmd  # no passthrough


def test_subtitles_scan_first_then_every_source_track(dvd_cmd):
    """Verified 2026-09-17 on a Blu-ray rip: explicit track list keeps all tracks AND runs the scan;
    --all-subtitles keeps them but skips the foreign audio search."""
    assert _opt(dvd_cmd, "-s") == "scan,1,2"
    assert "--subtitle-forced=1" in dvd_cmd
    assert "--subtitle-burned=1" in dvd_cmd
    assert "--all-subtitles" not in dvd_cmd


def test_eleven_subtitle_tracks_are_all_listed():
    cmd = build_command("a", "b", PROFILES[SourceClass.BLURAY], subtitle_count=11)
    assert _opt(cmd, "-s") == "scan," + ",".join(str(i) for i in range(1, 12))


def test_source_without_subtitles_still_gets_scan_track():
    cmd = build_command("a", "b", PROFILES[SourceClass.BLURAY])
    assert _opt(cmd, "-s") == "scan"


def test_profile_without_scan_or_subtitles():
    from dataclasses import replace
    p = replace(PROFILES[SourceClass.BLURAY], foreign_audio_scan_burn=False, all_subtitles=False)
    assert _opt(build_command("a", "b", p, subtitle_count=3), "-s") == "none"
    p = replace(PROFILES[SourceClass.BLURAY], foreign_audio_scan_burn=False)
    cmd = build_command("a", "b", p, subtitle_count=3)
    assert _opt(cmd, "-s") == "1,2,3" and "--subtitle-burned=1" not in cmd


def test_dvd_gets_decomb_and_ultralight_nlmeans(dvd_cmd):
    assert "--comb-detect" in dvd_cmd and "--decomb" in dvd_cmd
    assert "--nlmeans=ultralight" in dvd_cmd
    assert _opt(dvd_cmd, "--nlmeans-tune") == "none"


def test_grainy_dvd_uses_light_film():
    cmd = build_command("a", "b", PROFILES[SourceClass.DVD_GRAINY])
    assert "--nlmeans=light" in cmd
    assert _opt(cmd, "--nlmeans-tune") == "film"
    assert _opt(cmd, "-q") == "22"


def test_bluray_has_no_filters():
    cmd = build_command("a", "b", PROFILES[SourceClass.BLURAY])
    assert not any(a.startswith("--nlmeans") for a in cmd)
    assert "--decomb" not in cmd and "--comb-detect" not in cmd
    assert _opt(cmd, "-q") == "25"


def test_rf_override_and_great():
    assert _opt(build_command("a", "b", PROFILES[SourceClass.BLURAY].great), "-q") == "21"
    assert _opt(build_command("a", "b", PROFILES[SourceClass.BLURAY].with_rf(19.5)), "-q") == "19.5"


def test_title_selection_and_exe_override():
    cmd = build_command("a", "b", PROFILES[SourceClass.DVD], exe=r"C:\hb\HandBrakeCLI.exe", title=3)
    assert cmd[0] == r"C:\hb\HandBrakeCLI.exe"
    assert _opt(cmd, "-t") == "3"


def test_clip_window_flags():
    cmd = build_command("a", "b", PROFILES[SourceClass.BLURAY], clip=(600, 60))
    assert _opt(cmd, "--start-at") == "seconds:600"
    assert _opt(cmd, "--stop-at") == "seconds:60"
    assert "--start-at" not in build_command("a", "b", PROFILES[SourceClass.BLURAY])


def test_no_option_value_is_empty(dvd_cmd):
    assert all(part != "" for part in dvd_cmd)


@pytest.mark.parametrize("line,pct", [
    ("Encoding: task 1 of 1, 12.34 % (45.67 fps, avg 40.00 fps, ETA 00h10m00s)", 12.34),
    ("Encoding: task 2 of 2, 100.00 %", 100.0),
    ("Muxing: this may take awhile...", None),
])
def test_parse_progress(line, pct):
    assert parse_progress(line) == pct
