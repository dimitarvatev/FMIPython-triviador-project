"""Главно приложение на Triviador."""

import pygame
import sys
from typing import Optional

from triviador.core.config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, WHITE
from triviador.logic.game_logic import GameLogic
from triviador.ui.screens import (
    Screen, MainMenuScreen, GameSetupScreen,
    GameScreen, GameOverScreen, HighScoresScreen,
    HostGameScreen, JoinGameScreen,
    OnlineGameScreen,
)
from triviador.core.models import GameMode


class TriviadorGame:

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Triviador - Играта с въпроси")

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True

        self.game_logic = GameLogic()
        self.current_screen: Optional[Screen] = None
        self.online_lobby = None

        self._go_to_screen("main_menu")

    def _go_to_screen(self, screen_name: str, data: dict = None) -> None:

        data = data or {}

        if screen_name == "main_menu":
            if self.online_lobby:
                self.online_lobby.close()
                self.online_lobby = None
            self.current_screen = MainMenuScreen(self.screen)

        elif screen_name == "game_setup":
            categories = self.game_logic.get_categories()
            self.current_screen = GameSetupScreen(self.screen, categories)

        elif screen_name == "game":

            if data.get("continue_game"):
                game_logic = data.get("game_logic", self.game_logic)
                self.current_screen = GameScreen(self.screen, game_logic)
            else:
                player_names = data.get("player_names", ["Играч 1"])
                categories = data.get("categories", None)
                mode = data.get("mode", GameMode.STANDARD)

                self.game_logic.start_game(mode, player_names, categories)
                self.current_screen = GameScreen(self.screen, self.game_logic)

        elif screen_name == "game_over":
            results = data.get("results", {})
            self.current_screen = GameOverScreen(self.screen, results)

        elif screen_name == "highscores":
            highscores = self.game_logic.get_highscores()
            self.current_screen = HighScoresScreen(self.screen, highscores)

        elif screen_name == "host_game":
            self.current_screen = HostGameScreen(self.screen)

        elif screen_name == "join_game":
            self.current_screen = JoinGameScreen(self.screen)

        elif screen_name == "online_game":

            if hasattr(self.current_screen, 'lobby') and self.current_screen.lobby:
                self.online_lobby = self.current_screen.lobby

            self.current_screen = OnlineGameScreen(self.screen)
            self.current_screen.set_lobby(self.online_lobby)
            if data.get("categories"):
                self.current_screen.selected_categories = data["categories"]
            if data.get("mode"):
                self.current_screen.online_game_mode = data["mode"]

        if self.current_screen:
            self.current_screen.setup()

    def run(self) -> None:

        while self.running:
            dt = self.clock.tick(FPS) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif self.current_screen:
                    self.current_screen.handle_event(event)

            if self.current_screen:
                self.current_screen.update(dt)

                next_screen = self.current_screen.get_next_screen()
                if next_screen:
                    screen_name, screen_data = next_screen
                    self._go_to_screen(screen_name, screen_data)

            self.screen.fill(WHITE)
            if self.current_screen:
                self.current_screen.draw()

            pygame.display.flip()

        pygame.quit()
        sys.exit()


def main():
    """Входна точка за Triviador."""
    game = TriviadorGame()
    game.run()


if __name__ == "__main__":
    main()
