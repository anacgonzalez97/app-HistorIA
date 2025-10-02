from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle
from kivy.properties import StringProperty, ObjectProperty
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.core.image import Image as CoreImage
from kivy.uix.screenmanager import Screen
from io import BytesIO
import requests
from threading import Thread
from datetime import datetime
import random
from kivy.app import App
import os
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image

from translations import TRANSLATIONS

# Cargar estilos desde el archivo KV si lo tienes
kv_path = os.path.join(os.path.dirname(__file__), 'style', 'new.kv')
if os.path.exists(kv_path):
    Builder.load_file(kv_path)

class BackgroundWidget(BoxLayout):
    background_texture = ObjectProperty(None)

class BookStyleLabel(Label):
    pass

class NoticiaCard(BoxLayout):
    pass

class NoticiasScreen(Screen):
    background_source = StringProperty('')
    API_KEY = "pub_82940648238835a178f724b731697db8310ce"
    ULTIMA_ACTUALIZACION = ""
    fecha_actual = StringProperty('')
    language = StringProperty('Español')

    def __init__(self, **kwargs):
        super(NoticiasScreen, self).__init__(**kwargs)
        Window.bind(on_resize=self.on_window_resize)
        self.fecha_actual = datetime.now().strftime("%d/%m/%Y")
        self.language = App.get_running_app().language
        self.bind(language=self.update_ui)
        
        # Configurar el layout principal
        self.background_widget = FloatLayout()
        self.background_image = Image(source="imagen/fondo.png", allow_stretch=True, keep_ratio=False)
        self.background_widget.add_widget(self.background_image)
        
        self.main_layout = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(15))
        self.background_widget.add_widget(self.main_layout)
        self.add_widget(self.background_widget)

        # Título sin fecha
        self.title_label = Label(
            text=self.get_title_text(),
            size_hint=(1, None),
            height=dp(50),
            font_size='22sp',
            bold=True,
            color=(1, 1, 1, 1))
        self.main_layout.add_widget(self.title_label)

        # Área de scroll para noticias
        self.scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        self.results_container = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=dp(10),
            padding=[dp(10), dp(10), dp(10), dp(5)]
        )
        self.results_container.bind(minimum_height=self.results_container.setter('height'))
        self.scroll.add_widget(self.results_container)
        self.main_layout.add_widget(self.scroll)

        # Spinner de carga
        self.spinner = Label(
            text=self.get_translation('loading'),
            font_size='18sp',
            size_hint=(1, None),
            height=dp(50),
            color=(0, 0, 0, 1)
        )
        self.spinner.opacity = 0
        self.main_layout.add_widget(self.spinner)

        # Mostrar mensaje inicial
        self.mostrar_mensaje_inicial()

        # Botón de flecha (igual que en reto)
        self.back_btn = Button(
            background_normal='imagen/flecha.png',
            size_hint=(None, None),
            size=(dp(45), dp(45)),
            pos_hint={'x': 0.04, 'top': 0.96},
            border=(0, 0, 0, 0)
        )
        self.back_btn.bind(on_release=self.volver_al_menu)
        self.background_widget.add_widget(self.back_btn)

        # Llamar a obtener noticias en segundo plano
        Thread(target=self.obtener_noticias).start()

    def get_translation(self, key):
        """Obtiene la traducción según el idioma actual"""
        app = App.get_running_app()
        if hasattr(app, 'translate'):
            return app.translate(key)
        return TRANSLATIONS.get(self.language, {}).get(key, key)

    def get_title_text(self):
        """Devuelve solo el título sin fecha"""
        return self.get_translation('news_title')

    def get_back_button_text(self):
        """Devuelve el texto del botón de volver traducido"""
        return f"← {self.get_translation('back_to_menu')}"

    def mostrar_mensaje_inicial(self):
        mensajes = self.get_translation('loading_messages')
        self.results_container.clear_widgets()
        label = BookStyleLabel()
        label.text = f"[b][size=18]{self.get_translation('news_intro_title')}[/size][/b]\n\n[size=16]{random.choice(mensajes)}[/size]"
        self.results_container.add_widget(label)

    def set_background(self, source):
        try:
            if source.startswith('http'):
                response = requests.get(source, timeout=10)
                image_data = BytesIO(response.content)
                texture = CoreImage(image_data, ext='png').texture
            else:
                texture = CoreImage(source).texture
            self.background_image.texture = texture
            self.background_source = source
        except Exception as e:
            print(f"Error al cargar el fondo: {e}")

    def on_enter(self):
        """Se ejecuta al mostrar la pantalla"""
        self.language = App.get_running_app().language
        self.mostrar_mensaje_inicial()
        Thread(target=self.obtener_noticias).start()

    def obtener_noticias(self):
        try:
            lang = 'es' if self.language == 'Español' else 'en'
            url = f"https://newsdata.io/api/1/news?apikey={self.API_KEY}&language={lang}&category=top"
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                resultados = data.get("results", [])
                
                if resultados:
                    self.ULTIMA_ACTUALIZACION = datetime.now().strftime("%H:%M:%S")
                    Clock.schedule_once(lambda dt: self.mostrar_noticias(resultados), 0)
                else:
                    mensaje = f"[b][size=18]{self.get_translation('error')}[/size][/b]\n\n[size=16]{self.get_translation('no_news')}[/size]"
                    Clock.schedule_once(lambda dt: self.mostrar_error(mensaje), 0)
            else:
                mensaje = f"[b][size=18]{self.get_translation('error')}[/size][/b]\n\n[size=16]{self.get_translation('server_error')} {response.status_code}[/size]"
                Clock.schedule_once(lambda dt: self.mostrar_error(mensaje), 0)

        except requests.exceptions.Timeout:
            mensaje = f"[b][size=18]{self.get_translation('error')}[/size][/b]\n\n[size=16]{self.get_translation('timeout_error')}[/size]"
            Clock.schedule_once(lambda dt: self.mostrar_error(mensaje), 0)

        except Exception as e:
            mensaje = f"[b][size=18]{self.get_translation('error')}[/size][/b]\n\n[size=16]{str(e)}[/size]"
            Clock.schedule_once(lambda dt: self.mostrar_error(mensaje), 0)

    def mostrar_noticias(self, noticias):
        self.results_container.clear_widgets()

        for noticia in noticias[:3]:
            card = NoticiaCard()
            label = BookStyleLabel()
            label.text = self.formatear_noticia(noticia)
            card.add_widget(label)
            self.results_container.add_widget(card)

        if self.ULTIMA_ACTUALIZACION:
            actualizacion_label = Label(
                text=f"{self.get_translation('last_update')}: {self.ULTIMA_ACTUALIZACION}",
                size_hint=(1, None),
                height=dp(30),
                font_size='12sp',
                color=(0.5, 0.5, 0.5, 1))
            self.results_container.add_widget(actualizacion_label)

        self.finalizar_carga()

    def formatear_noticia(self, noticia):
        try:
            titulo = noticia.get("title", self.get_translation('no_title'))
            descripcion = noticia.get("description", "")
            contenido = noticia.get("content", "")
            fuente = noticia.get("source_id", self.get_translation('unknown_source'))
            fecha = noticia.get("pubDate", "")
            
            if fecha:
                try:
                    fecha_obj = datetime.strptime(fecha, "%Y-%m-%d %H:%M:%S")
                    fecha_formateada = fecha_obj.strftime("%H:%M - %d/%m/%Y")
                except:
                    fecha_formateada = fecha

            texto_noticia = f"""
[b][size=20]{titulo}[/size][/b]
[size=16][i]{fuente} - {fecha_formateada if fecha else ''}[/i][/size]

[size=16]{descripcion}[/size]

[size=16]{contenido}[/size]
"""
            return texto_noticia.strip()
        except Exception as e:
            print(f"Error al formatear noticia: {e}")
            return f"[b][size=18]{self.get_translation('error')}[/size][/b]\n\n[size=16]{self.get_translation('format_error')}[/size]"

    def mostrar_error(self, mensaje):
        self.results_container.clear_widgets()
        error_label = BookStyleLabel()
        error_label.text = mensaje
        self.results_container.add_widget(error_label)
        self.finalizar_carga()

    def finalizar_carga(self):
        self.spinner.opacity = 0
        self.scroll.scroll_y = 1.0

    def update_ui(self, *args):
        """Actualiza la interfaz cuando cambia el idioma"""
        self.language = App.get_running_app().language
        if hasattr(self, 'title_label'):
            self.title_label.text = self.get_title_text()
        if hasattr(self, 'spinner'):
            self.spinner.text = self.get_translation('loading')

    def volver_al_menu(self, instance):
        App.get_running_app().root.current = 'menu'

    def on_window_resize(self, instance, width, height):
        Clock.schedule_once(self.adjust_layout, 0.1)

    def adjust_layout(self, dt):
        pass