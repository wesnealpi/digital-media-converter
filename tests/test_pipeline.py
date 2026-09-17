from pathlib import Path

import pytest

from dmc import pipeline as pl
from dmc.handbrake import HandBrakeError
from dmc.pipeline import Folders, Job, pending_sources, plan, run, run_one
from dmc.profiles import SourceClass


def test_folders_ensure_creates_layout(tmp_path):
    f = Folders(tmp_path / "media").ensure()
    for p in (f.inbox, f.outbox, f.done, f.failed, f.logs):
        assert p.is_dir()


def test_pending_sources_filters_by_extension_and_temp_prefix(tmp_path):
    for name in ("b.mkv", "a.MP4", "notes.txt", "~partial.mkv", "c.m2ts"):
        (tmp_path / name).write_bytes(b"x")
    (tmp_path / "sub").mkdir()
    assert [p.name for p in pending_sources(tmp_path)] == ["a.MP4", "b.mkv", "c.m2ts"]


def test_plan_dvd_names_output_and_picks_profile(dvd_rip, tmp_path):
    job, profile = plan(dvd_rip, tmp_path, measure_grain=False)
    assert job.source is SourceClass.DVD
    assert job.dst == tmp_path / "Vegas Vacation.mkv"
    assert job.rf == 20 and profile.rf == 20
    assert job.subtitle_count == 2


def test_plan_keeps_plex_name_when_source_already_has_it(encoded_output, tmp_path):
    job, _ = plan(encoded_output, tmp_path, measure_grain=False)
    assert job.dst.name == "Vegas Vacation (1997) {imdb-tt0120434}.mkv"


def test_plan_force_great_and_rf(bluray_rip, tmp_path):
    job, profile = plan(bluray_rip, tmp_path, force=SourceClass.DVD_GRAINY, great=True)
    assert job.source is SourceClass.DVD_GRAINY and profile.rf == 18
    job, profile = plan(bluray_rip, tmp_path, rf_override=19)
    assert job.source is SourceClass.BLURAY and job.rf == 19
    assert profile.denoise is None


def test_plan_rejects_unknown(dvd_rip_json, tmp_path):
    from dmc.probe import parse_ffprobe
    dvd_rip_json["streams"][0].update(width=640, height=360, codec_name="h264")
    with pytest.raises(ValueError):
        plan(parse_ffprobe(dvd_rip_json), tmp_path)


def test_job_json_is_serialisable(dvd_rip, tmp_path):
    job, _ = plan(dvd_rip, tmp_path, measure_grain=False)
    text = job.to_json()
    assert '"profile_name": "dvd"' in text and "Vegas Vacation.mkv" in text


@pytest.fixture
def fake_env(monkeypatch, tmp_path, dvd_rip_json):
    """A pipeline with probe and encode replaced by fakes; no tools needed."""
    from dmc.probe import parse_ffprobe
    folders = Folders(tmp_path).ensure()
    src = folders.inbox / "Vegas Vacation_t00.mkv"
    src.write_bytes(b"0" * 1000)
    monkeypatch.setattr(pl, "probe", lambda p: parse_ffprobe(dvd_rip_json, p))
    monkeypatch.setattr(pl, "is_stable", lambda p, wait_s=0: True)
    calls = {}

    def fake_encode(s, d, profile, on_progress=None, title=None, clip=None, subtitle_count=0):
        calls["src"], calls["dst"], calls["profile"] = Path(s), Path(d), profile
        calls["subtitle_count"] = subtitle_count
        for pct in (10.0, 50.0, 100.0):
            on_progress(pct)
        Path(d).write_bytes(b"0" * 100)
        return Path(d)

    monkeypatch.setattr(pl, "encode", fake_encode)
    return folders, src, calls


def test_run_one_encodes_to_temp_then_renames_and_files_source(fake_env):
    folders, src, calls = fake_env
    job = run_one(src, folders, measure_grain=False)
    assert calls["dst"].name == "Vegas Vacation.part.mkv"
    assert calls["subtitle_count"] == 2  # both VOB subtitle tracks from the probe
    assert (folders.outbox / "Vegas Vacation.mkv").is_file()
    assert not calls["dst"].exists()
    assert (folders.done / src.name).is_file() and not src.exists()
    log = (folders.logs / "Vegas Vacation_t00.log").read_text()
    assert '"profile_name": "dvd"' in log and "result: 1000 -> 100 bytes, 10.00x" in log
    assert job.source is SourceClass.DVD


def test_run_one_failure_moves_source_to_failed(fake_env, monkeypatch):
    folders, src, _ = fake_env

    def boom(s, d, profile, on_progress=None, title=None, clip=None, subtitle_count=0):
        Path(d).write_bytes(b"partial")
        raise HandBrakeError("exit 1")

    monkeypatch.setattr(pl, "encode", boom)
    with pytest.raises(HandBrakeError):
        run_one(src, folders, measure_grain=False)
    assert (folders.failed / src.name).is_file()
    assert not list(folders.outbox.iterdir())
    assert "exit 1" in (folders.logs / "Vegas Vacation_t00.log").read_text()


def test_run_processes_inbox_and_counts(fake_env):
    folders, src, _ = fake_env
    assert run(folders, measure_grain=False) == 1
    assert not list(folders.inbox.iterdir())


def test_run_survives_a_bad_file(fake_env, monkeypatch):
    folders, src, _ = fake_env
    bad = folders.inbox / "0 broken.mkv"
    bad.write_bytes(b"?")
    from dmc.probe import ProbeError
    real_probe = pl.probe
    monkeypatch.setattr(pl, "probe", lambda p: (_ for _ in ()).throw(ProbeError("nope")) if p == bad else real_probe(p))
    assert run(folders, measure_grain=False) == 1
    assert (folders.failed / bad.name).is_file()
