# Importaciones de Kivy necesarias para construir la app
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.properties import StringProperty
from kivy.core.audio import SoundLoader

# Importación de las pantallas personalizadas de la app
from new import NoticiasScreen
from menu import MenuScreen
from consulta import ConsultaScreen
from registro import RegistroUsuario
from olvido import OlvidoScreen
from reto import RetoDiarioScreen
from quiz import QuizScreen
from politica import PoliticaScreen
from idiomas import IdiomasScreen

# Traducciones y configuración
from translations import TRANSLATIONS
import json
import os
from database import db  

IDIOMA_PATH = "config_idioma.json"

def cargar_idioma_predeterminado():
    if os.path.exists(IDIOMA_PATH):
        with open(IDIOMA_PATH, "r") as f:
            data = json.load(f)
            return data.get("idioma", "Español")
    return "Español"

# Establece el tamaño de la ventana de la aplicación (útil para pruebas en PC)
Window.size = (360, 640)

# Carga los estilos definidos en archivos .kv
Builder.load_file("style/login.kv")
Builder.load_file("style/registro.kv")
Builder.load_file("style/olvido.kv")

class LoginScreen(Screen):
    def abrir_idiomas(self):
        self.manager.current = 'idiomas'

    def update_ui(self):
        lang = App.get_running_app().language
        t = TRANSLATIONS[lang]

        self.ids.label_welcome.text = t['welcome']
        self.ids.label_username.text = t['username']
        self.ids.label_password.text = t['password']
        self.ids.button_forgot.text = t['forgot']
        self.ids.button_login.text = t['login']
        self.ids.button_register.text = t['register']

    def login(self):
        usuario = self.ids.usuario_input.text.strip()
        clave = self.ids.clave_input.text

        if not usuario or not clave:
            self.mostrar_popup("Error", "Todos los campos son obligatorios")
            return

        user_data = db.validar_login(usuario, clave)
        if user_data:
             App.get_running_app().login_success(user_data['id'])
        else:
            self.mostrar_popup("Error", "Usuario o contraseña incorrectos")

    def go_to_registro(self):
        self.manager.current = 'registro'

    def go_to_olvido(self):
        self.manager.current = 'olvido'

    def mostrar_popup(self, titulo, mensaje):
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        content.add_widget(Label(text=mensaje))
        btn = Button(text="Cerrar", size_hint=(1, None), height=dp(40))
        popup = Popup(title=titulo, content=content, size_hint=(0.8, 0.4))
        btn.bind(on_press=popup.dismiss)
        content.add_widget(btn)
        popup.open()

class WindowManager(ScreenManager):
    pass

class LoginApp(App):
    language = StringProperty(cargar_idioma_predeterminado())
    font_family = StringProperty('Roboto')
    font_size_level = StringProperty('medium')
    user_id = None

    def build(self):
        sm = WindowManager()
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(RegistroUsuario(name='registro'))
        sm.add_widget(OlvidoScreen(name='olvido'))
        sm.add_widget(MenuScreen(name='menu'))
        sm.add_widget(ConsultaScreen(name='consulta'))
        sm.add_widget(NoticiasScreen(name='noticias'))
        sm.add_widget(RetoDiarioScreen(name='reto_diario'))
        sm.add_widget(QuizScreen(name='quiz'))
        sm.add_widget(IdiomasScreen(name='idiomas'))
        sm.add_widget(PoliticaScreen(name='politica'))

        sm.current = 'login'
        return sm

    def login_success(self, user_id):
        self.user_id = user_id
        screens_to_update = ['reto_diario', 'quiz', 'menu', 'consulta', 'opciones']
        for screen_name in screens_to_update:
            if self.root.has_screen(screen_name):
                screen = self.root.get_screen(screen_name)
                if hasattr(screen, 'user_id'):
                    screen.user_id = user_id
        self.root.current = 'menu'

    def on_stop(self):
        if self.user_id and self.root.has_screen('reto_diario'):
            reto_screen = self.root.get_screen('reto_diario')
            reto_screen.save_user_data()
        return True

    def set_language(self, lang):
        self.language = lang
        for screen in self.root.screens:
            if hasattr(screen, 'update_ui'):
                screen.update_ui()

    def set_font(self, font):
        self.font_family = font

    def set_font_size(self, level):
        self.font_size_level = level

    def get_font_size(self):
        return {
            'small': 14,
            'medium': 18,
            'large': 22
        }.get(self.font_size_level, 18)

    def translate(self, key):
        lang = self.language
        value = TRANSLATIONS.get(lang, {}).get(key)
        if value is None and '.' in key:
            section, subkey = key.split('.')
            return TRANSLATIONS.get(lang, {}).get(section, {}).get(subkey, key)
        return value or key

if __name__ == '__main__':
    LoginApp().run()
