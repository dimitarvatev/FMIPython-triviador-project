import json
import random
import re
from pathlib import Path
from typing import Optional

from triviador.core.models import Question ,QuestionType
from triviador.core.config import QUESTIONS_FILE


BASE_DIR =Path (__file__ ).resolve ().parent .parent /"data"


QUESTIONS_TXT_FILE ="questions.txt"


class QuestionManager :


    def __init__ (self ,questions_file :str =None ):

        if questions_file :
            self .questions_file =BASE_DIR /questions_file
        elif (BASE_DIR /QUESTIONS_TXT_FILE ).exists ():
            self .questions_file =BASE_DIR /QUESTIONS_TXT_FILE
        else :
            self .questions_file =BASE_DIR /QUESTIONS_FILE

        self .questions :list [Question ]=[]
        self .categories :list [str ]=[]
        self ._load_questions ()

    def _load_questions (self )->None :

        if not self .questions_file .exists ():
            raise FileNotFoundError (f"Файлът с въпроси не е намерен: {self .questions_file }")

        if self .questions_file .suffix =='.txt':
            self ._load_from_txt ()
        else :
            self ._load_from_json ()

    def _load_from_json (self )->None :

        with open (self .questions_file ,"r",encoding ="utf-8")as f :
            data =json .load (f )

        self .categories =data .get ("categories",[])
        self .questions =[Question .from_dict (q )for q in data .get ("questions",[])]

    def _load_from_txt (self )->None :

        with open (self .questions_file ,"r",encoding ="utf-8")as f :
            content =f .read ()


        blocks =re .split (r'\n\s*\n',content )

        question_id =0
        categories_set =set ()

        for block in blocks :
            lines =[line .strip ()for line in block .strip ().split ('\n')
            if line .strip ()and not line .strip ().startswith ('#')]

            if not lines :
                continue


            question_data =self ._parse_question_block (lines )

            if question_data :
                question_id +=1
                question_data ['id']=question_id

                try :
                    question =Question .from_dict (question_data )
                    self .questions .append (question )
                    categories_set .add (question .category )
                except (KeyError ,ValueError )as e :
                    print (f"Грешка при зареждане на въпрос: {e }")
                    continue

        self .categories =sorted (list (categories_set ))

    def _parse_question_block (self ,lines :list [str ])->Optional [dict ]:

        data ={}

        for line in lines :

            if line .startswith ('[')and line .endswith (']'):
                data ['category']=line [1 :-1 ]


            elif line .lower ().startswith ('трудност:'):
                try :
                    data ['difficulty']=int (line .split (':',1 )[1 ].strip ())
                except ValueError :
                    data ['difficulty']=1


            elif line .lower ().startswith ('тип:'):
                type_str =line .split (':',1 )[1 ].strip ().lower ()
                if type_str in ('избор','multiple_choice','choice'):
                    data ['type']='multiple_choice'
                elif type_str in ('число','numeric','number'):
                    data ['type']='numeric'


            elif line .lower ().startswith ('въпрос:'):
                data ['question']=line .split (':',1 )[1 ].strip ()


            elif line .lower ().startswith ('отговор:'):
                answer =line .split (':',1 )[1 ].strip ()

                if data .get ('type')=='numeric':
                    try :
                        data ['correct_answer']=int (answer )
                    except ValueError :
                        try :
                            data ['correct_answer']=float (answer )
                        except ValueError :
                            data ['correct_answer']=answer
                else :
                    data ['correct_answer']=answer


            elif line .lower ().startswith ('опции:'):
                options_str =line .split (':',1 )[1 ].strip ()
                data ['options']=[opt .strip ()for opt in options_str .split (',')]


        required =['category','difficulty','type','question','correct_answer']
        if all (key in data for key in required ):
            if data ['type']=='multiple_choice'and 'options'not in data :
                return None
            return data

        return None

    def get_categories (self )->list [str ]:

        return self .categories .copy ()

    def get_questions_by_category (self ,category :str )->list [Question ]:

        return [q for q in self .questions if q .category ==category ]

    def get_questions_by_difficulty (self ,difficulty :int )->list [Question ]:

        return [q for q in self .questions if q .difficulty ==difficulty ]

    def get_random_questions (
    self ,
    count :int ,
    categories :Optional [list [str ]]=None ,
    difficulty_range :Optional [tuple [int ,int ]]=None ,
    exclude_ids :Optional [set [int ]]=None
    )->list [Question ]:

        filtered =self .questions .copy ()

        if categories :
            filtered =[q for q in filtered if q .category in categories ]

        if difficulty_range :
            min_diff ,max_diff =difficulty_range
            filtered =[q for q in filtered if min_diff <=q .difficulty <=max_diff ]

        if exclude_ids :
            filtered =[q for q in filtered if q .id not in exclude_ids ]

        if len (filtered )<count :
            count =len (filtered )

        return random .sample (filtered ,count )if filtered else []

    def get_questions_with_increasing_difficulty (
    self ,
    count :int ,
    categories :Optional [list [str ]]=None
    )->list [Question ]:

        questions =[]
        used_ids :set [int ]=set ()


        questions_per_level =max (1 ,count //5 )
        remainder =count %5

        for difficulty in range (1 ,6 ):
            num_questions =questions_per_level
            if difficulty <=remainder :
                num_questions +=1

            level_questions =self .get_random_questions (
            count =num_questions ,
            categories =categories ,
            difficulty_range =(difficulty ,difficulty ),
            exclude_ids =used_ids
            )

            questions .extend (level_questions )
            used_ids .update (q .id for q in level_questions )

        return questions

    def get_endless_mode_question (
    self ,
    current_score :int ,
    categories :Optional [list [str ]]=None ,
    exclude_ids :Optional [set [int ]]=None
    )->Optional [Question ]:


        if current_score <500 :
            difficulty_range =(1 ,2 )
        elif current_score <1500 :
            difficulty_range =(2 ,3 )
        elif current_score <3000 :
            difficulty_range =(3 ,4 )
        else :
            difficulty_range =(4 ,5 )

        questions =self .get_random_questions (
        count =1 ,
        categories =categories ,
        difficulty_range =difficulty_range ,
        exclude_ids =exclude_ids
        )


        if not questions :
            questions =self .get_random_questions (
            count =1 ,
            categories =categories ,
            exclude_ids =exclude_ids
            )

        return questions [0 ]if questions else None

    def add_question (self ,question_data :dict )->Question :


        max_id =max ((q .id for q in self .questions ),default =0 )
        question_data ["id"]=max_id +1

        question =Question .from_dict (question_data )
        self .questions .append (question )
        self ._save_questions ()

        return question

    def _save_questions (self )->None :

        data ={
        "categories":self .categories ,
        "questions":[
        {
        "id":q .id ,
        "category":q .category ,
        "difficulty":q .difficulty ,
        "type":q .question_type .value ,
        "question":q .question_text ,
        "correct_answer":q .correct_answer ,
        "options":q .options if q .question_type ==QuestionType .MULTIPLE_CHOICE else []
        }
        for q in self .questions
        ]
        }

        with open (self .questions_file ,"w",encoding ="utf-8")as f :
            json .dump (data ,f ,ensure_ascii =False ,indent =4 )
