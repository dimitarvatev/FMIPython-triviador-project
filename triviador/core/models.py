from dataclasses import dataclass ,field
from typing import Optional
from enum import Enum
import time


class QuestionType (Enum ):

    MULTIPLE_CHOICE ="multiple_choice"
    NUMERIC ="numeric"


class GameMode (Enum ):

    STANDARD ="standard"
    ENDLESS ="endless"


@dataclass
class Question :

    id :int
    category :str
    difficulty :int
    question_type :QuestionType
    question_text :str
    correct_answer :str |int |float
    options :list [str ]=field (default_factory =list )

    @classmethod
    def from_dict (cls ,data :dict )->"Question":

        return cls (
        id =data ["id"],
        category =data ["category"],
        difficulty =data ["difficulty"],
        question_type =QuestionType (data ["type"]),
        question_text =data ["question"],
        correct_answer =data ["correct_answer"],
        options =data .get ("options",[])
        )

    def check_answer (self ,answer :str |int |float ,tolerance :float =0.10 )->bool :

        if self .question_type ==QuestionType .NUMERIC :
            try :
                numeric_answer =float (answer )
                correct =float (self .correct_answer )

                margin =abs (correct *tolerance )
                return abs (numeric_answer -correct )<=margin
            except (ValueError ,TypeError ):
                return False
        else :
            return str (answer ).strip ().lower ()==str (self .correct_answer ).strip ().lower ()


@dataclass
class Player :

    name :str
    score :int =0
    correct_answers :int =0
    total_answers :int =0
    jokers :dict =field (default_factory =dict )

    def __post_init__ (self ):
        if not self .jokers :
            from triviador.core.config import JOKERS_PER_GAME
            self .jokers =JOKERS_PER_GAME .copy ()

    def add_score (self ,points :int )->None :

        self .score +=points

    def use_joker (self ,joker_type :str )->bool :

        if self .jokers .get (joker_type ,0 )>0 :
            self .jokers [joker_type ]-=1
            return True
        return False

    def has_joker (self ,joker_type :str )->bool :

        return self .jokers .get (joker_type ,0 )>0

    @property
    def accuracy (self )->float :

        if self .total_answers ==0 :
            return 0.0
        return (self .correct_answers /self .total_answers )*100


@dataclass
class GameState :

    mode :GameMode
    players :list [Player ]=field (default_factory =list )
    current_player_index :int =0
    current_question_index :int =0
    questions :list [Question ]=field (default_factory =list )
    selected_categories :list [str ]=field (default_factory =list )
    is_special_round :bool =False
    game_over :bool =False
    start_time :float =field (default_factory =time .time )

    @property
    def current_player (self )->Optional [Player ]:

        if self .players :
            return self .players [self .current_player_index ]
        return None

    @property
    def current_question (self )->Optional [Question ]:

        if self .current_question_index <len (self .questions ):
            return self .questions [self .current_question_index ]
        return None

    def next_player (self )->None :

        self .current_player_index =(self .current_player_index +1 )%len (self .players )

    def next_question (self )->bool :

        self .current_question_index +=1
        return self .current_question_index <len (self .questions )


@dataclass
class HighScore :

    player_name :str
    score :int
    mode :str
    questions_answered :int
    accuracy :float
    date :str

    def to_dict (self )->dict :

        return {
        "player_name":self .player_name ,
        "score":self .score ,
        "mode":self .mode ,
        "questions_answered":self .questions_answered ,
        "accuracy":self .accuracy ,
        "date":self .date
        }

    @classmethod
    def from_dict (cls ,data :dict )->"HighScore":

        return cls (
        player_name =data ["player_name"],
        score =data ["score"],
        mode =data ["mode"],
        questions_answered =data ["questions_answered"],
        accuracy =data ["accuracy"],
        date =data ["date"]
        )
