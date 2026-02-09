import random
import time
from typing import Optional

from triviador.core.models import Question ,Player ,GameState ,GameMode ,QuestionType
from triviador.logic.question_manager import QuestionManager
from triviador.logic.highscore_manager import HighScoreManager
from triviador.logic.joker_system import JokerSystem
from triviador.core.config import (
BASE_POINTS ,TIME_BONUS_MULTIPLIER ,DIFFICULTY_MULTIPLIER ,
SPECIAL_ROUND_MULTIPLIER ,SPECIAL_ROUND_CHANCE ,DEFAULT_TIME_LIMIT ,
QUESTIONS_PER_GAME ,NUMERIC_TOLERANCE
)


class GameLogic :


    def __init__ (self ):
        self .question_manager =QuestionManager ()
        self .highscore_manager =HighScoreManager ()
        self .joker_system =JokerSystem ()
        self .game_state :Optional [GameState ]=None
        self .question_start_time :float =0
        self .used_question_ids :set [int ]=set ()

    def start_game (
    self ,
    mode :GameMode ,
    player_names :list [str ],
    categories :Optional [list [str ]]=None
    )->GameState :

        players =[Player (name =name )for name in player_names ]

        if categories is None or len (categories )==0 :
            categories =self .question_manager .get_categories ()


        if mode ==GameMode .STANDARD :
            questions =self .question_manager .get_questions_with_increasing_difficulty (
            count =QUESTIONS_PER_GAME ,
            categories =categories
            )
        else :
            questions =[]

        self .game_state =GameState (
        mode =mode ,
        players =players ,
        questions =questions ,
        selected_categories =categories
        )

        self .used_question_ids =set ()
        self ._start_question_timer ()


        self ._check_special_round ()

        return self .game_state

    def _start_question_timer (self )->None :

        self .question_start_time =time .time ()

    def _check_special_round (self )->None :

        if self .game_state :
            self .game_state .is_special_round =random .random ()<SPECIAL_ROUND_CHANCE

    def get_current_question (self )->Optional [Question ]:

        if not self .game_state :
            return None

        if self .game_state .mode ==GameMode .ENDLESS :

            if self .game_state .current_question is None :
                self ._load_next_endless_question ()

        return self .game_state .current_question

    def _load_next_endless_question (self )->None :

        if not self .game_state :
            return

        current_score =self .game_state .current_player .score if self .game_state .current_player else 0

        question =self .question_manager .get_endless_mode_question (
        current_score =current_score ,
        categories =self .game_state .selected_categories ,
        exclude_ids =self .used_question_ids
        )

        if question :
            self .game_state .questions .append (question )
            self .used_question_ids .add (question .id )

    def get_remaining_time (self )->float :

        elapsed =time .time ()-self .question_start_time
        remaining =DEFAULT_TIME_LIMIT -elapsed
        return max (0 ,remaining )

    def is_time_up (self )->bool :

        return self .get_remaining_time ()<=0

    def calculate_points (self ,is_correct :bool ,remaining_time :float ,difficulty :int )->int :

        if not is_correct :
            return 0


        points =BASE_POINTS


        time_bonus =int (remaining_time *TIME_BONUS_MULTIPLIER )
        points +=time_bonus


        difficulty_bonus =int (points *(difficulty -1 )*(DIFFICULTY_MULTIPLIER -1 ))
        points +=difficulty_bonus


        if self .game_state and self .game_state .is_special_round :
            points =int (points *SPECIAL_ROUND_MULTIPLIER )

        return points

    def submit_answer (self ,answer :str |int |float )->dict :

        if not self .game_state or not self .game_state .current_question :
            return {"error":"Няма активна игра или въпрос"}

        question =self .game_state .current_question
        player =self .game_state .current_player

        if not player :
            return {"error":"Няма активен играч"}

        remaining_time =self .get_remaining_time ()
        is_correct =question .check_answer (answer ,NUMERIC_TOLERANCE )


        if remaining_time <=0 :
            is_correct =False

        points =self .calculate_points (is_correct ,remaining_time ,question .difficulty )


        player .total_answers +=1
        if is_correct :
            player .correct_answers +=1
            player .add_score (points )

        result ={
        "is_correct":is_correct ,
        "correct_answer":question .correct_answer ,
        "points":points ,
        "total_score":player .score ,
        "time_taken":DEFAULT_TIME_LIMIT -remaining_time ,
        "is_special_round":self .game_state .is_special_round
        }


        if self .game_state .mode ==GameMode .ENDLESS and not is_correct :
            self .game_state .game_over =True
            result ["game_over"]=True

        return result

    def next_question (self )->bool :

        if not self .game_state :
            return False

        has_next =self .game_state .next_question ()

        if self .game_state .mode ==GameMode .ENDLESS :

            if not self .game_state .game_over :
                self ._load_next_endless_question ()
                has_next =True

        if has_next :
            self ._start_question_timer ()
            self ._check_special_round ()
        else :
            self .game_state .game_over =True

        return has_next

    def use_joker (self ,joker_type :str )->dict :

        if not self .game_state or not self .game_state .current_question :
            return {"error":"Няма активна игра или въпрос"}

        player =self .game_state .current_player
        if not player :
            return {"error":"Няма активен играч"}


        can_use ,reason =self .joker_system .can_use_joker (
        player ,joker_type ,self .game_state .is_special_round
        )

        if not can_use :
            return {"error":reason }


        player .use_joker (joker_type )
        question =self .game_state .current_question

        from triviador.core.config import JOKER_5050 ,JOKER_AUDIENCE

        if joker_type ==JOKER_5050 :
            result =self .joker_system .apply_5050 (question )
            return {"type":"5050","remaining_options":result }

        elif joker_type ==JOKER_AUDIENCE :
            result =self .joker_system .apply_audience_help (question )
            return {"type":"audience","votes":result }

        return {"error":"Непознат тип жокер"}

    def end_game (self )->dict :

        if not self .game_state :
            return {"error":"Няма активна игра"}

        self .game_state .game_over =True

        results ={
        "mode":self .game_state .mode .value ,
        "players":[]
        }


        sorted_players =sorted (
        self .game_state .players ,
        key =lambda p :p .score ,
        reverse =True
        )

        for i ,player in enumerate (sorted_players ):
            player_result ={
            "rank":i +1 ,
            "name":player .name ,
            "score":player .score ,
            "correct_answers":player .correct_answers ,
            "total_answers":player .total_answers ,
            "accuracy":player .accuracy
            }


            highscore_rank =self .highscore_manager .add_score (player ,self .game_state .mode )
            if highscore_rank :
                player_result ["highscore_rank"]=highscore_rank

            results ["players"].append (player_result )

        return results

    def get_highscores (self )->list :

        return self .highscore_manager .get_top_scores ()

    def get_categories (self )->list [str ]:

        return self .question_manager .get_categories ()
