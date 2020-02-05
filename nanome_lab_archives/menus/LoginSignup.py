import os
import nanome

from ..LAClient import LAClient

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
LOGIN_MENU = os.path.join(DIR_PATH, 'json', 'login.json')

class LoginSignup:
    def __init__(self, plugin, close_callback=None):
        self.__plugin = plugin
        self.__menu = nanome.ui.Menu.io.from_json(LOGIN_MENU)
        self.__menu.register_closed_callback(close_callback if close_callback is not None else self.reopen_menu)

        self.__login_form = self.__menu.root.find_node('Login Form')
        self.__login_form_children = {
            'login': self.__login_form.find_node('login').find_node('input'),
            'password': self.__login_form.find_node('password').find_node('input')
        }

        self.__login_form_children['login'].get_content().input_text = 'max@nanome.ai'
        self.__login_form_children['password'].get_content().input_text = '12341234'

        self.__signup_form = self.__menu.root.find_node('Signup Form')
        self.__signup_form_children = {
            'email': self.__signup_form.find_node('email').find_node('input'),
            'login': self.__signup_form.find_node('login').find_node('input'),
            'password': self.__signup_form.find_node('password').find_node('input'),
            'fullname': self.__signup_form.find_node('fullname').find_node('input'),
            'notebook_name': self.__signup_form.find_node('notebook_name').find_node('input')
        }

        self.__state  = 'login'
        self.__btn_main = self.__menu.root.find_node('Button')
        self.__btn_main.get_content().register_pressed_callback(self.login_or_signup)
        self.__login_callback = None
        self.__signup_callback = None

        state_switch = self.__menu.root.find_node('State Switch')
        self.__switch_nodes = {'label': state_switch.find_node('label'), 'button': state_switch.find_node('button')}
        self.__switch_nodes['button'].get_content().register_pressed_callback(self.toggle_state)

    def open_menu(self):
        self.__menu.enabled = True
        self.__plugin.menu = self.__menu
        self.__plugin.update_menu(self.__menu)

    def reopen_menu(self, menu):
        self.__menu.enabled = True
        self.__plugin.update_menu(self.__menu)

    def register_login_callback(self, callback):
        self.__login_callback = callback

    def register_signup_callback(self, callback):
        self.__signup_callback = callback

    def login_or_signup(self, button):
        if self.__state == 'login':
            login = self.__login_form_children['login'].get_content().input_text
            password = self.__login_form_children['password'].get_content().input_text
            self.login(login, password)
        elif self.__state == 'signup':
            email = self.__signup_form_children['email'].get_content().input_text
            login = self.__signup_form_children['login'].get_content().input_text
            password = self.__signup_form_children['password'].get_content().input_text
            fullname = self.__signup_form_children['fullname'].get_content().input_text
            notebook_name = self.__signup_form_children['notebook_name'].get_content().input_text
            self.signup(email, login, password, fullname, notebook_name)

    def login(self, login, password):
        (err, res) = LAClient.Users.user_access_info(login, password)
        if err is None:
            self.__plugin.send_notification(nanome.util.enums.NotificationTypes.success, "Successfully Logged In")
        else:
            self.__plugin.send_notification(nanome.util.enums.NotificationTypes.error, "Error Logging In")

        if self.__login_callback is not None:
                self.__login_callback(err, res)

    def signup(self, email, login=None, password=None, fullname=None, notebook_name=None):
        (err, res) = LAClient.instance.users.create_user_account(email, login or None, password or None, fullname or None, notebook_name or None)
        if err is None:
            self.__plugin.send_notification(nanome.util.enums.NotificationTypes.success, "Successfully Signed Up! Please check your email.")
            return True
        else:
            # TODO: check whether this email already has an account
            # email_already_exists = res['already_exists']
            self.__plugin.send_notification(nanome.util.enums.NotificationTypes.error, "Error Signing Up")
            return False

        if self.__signup_callback is not None:
                self.__signup_callback(err, res)

    def toggle_state(self, button):
        if self.__state == 'login':
            self.switch_to_signup()
        elif self.__state == 'signup':
            self.switch_to_login()

    def switch_to_login(self):
        self.__state = 'login'
        self.__btn_main.get_content().set_all_text("Log in")

        self.__menu.title = 'Lab Archives - Welcome!'
        self.__login_form.enabled = True
        self.__signup_form.enabled = False

        self.__switch_nodes['label'].get_content().text_value = "Don't have an account?"
        self.__switch_nodes['button'].get_content().set_all_text("Sign up")

        self.__plugin.update_menu(self.__menu)

    def switch_to_signup(self):
        self.__state = 'signup'
        self.__btn_main.get_content().set_all_text("Sign up")

        self.__menu.title = 'Lab Archives - Sign Up'
        self.__login_form.enabled = False
        self.__signup_form.enabled = True

        self.__switch_nodes['label'].get_content().text_value = "Already have an account?"
        self.__switch_nodes['button'].get_content().set_all_text("Log in")

        self.__plugin.update_menu(self.__menu)