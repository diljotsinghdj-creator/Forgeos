from pathlib import Path

from creatorforge_worker.studio import score_bars as S


def test_plan_keeps_every_scene_in_tempo_range():
    cuts = [1.9, 3.7, 7.2, 9.0, 12.4, 13.6, 18.1]
    for sc in S.plan(cuts, 20.0, 84, 66, 104):
        assert 66 - 1e-6 <= sc["bpm"] <= 104 + 1e-6
        assert abs(sc["bars"] * 4 - round(sc["bars"] * 4)) < 1e-9      # whole beats


def test_score_lands_every_cut_on_a_beat_without_startle(tmp_path: Path):
    cuts = [2.5, 5.1, 7.4, 10.9, 13.0, 16.2, 19.8]
    wav, scenes = S.compose(cuts, 24.0, tmp_path / "s.wav", "minor", 50, 84)
    rows = S.sync_check(wav, cuts)
    assert rows and all(r["ok"] for r in rows), rows
