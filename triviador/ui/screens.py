"""Екрани за Triviador играта."""

import pygame
import time
from typing import Optional, Callable
from abc import ABC, abstractmethod

from triviador.core.config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, BLACK, GRAY, LIGHT_GRAY, DARK_GRAY,
    BLUE, GREEN, RED, YELLOW, PURPLE, ORANGE,
    FONT_SMALL, FONT_MEDIUM, FONT_LARGE, FONT_XLARGE, FONT_TITLE,
    DEFAULT_TIME_LIMIT, JOKER_5050, JOKER_AUDIENCE, DEFAULT_PORT
)
from triviador.ui.ui_components import (
    Button, TextInput, CheckBox, ProgressBar, Label, Panel,
    AnswerButton, JokerButton, DifficultyIndicator, AudienceChart
)
from triviador.core.models import GameMode, Question, QuestionType


class Screen(ABC):
    """Базов клас за екран."""
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.components = []
        self.next_screen: Optional[str] = None
        self.screen_data: dict = {}
    
    @abstractmethod
    def setup(self) -> None:
        """Инициализира екрана."""
        pass
    
    @abstractmethod
    def handle_event(self, event: pygame.event.Event) -> None:
        """Обработва събитие."""
        pass
    
    @abstractmethod
    def update(self, dt: float) -> None:
        """Обновява състоянието."""
        pass
    
    @abstractmethod
    def draw(self) -> None:
        """Рисува екрана."""
        pass
    
    def get_next_screen(self) -> Optional[tuple[str, dict]]:
        """Връща следващия екран и данните за него."""
        if self.next_screen:
            return (self.next_screen, self.screen_data)
        return None


class MainMenuScreen(Screen):
    """Главно меню."""
    
    def setup(self) -> None:
        center_x = SCREEN_WIDTH // 2
        
        # Заглавие
        self.title_font = pygame.font.Font(None, FONT_TITLE)
        
        # Бутони
        button_width = 300
        button_height = 60
        button_spacing = 15
        start_y = 250
        
        self.buttons = [
            Button(
                center_x - button_width // 2, start_y,
                button_width, button_height,
                "Нова игра", FONT_LARGE, BLUE,
                callback=self._on_new_game
            ),
            Button(
                center_x - button_width // 2, start_y + button_height + button_spacing,
                button_width, button_height,
                "Създай онлайн игра", FONT_LARGE, ORANGE,
                callback=self._on_host_game
            ),
            Button(
                center_x - button_width // 2, start_y + 2 * (button_height + button_spacing),
                button_width, button_height,
                "Присъедини се онлайн", FONT_LARGE, PURPLE,
                callback=self._on_join_game
            ),
            Button(
                center_x - button_width // 2, start_y + 3 * (button_height + button_spacing),
                button_width, button_height,
                "Топ 10 резултата", FONT_LARGE, GRAY,
                callback=self._on_highscores
            ),
            Button(
                center_x - button_width // 2, start_y + 4 * (button_height + button_spacing),
                button_width, button_height,
                "Изход", FONT_LARGE, RED,
                callback=self._on_exit
            )
        ]
    
    def _on_new_game(self) -> None:
        self.next_screen = "game_setup"
    
    def _on_host_game(self) -> None:
        self.next_screen = "host_game"
    
    def _on_join_game(self) -> None:
        self.next_screen = "join_game"
    
    def _on_highscores(self) -> None:
        self.next_screen = "highscores"
    
    def _on_exit(self) -> None:
        pygame.event.post(pygame.event.Event(pygame.QUIT))
    
    def handle_event(self, event: pygame.event.Event) -> None:
        for button in self.buttons:
            button.handle_event(event)
    
    def update(self, dt: float) -> None:
        pass
    
    def draw(self) -> None:
        self.screen.fill(LIGHT_GRAY)
        
        # Заглавие
        title = self.title_font.render("TRIVIADOR", True, BLUE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 120))
        self.screen.blit(title, title_rect)
        
        # Подзаглавие
        subtitle_font = pygame.font.Font(None, FONT_LARGE)
        subtitle = subtitle_font.render("Играта с въпроси и отговори", True, GRAY)
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, 190))
        self.screen.blit(subtitle, subtitle_rect)
        
        # Бутони
        for button in self.buttons:
            button.draw(self.screen)


class GameSetupScreen(Screen):
    """Екран за настройка на играта."""
    
    def __init__(self, screen: pygame.Surface, categories: list[str] = None):
        super().__init__(screen)
        self.available_categories = categories or []
        self.player_names: list[str] = []
        self.num_players = 1
        self.selected_categories: list[str] = []
        self.game_mode = GameMode.STANDARD
    
    def setup(self) -> None:
        center_x = SCREEN_WIDTH // 2
        
        # Полета за имена
        self._create_name_inputs()
        
        # Чекбоксове за категории
        self.category_checkboxes: list[CheckBox] = []
        categories_start_y = 150 + self.num_players * 55 + 50
        
        for i, category in enumerate(self.available_categories):
            col = i % 2
            row = i // 2
            self.category_checkboxes.append(
                CheckBox(
                    100 + col * 400, categories_start_y + row * 40,
                    25, category, checked=True
                )
            )
        
        # Бутони за режим
        mode_y = categories_start_y + ((len(self.available_categories) + 1) // 2) * 40 + 30
        
        self.mode_buttons = [
            Button(
                center_x - 310, mode_y, 200, 50,
                "Стандартен", FONT_MEDIUM, BLUE,
                callback=lambda: self._set_mode(GameMode.STANDARD)
            ),
            Button(
                center_x - 100, mode_y, 200, 50,
                "Безкраен", FONT_MEDIUM, ORANGE,
                callback=lambda: self._set_mode(GameMode.ENDLESS)
            )
        ]
        
        # Бутон за старт
        self.start_button = Button(
            center_x - 100, mode_y + 80, 200, 60,
            "Започни играта", FONT_LARGE, GREEN,
            callback=self._on_start
        )
        
        # Бутон за назад
        self.back_button = Button(
            50, SCREEN_HEIGHT - 70, 120, 50,
            "Назад", FONT_MEDIUM, GRAY,
            callback=self._on_back
        )
        
        self._update_mode_buttons()
    
    def _set_mode(self, mode: GameMode) -> None:
        self.game_mode = mode
        self._update_mode_buttons()
    
    def _create_name_inputs(self) -> None:
        """Създава полета за въвеждане на имена."""
        center_x = SCREEN_WIDTH // 2
        self.name_inputs = []
        
        self.name_inputs.append(
            TextInput(
                center_x - 150, 150, 300, 45,
                placeholder="Твоето име",
                max_length=15
            )
        )
    
    def _update_mode_buttons(self) -> None:
        colors = {GameMode.STANDARD: BLUE, GameMode.ENDLESS: ORANGE}
        for i, btn in enumerate(self.mode_buttons):
            mode = GameMode.STANDARD if i == 0 else GameMode.ENDLESS
            if mode == self.game_mode:
                btn.bg_color = colors[mode]
            else:
                btn.bg_color = GRAY
    
    def _on_start(self) -> None:
        # Събираме имената
        self.player_names = [inp.get_value().strip() or f"Играч {i+1}" 
                           for i, inp in enumerate(self.name_inputs)]
        
        # Събираме категориите
        self.selected_categories = [
            cb.label for cb in self.category_checkboxes if cb.checked
        ]
        
        if not self.selected_categories:
            self.selected_categories = self.available_categories.copy()
        
        self.next_screen = "game"
        self.screen_data = {
            "player_names": self.player_names,
            "categories": self.selected_categories,
            "mode": self.game_mode
        }
    
    def _on_back(self) -> None:
        self.next_screen = "main_menu"
    
    def handle_event(self, event: pygame.event.Event) -> None:
        for input_field in self.name_inputs:
            input_field.handle_event(event)
        
        for checkbox in self.category_checkboxes:
            checkbox.handle_event(event)
        
        for button in self.mode_buttons:
            button.handle_event(event)
        
        self.start_button.handle_event(event)
        self.back_button.handle_event(event)
    
    def update(self, dt: float) -> None:
        for input_field in self.name_inputs:
            input_field.update(dt)
    
    def draw(self) -> None:
        self.screen.fill(LIGHT_GRAY)
        
        # Заглавие
        title_font = pygame.font.Font(None, FONT_XLARGE)
        title_surface = title_font.render("Нова игра", True, BLUE)
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, 50))
        self.screen.blit(title_surface, title_rect)
        
        font = pygame.font.Font(None, FONT_MEDIUM)
        
        # Етикет за имена
        names_label = font.render("Въведете име:", True, BLACK)
        self.screen.blit(names_label, (SCREEN_WIDTH // 2 - 150, 120))
        
        # Полета за имена
        for input_field in self.name_inputs:
            input_field.draw(self.screen)
        
        # Етикет за категории
        cat_y = 170 + self.num_players * 55 + 20
        categories_label = font.render("Изберете категории:", True, BLACK)
        self.screen.blit(categories_label, (100, cat_y))
        
        # Чекбоксове
        for checkbox in self.category_checkboxes:
            checkbox.draw(self.screen)
        
        # Етикет за режим
        mode_y = cat_y + ((len(self.available_categories) + 1) // 2) * 40 + 30
        mode_label = font.render("Режим на игра:", True, BLACK)
        self.screen.blit(mode_label, (SCREEN_WIDTH // 2 - 310, mode_y - 30))
        
        # Бутони за режим
        for button in self.mode_buttons:
            button.draw(self.screen)
        
        # Бутони
        self.start_button.draw(self.screen)
        self.back_button.draw(self.screen)


class GameScreen(Screen):
    """Основен игрови екран."""
    
    def __init__(self, screen: pygame.Surface, game_logic):
        super().__init__(screen)
        self.game_logic = game_logic
        self.answer_buttons: list[AnswerButton] = []
        self.numeric_input: Optional[TextInput] = None
        self.joker_buttons: list[JokerButton] = []
        self.audience_chart: Optional[AudienceChart] = None
        self.show_audience = False
        self.answer_submitted = False
        self.waiting_for_next = False
        self.feedback_message = ""
        self.feedback_color = WHITE
    
    def setup(self) -> None:
        # Индикатор за трудност (трябва да е преди _setup_question_ui)
        self.difficulty_indicator = DifficultyIndicator(SCREEN_WIDTH - 150, 130)
        
        # Лента за време
        self.timer_bar = ProgressBar(
            50, 180, SCREEN_WIDTH - 100, 30,
            DEFAULT_TIME_LIMIT, GREEN
        )
        
        # Бутон за следващ въпрос
        self.next_button = Button(
            SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 80, 200, 50,
            "Следващ въпрос", FONT_MEDIUM, BLUE,
            callback=self._on_next_question
        )
        self.next_button.enabled = False
        
        self._setup_joker_buttons()
        self._setup_question_ui()
    
    def _setup_joker_buttons(self) -> None:
        player = self.game_logic.game_state.current_player
        if not player:
            return
        
        self.joker_buttons = [
            JokerButton(50, SCREEN_HEIGHT - 150, 150, 40, JOKER_5050, player.jokers.get(JOKER_5050, 0)),
            JokerButton(220, SCREEN_HEIGHT - 150, 180, 40, JOKER_AUDIENCE, player.jokers.get(JOKER_AUDIENCE, 0))
        ]
        
        for btn in self.joker_buttons:
            btn.callback = lambda jt=btn.joker_type: self._on_use_joker(jt)
    
    def _update_joker_button_text(self, question: Question) -> None:
        """Обновява текста на жокер бутоните според типа въпрос."""
        for btn in self.joker_buttons:
            if btn.joker_type == JOKER_5050:
                if question.question_type == QuestionType.NUMERIC:
                    btn.set_display_name("Диапазон")
                else:
                    btn.set_display_name("50/50")
    
    def _setup_question_ui(self) -> None:
        question = self.game_logic.get_current_question()
        if not question:
            return
        
        self.difficulty_indicator.set_difficulty(question.difficulty)
        self.answer_buttons = []
        self.numeric_input = None
        self.show_audience = False
        self.audience_chart = None
        self.answer_submitted = False
        self.waiting_for_next = False
        self.feedback_message = ""
        
        # Обновяваме текста на 50/50 бутона според типа въпрос
        self._update_joker_button_text(question)
        
        if question.question_type == QuestionType.MULTIPLE_CHOICE:
            # Бутони за отговори
            letters = ['A', 'B', 'C', 'D']
            for i, option in enumerate(question.options):
                row = i // 2
                col = i % 2
                btn = AnswerButton(
                    100 + col * 400, 350 + row * 80,
                    380, 60, option, letters[i]
                )
                btn.callback = lambda opt=option: self._on_answer(opt)
                self.answer_buttons.append(btn)
        else:
            # Поле за числов отговор
            self.numeric_input = TextInput(
                SCREEN_WIDTH // 2 - 150, 400, 300, 60,
                FONT_LARGE, "Въведете число...", 20, True
            )
            self.numeric_input.active = True
            
            # Бутон за потвърждение
            self.submit_button = Button(
                SCREEN_WIDTH // 2 - 100, 480, 200, 50,
                "Потвърди", FONT_MEDIUM, GREEN,
                callback=self._on_submit_numeric
            )
    
    def _on_answer(self, answer: str) -> None:
        if self.answer_submitted:
            return
        
        self.answer_submitted = True
        result = self.game_logic.submit_answer(answer)
        
        # Показваме резултата
        question = self.game_logic.game_state.current_question
        for btn in self.answer_buttons:
            if btn.text == question.correct_answer:
                btn.set_state("correct")
            elif btn.text == answer and not result["is_correct"]:
                btn.set_state("wrong")
        
        self._show_feedback(result)
    
    def _on_submit_numeric(self) -> None:
        if self.answer_submitted or not self.numeric_input:
            return
        
        answer = self.numeric_input.get_value()
        if not answer:
            return
        
        self.answer_submitted = True
        result = self.game_logic.submit_answer(answer)
        self._show_feedback(result)
    
    def _show_feedback(self, result: dict) -> None:
        if result.get("is_correct"):
            self.feedback_message = f"Правилно! +{result['points']} точки"
            self.feedback_color = GREEN
        else:
            self.feedback_message = f"Грешно! Правилният отговор е: {result['correct_answer']}"
            self.feedback_color = RED
        
        self.waiting_for_next = True
        self.next_button.enabled = True
        
        # Деактивираме жокерите
        for btn in self.joker_buttons:
            btn.enabled = False
    
    def _on_next_question(self) -> None:
        if self.game_logic.game_state.game_over:
            self.next_screen = "game_over"
            self.screen_data = {"results": self.game_logic.end_game()}
            return
        
        has_next = self.game_logic.next_question()
        if has_next:
            self._setup_joker_buttons()
            self._setup_question_ui()
            self._update_joker_buttons()
            self.next_button.enabled = False
            self.next_button.set_text("Следващ въпрос")
        else:
            self.next_screen = "game_over"
            self.screen_data = {"results": self.game_logic.end_game()}
    
    def _on_use_joker(self, joker_type: str) -> None:
        if self.answer_submitted:
            return
        
        result = self.game_logic.use_joker(joker_type)
        
        if "error" in result:
            self.feedback_message = result["error"]
            self.feedback_color = RED
            return
        
        self._update_joker_buttons()
        
        if result.get("type") == "5050":
            remaining = result.get("remaining_options", [])
            question = self.game_logic.game_state.current_question
            
            if question.question_type == QuestionType.MULTIPLE_CHOICE:
                for btn in self.answer_buttons:
                    if btn.text not in remaining:
                        btn.set_state("eliminated")
            else:
                # Показваме диапазона
                if remaining:
                    self.feedback_message = f"Диапазон: {remaining[0]}"
                    self.feedback_color = BLUE
        
        elif result.get("type") == "audience":
            votes = result.get("votes", {})
            question = self.game_logic.game_state.current_question
            
            if question.question_type == QuestionType.MULTIPLE_CHOICE:
                self.show_audience = True
                self.audience_chart = AudienceChart(
                    SCREEN_WIDTH // 2 - 200, 250, 400, 200
                )
                self.audience_chart.set_votes(votes)
            else:
                # За числови въпроси
                suggested = votes.get("suggested_value", "?")
                confidence = votes.get("confidence", 0)
                self.feedback_message = f"Публиката предлага: {suggested} (увереност: {confidence}%)"
                self.feedback_color = PURPLE
    
    def _update_joker_buttons(self) -> None:
        player = self.game_logic.game_state.current_player
        if not player:
            return
        
        is_special = self.game_logic.game_state.is_special_round
        
        for btn in self.joker_buttons:
            count = player.jokers.get(btn.joker_type, 0)
            btn.update_count(count)
            btn.enabled = count > 0 and not is_special and not self.answer_submitted
    
    def handle_event(self, event: pygame.event.Event) -> None:
        for btn in self.answer_buttons:
            if btn.enabled:
                btn.handle_event(event)
        
        if self.numeric_input and not self.answer_submitted:
            result = self.numeric_input.handle_event(event)
            if result is not None:  # Enter pressed
                self._on_submit_numeric()
            
            if hasattr(self, 'submit_button'):
                self.submit_button.handle_event(event)
        
        for btn in self.joker_buttons:
            if btn.enabled:
                btn.handle_event(event)
        
        self.next_button.handle_event(event)
    
    def update(self, dt: float) -> None:
        if self.numeric_input:
            self.numeric_input.update(dt)
        
        # Обновяваме таймера
        if not self.answer_submitted:
            remaining = self.game_logic.get_remaining_time()
            self.timer_bar.set_value(remaining)
            
            if remaining <= 0:
                # Времето изтече
                self.answer_submitted = True
                result = self.game_logic.submit_answer("")
                self._show_feedback({"is_correct": False, "correct_answer": 
                    self.game_logic.game_state.current_question.correct_answer})
    
    def draw(self) -> None:
        self.screen.fill(LIGHT_GRAY)
        
        question = self.game_logic.get_current_question()
        player = self.game_logic.game_state.current_player
        
        if not question or not player:
            return
        
        # Информация за играча
        font = pygame.font.Font(None, FONT_MEDIUM)
        player_info = font.render(f"Играч: {player.name} | Точки: {player.score}", True, BLACK)
        self.screen.blit(player_info, (50, 20))
        
        # Номер на въпрос
        q_num = self.game_logic.game_state.current_question_index + 1
        total = len(self.game_logic.game_state.questions) if self.game_logic.game_state.mode != GameMode.ENDLESS else "∞"
        question_num = font.render(f"Въпрос {q_num}/{total}", True, BLACK)
        self.screen.blit(question_num, (SCREEN_WIDTH - 200, 20))
        
        # Категория
        category = font.render(f"Категория: {question.category}", True, GRAY)
        self.screen.blit(category, (50, 50))
        
        # Индикатор за трудност
        difficulty_label = font.render("Трудност:", True, BLACK)
        self.screen.blit(difficulty_label, (SCREEN_WIDTH - 250, 130))
        self.difficulty_indicator.draw(self.screen)
        
        # Специален рунд
        if self.game_logic.game_state.is_special_round:
            special_font = pygame.font.Font(None, FONT_LARGE)
            special_text = special_font.render("★ СПЕЦИАЛЕН РУНД - ДВОЙНИ ТОЧКИ! ★", True, YELLOW)
            special_rect = special_text.get_rect(center=(SCREEN_WIDTH // 2, 100))
            pygame.draw.rect(self.screen, PURPLE, special_rect.inflate(20, 10), border_radius=5)
            self.screen.blit(special_text, special_rect)
        
        # Таймер
        self.timer_bar.draw(self.screen)
        time_text = font.render(f"{int(self.game_logic.get_remaining_time())}с", True, BLACK)
        self.screen.blit(time_text, (SCREEN_WIDTH - 45, 185))
        
        # Въпрос
        question_font = pygame.font.Font(None, FONT_LARGE)
        # Разбиваме дългите въпроси
        words = question.question_text.split()
        lines = []
        current_line = ""
        for word in words:
            test_line = current_line + " " + word if current_line else word
            if question_font.size(test_line)[0] < SCREEN_WIDTH - 100:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        lines.append(current_line)
        
        for i, line in enumerate(lines):
            text = question_font.render(line, True, BLACK)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, 250 + i * 40))
            self.screen.blit(text, text_rect)
        
        # Отговори
        for btn in self.answer_buttons:
            btn.draw(self.screen)
        
        if self.numeric_input:
            self.numeric_input.draw(self.screen)
            if hasattr(self, 'submit_button') and not self.answer_submitted:
                self.submit_button.draw(self.screen)
        
        # Графика за публиката
        if self.show_audience and self.audience_chart:
            self.audience_chart.draw(self.screen)
        
        # Жокери
        for btn in self.joker_buttons:
            btn.draw(self.screen)
        
        # Съобщение за обратна връзка
        if self.feedback_message:
            feedback_font = pygame.font.Font(None, FONT_LARGE)
            feedback = feedback_font.render(self.feedback_message, True, self.feedback_color)
            feedback_rect = feedback.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 130))
            
            # Фон за съобщението
            bg_rect = feedback_rect.inflate(20, 10)
            pygame.draw.rect(self.screen, BLACK, bg_rect, border_radius=5)
            self.screen.blit(feedback, feedback_rect)
        
        # Бутон за следващ въпрос
        self.next_button.draw(self.screen)


class GameOverScreen(Screen):
    """Екран за край на играта."""
    
    def __init__(self, screen: pygame.Surface, results: dict):
        super().__init__(screen)
        self.results = results
    
    def setup(self) -> None:
        center_x = SCREEN_WIDTH // 2
        
        self.menu_button = Button(
            center_x - 150, SCREEN_HEIGHT - 100, 130, 50,
            "Меню", FONT_MEDIUM, BLUE,
            callback=self._on_menu
        )
        
        self.play_again_button = Button(
            center_x + 20, SCREEN_HEIGHT - 100, 130, 50,
            "Нова игра", FONT_MEDIUM, GREEN,
            callback=self._on_play_again
        )
    
    def _on_menu(self) -> None:
        self.next_screen = "main_menu"
    
    def _on_play_again(self) -> None:
        self.next_screen = "game_setup"
    
    def handle_event(self, event: pygame.event.Event) -> None:
        self.menu_button.handle_event(event)
        self.play_again_button.handle_event(event)
    
    def update(self, dt: float) -> None:
        pass
    
    def draw(self) -> None:
        self.screen.fill(LIGHT_GRAY)
        
        # Заглавие
        title_font = pygame.font.Font(None, FONT_TITLE)
        title = title_font.render("КРАЙ НА ИГРАТА", True, BLUE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 80))
        self.screen.blit(title, title_rect)
        
        # Резултати
        players = self.results.get("players", [])
        
        font = pygame.font.Font(None, FONT_LARGE)
        small_font = pygame.font.Font(None, FONT_MEDIUM)
        
        for i, player in enumerate(players):
            y = 180 + i * 120
            
            # Позиция
            rank_colors = {1: (255, 215, 0), 2: (192, 192, 192), 3: (205, 127, 50)}
            rank_color = rank_colors.get(player["rank"], BLACK)
            
            rank_text = font.render(f"#{player['rank']}", True, rank_color)
            self.screen.blit(rank_text, (100, y))
            
            # Име и резултат
            name_text = font.render(player["name"], True, BLACK)
            self.screen.blit(name_text, (180, y))
            
            score_text = font.render(f"{player['score']} точки", True, GREEN)
            self.screen.blit(score_text, (400, y))
            
            # Статистика
            stats = f"Верни: {player['correct_answers']}/{player['total_answers']} ({player['accuracy']:.1f}%)"
            stats_text = small_font.render(stats, True, GRAY)
            self.screen.blit(stats_text, (180, y + 40))
            
            # Highscore
            if "highscore_rank" in player:
                hs_text = small_font.render(f"★ Нов highscore! Позиция #{player['highscore_rank']}", True, YELLOW)
                pygame.draw.rect(self.screen, PURPLE, 
                    pygame.Rect(175, y + 65, hs_text.get_width() + 10, 25), 
                    border_radius=3)
                self.screen.blit(hs_text, (180, y + 68))
        
        # Бутони
        self.menu_button.draw(self.screen)
        self.play_again_button.draw(self.screen)


class HighScoresScreen(Screen):
    """Екран за високи резултати."""
    
    def __init__(self, screen: pygame.Surface, highscores: list):
        super().__init__(screen)
        self.highscores = highscores
    
    def setup(self) -> None:
        self.back_button = Button(
            SCREEN_WIDTH // 2 - 75, SCREEN_HEIGHT - 80, 150, 50,
            "Назад", FONT_MEDIUM, BLUE,
            callback=self._on_back
        )
    
    def _on_back(self) -> None:
        self.next_screen = "main_menu"
    
    def handle_event(self, event: pygame.event.Event) -> None:
        self.back_button.handle_event(event)
    
    def update(self, dt: float) -> None:
        pass
    
    def draw(self) -> None:
        self.screen.fill(LIGHT_GRAY)
        
        # Заглавие
        title_font = pygame.font.Font(None, FONT_XLARGE)
        title = title_font.render("ТОП 10 РЕЗУЛТАТИ", True, PURPLE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 50))
        self.screen.blit(title, title_rect)
        
        if not self.highscores:
            font = pygame.font.Font(None, FONT_LARGE)
            no_scores = font.render("Все още няма записани резултати", True, GRAY)
            no_scores_rect = no_scores.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.screen.blit(no_scores, no_scores_rect)
        else:
            font = pygame.font.Font(None, FONT_MEDIUM)
            
            # Заглавен ред
            headers = ["#", "Име", "Точки", "Режим", "Верни", "Точност", "Дата"]
            header_x = [50, 100, 280, 400, 520, 620, 720]
            
            for i, header in enumerate(headers):
                text = font.render(header, True, DARK_GRAY)
                self.screen.blit(text, (header_x[i], 110))
            
            # Линия
            pygame.draw.line(self.screen, DARK_GRAY, (50, 140), (SCREEN_WIDTH - 50, 140), 2)
            
            # Резултати
            for i, hs in enumerate(self.highscores):
                y = 160 + i * 50
                
                # Цвят за топ 3
                colors = {0: (255, 215, 0), 1: (192, 192, 192), 2: (205, 127, 50)}
                color = colors.get(i, BLACK)
                
                data = [
                    str(i + 1),
                    hs.player_name[:12],
                    str(hs.score),
                    hs.mode[:8],
                    str(hs.questions_answered),
                    f"{hs.accuracy:.1f}%",
                    hs.date
                ]
                
                for j, value in enumerate(data):
                    text = font.render(value, True, color if j < 3 else BLACK)
                    self.screen.blit(text, (header_x[j], y))
        
        self.back_button.draw(self.screen)


class HostGameScreen(Screen):
    """Екран за хостване на онлайн игра."""
    
    def __init__(self, screen: pygame.Surface):
        super().__init__(screen)
        from triviador.network.network import GameLobby, OnlinePlayer
        
        self.lobby: Optional[GameLobby] = None
        self.status_message = ""
        self.error_message = ""
        
        # Въвеждане на име
        self.name_input = TextInput(
            SCREEN_WIDTH // 2 - 150, 200, 300, 50,
            placeholder="Въведи име...",
            max_length=15
        )
        
        # Бутони
        self.create_button = Button(
            SCREEN_WIDTH // 2 - 100, 280, 200, 50,
            "Създай игра", FONT_MEDIUM, GREEN
        )
        self.create_button.callback = self._on_create
        
        self.start_button = Button(
            SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 80, 200, 50,
            "Започни играта", FONT_MEDIUM, BLUE
        )
        self.start_button.callback = self._on_start
        self.start_button.enabled = False
        
        self.back_button = Button(
            50, SCREEN_HEIGHT - 80, 120, 50,
            "Назад", FONT_MEDIUM, GRAY
        )
        self.back_button.callback = self._on_back
        
        self.hosting = False
        self.players_in_lobby: list[OnlinePlayer] = []
        
        # Настройки за играта
        self.game_mode = GameMode.STANDARD
        self.available_categories: list[str] = []
        self.selected_categories: list[str] = []
        self.category_checkboxes: list[CheckBox] = []
        self.mode_buttons: list[Button] = []
    
    def setup(self) -> None:
        self.hosting = False
        self.status_message = ""
        self.error_message = ""
        self.players_in_lobby = []
        self.start_button.enabled = False
        self.game_mode = GameMode.STANDARD
        
        if self.lobby:
            self.lobby.close()
            self.lobby = None
        
        # Зареждаме категориите
        from triviador.logic.question_manager import QuestionManager
        qm = QuestionManager()
        self.available_categories = qm.get_categories()
        self.selected_categories = self.available_categories.copy()
        self._setup_settings_ui()
    
    def _setup_settings_ui(self) -> None:
        """Създава UI за настройки на играта."""
        center_x = SCREEN_WIDTH // 2
        
        # Чекбоксове за категории
        self.category_checkboxes = []
        cat_start_y = 360
        for i, category in enumerate(self.available_categories):
            col = i % 2
            row = i // 2
            self.category_checkboxes.append(
                CheckBox(
                    center_x - 200 + col * 210, cat_start_y + row * 35,
                    22, category, checked=True
                )
            )
        
        # Бутони за режим
        num_rows = (len(self.available_categories) + 1) // 2
        mode_y = cat_start_y + num_rows * 35 + 30
        
        self.mode_buttons = [
            Button(
                center_x - 220, mode_y, 200, 45,
                "Стандартен", FONT_MEDIUM, BLUE,
                callback=lambda: self._set_mode(GameMode.STANDARD)
            ),
            Button(
                center_x + 20, mode_y, 200, 45,
                "Безкраен", FONT_MEDIUM, ORANGE,
                callback=lambda: self._set_mode(GameMode.ENDLESS)
            )
        ]
        self._update_mode_buttons()
    
    def _set_mode(self, mode: GameMode) -> None:
        self.game_mode = mode
        self._update_mode_buttons()
    
    def _update_mode_buttons(self) -> None:
        colors = {GameMode.STANDARD: BLUE, GameMode.ENDLESS: ORANGE}
        for i, btn in enumerate(self.mode_buttons):
            mode = GameMode.STANDARD if i == 0 else GameMode.ENDLESS
            btn.bg_color = colors[mode] if mode == self.game_mode else GRAY
    
    def _on_create(self) -> None:
        from triviador.network.network import GameLobby
        
        name = self.name_input.get_value().strip()
        if not name:
            self.error_message = "Моля, въведи име!"
            return
        
        self.lobby = GameLobby(is_host=True)
        self.lobby.on_player_joined = self._on_player_joined
        self.lobby.on_player_left = self._on_player_left
        
        if self.lobby.host_game(name):
            self.hosting = True
            self.error_message = ""
            ip = self.lobby.get_local_ip()
            self.status_message = f"Игра създадена! IP: {ip}:{DEFAULT_PORT}"
            self.players_in_lobby = self.lobby.get_players_list()
        else:
            self.error_message = "Грешка при създаване на играта!"
    
    def _on_player_joined(self, player) -> None:
        self.players_in_lobby = self.lobby.get_players_list()
        self.start_button.enabled = len(self.players_in_lobby) >= 2
    
    def _on_player_left(self, player_id: str) -> None:
        self.players_in_lobby = self.lobby.get_players_list()
        self.start_button.enabled = len(self.players_in_lobby) >= 2
    
    def _on_start(self) -> None:
        if self.lobby and len(self.players_in_lobby) >= 2:
            # Събираме избраните категории
            self.selected_categories = [
                cb.label for cb in self.category_checkboxes if cb.checked
            ]
            if not self.selected_categories:
                self.selected_categories = self.available_categories.copy()
            
            self.next_screen = "online_game"
            self.screen_data = {
                "categories": self.selected_categories,
                "mode": self.game_mode
            }
    
    def _on_back(self) -> None:
        if self.lobby:
            self.lobby.close()
        self.next_screen = "main_menu"
    
    def handle_event(self, event: pygame.event.Event) -> None:
        self.name_input.handle_event(event)
        
        if not self.hosting:
            self.create_button.handle_event(event)
        else:
            self.start_button.handle_event(event)
            
            for cb in self.category_checkboxes:
                cb.handle_event(event)
            for btn in self.mode_buttons:
                btn.handle_event(event)
        
        self.back_button.handle_event(event)
    
    def update(self, dt: float) -> None:
        self.name_input.update(dt)
    
    def draw(self) -> None:
        self.screen.fill(LIGHT_GRAY)
        
        # Заглавие
        title_font = pygame.font.Font(None, FONT_XLARGE)
        title = title_font.render("СЪЗДАЙ ОНЛАЙН ИГРА", True, PURPLE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 80))
        self.screen.blit(title, title_rect)
        
        if not self.hosting:
            # Въвеждане на име
            font = pygame.font.Font(None, FONT_MEDIUM)
            name_label = font.render("Твоето име:", True, BLACK)
            self.screen.blit(name_label, (SCREEN_WIDTH // 2 - 150, 170))
            
            self.name_input.draw(self.screen)
            self.create_button.draw(self.screen)
        else:
            # Показваме статус
            font = pygame.font.Font(None, FONT_LARGE)
            status = font.render(self.status_message, True, GREEN)
            status_rect = status.get_rect(center=(SCREEN_WIDTH // 2, 150))
            self.screen.blit(status, status_rect)
            
            # Списък с играчи
            font = pygame.font.Font(None, FONT_MEDIUM)
            players_title = font.render("Играчи в лобито:", True, BLACK)
            self.screen.blit(players_title, (SCREEN_WIDTH // 2 - 100, 220))
            
            for i, player in enumerate(self.players_in_lobby):
                y = 260 + i * 40
                color = BLUE if player.id == "host" else BLACK
                marker = "👑 " if player.id == "host" else "• "
                text = font.render(f"{marker}{player.name}", True, color)
                self.screen.blit(text, (SCREEN_WIDTH // 2 - 80, y))
            
            # Чакаме играчи
            if len(self.players_in_lobby) < 2:
                wait_text = font.render("Чакаме играчи... (мин. 2)", True, GRAY)
                wait_rect = wait_text.get_rect(center=(SCREEN_WIDTH // 2, 200))
                self.screen.blit(wait_text, wait_rect)
            
            # Настройки на играта
            settings_label = font.render("Категории:", True, BLACK)
            self.screen.blit(settings_label, (SCREEN_WIDTH // 2 - 200, 330))
            
            for cb in self.category_checkboxes:
                cb.draw(self.screen)
            
            num_rows = (len(self.available_categories) + 1) // 2
            mode_label_y = 360 + num_rows * 35 + 5
            mode_label = font.render("Режим:", True, BLACK)
            self.screen.blit(mode_label, (SCREEN_WIDTH // 2 - 200, mode_label_y))
            
            for btn in self.mode_buttons:
                btn.draw(self.screen)
            
            self.start_button.draw(self.screen)
        
        # Грешка
        if self.error_message:
            error_font = pygame.font.Font(None, FONT_MEDIUM)
            error = error_font.render(self.error_message, True, RED)
            error_rect = error.get_rect(center=(SCREEN_WIDTH // 2, 350))
            self.screen.blit(error, error_rect)
        
        self.back_button.draw(self.screen)


class JoinGameScreen(Screen):
    """Екран за присъединяване към онлайн игра."""
    
    def __init__(self, screen: pygame.Surface):
        super().__init__(screen)
        from triviador.network.network import GameLobby, OnlinePlayer
        
        self.lobby: Optional[GameLobby] = None
        self.status_message = ""
        self.error_message = ""
        
        # Въвеждане на име
        self.name_input = TextInput(
            SCREEN_WIDTH // 2 - 150, 180, 300, 50,
            placeholder="Въведи име...",
            max_length=15
        )
        
        # Въвеждане на IP
        self.ip_input = TextInput(
            SCREEN_WIDTH // 2 - 150, 280, 300, 50,
            placeholder="IP адрес (напр. 192.168.1.10)",
            max_length=21
        )
        
        # Бутони
        self.join_button = Button(
            SCREEN_WIDTH // 2 - 100, 360, 200, 50,
            "Присъедини се", FONT_MEDIUM, BLUE
        )
        self.join_button.callback = self._on_join
        
        self.back_button = Button(
            50, SCREEN_HEIGHT - 80, 120, 50,
            "Назад", FONT_MEDIUM, GRAY
        )
        self.back_button.callback = self._on_back
        
        self.joined = False
        self.players_in_lobby: list[OnlinePlayer] = []
    
    def setup(self) -> None:
        self.joined = False
        self.status_message = ""
        self.error_message = ""
        self.players_in_lobby = []
        
        if self.lobby:
            self.lobby.close()
            self.lobby = None
    
    def _on_join(self) -> None:
        from triviador.network.network import GameLobby
        
        name = self.name_input.get_value().strip()
        if not name:
            self.error_message = "Моля, въведи име!"
            return
        
        ip = self.ip_input.get_value().strip()
        if not ip:
            self.error_message = "Моля, въведи IP адрес!"
            return
        
        # Парсваме IP и порт
        host = ip
        port = DEFAULT_PORT
        if ":" in ip:
            parts = ip.split(":")
            host = parts[0]
            try:
                port = int(parts[1])
            except:
                pass
        
        self.lobby = GameLobby(is_host=False)
        self.lobby.on_player_joined = self._on_player_joined
        self.lobby.on_player_left = self._on_player_left
        self.lobby.on_game_start = self._on_game_start
        self.lobby.on_error = self._on_error
        
        self.status_message = "Свързване..."
        self.error_message = ""
        
        if self.lobby.join_game(name, host, port):
            self.joined = True
            self.status_message = f"Свързан към {host}:{port}"
            # Изчакваме малко за да получим списъка с играчи
            pygame.time.wait(500)
            self.players_in_lobby = self.lobby.get_players_list()
        else:
            self.error_message = "Не може да се свърже със сървъра!"
            self.status_message = ""
    
    def _on_player_joined(self, player) -> None:
        self.players_in_lobby = self.lobby.get_players_list()
    
    def _on_player_left(self, player_id: str) -> None:
        self.players_in_lobby = self.lobby.get_players_list()
    
    def _on_game_start(self) -> None:
        self.next_screen = "online_game"
    
    def _on_error(self, message: str) -> None:
        self.error_message = message
    
    def _on_back(self) -> None:
        if self.lobby:
            self.lobby.close()
        self.next_screen = "main_menu"
    
    def handle_event(self, event: pygame.event.Event) -> None:
        if not self.joined:
            self.name_input.handle_event(event)
            self.ip_input.handle_event(event)
            self.join_button.handle_event(event)
        
        self.back_button.handle_event(event)
    
    def update(self, dt: float) -> None:
        self.name_input.update(dt)
        self.ip_input.update(dt)
        
        # Обновяваме списъка с играчи периодично
        if self.joined and self.lobby:
            self.players_in_lobby = self.lobby.get_players_list()
    
    def draw(self) -> None:
        self.screen.fill(LIGHT_GRAY)
        
        # Заглавие
        title_font = pygame.font.Font(None, FONT_XLARGE)
        title = title_font.render("ПРИСЪЕДИНИ СЕ КЪМ ИГРА", True, PURPLE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 80))
        self.screen.blit(title, title_rect)
        
        if not self.joined:
            font = pygame.font.Font(None, FONT_MEDIUM)
            
            # Име
            name_label = font.render("Твоето име:", True, BLACK)
            self.screen.blit(name_label, (SCREEN_WIDTH // 2 - 150, 150))
            self.name_input.draw(self.screen)
            
            # IP адрес
            ip_label = font.render("IP адрес на хоста:", True, BLACK)
            self.screen.blit(ip_label, (SCREEN_WIDTH // 2 - 150, 250))
            self.ip_input.draw(self.screen)
            
            self.join_button.draw(self.screen)
        else:
            # Показваме статус
            font = pygame.font.Font(None, FONT_LARGE)
            status = font.render(self.status_message, True, GREEN)
            status_rect = status.get_rect(center=(SCREEN_WIDTH // 2, 150))
            self.screen.blit(status, status_rect)
            
            # Списък с играчи
            font = pygame.font.Font(None, FONT_MEDIUM)
            players_title = font.render("Играчи в лобито:", True, BLACK)
            self.screen.blit(players_title, (SCREEN_WIDTH // 2 - 100, 220))
            
            for i, player in enumerate(self.players_in_lobby):
                y = 260 + i * 40
                color = BLUE if player.id == "host" else BLACK
                marker = "👑 " if player.id == "host" else "• "
                text = font.render(f"{marker}{player.name}", True, color)
                self.screen.blit(text, (SCREEN_WIDTH // 2 - 80, y))
            
            # Чакаме хоста
            wait_text = font.render("Чакаме хоста да започне играта...", True, GRAY)
            wait_rect = wait_text.get_rect(center=(SCREEN_WIDTH // 2, 450))
            self.screen.blit(wait_text, wait_rect)
        
        # Грешка
        if self.error_message:
            error_font = pygame.font.Font(None, FONT_MEDIUM)
            error = error_font.render(self.error_message, True, RED)
            error_rect = error.get_rect(center=(SCREEN_WIDTH // 2, 520))
            self.screen.blit(error, error_rect)
        
        self.back_button.draw(self.screen)


class OnlineGameScreen(Screen):
    """Екран за онлайн игра."""
    
    def __init__(self, screen: pygame.Surface, lobby=None):
        super().__init__(screen)
        from triviador.network.network import GameLobby
        
        self.lobby: Optional[GameLobby] = lobby
        self.is_host = False
        
        # Настройки
        self.selected_categories: Optional[list[str]] = None
        self.online_game_mode = GameMode.STANDARD
        
        # Състояние на играта
        self.current_question: Optional[dict] = None
        self.question_number = 0
        self.total_questions = 10
        self.time_left = DEFAULT_TIME_LIMIT
        self.answer_submitted = False
        self.waiting_for_results = False
        self.show_results = False
        self.results_data: Optional[dict] = None
        self.game_ended = False
        self.final_scores: list = []
        self.waiting_to_start = False
        self.start_delay = 0
        self.show_loser_reveal = False
        self.loser_names: list[str] = []
        
        # Елиминация (безкраен мултиплейър)
        self.eliminated_players: set[str] = set()
        self.am_eliminated = False
        self.show_elimination = False
        self.eliminated_this_round: list[str] = []
        
        # UI компоненти
        self.answer_buttons: list[Button] = []
        self.numeric_input: Optional[TextInput] = None
        self.submit_button: Optional[Button] = None
        self.joker_buttons: list[JokerButton] = []
        self.audience_chart: Optional[AudienceChart] = None
        self.show_audience = False
        self.feedback_message = ""
        self.feedback_color = WHITE
        self.is_special_round = False
        
        # Жокери за локалния играч
        from triviador.core.config import JOKERS_PER_GAME
        self.my_jokers = JOKERS_PER_GAME.copy()
        
        self.timer_bar = ProgressBar(50, 150, SCREEN_WIDTH - 100, 30, 1.0, RED)
        self.difficulty_indicator = DifficultyIndicator(SCREEN_WIDTH - 150, 80)
        
        # Бутони
        self.next_button = Button(
            SCREEN_WIDTH // 2 - 75, 550, 150, 50,
            "Продължи", FONT_MEDIUM, BLUE
        )
        self.next_button.callback = self._on_next
        
        self.back_button = Button(
            50, SCREEN_HEIGHT - 80, 120, 50,
            "Напусни", FONT_MEDIUM, RED
        )
        self.back_button.callback = self._on_back
    
    def set_lobby(self, lobby) -> None:
        """Задава lobby-то."""
        self.lobby = lobby
        if self.lobby:
            self.is_host = self.lobby.is_host
            self.lobby.on_question_received = self._on_question_received
            self.lobby.on_answer_result = self._on_answer_result
            self.lobby.on_round_end = self._on_round_end
            self.lobby.on_game_end = self._on_game_end
            self.lobby.on_joker_result = self._on_joker_result
    
    def setup(self) -> None:
        self.question_number = 0
        self.answer_submitted = False
        self.waiting_for_results = False
        self.show_results = False
        self.game_ended = False
        self.final_scores = []
        self.waiting_to_start = False
        self.start_delay = 0
        
        if self.is_host:
            # Хостът стартира играта и изпраща първия въпрос след кратко забавяне
            self._start_game_as_host()
    
    def _start_game_as_host(self) -> None:
        """Стартира играта като хост."""
        from triviador.logic.question_manager import QuestionManager
        from pathlib import Path
        from triviador.core.config import QUESTIONS_PER_GAME
        
        self.question_manager = QuestionManager()
        self.used_question_ids: set[int] = set()
        self.host_total_score = 0
        
        if self.online_game_mode == GameMode.ENDLESS:
            # В безкраен режим зареждаме въпроси един по един
            self.questions = []
            self.total_questions = 999  # Няма лимит
        else:
            # Стандартен режим
            self.total_questions = QUESTIONS_PER_GAME
            self.questions = self.question_manager.get_questions_with_increasing_difficulty(
                count=self.total_questions,
                categories=self.selected_categories
            )
        
        self.lobby.start_game()
        self.waiting_to_start = True
        self.start_delay = 1.0
    
    def _send_next_question(self) -> None:
        """Изпраща следващия въпрос."""
        import random
        from triviador.core.config import SPECIAL_ROUND_CHANCE
        
        if self.online_game_mode == GameMode.ENDLESS:
            # Безкраен режим - зареждаме следващия въпрос динамично
            question = self.question_manager.get_endless_mode_question(
                current_score=self.host_total_score,
                categories=self.selected_categories,
                exclude_ids=self.used_question_ids
            )
            if not question:
                self._end_game()
                return
            self.used_question_ids.add(question.id)
            # Добавяме към списъка за референция
            if self.question_number >= len(self.questions):
                self.questions.append(question)
            else:
                self.questions[self.question_number] = question
        else:
            # Стандартен режим
            if self.question_number >= len(self.questions):
                self._end_game()
                return
        
        # Определяме дали е специален рунд
        self.is_special_round = random.random() < SPECIAL_ROUND_CHANCE
        
        question = self.questions[self.question_number]
        question_data = {
            "text": question.question_text,
            "options": question.options if question.options else [],
            "question_type": question.question_type.value,
            "category": question.category,
            "difficulty": question.difficulty,
            "question_number": self.question_number + 1,
            "total_questions": self.total_questions,
            "correct_answer": question.correct_answer,
            "is_special_round": self.is_special_round,
            "game_mode": self.online_game_mode.value,
            "eliminated_players": list(self.eliminated_players)
        }
        
        self.lobby.send_question(question_data, self.eliminated_players)
        self._on_question_received(question_data)
    
    def _on_question_received(self, question_data: dict) -> None:
        """Получен е нов въпрос."""
        self.current_question = question_data
        self.time_left = DEFAULT_TIME_LIMIT
        self.answer_submitted = False
        self.waiting_for_results = False
        self.show_results = False
        self.show_audience = False
        self.audience_chart = None
        self.feedback_message = ""
        self.is_special_round = question_data.get("is_special_round", False)
        self.show_elimination = False
        self.eliminated_this_round = []
        
        # Обновяваме режима от данните (за клиенти)
        gm = question_data.get("game_mode")
        if gm:
            self.online_game_mode = GameMode(gm)
        
        # Обновяваме списъка с елиминирани от данните (за клиенти)
        elim = question_data.get("eliminated_players")
        if elim is not None:
            self.eliminated_players = set(elim)
        
        # Ако сме елиминирани, автоматично подаваме празен отговор
        if self.am_eliminated:
            self._setup_question_ui()
            self.answer_submitted = True
            self.waiting_for_results = True
            if self.lobby and not self.is_host:
                self.lobby.submit_answer("")
            return
        
        self._setup_question_ui()
        self._setup_joker_buttons()
    
    def _setup_question_ui(self) -> None:
        """Настройва UI за въпроса."""
        if not self.current_question:
            return
        
        self.answer_buttons = []
        self.numeric_input = None
        self.submit_button = None
        
        q_type = self.current_question.get("question_type", "multiple_choice")
        
        if q_type == "numeric":
            # Числов въпрос
            self.numeric_input = TextInput(
                SCREEN_WIDTH // 2 - 100, 350, 200, 50,
                placeholder="Твоят отговор...",
                numeric_only=True
            )
            self.submit_button = Button(
                SCREEN_WIDTH // 2 - 75, 420, 150, 50,
                "Отговори", FONT_MEDIUM, BLUE
            )
            self.submit_button.callback = self._submit_numeric_answer
        else:
            # Въпрос с избор
            options = self.current_question.get("options", [])
            letters = ['A', 'B', 'C', 'D']
            
            for i, option in enumerate(options):
                x = 50 if i % 2 == 0 else SCREEN_WIDTH // 2 + 25
                y = 300 + (i // 2) * 100
                
                btn = AnswerButton(
                    x, y, SCREEN_WIDTH // 2 - 75, 80,
                    option, letters[i]
                )
                btn.callback = lambda o=option: self._submit_answer(o)
                self.answer_buttons.append(btn)
        
        self.difficulty_indicator.set_difficulty(
            self.current_question.get("difficulty", 1)
        )
    
    def _setup_joker_buttons(self) -> None:
        """Настройва бутоните за жокери."""
        self.joker_buttons = [
            JokerButton(50, SCREEN_HEIGHT - 150, 150, 40, JOKER_5050, self.my_jokers.get(JOKER_5050, 0)),
            JokerButton(220, SCREEN_HEIGHT - 150, 180, 40, JOKER_AUDIENCE, self.my_jokers.get(JOKER_AUDIENCE, 0))
        ]
        
        for btn in self.joker_buttons:
            btn.callback = lambda jt=btn.joker_type: self._on_use_joker(jt)
        
        # Обновяваме текста за числови въпроси
        if self.current_question:
            q_type = self.current_question.get("question_type", "multiple_choice")
            for btn in self.joker_buttons:
                if btn.joker_type == JOKER_5050:
                    if q_type == "numeric":
                        btn.set_display_name("Диапазон")
                    else:
                        btn.set_display_name("50/50")
        
        self._update_joker_buttons()
    
    def _update_joker_buttons(self) -> None:
        """Обновява състоянието на жокер бутоните."""
        for btn in self.joker_buttons:
            count = self.my_jokers.get(btn.joker_type, 0)
            btn.update_count(count)
            btn.enabled = count > 0 and not self.is_special_round and not self.answer_submitted
    
    def _on_use_joker(self, joker_type: str) -> None:
        """Използва жокер."""
        if self.answer_submitted:
            return
        
        if self.is_special_round:
            self.feedback_message = "Жокерите не могат да се използват в специален рунд!"
            self.feedback_color = RED
            return
        
        if self.my_jokers.get(joker_type, 0) <= 0:
            self.feedback_message = "Нямате повече такива жокери!"
            self.feedback_color = RED
            return
        
        if self.is_host:
            # Хостът прилага жокера директно
            self._apply_joker_locally(joker_type)
        else:
            # Клиентът изпраща заявка до хоста
            from triviador.network.network import NetworkMessage, MessageTypes
            self.lobby.client.send(NetworkMessage(
                type=MessageTypes.USE_JOKER,
                data={"joker_type": joker_type, "is_special_round": self.is_special_round}
            ))
    
    def _apply_joker_locally(self, joker_type: str) -> None:
        """Прилага жокер локално (за хоста или след получаване на резултат)."""
        from triviador.logic.joker_system import JokerSystem
        from triviador.core.models import Question, QuestionType
        
        self.my_jokers[joker_type] = self.my_jokers.get(joker_type, 0) - 1
        self._update_joker_buttons()
        
        if not self.current_question:
            return
        
        q = self.current_question
        question = Question(
            id=0,
            category=q.get("category", ""),
            difficulty=q.get("difficulty", 1),
            question_type=QuestionType(q.get("question_type", "multiple_choice")),
            question_text=q.get("text", ""),
            correct_answer=q.get("correct_answer", ""),
            options=q.get("options", [])
        )
        
        if joker_type == JOKER_5050:
            result = JokerSystem.apply_5050(question)
            self._handle_joker_5050_result(result, question.question_type)
        elif joker_type == JOKER_AUDIENCE:
            result = JokerSystem.apply_audience_help(question)
            self._handle_joker_audience_result(result, question.question_type)
    
    def _on_joker_result(self, data: dict) -> None:
        """Получен е резултат от жокер (за клиенти)."""
        if "error" in data:
            self.feedback_message = data["error"]
            self.feedback_color = RED
            return
        
        joker_type = data.get("joker_type", "")
        remaining = data.get("remaining_count", 0)
        self.my_jokers[joker_type] = remaining
        self._update_joker_buttons()
        
        if data.get("type") == "5050":
            q_type = self.current_question.get("question_type", "multiple_choice") if self.current_question else "multiple_choice"
            self._handle_joker_5050_result(data.get("remaining_options", []), QuestionType(q_type))
        elif data.get("type") == "audience":
            q_type = self.current_question.get("question_type", "multiple_choice") if self.current_question else "multiple_choice"
            self._handle_joker_audience_result(data.get("votes", {}), QuestionType(q_type))
    
    def _handle_joker_5050_result(self, remaining, question_type) -> None:
        """Обработва резултата от 50/50 жокер."""
        if question_type == QuestionType.MULTIPLE_CHOICE:
            for btn in self.answer_buttons:
                if btn.text not in remaining:
                    btn.set_state("eliminated")
        else:
            # Числов въпрос - показваме диапазон
            if remaining:
                self.feedback_message = f"Диапазон: {remaining[0]}"
                self.feedback_color = BLUE
    
    def _handle_joker_audience_result(self, votes, question_type) -> None:
        """Обработва резултата от помощ от публиката."""
        if question_type == QuestionType.MULTIPLE_CHOICE:
            self.show_audience = True
            self.audience_chart = AudienceChart(
                SCREEN_WIDTH // 2 - 200, 250, 400, 200
            )
            self.audience_chart.set_votes(votes)
        else:
            suggested = votes.get("suggested_value", "?")
            confidence = votes.get("confidence", 0)
            self.feedback_message = f"Публиката предлага: {suggested} (увереност: {confidence}%)"
            self.feedback_color = PURPLE
    
    def _submit_answer(self, answer: str) -> None:
        """Изпраща отговор."""
        if self.answer_submitted:
            return
        
        self.answer_submitted = True
        self.waiting_for_results = True
        
        if self.lobby:
            self.lobby.submit_answer(answer)
        
        # Маркираме избрания отговор
        for btn in self.answer_buttons:
            if btn.text == answer:
                btn.selected = True
            btn.enabled = False
        
        # Деактивираме жокерите
        for btn in self.joker_buttons:
            btn.enabled = False
    
    def _submit_numeric_answer(self) -> None:
        """Изпраща числов отговор."""
        if self.answer_submitted or not self.numeric_input:
            return
        
        answer = self.numeric_input.get_value()
        if not answer:
            return
        
        self.answer_submitted = True
        self.waiting_for_results = True
        
        if self.lobby:
            self.lobby.submit_answer(answer)
        
        if self.submit_button:
            self.submit_button.enabled = False
        
        # Деактивираме жокерите
        for btn in self.joker_buttons:
            btn.enabled = False
    
    def _on_answer_result(self, results: dict) -> None:
        """Получени са резултатите от отговорите."""
        self.results_data = results
        self.show_results = True
        self.waiting_for_results = False
        
        # Показваме верния отговор
        correct = results.get("correct_answer", "")
        for btn in self.answer_buttons:
            if btn.text == correct:
                btn.is_correct = True
            elif btn.selected:
                btn.is_incorrect = True
        
        # Безкраен режим - елиминации
        eliminated_this_round = results.get("eliminated_this_round", [])
        if eliminated_this_round:
            self.eliminated_this_round = eliminated_this_round
            # Проверяваме дали ние сме елиминирани
            my_name = self.lobby.my_name if self.lobby else ""
            if my_name in eliminated_this_round:
                self.am_eliminated = True
            # Добавяме към общия списък
            self.eliminated_players.update(eliminated_this_round)
            
            if results.get("endless_game_over"):
                # Финал - показваме кой сбърка, после класиране
                self.loser_names = results.get("loser_names", eliminated_this_round)
                self.show_loser_reveal = True
            else:
                # Играта продължава - показваме кой е елиминиран
                self.show_elimination = True
        elif results.get("endless_game_over"):
            # Краен случай без елиминации
            self.loser_names = results.get("loser_names", [])
            self.show_loser_reveal = True
    
    def _on_round_end(self, results: list) -> None:
        """Край на рунда."""
        # Показваме класиране
        pass
    
    def _on_game_end(self, final_scores: list) -> None:
        """Край на играта."""
        self.game_ended = True
        self.final_scores = final_scores
    
    def _end_game(self) -> None:
        """Завършва играта (само хост)."""
        if not self.is_host:
            return
        
        scores = []
        for player in self.lobby.get_players_list():
            scores.append({
                "name": player.name,
                "score": player.score,
                "is_eliminated": player.name in self.eliminated_players
            })
        
        # Оцелелите (никога не са бъркали) са отгоре, елиминираните отдолу
        survivors = [s for s in scores if not s["is_eliminated"]]
        eliminated = [s for s in scores if s["is_eliminated"]]
        survivors.sort(key=lambda x: x["score"], reverse=True)
        eliminated.sort(key=lambda x: x["score"], reverse=True)
        scores = survivors + eliminated
        
        self.lobby.send_game_end(scores)
        self._on_game_end(scores)
    
    def _on_next(self) -> None:
        """Продължава към следващия въпрос."""
        if self.game_ended:
            if self.lobby:
                self.lobby.close()
            self.next_screen = "main_menu"
            return
        
        if self.show_loser_reveal:
            # Финален екран - показваме класирането
            self.show_loser_reveal = False
            if self.is_host:
                self._end_game()
            # Клиентът чака хостът да изпрати класирането
            return
        
        if self.show_elimination:
            # Елиминация - играта продължава
            self.show_elimination = False
            self.show_results = False
            if self.is_host:
                self.question_number += 1
                self._send_next_question()
            return
        
        if self.is_host:
            self.question_number += 1
            self._send_next_question()
    
    def _check_endless_game_over(self, results: dict) -> bool:
        """В безкраен режим - проверка дали всички са сгрешили."""
        if self.online_game_mode != GameMode.ENDLESS:
            return False
        player_results = results.get("player_results", [])
        all_wrong = all(not pr["is_correct"] for pr in player_results)
        return all_wrong
    
    def _on_back(self) -> None:
        """Напуска играта."""
        if self.lobby:
            self.lobby.close()
        self.next_screen = "main_menu"
    
    def handle_event(self, event: pygame.event.Event) -> None:
        if not self.answer_submitted:
            for btn in self.answer_buttons:
                btn.handle_event(event)
            
            if self.numeric_input:
                self.numeric_input.handle_event(event)
            
            if self.submit_button:
                self.submit_button.handle_event(event)
            
            for btn in self.joker_buttons:
                if btn.enabled:
                    btn.handle_event(event)
        
        if self.game_ended:
            self.next_button.handle_event(event)
        elif self.show_loser_reveal:
            self.next_button.handle_event(event)
        elif self.show_elimination:
            self.next_button.handle_event(event)
        elif self.show_results and self.is_host:
            self.next_button.handle_event(event)
        
        self.back_button.handle_event(event)
    
    def update(self, dt: float) -> None:
        if self.numeric_input:
            self.numeric_input.update(dt)
        
        # Забавяне преди първия въпрос (само хост)
        if self.waiting_to_start:
            self.start_delay -= dt
            if self.start_delay <= 0:
                self.waiting_to_start = False
                self._send_next_question()
            return
        
        # Таймер
        if not self.answer_submitted and not self.show_results and self.current_question:
            self.time_left -= dt
            self.timer_bar.set_value(self.time_left / DEFAULT_TIME_LIMIT)
            
            if self.time_left <= 0:
                # Времето изтече
                self._submit_answer("")
        
        # Проверка дали всички са отговорили (само хост)
        if self.is_host and self.waiting_for_results and self.lobby:
            if self.lobby.all_answers_received:
                self._calculate_and_send_results()
    
    def _calculate_and_send_results(self) -> None:
        """Изчислява и изпраща резултатите (само хост)."""
        from triviador.core.config import BASE_POINTS, TIME_BONUS_MULTIPLIER, DIFFICULTY_MULTIPLIER, NUMERIC_TOLERANCE, SPECIAL_ROUND_MULTIPLIER
        
        if not self.current_question:
            return
        
        correct_answer = self.current_question.get("correct_answer", "")
        q_type = self.current_question.get("question_type", "multiple_choice")
        difficulty = self.current_question.get("difficulty", 1)
        is_special = self.current_question.get("is_special_round", False)
        
        player_results = []
        
        for player in self.lobby.get_players_list():
            answer = player.current_answer or ""
            is_correct = False
            points = 0
            
            if q_type == "numeric":
                try:
                    user_val = float(answer)
                    correct_val = float(correct_answer)
                    tolerance = abs(correct_val * NUMERIC_TOLERANCE)
                    is_correct = abs(user_val - correct_val) <= tolerance
                except:
                    is_correct = False
            else:
                is_correct = answer.strip().lower() == str(correct_answer).strip().lower()
            
            if is_correct:
                points = BASE_POINTS
                remaining_time = DEFAULT_TIME_LIMIT - player.answer_time
                if remaining_time > 0:
                    time_bonus = int(remaining_time * TIME_BONUS_MULTIPLIER)
                    points += time_bonus
                difficulty_bonus = int(points * (difficulty - 1) * (DIFFICULTY_MULTIPLIER - 1))
                points += difficulty_bonus
            
            if is_special and is_correct:
                points = int(points * SPECIAL_ROUND_MULTIPLIER)
            
            player.score += points
            player_results.append({
                "player_id": player.id,
                "name": player.name,
                "answer": answer,
                "is_correct": is_correct,
                "points": points,
                "total_score": player.score
            })
        
        # Обновяваме общия резултат за безкраен режим
        if self.is_host:
            self.host_total_score = max(p.score for p in self.lobby.get_players_list())
        
        results = {
            "correct_answer": correct_answer,
            "player_results": player_results,
            "is_special_round": is_special
        }
        
        # Проверка за елиминации в безкраен режим
        if self.online_game_mode == GameMode.ENDLESS:
            # Активни играчи (неелиминирани)
            active_results = [pr for pr in player_results if pr["name"] not in self.eliminated_players]
            wrong_active = [pr["name"] for pr in active_results if not pr["is_correct"]]
            right_active = [pr["name"] for pr in active_results if pr["is_correct"]]
            
            if wrong_active:
                remaining_after = len(active_results) - len(wrong_active)
                
                if remaining_after == 1:
                    # Остава точно 1 играч - той печели, играта свършва
                    results["eliminated_this_round"] = wrong_active
                    results["endless_game_over"] = True
                    results["loser_names"] = wrong_active
                elif remaining_after == 0:
                    # Всички активни сбъркаха едновременно - печели този с повече точки
                    results["endless_game_over"] = True
                    # Определяме загубилите - всички освен най-високия резултат
                    best_score = max(pr["total_score"] for pr in active_results)
                    winners = [pr["name"] for pr in active_results if pr["total_score"] == best_score]
                    losers = [pr["name"] for pr in active_results if pr["total_score"] != best_score]
                    results["loser_names"] = losers if losers else []
                    results["eliminated_this_round"] = wrong_active
                else:
                    # Повече от 1 остават - елиминираме сбъркалите, играта продължава
                    results["eliminated_this_round"] = wrong_active
                    results["endless_game_over"] = False
        
        self.lobby.send_answer_results(results)
        self._on_answer_result(results)
    
    def draw(self) -> None:
        self.screen.fill(LIGHT_GRAY)
        
        if self.game_ended:
            self._draw_game_over()
            return
        
        if self.show_loser_reveal:
            self._draw_loser_reveal()
            return
        
        if self.show_elimination:
            self._draw_elimination()
            return
        
        if self.am_eliminated and not self.show_results:
            self._draw_spectator()
            return
        
        if self.waiting_to_start:
            # Показваме съобщение за стартиране
            font = pygame.font.Font(None, FONT_LARGE)
            text = font.render("Играта започва...", True, BLACK)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.screen.blit(text, text_rect)
            self.back_button.draw(self.screen)
            return
        
        if not self.current_question:
            # Чакаме въпрос
            font = pygame.font.Font(None, FONT_LARGE)
            text = font.render("Чакаме въпрос...", True, BLACK)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.screen.blit(text, text_rect)
            self.back_button.draw(self.screen)
            return
        
        # Заглавие и информация
        title_font = pygame.font.Font(None, FONT_LARGE)
        q_num = self.current_question.get("question_number", self.question_number + 1)
        if self.online_game_mode == GameMode.ENDLESS:
            info_text = f"Въпрос {q_num}"
        else:
            q_total = self.current_question.get("total_questions", self.total_questions)
            info_text = f"Въпрос {q_num}/{q_total}"
        info = title_font.render(info_text, True, BLACK)
        self.screen.blit(info, (50, 20))
        
        # Категория
        font = pygame.font.Font(None, FONT_MEDIUM)
        category = font.render(
            f"Категория: {self.current_question.get('category', 'Общи')}",
            True, PURPLE
        )
        self.screen.blit(category, (50, 60))
        
        # Трудност
        self.difficulty_indicator.draw(self.screen)
        
        # Специален рунд
        if self.is_special_round:
            special_font = pygame.font.Font(None, FONT_LARGE)
            special_text = special_font.render("★ СПЕЦИАЛЕН РУНД - ДВОЙНИ ТОЧКИ! ★", True, YELLOW)
            special_rect = special_text.get_rect(center=(SCREEN_WIDTH // 2, 100))
            pygame.draw.rect(self.screen, PURPLE, special_rect.inflate(20, 10), border_radius=5)
            self.screen.blit(special_text, special_rect)
        
        # Таймер
        self.timer_bar.draw(self.screen)
        timer_text = font.render(f"{max(0, int(self.time_left))}с", True, BLACK)
        self.screen.blit(timer_text, (SCREEN_WIDTH - 80, 120))
        
        # Въпрос
        question_font = pygame.font.Font(None, FONT_LARGE)
        question_text = self.current_question.get("text", "")
        
        # Разбиване на дълъг текст
        words = question_text.split()
        lines = []
        current_line = ""
        for word in words:
            test_line = current_line + " " + word if current_line else word
            if question_font.size(test_line)[0] < SCREEN_WIDTH - 100:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        
        for i, line in enumerate(lines):
            text_surface = question_font.render(line, True, BLACK)
            text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, 220 + i * 35))
            self.screen.blit(text_surface, text_rect)
        
        # Отговори
        for btn in self.answer_buttons:
            btn.draw(self.screen)
        
        if self.numeric_input:
            self.numeric_input.draw(self.screen)
        
        if self.submit_button:
            self.submit_button.draw(self.screen)
        
        # Графика за публиката
        if self.show_audience and self.audience_chart:
            self.audience_chart.draw(self.screen)
        
        # Жокери
        if not self.show_results:
            for btn in self.joker_buttons:
                btn.draw(self.screen)
        
        # Съобщение за обратна връзка
        if self.feedback_message:
            feedback_font = pygame.font.Font(None, FONT_LARGE)
            feedback = feedback_font.render(self.feedback_message, True, self.feedback_color)
            feedback_rect = feedback.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 130))
            bg_rect = feedback_rect.inflate(20, 10)
            pygame.draw.rect(self.screen, BLACK, bg_rect, border_radius=5)
            self.screen.blit(feedback, feedback_rect)
        
        # Резултати
        if self.show_results and self.results_data:
            self._draw_results()
            if self.is_host and not self.show_loser_reveal and not self.show_elimination:
                self.next_button.draw(self.screen)
        
        # Чакане
        if self.waiting_for_results:
            font = pygame.font.Font(None, FONT_MEDIUM)
            wait = font.render("Чакаме останалите играчи...", True, GRAY)
            wait_rect = wait.get_rect(center=(SCREEN_WIDTH // 2, 520))
            self.screen.blit(wait, wait_rect)
        
        self.back_button.draw(self.screen)
    
    def _draw_results(self) -> None:
        """Рисува резултатите."""
        if not self.results_data:
            return
        
        font = pygame.font.Font(None, FONT_MEDIUM)
        
        # Панел с резултати
        panel_rect = pygame.Rect(SCREEN_WIDTH - 250, 200, 230, 250)
        pygame.draw.rect(self.screen, WHITE, panel_rect, border_radius=10)
        pygame.draw.rect(self.screen, DARK_GRAY, panel_rect, 2, border_radius=10)
        
        title = font.render("Резултати:", True, BLACK)
        self.screen.blit(title, (panel_rect.x + 10, panel_rect.y + 10))
        
        for i, pr in enumerate(self.results_data.get("player_results", [])):
            y = panel_rect.y + 50 + i * 45
            
            color = GREEN if pr["is_correct"] else RED
            name = font.render(pr["name"][:10], True, BLACK)
            self.screen.blit(name, (panel_rect.x + 10, y))
            
            points = font.render(f"+{pr['points']}", True, color)
            self.screen.blit(points, (panel_rect.x + 120, y))
            
            total = font.render(f"({pr['total_score']})", True, GRAY)
            self.screen.blit(total, (panel_rect.x + 170, y))
    
    def _draw_spectator(self) -> None:
        """Рисува екран за елиминиран играч (наблюдател)."""
        # Фон
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, (0, 0))
        
        title_font = pygame.font.Font(None, FONT_XLARGE)
        title = title_font.render("ЕЛИМИНИРАН", True, RED)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 60))
        self.screen.blit(title, title_rect)
        
        font = pygame.font.Font(None, FONT_LARGE)
        text = font.render("Наблюдаваш играта...", True, WHITE)
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 10))
        self.screen.blit(text, text_rect)
        
        # Показваме колко играчи остават
        active_count = len(self.lobby.get_players_list()) - len(self.eliminated_players) if self.lobby else 0
        count_text = font.render(f"Остават {active_count} играчи", True, GRAY)
        count_rect = count_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 70))
        self.screen.blit(count_text, count_rect)
        
        self.back_button.draw(self.screen)
    
    def _draw_elimination(self) -> None:
        """Рисува екран за елиминация (играта продължава)."""
        # Фон
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        # Заглавие
        title_font = pygame.font.Font(None, FONT_XLARGE)
        title = title_font.render("ЕЛИМИНАЦИЯ!", True, (255, 165, 0))
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 120))
        self.screen.blit(title, title_rect)
        
        # Кой е елиминиран
        subtitle_font = pygame.font.Font(None, FONT_LARGE)
        if len(self.eliminated_this_round) == 1:
            elim_text = f"{self.eliminated_this_round[0]} е елиминиран!"
        else:
            elim_text = f"{", ".join(self.eliminated_this_round)} са елиминирани!"
        
        elim_surface = subtitle_font.render(elim_text, True, (255, 100, 100))
        elim_rect = elim_surface.get_rect(center=(SCREEN_WIDTH // 2, 210))
        self.screen.blit(elim_surface, elim_rect)
        
        # Верният отговор
        if self.results_data:
            correct = self.results_data.get("correct_answer", "")
            answer_font = pygame.font.Font(None, FONT_MEDIUM)
            answer_text = answer_font.render(f"Верен отговор: {correct}", True, GREEN)
            answer_rect = answer_text.get_rect(center=(SCREEN_WIDTH // 2, 290))
            self.screen.blit(answer_text, answer_rect)
        
        # Колко играчи остават
        font = pygame.font.Font(None, FONT_MEDIUM)
        active_count = len(self.lobby.get_players_list()) - len(self.eliminated_players) if self.lobby else 0
        remain_text = font.render(f"Остават {active_count} играчи", True, WHITE)
        remain_rect = remain_text.get_rect(center=(SCREEN_WIDTH // 2, 360))
        self.screen.blit(remain_text, remain_rect)
        
        # Бутон продължи
        self.next_button.draw(self.screen)
        self.back_button.draw(self.screen)
    
    def _draw_loser_reveal(self) -> None:
        """Рисува екрана с разкриване на загубилия."""
        # Фон
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        # Заглавие
        title_font = pygame.font.Font(None, FONT_XLARGE)
        title = title_font.render("КРАЙ НА ИГРАТА!", True, RED)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 120))
        self.screen.blit(title, title_rect)
        
        # Кой е сбъркал
        subtitle_font = pygame.font.Font(None, FONT_LARGE)
        if len(self.eliminated_this_round) == 1:
            elim_text = f"{self.eliminated_this_round[0]} сбърка!"
        else:
            elim_text = f"{", ".join(self.eliminated_this_round)} сбъркаха!"
        
        elim_surface = subtitle_font.render(elim_text, True, (255, 100, 100))
        elim_rect = elim_surface.get_rect(center=(SCREEN_WIDTH // 2, 210))
        self.screen.blit(elim_surface, elim_rect)
        
        # Верният отговор
        if self.results_data:
            correct = self.results_data.get("correct_answer", "")
            answer_font = pygame.font.Font(None, FONT_MEDIUM)
            answer_text = answer_font.render(f"Верен отговор: {correct}", True, GREEN)
            answer_rect = answer_text.get_rect(center=(SCREEN_WIDTH // 2, 290))
            self.screen.blit(answer_text, answer_rect)
        
        # Показваме кой е победител ако има
        active = [pr["name"] for pr in self.results_data.get("player_results", [])
                  if pr["name"] not in self.eliminated_players] if self.results_data else []
        if active:
            winner_font = pygame.font.Font(None, FONT_LARGE)
            winner_text = winner_font.render(f"Победител: {", ".join(active)}!", True, (255, 215, 0))
            winner_rect = winner_text.get_rect(center=(SCREEN_WIDTH // 2, 370))
            self.screen.blit(winner_text, winner_rect)
        
        # Бутон продължи (показва класирането)
        self.next_button.draw(self.screen)
        self.back_button.draw(self.screen)
    
    def _draw_game_over(self) -> None:
        """Рисува финалния екран."""
        title_font = pygame.font.Font(None, FONT_XLARGE)
        title = title_font.render("ИГРАТА ПРИКЛЮЧИ!", True, PURPLE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 100))
        self.screen.blit(title, title_rect)
        
        font = pygame.font.Font(None, FONT_LARGE)
        
        for i, score in enumerate(self.final_scores[:4]):
            y = 200 + i * 70
            
            # Медал за топ 3
            medals = {0: "🥇", 1: "🥈", 2: "🥉"}
            prefix = medals.get(i, f"{i + 1}.")
            
            colors = {0: (255, 215, 0), 1: (192, 192, 192), 2: (205, 127, 50)}
            color = colors.get(i, BLACK)
            
            text = font.render(f"{prefix} {score['name']}: {score['score']} точки", True, color)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, y))
            self.screen.blit(text, text_rect)
        
        self.next_button.draw(self.screen)
        self.back_button.draw(self.screen)
