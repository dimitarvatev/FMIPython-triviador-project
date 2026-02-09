"""Тестове за joker_system.py — JokerSystem."""
import pytest

from triviador.logic.joker_system import JokerSystem
from triviador.core.models import Question, Player, QuestionType
from triviador.core.config import JOKER_5050, JOKER_AUDIENCE


def _mc_question(correct="А"):
    return Question(
        id=1,
        category="Тест",
        difficulty=2,
        question_type=QuestionType.MULTIPLE_CHOICE,
        question_text="Въпрос?",
        correct_answer=correct,
        options=["А", "Б", "В", "Г"],
    )


def _numeric_question(correct=100):
    return Question(
        id=2,
        category="Математика",
        difficulty=3,
        question_type=QuestionType.NUMERIC,
        question_text="Колко?",
        correct_answer=correct,
    )


# ─── apply_5050 ─────────────────────────────────────────────────────

class TestApply5050:

    def test_mc_leaves_two_options(self):
        q = _mc_question()
        result = JokerSystem.apply_5050(q)
        assert len(result) == 2

    def test_mc_keeps_correct(self):
        q = _mc_question(correct="В")
        result = JokerSystem.apply_5050(q)
        assert "В" in result

    def test_mc_consistency(self):
        """Многократно прилагане винаги дава 2 опции с верния отговор."""
        q = _mc_question()
        for _ in range(20):
            result = JokerSystem.apply_5050(q)
            assert len(result) == 2
            assert "А" in result

    def test_numeric_returns_range(self):
        q = _numeric_question(correct=100)
        result = JokerSystem.apply_5050(q)
        assert len(result) == 1
        assert " - " in result[0]

    def test_numeric_range_contains_correct(self):
        q = _numeric_question(correct=100)
        result = JokerSystem.apply_5050(q)
        parts = result[0].split(" - ")
        low, high = int(parts[0]), int(parts[1])
        assert low <= 100 <= high


# ─── apply_audience_help ────────────────────────────────────────────

class TestApplyAudienceHelp:

    def test_mc_returns_all_options(self):
        q = _mc_question()
        result = JokerSystem.apply_audience_help(q)
        for opt in q.options:
            assert opt in result

    def test_mc_votes_sum_to_100(self):
        q = _mc_question()
        for _ in range(10):
            result = JokerSystem.apply_audience_help(q)
            assert sum(result.values()) == 100

    def test_mc_correct_usually_highest(self):
        """Верният отговор трябва да има най-много гласове в повечето случаи."""
        q = _mc_question()
        correct_wins = 0
        for _ in range(50):
            result = JokerSystem.apply_audience_help(q)
            if result["А"] == max(result.values()):
                correct_wins += 1
        # Поне 60% от времето верният трябва да е водещ
        assert correct_wins >= 30

    def test_numeric_returns_suggestion(self):
        q = _numeric_question(correct=100)
        result = JokerSystem.apply_audience_help(q)
        assert "suggested_value" in result
        assert "confidence" in result

    def test_numeric_suggestion_reasonable(self):
        q = _numeric_question(correct=100)
        for _ in range(20):
            result = JokerSystem.apply_audience_help(q)
            assert 90 <= result["suggested_value"] <= 110
            assert 60 <= result["confidence"] <= 85


# ─── can_use_joker ──────────────────────────────────────────────────

class TestCanUseJoker:

    def test_can_use_normal(self):
        p = Player(name="Тест")
        ok, msg = JokerSystem.can_use_joker(p, JOKER_5050, False)
        assert ok is True
        assert msg == ""

    def test_blocked_in_special_round(self):
        p = Player(name="Тест")
        ok, msg = JokerSystem.can_use_joker(p, JOKER_5050, True)
        assert ok is False
        assert "специален" in msg.lower() or "рунд" in msg.lower()

    def test_no_jokers_left(self):
        p = Player(name="Тест")
        p.jokers[JOKER_5050] = 0
        ok, msg = JokerSystem.can_use_joker(p, JOKER_5050, False)
        assert ok is False

    def test_can_use_audience(self):
        p = Player(name="Тест")
        ok, _ = JokerSystem.can_use_joker(p, JOKER_AUDIENCE, False)
        assert ok is True


# ─── helpers ────────────────────────────────────────────────────────

class TestJokerHelpers:

    def test_get_joker_name(self):
        assert "50/50" in JokerSystem.get_joker_name(JOKER_5050)

    def test_get_joker_description(self):
        desc = JokerSystem.get_joker_description(JOKER_5050)
        assert len(desc) > 0

    def test_unknown_joker_name(self):
        name = JokerSystem.get_joker_name("unknown")
        assert name == "unknown"
