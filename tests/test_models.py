"""Тестове за models.py — Question, Player, GameState, HighScore."""
import pytest

from triviador.core.models import Question, Player, GameState, GameMode, QuestionType, HighScore


# ─── Question ───────────────────────────────────────────────────────

class TestQuestion:
    """Тестове за класа Question."""

    def _mc_question(self, **kwargs):
        defaults = dict(
            id=1,
            category="История",
            difficulty=2,
            question_type=QuestionType.MULTIPLE_CHOICE,
            question_text="Коя е столицата на България?",
            correct_answer="София",
            options=["София", "Пловдив", "Варна", "Бургас"],
        )
        defaults.update(kwargs)
        return Question(**defaults)

    def _numeric_question(self, **kwargs):
        defaults = dict(
            id=2,
            category="Математика",
            difficulty=3,
            question_type=QuestionType.NUMERIC,
            question_text="Колко е 7 * 8?",
            correct_answer=56,
        )
        defaults.update(kwargs)
        return Question(**defaults)

    # -- from_dict --
    def test_from_dict_mc(self):
        data = {
            "id": 1,
            "category": "Наука",
            "difficulty": 1,
            "type": "multiple_choice",
            "question": "Въпрос?",
            "correct_answer": "Да",
            "options": ["Да", "Не", "Може би", "Никога"],
        }
        q = Question.from_dict(data)
        assert q.id == 1
        assert q.question_type == QuestionType.MULTIPLE_CHOICE
        assert q.correct_answer == "Да"
        assert len(q.options) == 4

    def test_from_dict_numeric(self):
        data = {
            "id": 2,
            "category": "Математика",
            "difficulty": 3,
            "type": "numeric",
            "question": "2+2?",
            "correct_answer": 4,
        }
        q = Question.from_dict(data)
        assert q.question_type == QuestionType.NUMERIC
        assert q.correct_answer == 4
        assert q.options == []

    # -- check_answer MC --
    def test_check_answer_correct(self):
        q = self._mc_question()
        assert q.check_answer("София") is True

    def test_check_answer_case_insensitive(self):
        q = self._mc_question()
        assert q.check_answer("софия") is True
        assert q.check_answer("СОФИЯ") is True

    def test_check_answer_whitespace(self):
        q = self._mc_question()
        assert q.check_answer("  София  ") is True

    def test_check_answer_wrong(self):
        q = self._mc_question()
        assert q.check_answer("Пловдив") is False

    # -- check_answer numeric --
    def test_check_numeric_exact(self):
        q = self._numeric_question()
        assert q.check_answer(56) is True

    def test_check_numeric_within_tolerance(self):
        q = self._numeric_question()  # correct = 56, tolerance 10% → ±5.6
        assert q.check_answer(55) is True
        assert q.check_answer(60) is True

    def test_check_numeric_outside_tolerance(self):
        q = self._numeric_question()
        assert q.check_answer(40) is False
        assert q.check_answer(70) is False

    def test_check_numeric_string(self):
        q = self._numeric_question()
        assert q.check_answer("56") is True

    def test_check_numeric_invalid_string(self):
        q = self._numeric_question()
        assert q.check_answer("abc") is False

    def test_check_numeric_zero_correct(self):
        q = self._numeric_question(correct_answer=0)
        # tolerance = 0 * 0.10 = 0, so only exact match
        assert q.check_answer(0) is True
        assert q.check_answer(1) is False


# ─── Player ─────────────────────────────────────────────────────────

class TestPlayer:
    """Тестове за класа Player."""

    def test_initial_state(self):
        p = Player(name="Иван")
        assert p.name == "Иван"
        assert p.score == 0
        assert p.correct_answers == 0
        assert p.total_answers == 0

    def test_initial_jokers(self):
        from triviador.core.config import JOKERS_PER_GAME
        p = Player(name="Иван")
        assert p.jokers == JOKERS_PER_GAME

    def test_add_score(self):
        p = Player(name="Иван")
        p.add_score(100)
        assert p.score == 100
        p.add_score(50)
        assert p.score == 150

    def test_accuracy_zero_answers(self):
        p = Player(name="Иван")
        assert p.accuracy == 0.0

    def test_accuracy_calculation(self):
        p = Player(name="Иван")
        p.correct_answers = 3
        p.total_answers = 4
        assert p.accuracy == 75.0

    def test_accuracy_all_correct(self):
        p = Player(name="Иван")
        p.correct_answers = 10
        p.total_answers = 10
        assert p.accuracy == 100.0

    def test_use_joker_success(self):
        from triviador.core.config import JOKER_5050
        p = Player(name="Иван")
        initial_count = p.jokers[JOKER_5050]
        assert p.use_joker(JOKER_5050) is True
        assert p.jokers[JOKER_5050] == initial_count - 1

    def test_use_joker_exhausted(self):
        from triviador.core.config import JOKER_5050
        p = Player(name="Иван")
        p.jokers[JOKER_5050] = 0
        assert p.use_joker(JOKER_5050) is False

    def test_has_joker(self):
        from triviador.core.config import JOKER_5050
        p = Player(name="Иван")
        assert p.has_joker(JOKER_5050) is True
        p.jokers[JOKER_5050] = 0
        assert p.has_joker(JOKER_5050) is False

    def test_has_joker_unknown_type(self):
        p = Player(name="Иван")
        assert p.has_joker("nonexistent") is False


# ─── GameState ──────────────────────────────────────────────────────

class TestGameState:
    """Тестове за класа GameState."""

    def _make_questions(self, n=3):
        return [
            Question(
                id=i,
                category="Тест",
                difficulty=1,
                question_type=QuestionType.MULTIPLE_CHOICE,
                question_text=f"Въпрос {i}?",
                correct_answer="A",
                options=["A", "B", "C", "D"],
            )
            for i in range(1, n + 1)
        ]

    def test_current_player(self):
        gs = GameState(
            mode=GameMode.STANDARD,
            players=[Player(name="А"), Player(name="Б")],
        )
        assert gs.current_player.name == "А"

    def test_current_player_empty(self):
        gs = GameState(mode=GameMode.STANDARD, players=[])
        assert gs.current_player is None

    def test_current_question(self):
        qs = self._make_questions(3)
        gs = GameState(mode=GameMode.STANDARD, questions=qs)
        assert gs.current_question.id == 1

    def test_current_question_none(self):
        gs = GameState(mode=GameMode.STANDARD, questions=[])
        assert gs.current_question is None

    def test_next_question(self):
        qs = self._make_questions(3)
        gs = GameState(mode=GameMode.STANDARD, questions=qs)
        assert gs.next_question() is True
        assert gs.current_question.id == 2

    def test_next_question_past_end(self):
        qs = self._make_questions(1)
        gs = GameState(mode=GameMode.STANDARD, questions=qs)
        assert gs.next_question() is False
        assert gs.current_question is None

    def test_next_player_wraps(self):
        gs = GameState(
            mode=GameMode.STANDARD,
            players=[Player(name="А"), Player(name="Б")],
        )
        gs.next_player()
        assert gs.current_player.name == "Б"
        gs.next_player()
        assert gs.current_player.name == "А"


# ─── HighScore ──────────────────────────────────────────────────────

class TestHighScore:
    """Тестове за класа HighScore."""

    def _sample(self):
        return HighScore(
            player_name="Мария",
            score=500,
            mode="standard",
            questions_answered=10,
            accuracy=80.0,
            date="2026-01-01 12:00",
        )

    def test_to_dict(self):
        hs = self._sample()
        d = hs.to_dict()
        assert d["player_name"] == "Мария"
        assert d["score"] == 500

    def test_roundtrip(self):
        hs = self._sample()
        d = hs.to_dict()
        hs2 = HighScore.from_dict(d)
        assert hs2.player_name == hs.player_name
        assert hs2.score == hs.score
        assert hs2.accuracy == hs.accuracy
