"""Тестове за game_logic.py — GameLogic."""
import pytest
import time
from unittest.mock import patch, MagicMock

from triviador.logic.game_logic import GameLogic
from triviador.core.models import Question, Player, GameState, GameMode, QuestionType
from triviador.core.config import (
    BASE_POINTS, TIME_BONUS_MULTIPLIER, DIFFICULTY_MULTIPLIER,
    SPECIAL_ROUND_MULTIPLIER, DEFAULT_TIME_LIMIT, JOKER_5050,
    JOKER_AUDIENCE, NUMERIC_TOLERANCE,
)


@pytest.fixture
def logic():
    """GameLogic с заредени въпроси."""
    return GameLogic()


@pytest.fixture
def started_game(logic):
    """Стартирана стандартна игра с 1 играч."""
    logic.start_game(GameMode.STANDARD, ["Тестов"])
    return logic


def _make_mc_question(qid=1, correct="А", difficulty=1):
    return Question(
        id=qid,
        category="Тест",
        difficulty=difficulty,
        question_type=QuestionType.MULTIPLE_CHOICE,
        question_text="Въпрос?",
        correct_answer=correct,
        options=["А", "Б", "В", "Г"],
    )


def _make_numeric_question(qid=1, correct=42, difficulty=1):
    return Question(
        id=qid,
        category="Математика",
        difficulty=difficulty,
        question_type=QuestionType.NUMERIC,
        question_text="Колко?",
        correct_answer=correct,
    )


# ─── start_game ─────────────────────────────────────────────────────

class TestStartGame:

    def test_standard_creates_state(self, logic):
        gs = logic.start_game(GameMode.STANDARD, ["Иван"])
        assert isinstance(gs, GameState)
        assert gs.mode == GameMode.STANDARD
        assert len(gs.players) == 1
        assert gs.players[0].name == "Иван"
        assert gs.game_over is False

    def test_standard_has_questions(self, logic):
        gs = logic.start_game(GameMode.STANDARD, ["Иван"])
        assert len(gs.questions) > 0

    def test_endless_starts_empty(self, logic):
        gs = logic.start_game(GameMode.ENDLESS, ["Иван"])
        assert gs.mode == GameMode.ENDLESS
        assert gs.questions == []

    def test_multiple_players(self, logic):
        gs = logic.start_game(GameMode.STANDARD, ["А", "Б", "В"])
        assert len(gs.players) == 3

    def test_with_categories(self, logic):
        cats = logic.get_categories()
        if cats:
            gs = logic.start_game(GameMode.STANDARD, ["Иван"], categories=[cats[0]])
            assert gs.selected_categories == [cats[0]]


# ─── calculate_points ───────────────────────────────────────────────

class TestCalculatePoints:

    def test_wrong_answer_zero(self, logic):
        assert logic.calculate_points(False, 10.0, 1) == 0

    def test_correct_base_no_time(self, logic):
        pts = logic.calculate_points(True, 0.0, 1)
        assert pts == BASE_POINTS

    def test_correct_with_time_bonus(self, logic):
        pts = logic.calculate_points(True, 10.0, 1)
        expected = BASE_POINTS + int(10.0 * TIME_BONUS_MULTIPLIER)
        assert pts == expected

    def test_difficulty_bonus(self, logic):
        pts_d1 = logic.calculate_points(True, 10.0, 1)
        pts_d3 = logic.calculate_points(True, 10.0, 3)
        assert pts_d3 > pts_d1

    def test_special_round_multiplier(self, started_game):
        started_game.game_state.is_special_round = True
        pts = started_game.calculate_points(True, 5.0, 1)
        started_game.game_state.is_special_round = False
        pts_normal = started_game.calculate_points(True, 5.0, 1)
        assert pts == int(pts_normal * SPECIAL_ROUND_MULTIPLIER)


# ─── submit_answer ──────────────────────────────────────────────────

class TestSubmitAnswer:

    def test_no_game(self, logic):
        result = logic.submit_answer("test")
        assert "error" in result

    def test_correct_mc(self, started_game):
        q = _make_mc_question()
        started_game.game_state.questions = [q]
        started_game.game_state.current_question_index = 0
        started_game._start_question_timer()

        result = started_game.submit_answer("А")
        assert result["is_correct"] is True
        assert result["points"] > 0
        assert result["total_score"] > 0

    def test_wrong_mc(self, started_game):
        q = _make_mc_question()
        started_game.game_state.questions = [q]
        started_game.game_state.current_question_index = 0
        started_game._start_question_timer()

        result = started_game.submit_answer("Б")
        assert result["is_correct"] is False
        assert result["points"] == 0

    def test_correct_numeric(self, started_game):
        q = _make_numeric_question(correct=100)
        started_game.game_state.questions = [q]
        started_game.game_state.current_question_index = 0
        started_game._start_question_timer()

        result = started_game.submit_answer(100)
        assert result["is_correct"] is True

    def test_updates_player_stats(self, started_game):
        q = _make_mc_question()
        started_game.game_state.questions = [q]
        started_game.game_state.current_question_index = 0
        started_game._start_question_timer()

        started_game.submit_answer("А")
        p = started_game.game_state.current_player
        assert p.total_answers == 1
        assert p.correct_answers == 1

    def test_wrong_updates_stats(self, started_game):
        q = _make_mc_question()
        started_game.game_state.questions = [q]
        started_game.game_state.current_question_index = 0
        started_game._start_question_timer()

        started_game.submit_answer("Б")
        p = started_game.game_state.current_player
        assert p.total_answers == 1
        assert p.correct_answers == 0

    def test_time_expired_is_wrong(self, started_game):
        q = _make_mc_question()
        started_game.game_state.questions = [q]
        started_game.game_state.current_question_index = 0
        # Симулираме изтекло време
        started_game.question_start_time = time.time() - DEFAULT_TIME_LIMIT - 1

        result = started_game.submit_answer("А")
        assert result["is_correct"] is False

    def test_endless_game_over_on_wrong(self, logic):
        logic.start_game(GameMode.ENDLESS, ["Иван"])
        q = _make_mc_question()
        logic.game_state.questions = [q]
        logic.game_state.current_question_index = 0
        logic._start_question_timer()

        result = logic.submit_answer("Б")
        assert result.get("game_over") is True
        assert logic.game_state.game_over is True


# ─── next_question ──────────────────────────────────────────────────

class TestNextQuestion:

    def test_advances(self, started_game):
        qs = [_make_mc_question(qid=i) for i in range(1, 4)]
        started_game.game_state.questions = qs
        started_game.game_state.current_question_index = 0

        assert started_game.next_question() is True
        assert started_game.game_state.current_question.id == 2

    def test_game_over_at_end(self, started_game):
        started_game.game_state.questions = [_make_mc_question()]
        started_game.game_state.current_question_index = 0

        result = started_game.next_question()
        assert result is False
        assert started_game.game_state.game_over is True

    def test_no_game_state(self, logic):
        assert logic.next_question() is False


# ─── timer ──────────────────────────────────────────────────────────

class TestTimer:

    def test_remaining_time(self, started_game):
        started_game._start_question_timer()
        remaining = started_game.get_remaining_time()
        assert 0 < remaining <= DEFAULT_TIME_LIMIT

    def test_time_up(self, started_game):
        started_game.question_start_time = time.time() - DEFAULT_TIME_LIMIT - 1
        assert started_game.is_time_up() is True

    def test_time_not_up(self, started_game):
        started_game._start_question_timer()
        assert started_game.is_time_up() is False


# ─── use_joker ──────────────────────────────────────────────────────

class TestUseJoker:

    def test_no_game(self, logic):
        result = logic.use_joker(JOKER_5050)
        assert "error" in result

    def test_5050_mc(self, started_game):
        q = _make_mc_question()
        started_game.game_state.questions = [q]
        started_game.game_state.current_question_index = 0
        started_game.game_state.is_special_round = False

        result = started_game.use_joker(JOKER_5050)
        assert result["type"] == "5050"
        assert len(result["remaining_options"]) == 2
        assert "А" in result["remaining_options"]  # верният отговор винаги остава

    def test_audience_mc(self, started_game):
        q = _make_mc_question()
        started_game.game_state.questions = [q]
        started_game.game_state.current_question_index = 0
        started_game.game_state.is_special_round = False

        result = started_game.use_joker(JOKER_AUDIENCE)
        assert result["type"] == "audience"
        assert "А" in result["votes"]

    def test_cannot_use_in_special_round(self, started_game):
        q = _make_mc_question()
        started_game.game_state.questions = [q]
        started_game.game_state.current_question_index = 0
        started_game.game_state.is_special_round = True

        result = started_game.use_joker(JOKER_5050)
        assert "error" in result

    def test_joker_depleted(self, started_game):
        q = _make_mc_question()
        started_game.game_state.questions = [q]
        started_game.game_state.current_question_index = 0
        started_game.game_state.is_special_round = False
        started_game.game_state.current_player.jokers[JOKER_AUDIENCE] = 0

        result = started_game.use_joker(JOKER_AUDIENCE)
        assert "error" in result


# ─── end_game ───────────────────────────────────────────────────────

class TestEndGame:

    def test_no_game(self, logic):
        result = logic.end_game()
        assert "error" in result

    def test_end_game_returns_results(self, started_game):
        started_game.game_state.current_player.add_score(200)
        result = started_game.end_game()
        assert started_game.game_state.game_over is True
        assert result["mode"] == "standard"
        assert len(result["players"]) == 1
        assert result["players"][0]["score"] == 200

    def test_end_game_sorted_by_score(self, logic):
        logic.start_game(GameMode.STANDARD, ["А", "Б"])
        logic.game_state.players[0].add_score(100)
        logic.game_state.players[1].add_score(300)
        result = logic.end_game()
        assert result["players"][0]["name"] == "Б"
        assert result["players"][1]["name"] == "А"
