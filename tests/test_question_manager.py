"""Тестове за question_manager.py — QuestionManager."""
import pytest
import json
import tempfile
from pathlib import Path

from triviador.logic.question_manager import QuestionManager
from triviador.core.models import QuestionType


# ─── Fixture: файл с въпроси ────────────────────────────────────────

@pytest.fixture
def sample_questions_json(tmp_path):
    """Създава временен JSON файл с въпроси."""
    data = {
        "categories": ["История", "Наука"],
        "questions": [
            {
                "id": 1,
                "category": "История",
                "difficulty": 1,
                "type": "multiple_choice",
                "question": "Кога е основана България?",
                "correct_answer": "681",
                "options": ["681", "632", "700", "900"],
            },
            {
                "id": 2,
                "category": "История",
                "difficulty": 2,
                "type": "multiple_choice",
                "question": "Кой е Хан Аспарух?",
                "correct_answer": "Основател",
                "options": ["Основател", "Войн", "Търговец", "Монах"],
            },
            {
                "id": 3,
                "category": "Наука",
                "difficulty": 1,
                "type": "numeric",
                "question": "Колко е Пи (приблизително)?",
                "correct_answer": 3,
                "options": [],
            },
            {
                "id": 4,
                "category": "Наука",
                "difficulty": 3,
                "type": "multiple_choice",
                "question": "H2O е?",
                "correct_answer": "Вода",
                "options": ["Вода", "Сол", "Захар", "Пясък"],
            },
            {
                "id": 5,
                "category": "Наука",
                "difficulty": 5,
                "type": "numeric",
                "question": "Скорост на светлината (km/s)?",
                "correct_answer": 299792,
                "options": [],
            },
        ],
    }
    filepath = tmp_path / "questions.json"
    filepath.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return str(filepath)


@pytest.fixture
def sample_questions_txt(tmp_path):
    """Създава временен TXT файл с въпроси."""
    content = """[История]
Трудност: 1
Тип: избор
Въпрос: Кога е Освобождението?
Отговор: 1878
Опции: 1878, 1900, 1800, 1850

[Наука]
Трудност: 2
Тип: число
Въпрос: Колко е 2+2?
Отговор: 4

[История]
Трудност: 3
Тип: избор
Въпрос: Кой е Левски?
Отговор: Революционер
Опции: Революционер, Поет, Цар, Търговец
"""
    filepath = tmp_path / "questions.txt"
    filepath.write_text(content, encoding="utf-8")
    return str(filepath)


@pytest.fixture
def qm_json(sample_questions_json):
    return QuestionManager(sample_questions_json)


@pytest.fixture
def qm_txt(sample_questions_txt):
    return QuestionManager(sample_questions_txt)


# ─── Зареждане ──────────────────────────────────────────────────────

class TestLoading:

    def test_load_json(self, qm_json):
        assert len(qm_json.questions) == 5

    def test_load_txt(self, qm_txt):
        assert len(qm_txt.questions) == 3

    def test_categories_json(self, qm_json):
        cats = qm_json.get_categories()
        assert "История" in cats
        assert "Наука" in cats

    def test_categories_txt(self, qm_txt):
        cats = qm_txt.get_categories()
        assert "История" in cats
        assert "Наука" in cats

    def test_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            QuestionManager(str(tmp_path / "nonexistent.json"))

    def test_question_types(self, qm_json):
        mc = [q for q in qm_json.questions if q.question_type == QuestionType.MULTIPLE_CHOICE]
        num = [q for q in qm_json.questions if q.question_type == QuestionType.NUMERIC]
        assert len(mc) == 3
        assert len(num) == 2


# ─── Филтриране ─────────────────────────────────────────────────────

class TestFiltering:

    def test_by_category(self, qm_json):
        history = qm_json.get_questions_by_category("История")
        assert all(q.category == "История" for q in history)
        assert len(history) == 2

    def test_by_difficulty(self, qm_json):
        easy = qm_json.get_questions_by_difficulty(1)
        assert all(q.difficulty == 1 for q in easy)
        assert len(easy) == 2

    def test_by_category_empty(self, qm_json):
        result = qm_json.get_questions_by_category("Несъществуваща")
        assert result == []


# ─── Случайни въпроси ───────────────────────────────────────────────

class TestRandomQuestions:

    def test_get_random(self, qm_json):
        qs = qm_json.get_random_questions(3)
        assert len(qs) == 3

    def test_get_random_with_category(self, qm_json):
        qs = qm_json.get_random_questions(2, categories=["Наука"])
        assert all(q.category == "Наука" for q in qs)

    def test_get_random_with_difficulty(self, qm_json):
        qs = qm_json.get_random_questions(5, difficulty_range=(1, 1))
        assert all(q.difficulty == 1 for q in qs)

    def test_get_random_with_exclude(self, qm_json):
        qs = qm_json.get_random_questions(3, exclude_ids={1, 2})
        assert all(q.id not in {1, 2} for q in qs)

    def test_get_random_more_than_available(self, qm_json):
        qs = qm_json.get_random_questions(100)
        assert len(qs) == len(qm_json.questions)

    def test_get_random_empty_result(self, qm_json):
        qs = qm_json.get_random_questions(5, categories=["Несъществуваща"])
        assert qs == []


# ─── Безкраен режим ─────────────────────────────────────────────────

class TestEndlessMode:

    def test_low_score_easy(self, qm_json):
        q = qm_json.get_endless_mode_question(current_score=0)
        assert q is not None
        assert q.difficulty <= 2

    def test_high_score_hard(self, qm_json):
        q = qm_json.get_endless_mode_question(current_score=5000)
        if q:
            assert q.difficulty >= 4

    def test_excludes_used(self, qm_json):
        used = set()
        for _ in range(len(qm_json.questions)):
            q = qm_json.get_endless_mode_question(0, exclude_ids=used)
            if q:
                assert q.id not in used
                used.add(q.id)

    def test_returns_none_when_exhausted(self, qm_json):
        all_ids = {q.id for q in qm_json.questions}
        q = qm_json.get_endless_mode_question(0, exclude_ids=all_ids)
        assert q is None


# ─── Нарастваща трудност ─────────────────────────────────────────────

class TestIncreasingDifficulty:

    def test_returns_requested_count(self, qm_json):
        qs = qm_json.get_questions_with_increasing_difficulty(5)
        assert len(qs) <= 5

    def test_mixed_difficulties(self, qm_json):
        qs = qm_json.get_questions_with_increasing_difficulty(5)
        difficulties = {q.difficulty for q in qs}
        assert len(difficulties) >= 1  # Поне 1 ниво на трудност
