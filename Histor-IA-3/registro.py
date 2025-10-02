from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.metrics import dp
from kivy.properties import ObjectProperty
from kivy.app import App
from datetime import datetime
from database import db  # ✅ CAMBIO AQUÍ
from translations import TRANSLATIONS

class RegistroUsuario(Screen):
    nombre = ObjectProperty(None)
    contrasena = ObjectProperty(None)
    confirmar = ObjectProperty(None)

    def on_pre_enter(self):
        self.update_ui()

    def update_ui(self):
        lang = App.get_running_app().language.strip()
        t = TRANSLATIONS.get(lang, TRANSLATIONS['Español'])

        self.ids.register_title.text = t.get('register_title', 'Registro de Usuario')
        self.ids.username.text = t.get('username', 'Nombre de usuario')
        self.ids.password.text = t.get('password', 'Contraseña')
        self.ids.confirm_password.text = t.get('confirm_password', 'Confirmar Contraseña')
        self.ids.birth_date.text = t.get('birthday_date', 'Fecha de nacimiento')
        self.ids.register.text = t.get('register', 'Registrarse')
        self.ids.back_to_login_button.text = t.get('back_to_login_button', 'Volver al Inicio')

        self.ids.nombre.hint_text = t.get('username_hint', 'Introduce tu nombre de usuario')
        self.ids.contrasena.hint_text = t.get('password_hint', 'Introduce tu contraseña')
        self.ids.confirmar.hint_text = t.get('confirm_password_hint', 'Repite la contraseña')
        self.ids.fecha_nacimiento.hint_text = t.get('birth_date', 'Ejemplo: 05/12/1994')

    def registrar_usuario(self):
        nombre = self.ids.nombre.text.strip()
        contrasena = self.ids.contrasena.text
        confirmacion = self.ids.confirmar.text
        fecha_nac = self.ids.fecha_nacimiento.text.strip()

        if not all([nombre, contrasena, confirmacion, fecha_nac]):
            self.mostrar_popup("Error", "Todos los campos son obligatorios")
            return

        try:
           fecha_obj = datetime.strptime(fecha_nac, '%d/%m/%Y')
           fecha_formateada = fecha_obj.strftime('%Y-%m-%d')
        except ValueError:
           self.mostrar_popup("Error", "Formato de fecha incorrecto. Use dd/mm/aaaa")
           return

        if contrasena != confirmacion:
           self.mostrar_popup("Error", "Las contraseñas no coinciden")
           return

        if len(contrasena) < 6:
           self.mostrar_popup("Error", "La contraseña debe tener al menos 6 caracteres")
           return

        # Verificar si el usuario ya existe
        if db.recuperar_usuario(nombre):
           self.mostrar_popup("Error", "El nombre de usuario ya existe")
           return

        # Registrar el usuario con la fecha de nacimiento
        if db.registrar_usuario(nombre, contrasena, fecha_formateada):
           self.mostrar_popup_exito("Éxito", "Usuario registrado correctamente")
        else:
           self.mostrar_popup("Error", "No se pudo registrar el usuario")

    def volver_a_login(self):
        self.manager.current = 'login'
        self.limpiar_campos()

    def mostrar_popup(self, titulo, mensaje):
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        content.add_widget(Label(text=mensaje, color=(0, 0, 0, 1)))

        btn = Button(
            text='Cerrar',
            size_hint=(1, None),
            height=dp(40),
            background_color=(0.85, 0.90, 0.95, 0.5),
            color=(1, 1, 1, 1),
            bold=True,
            font_size='16sp'
        )
        popup = Popup(
            title=titulo,
            content=content,
            size_hint=(0.8, 0.4),
            title_color=(0, 0, 0, 1)
        )
        btn.bind(on_press=popup.dismiss)
        content.add_widget(btn)
        popup.open()

    def mostrar_popup_exito(self, titulo, mensaje):
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        content.add_widget(Label(text=mensaje, color=(0, 0, 0, 1)))

        btn_volver = Button(
            text='Volver al Inicio',
            size_hint=(1, None),
            height=dp(40),
            background_color=(0.85, 0.90, 0.95, 0.5),
            color=(1, 1, 1, 1),
            bold=True,
            font_size='16sp'
        )

        popup = Popup(
            title=titulo,
            content=content,
            size_hint=(0.8, 0.4),
            title_color=(0, 0, 0, 1)
        )

        btn_volver.bind(on_press=popup.dismiss)
        btn_volver.bind(on_press=lambda x: self.volver_a_login())
        content.add_widget(btn_volver)
        popup.open()

    def limpiar_campos(self):
        self.ids.nombre.text = ''
        self.ids.contrasena.text = ''
        self.ids.confirmar.text = ''
        self.ids.fecha_nacimiento.text = ''
