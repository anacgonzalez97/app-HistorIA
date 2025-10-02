from kivy.uix.screenmanager import Screen
from kivy.uix.image import Image
from kivy.lang import Builder
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
import bcrypt
from database import db
from datetime import datetime, date
from kivy.app import App

Builder.load_file('style/olvido.kv')

class OlvidoScreen(Screen):
    
    def __init__(self, **kwargs):
        super(OlvidoScreen, self).__init__(**kwargs)
        with self.canvas.before:
            self.bg = Image(source='imagen/fondo.png', fit_mode='fill')
            self.bind(size=self._update_bg, pos=self._update_bg)

    def _update_bg(self, instance, value):
        self.bg.size = instance.size
        self.bg.pos = instance.pos

    def formatear_fecha(self, textinput):
        texto = textinput.text.replace("/", "")
        if len(texto) == 2 or len(texto) == 4:
            textinput.text = texto + "/"

    def show_message(self, title, message):
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        content.add_widget(Label(text=message))
        btn = Button(text='Cerrar', size_hint=(1, None), height=40)
        popup = Popup(title=title, content=content, size_hint=(0.8, 0.4))
        btn.bind(on_press=popup.dismiss)
        content.add_widget(btn)
        popup.open()

    def recover_password(self):
        username = self.ids.username.text.strip()
        new_password = self.ids.new_password_input.text.strip()
        confirm_password = self.ids.confirm_password_input.text.strip()
        fecha_input = self.ids.birthday_date_hint.text.strip()

        if not all([username, new_password, confirm_password, fecha_input]):
            self.show_message("Error", "Todos los campos son obligatorios")
            return

        if new_password != confirm_password:
            self.show_message("Error", "Las contraseñas no coinciden")
            return

        if len(new_password) < 6:
            self.show_message("Error", "La contraseña debe tener al menos 6 caracteres")
            return

        try:
            fecha_obj = datetime.strptime(fecha_input, '%d/%m/%Y').date()
        except ValueError:
            self.show_message("Error", "Formato incorrecto. Use dd/mm/aaaa")
            return

        user_data = db.recuperar_usuario(username)
        if not user_data:
            self.show_message("Error", "Usuario no encontrado")
            return

        stored_date_str = user_data.get('fecha', '')
        try:
            stored_date = datetime.strptime(stored_date_str[:10], '%Y-%m-%d').date()
        except ValueError:
            self.show_message("Error", "Error en la fecha almacenada")
            return

        if stored_date != fecha_obj:
            self.show_message("Error", "La fecha de nacimiento no coincide")
            return

        if db.actualizar_clave(username, new_password):
            self.show_message("Éxito", "Contraseña actualizada correctamente")
            self.go_to_login()
        else:
            self.show_message("Error", "No se pudo actualizar la contraseña")

    def go_to_login(self, instance=None):
        self.manager.current = 'login'
        self.ids.username.text = ""
        self.ids.new_password_input.text = ""
        self.ids.confirm_password_input.text = ""
        self.ids.birthday_date_hint.text = ""

    def update_ui(self):
        t = App.get_running_app().translate

        self.ids.forgot_password_title.text = t('forgot_password_title')
        self.ids.username_hint.text = t('username')
        self.ids.username.hint_text = t('username_hint')
        self.ids.birthday_date.text = t('birthday_date')
        self.ids.birthday_date_hint.hint_text = t('birthday_date_hint')
        self.ids.new_password.text = t('new_password')
        self.ids.new_password_input.hint_text = t('new_password_input')
        self.ids.confirm_password.text = t('confirm_password')
        self.ids.confirm_password_input.hint_text = t('confirm_password_input')
        self.ids.update_password_button.text = t('update_password_button')
        self.ids.back_to_login_button.text = t('back_to_login_button')