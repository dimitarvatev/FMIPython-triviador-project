import random
from typing import Optional

from triviador.core.models import Question ,QuestionType ,Player
from triviador.core.config import JOKER_5050 ,JOKER_AUDIENCE


class JokerSystem :


    @staticmethod
    def apply_5050 (question :Question )->list [str ]:

        if question .question_type ==QuestionType .MULTIPLE_CHOICE :

            correct =question .correct_answer
            wrong_options =[opt for opt in question .options if opt !=correct ]

            if len (wrong_options )>=1 :

                kept_wrong =random .choice (wrong_options )
                remaining =[correct ,kept_wrong ]
                random .shuffle (remaining )
                return remaining
            return question .options

        elif question .question_type ==QuestionType .NUMERIC :

            correct =float (question .correct_answer )
            margin =correct *0.25
            low =int (correct -margin )
            high =int (correct +margin )
            return [f"{low } - {high }"]

        return []

    @staticmethod
    def apply_audience_help (question :Question )->dict [str ,int ]:

        if question .question_type !=QuestionType .MULTIPLE_CHOICE :

            correct =float (question .correct_answer )

            noise =correct *random .uniform (-0.05 ,0.05 )
            suggested =int (correct +noise )
            return {"suggested_value":suggested ,"confidence":random .randint (60 ,85 )}

        correct =question .correct_answer
        options =question .options


        difficulty =question .difficulty

        base_correct_percent =max (30 ,90 -(difficulty *10 ))


        results ={}
        remaining =100


        correct_votes =random .randint (base_correct_percent -10 ,base_correct_percent +10 )
        correct_votes =min (correct_votes ,95 )
        results [correct ]=correct_votes
        remaining -=correct_votes


        wrong_options =[opt for opt in options if opt !=correct ]

        for i ,opt in enumerate (wrong_options ):
            if i ==len (wrong_options )-1 :

                results [opt ]=remaining
            else :
                votes =random .randint (0 ,remaining )
                results [opt ]=votes
                remaining -=votes

        return results

    @staticmethod
    def can_use_joker (player :Player ,joker_type :str ,is_special_round :bool )->tuple [bool ,str ]:

        if is_special_round :
            return False ,"Жокерите не могат да се използват в специален рунд!"

        if not player .has_joker (joker_type ):
            return False ,f"Нямате повече жокери от тип {JokerSystem .get_joker_name (joker_type )}!"

        return True ,""

    @staticmethod
    def get_joker_name (joker_type :str )->str :

        names ={
        JOKER_5050 :"50/50",
        JOKER_AUDIENCE :"Помощ от публиката"
        }
        return names .get (joker_type ,joker_type )

    @staticmethod
    def get_joker_description (joker_type :str )->str :

        descriptions ={
        JOKER_5050 :"Премахва два грешни отговора или показва диапазон за числа",
        JOKER_AUDIENCE :"Показва как би гласувала публиката"
        }
        return descriptions .get (joker_type ,"")
