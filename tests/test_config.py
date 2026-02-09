"""Тестове за config.py — проверка на конфигурационните стойности."""
import pytest

from triviador.core.config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, DEFAULT_TIME_LIMIT,
    BASE_POINTS, TIME_BONUS_MULTIPLIER, DIFFICULTY_MULTIPLIER,
    SPECIAL_ROUND_MULTIPLIER, SPECIAL_ROUND_CHANCE,
    QUESTIONS_PER_GAME, NUMERIC_TOLERANCE,
    JOKER_5050, JOKER_AUDIENCE, JOKERS_PER_GAME,
    DEFAULT_PORT, BUFFER_SIZE, FPS,
)


class TestConfig:
    """Валидация на конфигурационните стойности."""

    def test_screen_dimensions_positive(self):
        assert SCREEN_WIDTH > 0
        assert SCREEN_HEIGHT > 0

    def test_time_limit_positive(self):
        assert DEFAULT_TIME_LIMIT > 0

    def test_base_points_positive(self):
        assert BASE_POINTS > 0

    def test_multipliers(self):
        assert TIME_BONUS_MULTIPLIER > 0
        assert DIFFICULTY_MULTIPLIER >= 1.0
        assert SPECIAL_ROUND_MULTIPLIER >= 1

    def test_special_round_chance_valid(self):
        assert 0 <= SPECIAL_ROUND_CHANCE <= 1

    def test_questions_per_game(self):
        assert QUESTIONS_PER_GAME > 0

    def test_numeric_tolerance(self):
        assert 0 < NUMERIC_TOLERANCE < 1

    def test_joker_types_defined(self):
        assert isinstance(JOKER_5050, str)
        assert isinstance(JOKER_AUDIENCE, str)

    def test_jokers_per_game(self):
        assert JOKER_5050 in JOKERS_PER_GAME
        assert JOKER_AUDIENCE in JOKERS_PER_GAME
        assert all(v >= 0 for v in JOKERS_PER_GAME.values())

    def test_network_config(self):
        assert 1024 <= DEFAULT_PORT <= 65535
        assert BUFFER_SIZE > 0

    def test_fps(self):
        assert FPS > 0
