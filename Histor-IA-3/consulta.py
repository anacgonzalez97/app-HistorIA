from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.checkbox import CheckBox
from kivy.uix.gridlayout import GridLayout
from kivy.uix.slider import Slider
from kivy.core.window import Window
from kivy.metrics import dp, sp
from kivy.utils import platform
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line
from kivy.properties import BooleanProperty, ListProperty, NumericProperty, StringProperty, ObjectProperty
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.core.image import Image as CoreImage
from kivy.app import App
from io import BytesIO
import requests
from openai import OpenAI

Builder.load_file("style/consulta.kv")

client = OpenAI(
    api_key="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",
    base_url="https://openrouter.ai/api/v1"
)

class BackgroundWidget(BoxLayout):
    background_texture = ObjectProperty(None)

class BookStyleLabel(Label):
    pass

class YearSlider(BoxLayout):
    min_year = NumericProperty(0)
    max_year = NumericProperty(2025)
    value = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ids.slider.bind(value=self.on_value_change)

    def on_value_change(self, instance, value):
        self.value = int(value)

    def increase_year(self):
        if self.value < self.max_year:
            self.value += 1
            self.ids.slider.value = self.value

    def decrease_year(self):
        if self.value > self.min_year:
            self.value -= 1
            self.ids.slider.value = self.value

class CategoryButton(BoxLayout):
    selected = BooleanProperty(False)
    bg_color = ListProperty([0.3, 0.3, 0.3, 1])
    normal_color = ListProperty([0.3, 0.3, 0.3, 1])
    selected_color = ListProperty([0.2, 0.5, 0.8, 1])
    
    def __init__(self, text='', normal_color=None, selected_color=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint = (None, None)
        self.spacing = dp(5)
        self.category_name = text

        self.label = Label(text=text, size_hint=(1, 1), halign='center', valign='middle', padding=(dp(10), dp(5)))
        self.label.texture_update()
        self.width = max(dp(80), min(dp(200), self.label.texture_size[0] + dp(30)))
        self.height = max(dp(30), min(dp(50), self.label.texture_size[1] + dp(10)))

        if normal_color:
            self.normal_color = normal_color
        if selected_color:
            self.selected_color = selected_color

        self.bg_color = self.normal_color

        self.checkbox = CheckBox(size=(0, 0), size_hint=(None, None), opacity=0)
        self.checkbox.active = False

        self.add_widget(self.label)
        self.add_widget(self.checkbox)

        self.bind(pos=self.update_rect, size=self.update_rect)
        self.bind(selected=self.update_style)
        self.update_style()

    def update_rect(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.bg_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])
            Color(1, 1, 1, 1)
            Line(rounded_rectangle=[self.pos[0], self.pos[1], self.size[0], self.size[1], dp(10)], width=dp(0.75))

    def update_style(self, *args):
        self.bg_color = self.selected_color if self.selected else self.normal_color
        self.label.color = [1, 1, 1, 1] if self.selected else [0.9, 0.9, 0.9, 1]
        self.update_rect()

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.toggle_selection()
            return True
        return super().on_touch_down(touch)

    def toggle_selection(self):
        self.selected = not self.selected
        self.checkbox.active = self.selected

class ConsultaScreen(Screen):
    background_source = StringProperty('')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build()

    def build(self):
        Window.size = (dp(360), dp(640))
        self.background_widget = BackgroundWidget(orientation='vertical')
        self.main_layout = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(15))
        self.set_background('imagen/fondo.png')
        self.background_widget.add_widget(self.main_layout)
        self.add_widget(self.background_widget)
        
        t = App.get_running_app().translate 

        self.title_label = Label(text=t('consulta_title'), size_hint=(1, None), height=dp(50), font_size='25sp', bold=True, color=(1, 1, 1, 1))
        self.main_layout.add_widget(self.title_label)
        self.year_slider = YearSlider()
        self.main_layout.add_widget(self.year_slider)

        self.select_label = Label(text=t('select_categories'), size_hint=(1, None), height=dp(30), font_size='16sp', bold=True, color=(1, 1, 1, 1))
        self.main_layout.add_widget(self.select_label)
        self.category_layout = GridLayout(cols=3, rows=2, spacing=dp(5), size_hint=(1, None), height=dp(120))        
        self.categories = [
            {"key": "history", "normal": [0.3, 0.3, 0.3, 0.5], "selected": [0.698, 0.651, 0.161, 0.5]},
            {"key": "sports", "normal": [0.3, 0.3, 0.3, 0.5], "selected": [0.918, 0.447, 0.055, 0.5]},
            {"key": "science", "normal": [0.3, 0.3, 0.3, 0.5], "selected": [0.11, 0.533, 0.071, 0.5]},
            {"key": "geography", "normal": [0.3, 0.3, 0.3, 0.5], "selected": [0.161, 0.490, 0.698, 0.5]},
            {"key": "art", "normal": [0.3, 0.3, 0.3, 0.5], "selected": [0.753, 0.188, 0.086, 0.5]},
            {"key": "entertainment", "normal": [0.3, 0.3, 0.3, 0.5], "selected": [0.796, 0.278, 0.843, 0.5]}
        ]
        self.selected_categories = []
        self.category_buttons = {}
        for cat in self.categories:
            label_text = t('categories')[cat['key']]
            btn = CategoryButton(text=label_text, normal_color=cat['normal'], selected_color=cat['selected'])
            btn.checkbox.bind(active=lambda inst, val, key=cat['key']: self.toggle_category(key, val))
            self.category_buttons[cat['key']] = btn
            self.category_layout.add_widget(btn)

        self.main_layout.add_widget(self.category_layout)

        self.consult_btn = Button(text='Consultar', size_hint=(1, None), height=dp(50), background_color=(0.85, 0.90, 0.95, 1), color=(1, 1, 1, 1), bold=True)
        self.consult_btn.bind(on_press=self.query_year)
        self.main_layout.add_widget(self.consult_btn)

        self.results_label = Label(text=t('results:'), size_hint=(1, None), height=dp(30), font_size='16sp', bold=True, color=(1, 1, 1, 1))
        self.main_layout.add_widget(self.results_label)
        self.scroll = ScrollView(size_hint=(1, 1))
        self.results_container = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(5), padding=[dp(15), dp(15), dp(15), dp(5)])
        self.results_container.bind(minimum_height=self.results_container.setter('height'))
        with self.results_container.canvas.before:
            Color(0.98, 0.98, 0.96, 0.85)
            self.bg_rect = Rectangle(pos=self.results_container.pos, size=self.results_container.size)
        self.results_container.bind(pos=self.update_bg_rect, size=self.update_bg_rect)
        self.book_result = BookStyleLabel(text="[b][size=18]Bienvenido[/size][/b]\n\n[size=16]Aquí aparecerán los resultados de tus consultas históricas.[/size]")
        self.results_container.add_widget(self.book_result)
        self.scroll.add_widget(self.results_container)
        self.main_layout.add_widget(self.scroll)

        Clock.schedule_once(self.adjust_layout, 0.1)

        self.btn_volver = Button(
            background_normal='imagen/flecha.png',
            size_hint=(None, None),
            size=(dp(45), dp(45)),
            pos_hint={'x': 0.06, 'top': 0.975},
            border=(0, 0, 0, 0)
        )
        self.btn_volver.bind(on_press=self.volver_a_menu)
        self.add_widget(self.btn_volver)
        
    def volver_a_menu(self, instance):
        self.manager.current = 'menu'

    def set_background(self, source):
        try:
            if source.startswith('http'):
                resp = requests.get(source)
                buf = BytesIO(resp.content)
                tex = CoreImage(buf, ext='png').texture
            else:
                tex = CoreImage(source).texture
            self.background_widget.background_texture = tex
            self.background_source = source
        except Exception as e:
            print(f"Error cargando fondo: {e}")

    def update_bg_rect(self, *a):
        self.bg_rect.pos = self.results_container.pos
        self.bg_rect.size = self.results_container.size

    def adjust_layout(self, dt):
       # Fijamos 3 columnas y 2 filas
       self.category_layout.cols = 3
       self.category_layout.rows = 2

       # Definimos el tamaño de los botones
       btn_height = dp(50)  # Altura suficiente para el texto
       btn_width = dp(110)  # Ancho para que quepa el texto sin cortarse

       # Calculamos el espacio total necesario
       total_width = (btn_width * 3) + (dp(5) * 2)  # 3 botones + 2 espacios
       total_height = (btn_height * 2) + dp(5)      # 2 filas + 1 espacio

       # Ajustamos el tamaño del GridLayout
       self.category_layout.size_hint = (None, None)
       self.category_layout.width = total_width
       self.category_layout.height = total_height
       self.category_layout.pos_hint = {'center_x': 0.5}  # Centrar horizontalmente

       # Aplicamos el tamaño a cada botón
       for btn in self.category_buttons.values():
           btn.size_hint = (None, None)
           btn.width = btn_width
           btn.height = btn_height

    def toggle_category(self, cat, val):
        if val and cat not in self.selected_categories:
            self.selected_categories.append(cat)
        if not val and cat in self.selected_categories:
            self.selected_categories.remove(cat)

    def clean_api_text(self, text):
        text = text.replace('*', '').replace('_', '')
        lines = text.split('\n')
        out = []
        for l in lines:
            if l.strip().endswith(':'):
                out.append(f"[b][size=18]{l.strip()}[/size][/b]")
            elif l.strip():
                out.append(f"[size=16]{l.strip()}[/size]")
        return '\n\n'.join(out)

    def query_year(self, inst):
        year = int(self.year_slider.value)
        t = App.get_running_app().translate
        if not self.selected_categories:
            self.book_result.text = f"[b][size=18]{t('warning')}[/size][/b]\n\n[size=16]{t('warning_select')}[/size]"
            return

        cats = ', '.join(self.selected_categories)
        self.book_result.text = f"[b][size=18]{t('searching')}[/size][/b]\n\n[size=16]{t('searching_for').format(cats=cats, year=year)}[/size]"

        try:
            chat = client.chat.completions.create(
                model="deepseek/deepseek-r1:free",
                messages=[{"role": "user", "content": f"Describe en español qué pasó en {year} relacionado con {','.join(self.selected_categories).lower()}."}]
            )
            cleaned = self.clean_api_text(chat.choices[0].message.content)
            self.book_result.text = cleaned
        except Exception as e:
            self.book_result.text = f"[b][size=18]{t('error')}[/size][/b]\n\n[size=16]{e}[/size]"


    def update_ui(self):
        t = App.get_running_app().translate
        self.consult_btn.text = t('consult')
        self.title_label.text = t('consulta_title')
        self.select_label.text = t('select_categories')
        self.results_label.text = t('results:') 
        self.book_result.text = f"[b][size=18]{t('welcome_text')}[/size][/b]\n\n[size=16]{t('welcome_subtext')}[/size]"

        for key, btn in self.category_buttons.items():
            btn.label.text = t('categories')[key]