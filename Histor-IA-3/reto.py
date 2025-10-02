from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.properties import NumericProperty, ObjectProperty, StringProperty
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.popup import Popup
from openai import OpenAI
from datetime import datetime, date, timedelta
import json
from database import db

from translations import TRANSLATIONS

deepseek_client = OpenAI(
    api_key="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",
    base_url="https://openrouter.ai/api/v1"
)

class RetoDiarioScreen(Screen):
    current_question = ObjectProperty(None)
    user_answer = NumericProperty(-1)
    correct_answer = NumericProperty(-1)
    streak = NumericProperty(0)
    last_played_date = ObjectProperty(None, allownone=True)
    question_generated = False
    user_id = NumericProperty(None)
    language = StringProperty('Español')

    def __init__(self, user_id=None, **kwargs):
        super(RetoDiarioScreen, self).__init__(**kwargs)
        self.user_id = user_id
        self.current_question = None
        self.question_generated = False
        self.reto_data = {}
        self.language = App.get_running_app().language

        # Layout con fondo
        fondo_layout = FloatLayout()

        # Fondo
        fondo = Image(source="imagen/fondo.png", allow_stretch=True, keep_ratio=False,
                      size_hint=(1, 1), pos_hint={"x": 0, "y": 0})
        fondo_layout.add_widget(fondo)

        # Layout principal sobre el fondo
        self.main_layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        fondo_layout.add_widget(self.main_layout)
        
        # Botón de ranking
        self.ranking_btn = Button(
            background_normal='imagen/ranking.png',
            size_hint=(None, None),
            size=(dp(45), dp(45)),
            pos_hint={'right': 0.96, 'top': 0.96},
            border=(0, 0, 0, 0)
        )
        self.ranking_btn.bind(on_release=self.show_ranking_popup)
        fondo_layout.add_widget(self.ranking_btn)
        
        # Botón de volver (nuevo botón con flecha)
        self.back_btn = Button(
            background_normal='imagen/flecha.png',
            size_hint=(None, None),
            size=(dp(45), dp(45)),
            pos_hint={'x': 0.04, 'top': 0.96},
            border=(0, 0, 0, 0)
        )
        self.back_btn.bind(on_release=self.go_to_menu)
        fondo_layout.add_widget(self.back_btn)
        
        self.add_widget(fondo_layout)

        # Etiquetas
        self.title_label = Label(size_hint=(1, None), height=dp(50),
                                 font_size='24sp', bold=True, color=(1, 1, 1, 1))
        self.streak_label = Label(size_hint=(1, None),
                                  height=dp(30), font_size='16sp')
        self.time_left_label = Label(size_hint=(1, None), height=dp(30), font_size='14sp')

        # Contenedor de preguntas
        self.question_container = BoxLayout(orientation='vertical', size_hint=(1, 1), spacing=dp(15))

        # Botón de comenzar reto (ahora único)
        self.start_button = Button(size_hint=(1, None), height=dp(50),
                                  background_color=(0.85, 0.90, 0.95, 0.5), color=(1, 1, 1, 1))
        self.start_button.bind(on_press=self.on_start_click)

        # Construcción del layout
        self.main_layout.add_widget(self.title_label)
        self.main_layout.add_widget(self.streak_label)
        self.main_layout.add_widget(self.time_left_label)
        self.main_layout.add_widget(self.question_container)
        self.main_layout.add_widget(self.start_button)

        # Verificamos estado inicial del reto
        self.check_daily_status()
        self.update_ui()

    def get_translation(self, key):
        """Obtiene la traducción según el idioma actual"""
        app = App.get_running_app()
        if hasattr(app, 'translate'):
            return app.translate(key)
        return TRANSLATIONS.get(self.language, {}).get(key, key)

    def update_ui(self):
        """Actualiza los textos según el idioma seleccionado"""
        self.title_label.text = self.get_translation('daily_challenge_title')
        self.update_streak_display()
        
        # Actualizar botón según estado
        if hasattr(self, 'start_button'):
            if self.last_played_date and self.last_played_date == date.today().isoformat():
                self.start_button.text = self.get_translation('view_result')
            else:
                self.start_button.text = self.get_translation('start_daily_challenge')

    def show_ranking_popup(self, instance):
        try:
            ranking_data = db.get_top_streaks(limit=10)
            if not ranking_data:  # Si no hay datos
                self.show_message("Info", "No hay datos de ranking disponibles")
                return
                
            content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
            
            t = TRANSLATIONS.get(self.language, TRANSLATIONS['Español'])
            title = Label(text=t.get('ranking_title', '🏆 Top Usuarios'), 
                         font_size='20sp', size_hint=(1, None), height=dp(40))
            content.add_widget(title)

            for i, item in enumerate(ranking_data, start=1):
                user_display = f"{i}. {item.get('usuario', 'Desconocido')} - {item.get('streak', 0)}"
                content.add_widget(Label(text=user_display, size_hint=(1, None), height=dp(30)))

            close_btn = Button(text=t.get('close', 'Cerrar'), size_hint=(1, None), height=dp(40))
            content.add_widget(close_btn)

            popup = Popup(title='', content=content, size_hint=(0.8, 0.8), auto_dismiss=False)
            close_btn.bind(on_press=popup.dismiss)
            popup.open()

        except Exception as e:
            print(f"Error mostrando clasificación: {e}")
            self.show_message("Error", "No se pudo cargar el ranking")

    def on_enter(self):
        """Se ejecuta cuando la pantalla se muestra"""
        self.language = App.get_running_app().language
        self.check_daily_status()
        self.update_ui()

    def check_daily_status(self):
        """Verifica si el usuario puede jugar hoy"""
        self.load_user_data()
    
        if self.last_played_date:
            try:
                # Asegurarse de que last_played_date es un objeto date
                if isinstance(self.last_played_date, str):
                    last_played = datetime.strptime(self.last_played_date, "%Y-%m-%d").date()
                else:
                    last_played = self.last_played_date
            
                today = date.today()
            
                # Si ya jugó hoy, deshabilitamos
                if last_played == today:
                    self.show_start_button(already_played=True)
                    self.update_time_left()
                    return
            
                # Si no jugó ayer, reiniciamos racha
                yesterday = today - timedelta(days=1)
                if last_played < yesterday:
                    self.streak = 0
                    self.save_user_data()
            except Exception as e:
                print(f"Error al verificar fecha: {e}")
                self.last_played_date = None
                self.streak = 0
                self.save_user_data()
    
        self.show_start_button()

    def update_time_left(self):
        """Muestra el tiempo restante para volver a jugar"""
        if not self.last_played_date:
            self.time_left_label.text = ""
            return
        
        try:
            last_played = datetime.strptime(self.last_played_date, "%Y-%m-%d").date() if isinstance(self.last_played_date, str) else self.last_played_date
            today = date.today()
            
            if last_played == today:
                now = datetime.now()
                reset_time = datetime.combine(today, datetime.min.time()) + timedelta(days=1)
                time_left = reset_time - now
                
                hours, remainder = divmod(time_left.seconds, 3600)
                minutes, _ = divmod(remainder, 60)
                
                t = TRANSLATIONS.get(self.language, TRANSLATIONS['Español'])
                self.time_left_label.text = t.get('time_left_message', 'Puedes volver a jugar en: {hours}h {minutes}m').format(
                    hours=hours, minutes=minutes)
            else:
                self.time_left_label.text = ""
        except Exception as e:
            print(f"Error al calcular tiempo restante: {e}")
            self.time_left_label.text = ""

    def show_start_button(self, already_played=False):
        self.question_container.clear_widgets()
        
        t = TRANSLATIONS.get(self.language, TRANSLATIONS['Español'])
        info_text = t.get('already_played_today', 'Ya completaste el reto de hoy. Vuelve mañana!') if already_played else t.get('streak_info', 'Hoy puedes aumentar tu racha!')
        
        # Actualizamos el botón inferior en lugar de crear uno nuevo
        self.start_button.disabled = already_played
        self.start_button.text = t.get('view_result', 'Ver Resultado') if already_played else t.get('start_daily_challenge', 'Comenzar Reto Diario')
        
        info_label = Label(text=info_text, size_hint=(1, None), height=dp(60), font_size='16sp', halign='center')
        self.question_container.add_widget(info_label)

    def on_start_click(self, instance):
        instance.disabled = True
        
        t = TRANSLATIONS.get(self.language, TRANSLATIONS['Español'])
        instance.text = t.get('generating_question', 'Generando pregunta...')
        
        self.question_container.clear_widgets()
        loading_label = Label(text=t.get('preparing_challenge', 'Preparando tu reto diario...'), 
                             size_hint=(1, None), height=dp(100), font_size='18sp', halign='center')
        self.question_container.add_widget(loading_label)
        Clock.schedule_once(lambda dt: self._generate_question(), 0.1)

    def _generate_question(self):
        try:
            idioma_prompt = "en español" if self.language == "Español" else "in English"
            
            prompt = (
                f"Genera una pregunta difícil y variada {idioma_prompt} sobre un país del mundo elegido al azar. "
                "La pregunta debe cubrir uno de estos temas: historia, ciencia, arte, geografía, entretenimiento o deporte. "
                "Debe tener 4 opciones de respuesta (A, B, C, D), siendo solo una correcta. "
                "Formato exacto:\nPaís: [nombre del país]\nPregunta: [texto de la pregunta]\nOpciones:\n" \
                "A) [opción A]\nB) [opción B]\nC) [opción C]\nD) [opción D]\nRespuesta correcta: [letra A-D]"
            )
            response = deepseek_client.chat.completions.create(
                model="deepseek/deepseek-r1:free",
                messages=[{"role": "user", "content": prompt}]
            )
            raw_text = response.choices[0].message.content

            # Parseo de la respuesta
            country_line = raw_text.split('Pregunta:')[0]
            country = country_line.replace('País:', '').strip()
            question_part = raw_text.split('Opciones:')[0]
            question_text = question_part.split('Pregunta:')[1].strip()
            options_part = raw_text.split('Opciones:')[1].split('Respuesta correcta:')
            options = [opt.strip() for opt in options_part[0].split('\n') if ')' in opt]
            correct_answer = options_part[1].strip().upper()

            letter_to_index = {'A': 0, 'B': 1, 'C': 2, 'D': 3}
            self.current_question = {'text': question_text, 'options': options, 'country': country}
            self.correct_answer = letter_to_index[correct_answer[0]]
            self.question_generated = True
            self.show_question()

        except Exception as e:
            self.show_start_button()
            error_label = Label(text=f"{self.get_translation('error_generating_question')}: {e}", 
                               size_hint=(1, None), height=dp(100), font_size='16sp', color=(1, 0, 0, 1))
            self.question_container.add_widget(error_label)

    def show_question(self):
        self.question_container.clear_widgets()
        question_label = Label(
            text=self.current_question['text'], size_hint=(1, None), height=dp(80),
            font_size='18sp', halign='center', valign='middle', text_size=(self.width - dp(40), None)
        )
        self.question_container.add_widget(question_label)

        t = TRANSLATIONS.get(self.language, TRANSLATIONS['Español'])
        country_label = Label(text=f"{t.get('country_label', 'País')}: {self.current_question['country']}", 
                             size_hint=(1, None), height=dp(30), font_size='14sp', halign='center')
        self.question_container.add_widget(country_label)

        options_grid = GridLayout(cols=1, spacing=dp(10), size_hint=(1, None))
        options_grid.bind(minimum_height=options_grid.setter('height'))
        for i, option in enumerate(self.current_question['options']):
            btn = Button(
                text=option, size_hint=(1, None), height=dp(50), 
                background_color=(0.85, 0.90, 0.95, 0.5), color=(1, 1, 1, 1), 
                halign='left', padding=(dp(20), 0)
            )
            btn.bind(on_press=lambda instance, idx=i: self.check_answer(idx))
            options_grid.add_widget(btn)

        scroll = ScrollView(size_hint=(1, 1))
        scroll.add_widget(options_grid)
        self.question_container.add_widget(scroll)

    def check_answer(self, selected_index):
        self.user_answer = selected_index
        today = date.today().isoformat()
    
        # Solo actualizar racha si es la primera vez que juega hoy
        if self.last_played_date != today:
            if selected_index == self.correct_answer:
                self.streak += 1
            else:
                self.streak = 0
        
            # Actualizar fecha solo si es un nuevo día
            self.last_played_date = today
            self.update_streak_display()
            self.save_user_data()
    
        # Mostrar feedback visual
        for child in self.question_container.children:
            if isinstance(child, ScrollView):
                for btn in child.children[0].children:
                    if isinstance(btn, Button):
                        idx = ord(btn.text[0]) - ord('A')
                        if idx == selected_index:
                            btn.background_color = (0, 1, 0, 0.7) if selected_index == self.correct_answer else (1, 0, 0, 0.7)
                        if idx == self.correct_answer:
                            btn.background_color = (0, 1, 0, 0.7)

        Clock.schedule_once(lambda dt: self.show_result(), 1.5)

    def show_result(self):
        self.question_container.clear_widgets()
        t = TRANSLATIONS.get(self.language, TRANSLATIONS['Español'])
        
        if self.user_answer == self.correct_answer:
            result_text = t.get('correct_result', '¡Correcto!\nHas aumentado tu racha a {streak} días').format(
                streak=self.streak)
            c = (0, 1, 0, 1)
        else:
            result_text = t.get('wrong_result', 'Incorrecto\nLa respuesta correcta era: {answer}').format(
                answer=chr(65 + self.correct_answer))
            c = (1, 0, 0, 1)
            
        self.question_container.add_widget(Label(
            text=result_text, size_hint=(1, None), height=dp(80), 
            font_size='20sp', color=c, halign='center'))
            
        self.question_container.add_widget(Label(
            text=self.current_question['text'], size_hint=(1, None), height=dp(60), 
            font_size='16sp', halign='center', text_size=(self.width - dp(40), None)))
            
        self.question_container.add_widget(Label(
            text=f"{t.get('correct_answer_label', 'Respuesta correcta')}: {self.current_question['options'][self.correct_answer]}", 
            size_hint=(1, None), height=dp(40), font_size='16sp', 
            color=(0, 1, 0, 1), halign='center'))

    def load_user_data(self):
        if not self.user_id:
            self.streak = 0
            self.last_played_date = None
            self.update_streak_display()
            return
        
        data = db.get_user_reto(self.user_id)
        print(f"[DEBUG] Datos recibidos de DB: {data}")  # Para depuración
        
        # Caso 1: Si data es None (primer uso)
        if data is None:
            self.streak = 0
            self.last_played_date = None
            self.update_streak_display()
            return
        
        # Caso 2: Si data es un string (JSON)
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                data = {}
        
        # Caso 3: Si data es un diccionario (formato esperado)
        if isinstance(data, dict):
            self.streak = data.get('streak', 0)
            self.last_played_date = data.get('last_played_date', None)
        # Caso 4: Si data es un número (backward compatibility)
        elif isinstance(data, (int, float)):
            self.streak = int(data)
            self.last_played_date = None
        # Caso 5: Otros tipos no esperados
        else:
            self.streak = 0
            self.last_played_date = None
        
        self.update_streak_display()
        print(f"[DEBUG] Datos cargados - Racha: {self.streak}, Última jugada: {self.last_played_date}")

    def update_streak_display(self):
        """Actualiza consistentemente la visualización de la racha"""
        t = TRANSLATIONS.get(self.language, TRANSLATIONS['Español'])
        self.streak_label.text = f"{t.get('current_streak', 'Racha actual')}: {self.streak} {t.get('days', 'días')}"
    
    def save_user_data(self):
        if not self.user_id:
            return
    
        # Asegurar formato consistente de fecha (siempre string YYYY-MM-DD)
        last_played_str = None
        if self.last_played_date:
            if isinstance(self.last_played_date, str):
                last_played_str = self.last_played_date
            else:
                last_played_str = self.last_played_date.isoformat()
    
        reto_data = {
            'streak': self.streak,
            'last_played_date': last_played_str
        }
    
        db.update_user_reto(self.user_id, reto_data)
        print(f"[DEBUG] Datos guardados: {reto_data}")

    def go_to_menu(self, instance):
        self.manager.current = 'menu'