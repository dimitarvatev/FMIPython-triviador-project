import pygame
from typing import Callable ,Optional ,Any

from triviador.core.config import (
WHITE ,BLACK ,GRAY ,LIGHT_GRAY ,DARK_GRAY ,
RED ,GREEN ,BLUE ,YELLOW ,PURPLE ,ORANGE ,
FONT_SMALL ,FONT_MEDIUM ,FONT_LARGE ,FONT_XLARGE ,
DIFFICULTY_COLORS
)


class Button :


    def __init__ (
    self ,
    x :int ,
    y :int ,
    width :int ,
    height :int ,
    text :str ,
    font_size :int =FONT_MEDIUM ,
    bg_color :tuple =BLUE ,
    hover_color :tuple =None ,
    text_color :tuple =WHITE ,
    disabled_color :tuple =GRAY ,
    border_radius :int =10 ,
    callback :Optional [Callable ]=None
    ):
        self .rect =pygame .Rect (x ,y ,width ,height )
        self .text =text
        self .font_size =font_size
        self .bg_color =bg_color
        self .hover_color =hover_color or tuple (min (c +30 ,255 )for c in bg_color )
        self .text_color =text_color
        self .disabled_color =disabled_color
        self .border_radius =border_radius
        self .callback =callback
        self .enabled =True
        self .hovered =False
        self .font =pygame .font .Font (None ,font_size )

    def draw (self ,surface :pygame .Surface )->None :

        if not self .enabled :
            color =self .disabled_color
        elif self .hovered :
            color =self .hover_color
        else :
            color =self .bg_color

        pygame .draw .rect (surface ,color ,self .rect ,border_radius =self .border_radius )
        pygame .draw .rect (surface ,DARK_GRAY ,self .rect ,2 ,border_radius =self .border_radius )

        text_surface =self .font .render (self .text ,True ,self .text_color if self .enabled else LIGHT_GRAY )
        text_rect =text_surface .get_rect (center =self .rect .center )
        surface .blit (text_surface ,text_rect )

    def handle_event (self ,event :pygame .event .Event )->bool :

        if not self .enabled :
            return False

        if event .type ==pygame .MOUSEMOTION :
            self .hovered =self .rect .collidepoint (event .pos )

        elif event .type ==pygame .MOUSEBUTTONDOWN :
            if self .rect .collidepoint (event .pos ):
                if self .callback :
                    self .callback ()
                return True

        return False

    def set_text (self ,text :str )->None :

        self .text =text


class TextInput :


    def __init__ (
    self ,
    x :int ,
    y :int ,
    width :int ,
    height :int ,
    font_size :int =FONT_MEDIUM ,
    placeholder :str ="",
    max_length :int =50 ,
    numeric_only :bool =False
    ):
        self .rect =pygame .Rect (x ,y ,width ,height )
        self .text =""
        self .placeholder =placeholder
        self .max_length =max_length
        self .numeric_only =numeric_only
        self .font =pygame .font .Font (None ,font_size )
        self .active =False
        self .cursor_visible =True
        self .cursor_timer =0

    def draw (self ,surface :pygame .Surface )->None :


        bg_color =WHITE if self .active else LIGHT_GRAY
        pygame .draw .rect (surface ,bg_color ,self .rect ,border_radius =5 )


        border_color =BLUE if self .active else GRAY
        pygame .draw .rect (surface ,border_color ,self .rect ,2 ,border_radius =5 )


        if self .text :
            text_surface =self .font .render (self .text ,True ,BLACK )
        else :
            text_surface =self .font .render (self .placeholder ,True ,GRAY )

        text_rect =text_surface .get_rect (midleft =(self .rect .x +10 ,self .rect .centery ))
        surface .blit (text_surface ,text_rect )


        if self .active and self .cursor_visible :
            cursor_x =text_rect .right +2
            pygame .draw .line (
            surface ,BLACK ,
            (cursor_x ,self .rect .y +10 ),
            (cursor_x ,self .rect .bottom -10 ),
            2
            )

    def update (self ,dt :float )->None :

        self .cursor_timer +=dt
        if self .cursor_timer >=0.5 :
            self .cursor_visible =not self .cursor_visible
            self .cursor_timer =0

    def handle_event (self ,event :pygame .event .Event )->Optional [str ]:

        if event .type ==pygame .MOUSEBUTTONDOWN :
            self .active =self .rect .collidepoint (event .pos )

        elif event .type ==pygame .KEYDOWN and self .active :
            if event .key ==pygame .K_RETURN :
                return self .text
            elif event .key ==pygame .K_BACKSPACE :
                self .text =self .text [:-1 ]
            else :
                if len (self .text )<self .max_length :
                    char =event .unicode
                    if self .numeric_only :
                        if char .isdigit ()or (char =='-'and len (self .text )==0 )or char =='.':
                            self .text +=char
                    else :
                        if char .isprintable ():
                            self .text +=char

        return None

    def clear (self )->None :

        self .text =""

    def get_value (self )->str :

        return self .text


class CheckBox :


    def __init__ (
    self ,
    x :int ,
    y :int ,
    size :int ,
    label :str ,
    font_size :int =FONT_MEDIUM ,
    checked :bool =False
    ):
        self .rect =pygame .Rect (x ,y ,size ,size )
        self .label =label
        self .font =pygame .font .Font (None ,font_size )
        self .checked =checked

    def draw (self ,surface :pygame .Surface )->None :


        pygame .draw .rect (surface ,WHITE ,self .rect ,border_radius =3 )
        pygame .draw .rect (surface ,DARK_GRAY ,self .rect ,2 ,border_radius =3 )


        if self .checked :
            padding =4
            inner_rect =self .rect .inflate (-padding *2 ,-padding *2 )
            pygame .draw .rect (surface ,GREEN ,inner_rect ,border_radius =2 )


        text_surface =self .font .render (self .label ,True ,BLACK )
        text_rect =text_surface .get_rect (midleft =(self .rect .right +10 ,self .rect .centery ))
        surface .blit (text_surface ,text_rect )

    def handle_event (self ,event :pygame .event .Event )->bool :

        if event .type ==pygame .MOUSEBUTTONDOWN :

            label_width =self .font .size (self .label )[0 ]
            click_rect =pygame .Rect (
            self .rect .x ,self .rect .y ,
            self .rect .width +10 +label_width ,self .rect .height
            )
            if click_rect .collidepoint (event .pos ):
                self .checked =not self .checked
                return True
        return False


class ProgressBar :


    def __init__ (
    self ,
    x :int ,
    y :int ,
    width :int ,
    height :int ,
    max_value :float ,
    color :tuple =GREEN ,
    bg_color :tuple =LIGHT_GRAY
    ):
        self .rect =pygame .Rect (x ,y ,width ,height )
        self .max_value =max_value
        self .current_value =max_value
        self .color =color
        self .bg_color =bg_color

    def draw (self ,surface :pygame .Surface )->None :


        pygame .draw .rect (surface ,self .bg_color ,self .rect ,border_radius =5 )


        if self .current_value >0 :
            progress_width =int ((self .current_value /self .max_value )*self .rect .width )
            progress_rect =pygame .Rect (self .rect .x ,self .rect .y ,progress_width ,self .rect .height )


            if self .current_value /self .max_value >0.5 :
                color =self .color
            elif self .current_value /self .max_value >0.25 :
                color =YELLOW
            else :
                color =RED

            pygame .draw .rect (surface ,color ,progress_rect ,border_radius =5 )


        pygame .draw .rect (surface ,DARK_GRAY ,self .rect ,2 ,border_radius =5 )

    def set_value (self ,value :float )->None :

        self .current_value =max (0 ,min (value ,self .max_value ))


class Label :


    def __init__ (
    self ,
    x :int ,
    y :int ,
    text :str ,
    font_size :int =FONT_MEDIUM ,
    color :tuple =BLACK ,
    center :bool =False
    ):
        self .x =x
        self .y =y
        self .text =text
        self .font =pygame .font .Font (None ,font_size )
        self .color =color
        self .center =center

    def draw (self ,surface :pygame .Surface )->None :

        text_surface =self .font .render (self .text ,True ,self .color )
        if self .center :
            text_rect =text_surface .get_rect (center =(self .x ,self .y ))
        else :
            text_rect =text_surface .get_rect (topleft =(self .x ,self .y ))
        surface .blit (text_surface ,text_rect )

    def set_text (self ,text :str )->None :

        self .text =text


class Panel :


    def __init__ (
    self ,
    x :int ,
    y :int ,
    width :int ,
    height :int ,
    bg_color :tuple =WHITE ,
    border_color :tuple =DARK_GRAY ,
    border_width :int =2 ,
    border_radius :int =10
    ):
        self .rect =pygame .Rect (x ,y ,width ,height )
        self .bg_color =bg_color
        self .border_color =border_color
        self .border_width =border_width
        self .border_radius =border_radius

    def draw (self ,surface :pygame .Surface )->None :

        pygame .draw .rect (surface ,self .bg_color ,self .rect ,border_radius =self .border_radius )
        if self .border_width >0 :
            pygame .draw .rect (
            surface ,self .border_color ,self .rect ,
            self .border_width ,border_radius =self .border_radius
            )


class AnswerButton (Button ):


    def __init__ (self ,x :int ,y :int ,width :int ,height :int ,text :str ,option_letter :str =""):
        super ().__init__ (x ,y ,width ,height ,text ,FONT_MEDIUM ,LIGHT_GRAY ,None ,BLACK )
        self .option_letter =option_letter
        self .state ="normal"
        self .selected =False
        self .is_correct =False
        self .is_incorrect =False

    def draw (self ,surface :pygame .Surface )->None :

        if self .is_correct :
            color =GREEN
        elif self .is_incorrect :
            color =RED
        elif self .selected :
            color =BLUE
        elif self .state =="correct":
            color =GREEN
        elif self .state =="wrong":
            color =RED
        elif self .state =="eliminated":
            color =GRAY
            self .enabled =False
        elif self .hovered and self .enabled :
            color =self .hover_color
        else :
            color =self .bg_color

        pygame .draw .rect (surface ,color ,self .rect ,border_radius =self .border_radius )
        pygame .draw .rect (surface ,DARK_GRAY ,self .rect ,2 ,border_radius =self .border_radius )


        letter_font =pygame .font .Font (None ,FONT_LARGE )
        letter_surface =letter_font .render (f"{self .option_letter })",True ,BLUE )
        letter_rect =letter_surface .get_rect (midleft =(self .rect .x +15 ,self .rect .centery ))
        surface .blit (letter_surface ,letter_rect )


        text_color =LIGHT_GRAY if self .state =="eliminated"else self .text_color
        text_surface =self .font .render (self .text ,True ,text_color )
        text_rect =text_surface .get_rect (midleft =(self .rect .x +50 ,self .rect .centery ))


        max_width =self .rect .width -70
        if text_rect .width >max_width :

            small_font =pygame .font .Font (None ,FONT_SMALL )
            text_surface =small_font .render (self .text ,True ,text_color )
            text_rect =text_surface .get_rect (midleft =(self .rect .x +50 ,self .rect .centery ))

        surface .blit (text_surface ,text_rect )

    def set_state (self ,state :str )->None :

        self .state =state
        self .enabled =state not in ("eliminated","correct","wrong")


class JokerButton (Button ):


    def __init__ (self ,x :int ,y :int ,width :int ,height :int ,joker_type :str ,count :int ):
        from triviador.logic.joker_system import JokerSystem
        self .display_name =JokerSystem .get_joker_name (joker_type )
        text =f"{self .display_name } ({count })"
        super ().__init__ (x ,y ,width ,height ,text ,FONT_SMALL ,PURPLE )
        self .joker_type =joker_type
        self .count =count

    def update_count (self ,count :int )->None :

        self .count =count
        self .text =f"{self .display_name } ({count })"
        self .enabled =count >0

    def set_display_name (self ,name :str )->None :

        self .display_name =name
        self .text =f"{self .display_name } ({self .count })"


class DifficultyIndicator :


    def __init__ (self ,x :int ,y :int ,size :int =20 ):
        self .x =x
        self .y =y
        self .size =size
        self .difficulty =1

    def draw (self ,surface :pygame .Surface )->None :

        for i in range (5 ):
            color =DIFFICULTY_COLORS .get (i +1 ,GRAY )
            if i +1 >self .difficulty :
                color =LIGHT_GRAY

            rect =pygame .Rect (
            self .x +i *(self .size +5 ),
            self .y ,
            self .size ,
            self .size
            )
            pygame .draw .rect (surface ,color ,rect ,border_radius =3 )
            pygame .draw .rect (surface ,DARK_GRAY ,rect ,1 ,border_radius =3 )

    def set_difficulty (self ,difficulty :int )->None :

        self .difficulty =max (1 ,min (5 ,difficulty ))


class AudienceChart :


    def __init__ (self ,x :int ,y :int ,width :int ,height :int ):
        self .rect =pygame .Rect (x ,y ,width ,height )
        self .votes :dict [str ,int ]={}

    def draw (self ,surface :pygame .Surface )->None :

        if not self .votes :
            return


        pygame .draw .rect (surface ,WHITE ,self .rect ,border_radius =10 )
        pygame .draw .rect (surface ,DARK_GRAY ,self .rect ,2 ,border_radius =10 )


        font =pygame .font .Font (None ,FONT_MEDIUM )
        title =font .render ("Помощ от публиката",True ,BLACK )
        title_rect =title .get_rect (centerx =self .rect .centerx ,top =self .rect .top +10 )
        surface .blit (title ,title_rect )


        bar_height =30
        bar_spacing =10
        bar_start_y =self .rect .y +50
        max_bar_width =self .rect .width -100

        colors =[BLUE ,GREEN ,ORANGE ,PURPLE ]

        for i ,(option ,percent )in enumerate (self .votes .items ()):
            y =bar_start_y +i *(bar_height +bar_spacing )


            small_font =pygame .font .Font (None ,FONT_SMALL )
            label =small_font .render (f"{option [:20 ]}",True ,BLACK )
            surface .blit (label ,(self .rect .x +10 ,y +5 ))


            bar_width =int ((percent /100 )*max_bar_width )
            bar_rect =pygame .Rect (self .rect .x +10 ,y +25 ,bar_width ,bar_height -20 )
            pygame .draw .rect (surface ,colors [i %len (colors )],bar_rect ,border_radius =3 )


            percent_text =small_font .render (f"{percent }%",True ,BLACK )
            surface .blit (percent_text ,(self .rect .x +15 +bar_width ,y +25 ))

    def set_votes (self ,votes :dict [str ,int ])->None :

        self .votes =votes
