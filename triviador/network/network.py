import socket
import threading
import json
import time
from typing import Callable ,Optional
from dataclasses import dataclass ,field
from queue import Queue

from triviador.core.config import DEFAULT_PORT ,BUFFER_SIZE


@dataclass
class NetworkMessage :

    type :str
    data :dict
    sender_id :Optional [str ]=None

    def to_json (self )->str :
        return json .dumps ({
        "type":self .type ,
        "data":self .data ,
        "sender_id":self .sender_id
        })

    @classmethod
    def from_json (cls ,json_str :str )->"NetworkMessage":
        data =json .loads (json_str )
        return cls (
        type =data ["type"],
        data =data ["data"],
        sender_id =data .get ("sender_id")
        )


@dataclass
class OnlinePlayer :

    id :str
    name :str
    score :int =0
    ready :bool =False
    connected :bool =True
    current_answer :Optional [str ]=None
    answer_time :float =0.0
    jokers :dict =field (default_factory =dict )

    def __post_init__ (self ):
        if not self .jokers :
            from triviador.core.config import JOKERS_PER_GAME
            self .jokers =JOKERS_PER_GAME .copy ()

    def has_joker (self ,joker_type :str )->bool :
        return self .jokers .get (joker_type ,0 )>0

    def use_joker (self ,joker_type :str )->bool :
        if self .jokers .get (joker_type ,0 )>0 :
            self .jokers [joker_type ]-=1
            return True
        return False


class GameServer :


    def __init__ (self ,port :int =DEFAULT_PORT ):
        self .port =port
        self .server_socket :Optional [socket .socket ]=None
        self .clients :dict [str ,socket .socket ]={}
        self .running =False
        self .on_message :Optional [Callable [[NetworkMessage ,str ],None ]]=None
        self .on_client_connected :Optional [Callable [[str ],None ]]=None
        self .on_client_disconnected :Optional [Callable [[str ],None ]]=None

    def start (self )->bool :

        try :
            self .server_socket =socket .socket (socket .AF_INET ,socket .SOCK_STREAM )
            self .server_socket .setsockopt (socket .SOL_SOCKET ,socket .SO_REUSEADDR ,1 )
            self .server_socket .bind (('0.0.0.0',self .port ))
            self .server_socket .listen (5 )
            self .running =True


            accept_thread =threading .Thread (target =self ._accept_connections ,daemon =True )
            accept_thread .start ()

            return True
        except Exception as e :
            print (f"Грешка при стартиране на сървъра: {e }")
            return False

    def _accept_connections (self )->None :

        while self .running :
            try :
                client_socket ,address =self .server_socket .accept ()
                client_id =f"{address [0 ]}:{address [1 ]}"
                self .clients [client_id ]=client_socket

                if self .on_client_connected :
                    self .on_client_connected (client_id )


                client_thread =threading .Thread (
                target =self ._handle_client ,
                args =(client_id ,client_socket ),
                daemon =True
                )
                client_thread .start ()
            except :
                break

    def _handle_client (self ,client_id :str ,client_socket :socket .socket )->None :

        while self .running :
            try :
                data =client_socket .recv (BUFFER_SIZE )
                if not data :
                    break

                message =NetworkMessage .from_json (data .decode ('utf-8'))
                message .sender_id =client_id

                if self .on_message :
                    self .on_message (message ,client_id )
            except :
                break


        if client_id in self .clients :
            del self .clients [client_id ]
            if self .on_client_disconnected :
                self .on_client_disconnected (client_id )

    def send_to_client (self ,client_id :str ,message :NetworkMessage )->bool :

        if client_id not in self .clients :
            return False

        try :
            self .clients [client_id ].send (message .to_json ().encode ('utf-8'))
            return True
        except :
            return False

    def broadcast (self ,message :NetworkMessage ,exclude :Optional [str ]=None )->None :

        for client_id in list (self .clients .keys ()):
            if client_id !=exclude :
                self .send_to_client (client_id ,message )

    def stop (self )->None :

        self .running =False

        for client_socket in list (self .clients .values ()):
            try :
                client_socket .close ()
            except :
                pass

        self .clients .clear ()

        if self .server_socket :
            try :
                self .server_socket .close ()
            except :
                pass

    def get_local_ip (self )->str :

        try :
            s =socket .socket (socket .AF_INET ,socket .SOCK_DGRAM )
            s .connect (("8.8.8.8",80 ))
            ip =s .getsockname ()[0 ]
            s .close ()
            return ip
        except :
            return "127.0.0.1"


class GameClient :


    def __init__ (self ):
        self .socket :Optional [socket .socket ]=None
        self .running =False
        self .on_message :Optional [Callable [[NetworkMessage ],None ]]=None
        self .on_disconnected :Optional [Callable [[],None ]]=None

    def connect (self ,host :str ,port :int =DEFAULT_PORT )->bool :

        try :
            self .socket =socket .socket (socket .AF_INET ,socket .SOCK_STREAM )
            self .socket .connect ((host ,port ))
            self .running =True


            receive_thread =threading .Thread (target =self ._receive_messages ,daemon =True )
            receive_thread .start ()

            return True
        except Exception as e :
            print (f"Грешка при свързване: {e }")
            return False

    def _receive_messages (self )->None :

        while self .running :
            try :
                data =self .socket .recv (BUFFER_SIZE )
                if not data :
                    break

                message =NetworkMessage .from_json (data .decode ('utf-8'))

                if self .on_message :
                    self .on_message (message )
            except :
                break

        if self .on_disconnected :
            self .on_disconnected ()

    def send (self ,message :NetworkMessage )->bool :

        if not self .socket :
            return False

        try :
            self .socket .send (message .to_json ().encode ('utf-8'))
            return True
        except :
            return False

    def disconnect (self )->None :

        self .running =False

        if self .socket :
            try :
                self .socket .close ()
            except :
                pass


class MessageTypes :


    JOIN_GAME ="join_game"
    PLAYER_JOINED ="player_joined"
    PLAYER_LEFT ="player_left"
    GAME_START ="game_start"


    QUESTION ="question"
    ANSWER ="answer"
    ANSWER_RESULT ="answer_result"
    ROUND_END ="round_end"
    GAME_END ="game_end"


    USE_JOKER ="use_joker"
    JOKER_RESULT ="joker_result"


    CHAT_MESSAGE ="chat_message"


    SYNC_STATE ="sync_state"
    PING ="ping"
    PONG ="pong"


class GameLobby :


    def __init__ (self ,is_host :bool =False ):
        self .is_host =is_host
        self .players :dict [str ,OnlinePlayer ]={}
        self .my_id :Optional [str ]=None
        self .my_name :str =""
        self .game_started =False
        self .current_question :Optional [dict ]=None
        self .question_start_time :float =0
        self .all_answers_received =False
        self .round_results :list [dict ]=[]


        self .server :Optional [GameServer ]=None
        self .client :Optional [GameClient ]=None


        self .message_queue :Queue =Queue ()


        self .on_player_joined :Optional [Callable [[OnlinePlayer ],None ]]=None
        self .on_player_left :Optional [Callable [[str ],None ]]=None
        self .on_game_start :Optional [Callable [[],None ]]=None
        self .on_question_received :Optional [Callable [[dict ],None ]]=None
        self .on_answer_result :Optional [Callable [[dict ],None ]]=None
        self .on_round_end :Optional [Callable [[list ],None ]]=None
        self .on_game_end :Optional [Callable [[list ],None ]]=None
        self .on_joker_result :Optional [Callable [[dict ],None ]]=None
        self .on_error :Optional [Callable [[str ],None ]]=None

    def host_game (self ,player_name :str ,port :int =DEFAULT_PORT )->bool :

        self .is_host =True
        self .my_name =player_name
        self .server =GameServer (port )

        self .server .on_message =self ._handle_server_message
        self .server .on_client_connected =self ._on_client_connected
        self .server .on_client_disconnected =self ._on_client_disconnected

        if not self .server .start ():
            return False


        self .my_id ="host"
        host_player =OnlinePlayer (id ="host",name =player_name ,ready =True )
        self .players ["host"]=host_player

        return True

    def join_game (self ,player_name :str ,host_ip :str ,port :int =DEFAULT_PORT )->bool :

        self .is_host =False
        self .my_name =player_name
        self .client =GameClient ()

        self .client .on_message =self ._handle_client_message
        self .client .on_disconnected =self ._on_disconnected

        if not self .client .connect (host_ip ,port ):
            return False


        self .client .send (NetworkMessage (
        type =MessageTypes .JOIN_GAME ,
        data ={"name":player_name }
        ))

        return True

    def _on_client_connected (self ,client_id :str )->None :

        pass

    def _on_client_disconnected (self ,client_id :str )->None :

        if client_id in self .players :
            player =self .players [client_id ]
            del self .players [client_id ]


            if self .server :
                self .server .broadcast (NetworkMessage (
                type =MessageTypes .PLAYER_LEFT ,
                data ={"player_id":client_id ,"name":player .name }
                ))

            if self .on_player_left :
                self .on_player_left (client_id )

    def _on_disconnected (self )->None :

        if self .on_error :
            self .on_error ("Връзката със сървъра беше прекъсната")

    def _handle_server_message (self ,message :NetworkMessage ,client_id :str )->None :

        if message .type ==MessageTypes .JOIN_GAME :

            player_name =message .data .get ("name","Player")

            if len (self .players )>=4 :
                self .server .send_to_client (client_id ,NetworkMessage (
                type ="error",
                data ={"message":"Играта е пълна"}
                ))
                return

            if self .game_started :
                self .server .send_to_client (client_id ,NetworkMessage (
                type ="error",
                data ={"message":"Играта вече е започнала"}
                ))
                return


            new_player =OnlinePlayer (id =client_id ,name =player_name )
            self .players [client_id ]=new_player


            players_data =[{"id":p .id ,"name":p .name ,"ready":p .ready }
            for p in self .players .values ()]

            self .server .send_to_client (client_id ,NetworkMessage (
            type =MessageTypes .PLAYER_JOINED ,
            data ={
            "your_id":client_id ,
            "players":players_data ,
            "success":True
            }
            ))


            self .server .broadcast (NetworkMessage (
            type =MessageTypes .PLAYER_JOINED ,
            data ={
            "player":{"id":client_id ,"name":player_name },
            "players":players_data
            }
            ),exclude =client_id )

            if self .on_player_joined :
                self .on_player_joined (new_player )

        elif message .type ==MessageTypes .ANSWER :

            self ._process_player_answer (client_id ,message .data )

        elif message .type ==MessageTypes .USE_JOKER :

            self ._process_joker_use (client_id ,message .data )

    def _handle_client_message (self ,message :NetworkMessage )->None :

        if message .type ==MessageTypes .PLAYER_JOINED :
            if "your_id"in message .data :

                self .my_id =message .data ["your_id"]


                for p_data in message .data .get ("players",[]):
                    player =OnlinePlayer (
                    id =p_data ["id"],
                    name =p_data ["name"],
                    ready =p_data .get ("ready",False )
                    )
                    self .players [p_data ["id"]]=player
            else :

                p_data =message .data .get ("player",{})
                if p_data :
                    player =OnlinePlayer (id =p_data ["id"],name =p_data ["name"])
                    self .players [p_data ["id"]]=player

                    if self .on_player_joined :
                        self .on_player_joined (player )

        elif message .type ==MessageTypes .PLAYER_LEFT :
            player_id =message .data .get ("player_id")
            if player_id in self .players :
                del self .players [player_id ]
                if self .on_player_left :
                    self .on_player_left (player_id )

        elif message .type ==MessageTypes .GAME_START :
            self .game_started =True
            if self .on_game_start :
                self .on_game_start ()

        elif message .type ==MessageTypes .QUESTION :
            self .current_question =message .data
            self .question_start_time =time .time ()
            if self .on_question_received :
                self .on_question_received (message .data )

        elif message .type ==MessageTypes .ANSWER_RESULT :
            if self .on_answer_result :
                self .on_answer_result (message .data )

        elif message .type ==MessageTypes .ROUND_END :
            self .round_results =message .data .get ("results",[])
            if self .on_round_end :
                self .on_round_end (self .round_results )

        elif message .type ==MessageTypes .GAME_END :
            if self .on_game_end :
                self .on_game_end (message .data .get ("final_scores",[]))

        elif message .type ==MessageTypes .JOKER_RESULT :
            if self .on_joker_result :
                self .on_joker_result (message .data )

        elif message .type =="error":
            if self .on_error :
                self .on_error (message .data .get ("message","Неизвестна грешка"))

    def _process_player_answer (self ,player_id :str ,data :dict )->None :

        if player_id not in self .players :
            return

        player =self .players [player_id ]
        player .current_answer =data .get ("answer")
        player .answer_time =data .get ("time",0 )


        all_answered =all (
        p .current_answer is not None
        for p in self .players .values ()
        )

        if all_answered :
            self .all_answers_received =True

    def _process_joker_use (self ,player_id :str ,data :dict )->None :
        from triviador.logic.joker_system import JokerSystem
        from triviador.core.models import Question ,QuestionType

        joker_type =data .get ("joker_type")
        if not joker_type or player_id not in self .players :
            return

        player =self .players [player_id ]
        is_special =data .get ("is_special_round",False )

        if is_special :
            self .server .send_to_client (player_id ,NetworkMessage (
            type =MessageTypes .JOKER_RESULT ,
            data ={"error":"Жокерите не могат да се използват в специален рунд!"}
            ))
            return

        if not player .has_joker (joker_type ):
            self .server .send_to_client (player_id ,NetworkMessage (
            type =MessageTypes .JOKER_RESULT ,
            data ={"error":"Нямате повече такива жокери!"}
            ))
            return

        player .use_joker (joker_type )

        if not self .current_question :
            return

        q =self .current_question
        question =Question (
            id =0 ,
            category =q .get ("category",""),
            difficulty =q .get ("difficulty",1 ),
            question_type =QuestionType (q .get ("question_type","multiple_choice")),
            question_text =q .get ("text",""),
            correct_answer =q .get ("correct_answer",""),
            options =q .get ("options",[])
        )

        from triviador.core.config import JOKER_5050 ,JOKER_AUDIENCE

        if joker_type ==JOKER_5050 :
            result =JokerSystem .apply_5050 (question )
            result_data ={"type":"5050","remaining_options":result ,
                "joker_type":joker_type ,"remaining_count":player .jokers .get (joker_type ,0 )}
        elif joker_type ==JOKER_AUDIENCE :
            result =JokerSystem .apply_audience_help (question )
            result_data ={"type":"audience","votes":result ,
                "joker_type":joker_type ,"remaining_count":player .jokers .get (joker_type ,0 )}
        else :
            return

        self .server .send_to_client (player_id ,NetworkMessage (
        type =MessageTypes .JOKER_RESULT ,
        data =result_data
        ))


    def start_game (self )->bool :

        if not self .is_host :
            return False

        if len (self .players )<2 :
            return False

        self .game_started =True


        self .server .broadcast (NetworkMessage (
        type =MessageTypes .GAME_START ,
        data ={"players":[{"id":p .id ,"name":p .name }for p in self .players .values ()]}
        ))

        if self .on_game_start :
            self .on_game_start ()

        return True

    def send_question (self ,question_data :dict ,eliminated :set =None )->None :

        if not self .is_host :
            return

        eliminated =eliminated or set ()

        for player in self .players .values ():
            if player .name in eliminated :
                player .current_answer =""
                player .answer_time =0
            else :
                player .current_answer =None
                player .answer_time =0

        self .all_answers_received =False
        self .current_question =question_data
        self .question_start_time =time .time ()

        self .server .broadcast (NetworkMessage (
        type =MessageTypes .QUESTION ,
        data =question_data
        ))

    def submit_answer (self ,answer :str )->None :

        answer_time =time .time ()-self .question_start_time

        if self .is_host :

            self .players ["host"].current_answer =answer
            self .players ["host"].answer_time =answer_time


            all_answered =all (
            p .current_answer is not None
            for p in self .players .values ()
            )
            if all_answered :
                self .all_answers_received =True
        else :

            self .client .send (NetworkMessage (
            type =MessageTypes .ANSWER ,
            data ={"answer":answer ,"time":answer_time }
            ))

    def send_answer_results (self ,results :dict )->None :

        if not self .is_host :
            return

        self .server .broadcast (NetworkMessage (
        type =MessageTypes .ANSWER_RESULT ,
        data =results
        ))

    def send_round_end (self ,results :list )->None :

        if not self .is_host :
            return

        self .server .broadcast (NetworkMessage (
        type =MessageTypes .ROUND_END ,
        data ={"results":results }
        ))

    def send_game_end (self ,final_scores :list )->None :

        if not self .is_host :
            return

        self .server .broadcast (NetworkMessage (
        type =MessageTypes .GAME_END ,
        data ={"final_scores":final_scores }
        ))

    def get_local_ip (self )->str :

        try :
            s =socket .socket (socket .AF_INET ,socket .SOCK_DGRAM )
            s .connect (("8.8.8.8",80 ))
            ip =s .getsockname ()[0 ]
            s .close ()
            return ip
        except :
            return "127.0.0.1"

    def get_players_list (self )->list [OnlinePlayer ]:

        return list (self .players .values ())

    def close (self )->None :

        if self .server :
            self .server .stop ()
        if self .client :
            self .client .disconnect ()
