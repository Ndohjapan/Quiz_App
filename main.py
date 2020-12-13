# Marist Pedia client main.py app
# Written by: Promise Sheggsmann

import os, sys
from kivy.resources import resource_add_path, resource_find
from kivy.lang import Builder
from kivymd.app import MDApp
from kivy.animation import Animation
from kivy.clock import Clock
import MbjQuiz
from MbjQuiz.Displayed_Client.network import Network
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.config import Config
from kivy.core.audio import SoundLoader
import time

Builder.load_string('''
#:import utils kivy.utils
''')


class MainApp(Screen):
    pass


# Main App class
class MaristApp(MDApp):
    network = None
    username = ''
    question_number = 0
    NUM = 0
    timer_called = True
    interval = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = 'MaristPedia'
        self.theme_cls.theme_style = 'Light'
        self.theme_cls.primary_palette = 'Blue'
        self.sm = ScreenManager()
        self.time_sec = 1
        self.angle = 360 / self.time_sec
        self.current_time = self.time_sec
        self.time = None
        self.sound = None
        self.sound_file = 'tick.mp3'

    def login(self):
        '''
        Handles how the user logs in and connects to the server
        :return: None
        '''
        # self.sm.current = 'Quiz_Page'
        self.username = self.root.ids.username_field.text
        ip_field = self.root.ids.ip_field.text
        print('[USERNAME]: ', self.username)
        print('[IP ADDRESS]: ', ip_field)
        # Network(ip_field, self.username, self.root.ids.screen_manager)
        self.network = Network(self.root, ip_field, self.username, self.root.ids.screen_manager)
        if self.network:
            self.root.ids.screen_manager.current = 'Home_Page'

    def change_time_sec(self, *args):
        self.time_sec = self.network.number_of_seconds
        self.root.ids.label.text = str(self.time_sec)
        self.angle = 360 / self.time_sec
        self.current_time = self.time_sec

    def choose_option(self, text, cur_time):
        '''
        This handles how the option chosen by the user
        :param cur_time:
        :param text: The current option chosen which defaults E if timer runs out
        :return: None
        '''
        if self.network:
            self.network.send_msg(f'{self.username} {text} {str(cur_time)}')
            print('SENT...')
        else:
            print(text)
        # Disable the buttons
        self.root.ids.options_layout_1.disabled = False
        self.root.ids.options_layout_2.disabled = False
        self.network.screen_enabled = False
        # reset the timer
        self.reset_timer()
        self.interval.cancel()
        self.timer_called = True

    def activate_screen(self, *args):
        '''
        Called in a shedule interval to know when the user activates the buttons and timer
        :param args: ...
        :return: None
        '''
        if self.network.screen_enabled:
            self.root.ids.options_layout_1.disabled = False
            self.root.ids.options_layout_2.disabled = False
            self.question_number += 1
            if self.timer_called:
                self.reset_timer()
                self._start_timer()
                self.timer_called = False

    def update_question(self, *args):
        '''
        Handles how the questions are updated
        :param args:
        :return: None
        '''
        if self.network and self.network.current_question:
            if self.question_number < 1:
                self.root.ids.screen_manager.current = 'Quiz_Page'
                self.change_time_sec()
            self.root.ids.question_display.text = f'[b][size=30][color=#FBDE44FF]{self.network.current_question}[/color][/size][/b]'

            Clock.schedule_interval(self.activate_screen, 0.1)
            self.root.ids.options_layout_1.disabled = False
            self.root.ids.options_layout_2.disabled = False

    def reset_timer(self, *args):
        self.NUM = 0
        self.root.ids.w_canvas.canvas.get_group('a')[0].angle_end = 360
        self.root.ids.label.text = str(self.time_sec)
        self.current_time = self.time_sec

    def animate_timer(self, *args):
        self.NUM += 1
        self.sound.play()  # Call the sound file to play
        self.time = self.time_sec - self.current_time
        if self.current_time == 0:
            self.choose_option('E', self.time)
        else:
            if self.NUM < self.time_sec + 1:
                self.current_time -= 1
                self.root.ids.w_canvas.canvas.get_group('a')[0].angle_end -= self.angle
                self.root.ids.label.text = str(self.current_time)

    def animate_card(self, *args):
        anim = Animation(pos_hint={'center_y': 0.5})
        anim.start(self.root.ids.card)

    def _start_timer(self, *args):
        self.interval = Clock.schedule_interval(self.animate_timer, 1)

    def on_start(self):
        Clock.schedule_interval(self.update_question, 0.1)
        self.animate_card('main')
        self.sound = SoundLoader.load(self.sound_file)  # initialize the sound file

    def build(self):
        return MainApp()


if __name__ == '__main__':
    if hasattr(sys, '_MEIPASS'):
        resource_add_path(os.path.join(sys._MEIPASS))
    # Config.set('graphics', 'width', '1300')
    # Config.set('graphics', 'height', '780')
    Config.set('graphics', 'resizable', False)

    MaristApp().run()
