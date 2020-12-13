import socket
import pickle
import threading
from kivymd.toast import toast
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivy.clock import Clock
from kivymd.uix.list import OneLineListItem


class ListItem(OneLineListItem):
    def __init__(self, **kwargs):
        super(ListItem, self).__init__(**kwargs)
        pass


class Network:
    PORT = 5000
    BYTES = 2048
    FORMAT = 'UTF-8'

    def __init__(self, root, ip, username, screen):
        self.username = username
        self.ip = ip
        self.screen = screen
        self.current_question = None
        self.current_msg = None
        self.status = 'Wrong'
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.screen_enabled = False
        self.received_question = False
        self._dialog = None
        self.number_of_seconds = 5
        self.correct_option = None
        self.root = root
        self.all_users = None
        self.current_button = None
        self.contest_over = False
        self.final_result = None
        # Connect the User to the Server
        try:
            self.connect_user()
        except:
            print('[ERROR]: Could not connect to server')
            MDDialog(
                title='ERROR',
                text='Could Not Connect To Server!',
                buttons=[
                    MDFlatButton(
                        text='OK'
                    )
                ]
            ).open()

    def connect_user(self):
        self.client.connect((self.ip, self.PORT))
        self.client.send(self.username.encode(self.FORMAT))
        self.start_thread()

    def reset(self):
        self.current_button.background_color = (246, 0.31, 0.35, 0.45)

    def display_result_screen(self, *args):
        # Display the result screen after everybody has sent an option or timer is up
        # It displays after two seconds, called from the correct_opt_btn function
        self.reset()
        all_users = self.all_users[0]
        self.root.ids.correct_option.text = f'Correct Option: {self.correct_option}'
        self.root.ids.round_num.text = f'[size=40][color=#FBDE44FF]Round {self.all_users[-1]}[/color][/size]'
        for user, info in all_users.items():
            if not user.lower() == 'screen':
                if info[-1] == 'G':
                    self.root.ids.result_screen.add_widget(
                        ListItem(
                            text=f'[size=20][color=#000000]{user}: {info[1]} sec(s)[/color][/size]'.center(330),
                            bg_color=[0, 1, 0, 1]
                        )
                    )
                else:
                    self.root.ids.result_screen.add_widget(
                        ListItem(
                            text=f'[size=20][color=#000000]{user}: {info[1]} sec(s)[/color][/size]'.center(330),
                            bg_color=[1, 0, 0, 1]
                        )
                    )

        self.screen.current = 'result_sheet'

    def correct_opt_btn(self, option):
        # Change the color of the correct option to green
        # To indicate correct options
        dict_buttons = {'A': self.root.ids.button_a,
                        'B': self.root.ids.button_b,
                        'C': self.root.ids.button_c,
                        'D': self.root.ids.button_d}
        dict_buttons[option].background_color = (0, 1, 0, 1)
        self.current_button = dict_buttons[option]
        Clock.schedule_once(self.display_result_screen, 3)

    def send_msg(self, msg):
        # Handles all the sending of messages to the server
        self.client.send(msg.encode(self.FORMAT))
        self.all_users = pickle.loads(self.client.recv(self.BYTES))

        self.correct_option = self.all_users[1]
        self.correct_opt_btn(self.correct_option)

        print('[CONNECTED USERS]: ', self.all_users)

    def waiting_screen(self):
        self.screen.current = 'Home_Page'

        # Wait to receive final result from the user
        while True:
            self.final_result = pickle.loads(self.client.recv(self.BYTES))
            print('[FINAL RESULT]:', self.final_result)
            if self.final_result:
                break

        self.screen.current = 'final_result'

        for result in self.final_result:
            if result[0].lower() != 'screen':
                self.root.ids.final_result_sheet.add_widget(
                    ListItem(
                        text=f'[size=25][color=#FBDE44FF]{result[0]}: {result[1]}[/color][/size]'.center(340)
                    )
                )

    def receive_message(self, client):
        # Try to receive the number of seconds, or set it to a default value
        try:
            self.number_of_seconds = int(client.recv(self.BYTES).decode(self.FORMAT))
        except:
            # Will use default time (5 seconds)
            pass

        while True:
            # Receive the questions from the server
            question = pickle.loads(client.recv(self.BYTES))

            if not question:
                break
            else:
                ind = 65
                question = str(question).split(',')
                if not question[0].startswith('[Contest'):
                    for ques in range(1, len(question) - 1):
                        question[ques] = f'{chr(ind)}: {question[ques]}'
                        ind += 1

                    self.current_question = '\n'.join(question)
                    self.screen.current = 'Quiz_Page'
                    self.root.ids.result_screen.clear_widgets()

                    print(f'[QUESTION RECEIVED]: {self.current_question}')
                    self.received_question = True

                    options_state = client.recv(self.BYTES).decode(self.FORMAT)

                    if options_state == '[ACTIVATE SCREEN]':
                        self.screen_enabled = True

                    status = client.recv(self.BYTES).decode(self.FORMAT)
                    if status == 'R':
                        toast('Failed!', 3)
                    elif status == 'G':
                        toast('Correct!', 3)
                else:
                    self.waiting_screen()

        print('Closed..')
        client.close()

    def start_thread(self):
        t = threading.Thread(target=self.receive_message, args=(self.client,))
        t.daemon = True
        t.start()
