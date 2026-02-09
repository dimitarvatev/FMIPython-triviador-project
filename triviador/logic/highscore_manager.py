import json
from pathlib import Path
from datetime import datetime
from typing import Optional

from triviador.core.models import HighScore ,Player ,GameMode
from triviador.core.config import HIGHSCORES_FILE


BASE_DIR =Path (__file__ ).resolve ().parent .parent /"data"


class HighScoreManager :


    MAX_HIGHSCORES =10

    def __init__ (self ,highscores_file :str =HIGHSCORES_FILE ):
        self .highscores_file =BASE_DIR /highscores_file
        self .highscores :list [HighScore ]=[]
        self ._load_highscores ()

    def _load_highscores (self )->None :

        if not self .highscores_file .exists ():
            self .highscores =[]
            return

        try :
            with open (self .highscores_file ,"r",encoding ="utf-8")as f :
                data =json .load (f )
            self .highscores =[HighScore .from_dict (hs )for hs in data ]
        except (json .JSONDecodeError ,KeyError ):
            self .highscores =[]

    def _save_highscores (self )->None :

        data =[hs .to_dict ()for hs in self .highscores ]
        with open (self .highscores_file ,"w",encoding ="utf-8")as f :
            json .dump (data ,f ,ensure_ascii =False ,indent =4 )

    def add_score (self ,player :Player ,mode :GameMode )->Optional [int ]:

        highscore =HighScore (
        player_name =player .name ,
        score =player .score ,
        mode =mode .value ,
        questions_answered =player .total_answers ,
        accuracy =player .accuracy ,
        date =datetime .now ().strftime ("%Y-%m-%d %H:%M")
        )

        self .highscores .append (highscore )
        self .highscores .sort (key =lambda x :x .score ,reverse =True )


        self .highscores =self .highscores [:self .MAX_HIGHSCORES ]
        self ._save_highscores ()


        for i ,hs in enumerate (self .highscores ):
            if hs .player_name ==player .name and hs .score ==player .score :
                return i +1

        return None

    def get_top_scores (self ,count :int =10 )->list [HighScore ]:

        return self .highscores [:count ]

    def get_scores_by_mode (self ,mode :str )->list [HighScore ]:

        return [hs for hs in self .highscores if hs .mode ==mode ]

    def is_highscore (self ,score :int )->bool :

        if len (self .highscores )<self .MAX_HIGHSCORES :
            return True
        return score >self .highscores [-1 ].score

    def clear_highscores (self )->None :

        self .highscores =[]
        self ._save_highscores ()
