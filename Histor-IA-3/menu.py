from kivy.metrics import dp
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import StringProperty, ListProperty, NumericProperty, ObjectProperty
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.lang import Builder
import os
from kivy.core.window import Window
from quiz import QuizScreen
from reto import RetoDiarioScreen
import webbrowser
from politica import PoliticaScreen

from translations import TRANSLATIONS

# Tamaño por defecto
Window.size = (360, 640)

# Función para obtener la ruta de la imagen
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def imagen(path):
    full_path = os.path.join(BASE_DIR, path)
    return full_path if os.path.exists(full_path) else ''

Builder.load_string('''
<MenuButton>:
    background_normal: ''
    background_down: ''
    background_color: 0, 0, 0, 0
    canvas.before:
        Color:
            rgba: self.border_color
        Line:
            rounded_rectangle: [self.x, self.y, self.width, self.height, self.border_radius]
            width: self.border_width
        Color:
            rgba: self.image_opacity if self.source else [0, 0, 0, 0]
        RoundedRectangle:
            source: self.source
            pos: self.pos
            size: self.size
            radius: [self.border_radius,]
            
<CustomButton>:
    background_normal: ''
    background_down: ''
    background_color: 0, 0, 0, 0
    canvas.before:
        Color:
            rgba: self.border_color
        Line:
            rounded_rectangle: [self.x, self.y, self.width, self.height, self.border_radius]
            width: self.border_width
''')

class MenuButton(Button):
    source = StringProperty('')
    border_color = ListProperty([0.2, 0.6, 0.9, 1])
    border_radius = NumericProperty(dp(15))
    border_width = NumericProperty(dp(1.5))
    image_opacity = ListProperty([1, 1, 1, 1])  # RGBA para controlar opacidad
    text_label = ObjectProperty(None)
    
    def __init__(self, **kwargs):
        kwargs['text'] = ''
        super().__init__(**kwargs)
        
        self.text_label = Label(
            text=kwargs.get('text', ''),
            color=[1, 1, 1, 1],
            font_size=dp(16),
            bold=True,
            size_hint=(1, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        self.add_widget(self.text_label)
        
        self.bind(
            pos=self._update_rect, 
            size=self._update_rect, 
            source=self._update_rect,
            border_radius=self._update_rect,
            image_opacity=self._update_rect
        )

    def _update_rect(self, *args):
        if self.text_label:
            self.text_label.pos = self.pos
            self.text_label.size = self.size

class CustomButton(Button):
    source = StringProperty('')
    border_color = ListProperty([0.2, 0.6, 0.9, 1])
    border_radius = NumericProperty(dp(15))
    border_width = NumericProperty(dp(1.5))
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            self._bg_color = Color(1, 1, 1, 1)
            self._bg_rect = RoundedRectangle(
                source=self.source, 
                pos=self.pos, 
                size=self.size,
                radius=[self.border_radius,]
            )
        self.bind(
            pos=self._update_rect, 
            size=self._update_rect, 
            source=self._update_rect,
            border_radius=self._update_rect
        )

    def _update_rect(self, *args):
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size
        self._bg_rect.source = self.source
        self._bg_rect.radius = [self.border_radius,]

class MenuScreen(Screen):
    def __init__(self, **kwargs):
        super(MenuScreen, self).__init__(**kwargs)
        self.add_widget(MenuRootLayout())

    def update_ui(self):
        if hasattr(self, 'children'):
            for child in self.children:
                if hasattr(child, 'update_texts'):
                    child.update_texts()

class MenuRootLayout(FloatLayout):
    def __init__(self, **kwargs):
        super(MenuRootLayout, self).__init__(**kwargs)
        
        self.bg_source = imagen('imagen/fondo.png')
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self.bg_rect = Rectangle(source=self.bg_source, pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)
        
        # Contenedor principal para los 4 botones
        self.main_container = FloatLayout()
        self.add_widget(self.main_container)
        
        # Contenedor centrado para los botones
        self.center_container = BoxLayout(
            orientation='vertical',
            size_hint=(None, None),
            size=(dp(200), dp(400)),
            spacing=dp(20),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        self.main_container.add_widget(self.center_container)
        
        # Crear los 4 botones principales con texto y opacidad personalizable
        self.buttons_data = [
        {
           'source': 'imagen/busqueda.png', 
           'color': [0, 0, 0, 0],
           'action': self.go_to_consulta,
           'text_key': 'BÚSQUEDA',
           'text_color': [1, 1, 1, 1],
           'text_size': dp(22),
           'opacity': [1, 1, 1, 0.5],
        },
        {
           'source': 'imagen/quiz.png', 
           'color': [0, 0, 0, 0],
           'action': self.go_to_quiz,
           'text_key': 'QUIZ',
           'text_color': [1, 1, 1, 1],
           'text_size': dp(22),
           'opacity': [1, 1, 1, 0.5],
        },
        {
           'source': 'imagen/noticia.png', 
           'color': [0, 0, 0, 0],
           'action': self.go_to_noticias,
           'text_key': 'NOTICIAS',
           'text_color': [1, 1, 1, 1],
           'text_size': dp(22),
           'opacity': [1, 1, 1, 0.5],
       },
       {
           'source': 'imagen/reto.png', 
           'color': [0, 0, 0, 0],
           'action': self.go_to_reto_diario,
           'text_key': 'RETO',
           'text_color': [1, 1, 1, 1],
           'text_size': dp(22),
           'opacity': [1, 1, 1, 0.5],
        }
      ]

        for btn in self.buttons_data:
            button = MenuButton(
                source=imagen(btn['source']),
                size_hint=(None, None),
                size=(dp(180), dp(80)),
                border_color=btn['color'],
                border_radius=dp(15),
                border_width=dp(1.5),
                image_opacity=btn['opacity']
            )
            button.text_label.text = App.get_running_app().translate(btn['text_key']).capitalize()
            button.text_label.color = btn['text_color']
            button.text_label.font_size = btn['text_size']
            button.bind(on_press=btn['action'])
            self.center_container.add_widget(button)

        # Botón superior izquierdo
        self.top_left_btn = Button(
            size_hint=(None, None),
            size=(dp(45), dp(45)),
            pos_hint={'x': 0.04, 'top': 0.96},
            border=(0, 0, 0, 0),
            background_normal=imagen('imagen/cerrar.png'),
            background_down=imagen('imagen/cerrar.png'),
            background_color=(1, 1, 1, 1),
            on_release=self.btn_logout
        )
        self.add_widget(self.top_left_btn)

        # Botón superior derecho
        self.top_right_btn = Button(
            size_hint=(None, None),
            size=(dp(45), dp(45)),
            pos_hint={'right': 0.96, 'top': 0.96},
            border=(0, 0, 0, 0),
            background_normal=imagen('imagen/formulario.png'),
            background_down=imagen('imagen/formulario.png'),
            background_color=(1, 1, 1, 1),
            on_release=self.open_formulario_web
        )
        self.add_widget(self.top_right_btn)

        # Botón inferior izquierdo
        self.bottom_left_btn = Button(
            size_hint=(None, None),
            size=(dp(45), dp(45)),
            pos_hint={'x': 0.04, 'y': 0.04},
            border=(0, 0, 0, 0),
            background_normal=imagen('imagen/politica.png'),
            background_down=imagen('imagen/politica.png'),
            background_color=(1, 1, 1, 1),
            on_release=self.go_to_politica
        )
        self.add_widget(self.bottom_left_btn)

        Window.bind(on_resize=self._on_window_resize)

    def _on_window_resize(self, window, width, height):
        self._update_bg()
        self.center_container.pos_hint = {'center_x': 0.5, 'center_y': 0.5}

    def _update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def update_texts(self):
        for i, btn in enumerate(self.center_container.children[::-1]):
            btn.text_label.text = App.get_running_app().translate(self.buttons_data[i]['text_key'])

    def btn_logout(self, instance):
        App.get_running_app().root.current = 'login'

    def go_to_politica(self, instance):
        app = App.get_running_app()
        if 'politica' not in app.root.screen_names:
            app.root.add_widget(PoliticaScreen(name='politica'))
        app.root.current = 'politica'

    def go_to_consulta(self, instance):
        App.get_running_app().root.current = 'consulta'

    def go_to_noticias(self, instance):
        App.get_running_app().root.current = 'noticias'

    def go_to_quiz(self, instance):
        app = App.get_running_app()
        if 'quiz' not in app.root.screen_names:
            app.root.add_widget(QuizScreen(name='quiz'))
        app.root.current = 'quiz'

    def go_to_reto_diario(self, instance):
        app = App.get_running_app()
        if 'reto_diario' not in app.root.screen_names:
            app.root.add_widget(RetoDiarioScreen(name='reto_diario'))
        app.root.current = 'reto_diario'

    def open_formulario_web(self, instance):
        # URL de prueba (cámbiala por la que necesites)
        formulario_url = "https://docs.google.com/forms/d/e/1FAIpQLSe4vEw-Pg4b6JI_HEAUgLABePhOHXHPEK1poL30iGWB9BNCqQ/viewform?usp=sharing&ouid=101423406312035528395"
        try:
            webbrowser.open(formulario_url)
        except Exception as e:
            print(f"Error al abrir el formulario: {e}")