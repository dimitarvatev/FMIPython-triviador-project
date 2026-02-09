"""Тестове за highscore_manager.py — HighScoreManager."""
import pytest
import json
from pathlib import Path

from triviador.logic.highscore_manager import HighScoreManager
from triviador.core.models import Player, GameMode


@pytest.fixture
def hsm(tmp_path, monkeypatch):
    """HighScoreManager с временен файл."""
    monkeypatch.setattr("triviador.logic.highscore_manager.BASE_DIR", tmp_path)
    return HighScoreManager("test_highscores.json")


def _player(name="Иван", score=500, correct=8, total=10):
    p = Player(name=name)
    p.score = score
    p.correct_answers = correct
    p.total_answers = total
    return p


# ─── Добавяне ───────────────────────────────────────────────────────

class TestAddScore:

    def test_add_first_score(self, hsm):
        rank = hsm.add_score(_player(), GameMode.STANDARD)
        assert rank == 1
        assert len(hsm.highscores) == 1

    def test_multiple_scores_sorted(self, hsm):
        hsm.add_score(_player("А", 100), GameMode.STANDARD)
        hsm.add_score(_player("Б", 300), GameMode.STANDARD)
        hsm.add_score(_player("В", 200), GameMode.STANDARD)

        assert hsm.highscores[0].player_name == "Б"
        assert hsm.highscores[1].player_name == "В"
        assert hsm.highscores[2].player_name == "А"

    def test_max_highscores_limit(self, hsm):
        for i in range(15):
            hsm.add_score(_player(f"P{i}", i * 100), GameMode.STANDARD)
        assert len(hsm.highscores) == HighScoreManager.MAX_HIGHSCORES

    def test_low_score_pushed_out(self, hsm):
        for i in range(10):
            hsm.add_score(_player(f"P{i}", (i + 1) * 100), GameMode.STANDARD)
        # Добавяме нисък резултат
        rank = hsm.add_score(_player("Нисък", 5), GameMode.STANDARD)
        assert rank is None  # Не влиза в класирането
        assert len(hsm.highscores) == 10


# ─── Извличане ──────────────────────────────────────────────────────

class TestGetScores:

    def test_get_top_scores_empty(self, hsm):
        assert hsm.get_top_scores() == []

    def test_get_top_scores(self, hsm):
        for i in range(5):
            hsm.add_score(_player(f"P{i}", i * 100), GameMode.STANDARD)
        top = hsm.get_top_scores(3)
        assert len(top) == 3
        assert top[0].score >= top[1].score

    def test_get_scores_by_mode(self, hsm):
        hsm.add_score(_player("А", 100), GameMode.STANDARD)
        hsm.add_score(_player("Б", 200), GameMode.ENDLESS)
        hsm.add_score(_player("В", 300), GameMode.STANDARD)

        standard = hsm.get_scores_by_mode("standard")
        assert len(standard) == 2

        endless = hsm.get_scores_by_mode("endless")
        assert len(endless) == 1


# ─── is_highscore ──────────────────────────────────────────────────

class TestIsHighscore:

    def test_empty_is_always_highscore(self, hsm):
        assert hsm.is_highscore(1) is True

    def test_higher_than_lowest(self, hsm):
        for i in range(10):
            hsm.add_score(_player(f"P{i}", (i + 1) * 100), GameMode.STANDARD)
        assert hsm.is_highscore(1000) is True
        assert hsm.is_highscore(50) is False


# ─── Запазване / зареждане ──────────────────────────────────────────

class TestPersistence:

    def test_save_and_load(self, hsm, tmp_path, monkeypatch):
        hsm.add_score(_player("Тест", 999), GameMode.STANDARD)

        monkeypatch.setattr("triviador.logic.highscore_manager.BASE_DIR", tmp_path)
        hsm2 = HighScoreManager("test_highscores.json")
        assert len(hsm2.highscores) == 1
        assert hsm2.highscores[0].player_name == "Тест"
        assert hsm2.highscores[0].score == 999

    def test_clear(self, hsm):
        hsm.add_score(_player(), GameMode.STANDARD)
        hsm.clear_highscores()
        assert hsm.highscores == []

    def test_corrupt_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr("triviador.logic.highscore_manager.BASE_DIR", tmp_path)
        (tmp_path / "corrupt.json").write_text("not json", encoding="utf-8")
        hsm = HighScoreManager("corrupt.json")
        assert hsm.highscores == []
