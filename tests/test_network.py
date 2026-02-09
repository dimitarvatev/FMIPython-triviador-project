"""Тестове за network.py — NetworkMessage, OnlinePlayer, GameLobby."""
import pytest
import time

from triviador.network.network import NetworkMessage, OnlinePlayer, GameLobby
from triviador.core.config import JOKER_5050, JOKER_AUDIENCE


# ─── NetworkMessage ─────────────────────────────────────────────────

class TestNetworkMessage:

    def test_to_json(self):
        msg = NetworkMessage(type="test", data={"key": "value"})
        json_str = msg.to_json()
        assert '"type"' in json_str
        assert '"test"' in json_str

    def test_from_json(self):
        msg = NetworkMessage(type="question", data={"text": "Въпрос?"})
        json_str = msg.to_json()
        restored = NetworkMessage.from_json(json_str)
        assert restored.type == "question"
        assert restored.data["text"] == "Въпрос?"

    def test_roundtrip(self):
        original = NetworkMessage(
            type="answer",
            data={"answer": "А", "time": 5.3},
            sender_id="player1",
        )
        restored = NetworkMessage.from_json(original.to_json())
        assert restored.type == original.type
        assert restored.data == original.data
        assert restored.sender_id == original.sender_id

    def test_from_json_no_sender(self):
        msg = NetworkMessage(type="test", data={})
        restored = NetworkMessage.from_json(msg.to_json())
        assert restored.sender_id is None


# ─── OnlinePlayer ───────────────────────────────────────────────────

class TestOnlinePlayer:

    def test_initial_state(self):
        p = OnlinePlayer(id="123", name="Иван")
        assert p.score == 0
        assert p.ready is False
        assert p.connected is True
        assert p.current_answer is None

    def test_jokers_initialized(self):
        p = OnlinePlayer(id="1", name="Тест")
        assert p.has_joker(JOKER_5050) is True
        assert p.has_joker(JOKER_AUDIENCE) is True

    def test_use_joker(self):
        p = OnlinePlayer(id="1", name="Тест")
        initial = p.jokers[JOKER_5050]
        assert p.use_joker(JOKER_5050) is True
        assert p.jokers[JOKER_5050] == initial - 1

    def test_use_joker_exhausted(self):
        p = OnlinePlayer(id="1", name="Тест")
        p.jokers[JOKER_5050] = 0
        assert p.use_joker(JOKER_5050) is False
        assert p.has_joker(JOKER_5050) is False

    def test_score_tracking(self):
        p = OnlinePlayer(id="1", name="Тест")
        p.score = 100
        p.score += 50
        assert p.score == 150


# ─── GameLobby (unit, без реална мрежа) ─────────────────────────────

class TestGameLobby:

    def test_create_as_host(self):
        lobby = GameLobby(is_host=True)
        assert lobby.is_host is True
        assert lobby.game_started is False
        assert len(lobby.players) == 0

    def test_create_as_client(self):
        lobby = GameLobby(is_host=False)
        assert lobby.is_host is False

    def test_get_players_list(self):
        lobby = GameLobby(is_host=True)
        lobby.players["1"] = OnlinePlayer(id="1", name="А")
        lobby.players["2"] = OnlinePlayer(id="2", name="Б")
        players = lobby.get_players_list()
        assert len(players) == 2

    def test_start_game_not_host(self):
        lobby = GameLobby(is_host=False)
        assert lobby.start_game() is False

    def test_start_game_too_few_players(self):
        lobby = GameLobby(is_host=True)
        lobby.players["host"] = OnlinePlayer(id="host", name="Хост")
        assert lobby.start_game() is False

    def test_close_without_server(self):
        lobby = GameLobby(is_host=True)
        # Не трябва да хвърля грешка
        lobby.close()

    def test_get_local_ip(self):
        lobby = GameLobby(is_host=True)
        ip = lobby.get_local_ip()
        assert isinstance(ip, str)
        assert len(ip) > 0
