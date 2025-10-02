from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.properties import NumericProperty, StringProperty, ObjectProperty, ListProperty
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.clock import Clock
from openai import OpenAI
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
import random
import os
import sqlite3
from dotenv import load_dotenv
from kivy.uix.floatlayout import FloatLayout
from datetime import datetime
from kivy.app import App
from kivy.lang import Builder

from translations import TRANSLATIONS
from database import db

Builder.load_file("style/quiz.kv")
load_dotenv()

# Configuración de la API
api_key = os.getenv("API_KEY") or "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"
client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")

# Datos de continentes y países
CONTINENTS = {
    "América": [
        "United States", "Antigua and Barbuda", "Barbados","Saint Vincent and the Grenadines","Saint Lucia",
        "Saint Kitts and Nevis","Grenada","Dominica","Canada", "Mexico", "Guatemala", "Belize", "Honduras", 
        "El Salvador", "Nicaragua", "Costa Rica", "Panama","Cuba", "Dominican Republic",
        "Haiti", "Jamaica", "Puerto Rico", "Bahamas", "Trinidad and Tobago",
        "Brazil", "Argentina", "Colombia", "Peru", "Chile", "Ecuador", "Venezuela", 
        "Bolivia", "Paraguay", "Uruguay", "Guyana", "Suriname", "French Guiana"
    ],
    "Europa": [
        "Spain", "France", "Italy", "Germany", "United Kingdom", "Portugal", 
        "Netherlands", "Belgium", "Switzerland", "Sweden", "Norway", "Finland", 
        "Denmark", "Austria", "Poland", "Greece", "Russia","Czech Republic", "Hungary",
        "Romania", "Bulgaria", "Serbia", "Croatia", "Slovenia", "Slovakia",
        "Ukraine", "Belarus", "Lithuania", "Latvia", "Estonia", "Ireland",
        "Iceland", "Luxembourg", "Monaco", "Andorra", "San Marino", "Vatican City",
        "Albania", "North Macedonia", "Montenegro", "Bosnia and Herzegovina"
    ],
    "África": [
        "South Africa", "Egypt", "Nigeria", "Kenya","São Tomé and Príncipe", "Morocco", "Comoros","Ghana", 
        "Algeria", "Ethiopia", "Tanzania", "Angola", "Libya", "Tunisia",
        "Sudan", "South Sudan", "Somalia", "Senegal", "Cameroon", "Ivory Coast",
        "Madagascar", "Mozambique", "Zambia", "Zimbabwe", "Democratic Republic of the Congo",
        "Republic of the Congo", "Gabon", "Guinea", "Equatorial Guinea", "Benin",
        "Burkina Faso", "Mali", "Niger", "Chad", "Central African Republic", "Rwanda",
        "Burundi", "Uganda", "Namibia", "Botswana", "Lesotho", "Eswatini",
        "Liberia", "Sierra Leone", "Togo", "Djibouti", "Eritrea", "Mauritius", "Seychelles"
    ],
    "Asia": [
        "China", "Japan", "India", "South Korea","Palestine", "Thailand", 
        "Vietnam", "Indonesia", "Malaysia", "Philippines", "North Korea",
        "Pakistan", "Bangladesh", "Afghanistan", "Iran", "Iraq", "Saudi Arabia",
        "Turkey", "Israel", "Jordan", "Lebanon", "Bahrain","Syria", "Yemen", "Oman",
        "United Arab Emirates", "Qatar", "Kuwait", "Kazakhstan", "Uzbekistan",
        "Turkmenistan", "Kyrgyzstan", "Tajikistan", "Georgia", "Armenia", "Azerbaijan",
        "Sri Lanka", "Nepal", "Bhutan", "Maldives", "Singapore", "Brunei", "East Timor",
        "Cambodia", "Laos", "Myanmar", "Mongolia", "Taiwan"
    ],
    "Oceanía": [
        "Australia", "New Zealand", "Fiji", "Papua New Guinea", "Samoa", 
        "Tonga", "Solomon Islands", "Vanuatu", "Kiribati", "Tuvalu", "Nauru",
        "Palau", "Marshall Islands", "Micronesia", "French Polynesia", "New Caledonia",
        "Guam", "Northern Mariana Islands", "Cook Islands", "Niue", "Tokelau"
    ]
}

def init_db():
    conn = sqlite3.connect('quiz_users.db')
    cursor = conn.cursor()
    
    # Tabla de usuarios
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Tabla de resultados de quizzes
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS quiz_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        country TEXT NOT NULL,
        score INTEGER NOT NULL,
        total_questions INTEGER NOT NULL,
        approved BOOLEAN NOT NULL CHECK (approved IN (0, 1)),
        completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')
    
    conn.commit()
    conn.close()

init_db()

class ContinentButton(Button):
    def __init__(self, continent, **kwargs):
        super(ContinentButton, self).__init__(**kwargs)
        self.continent = continent
        self.text = self.get_translated_continent(continent)
        self.size_hint_y = None
        self.height = dp(40)
        self.background_color = (0.85, 0.90, 0.95, 0.5)
        self.color = (1, 1, 1, 1)
        self.font_size = '16sp'
        self.selected = False
        self.original_color = (0.85, 0.90, 0.95, 0.5)
        self.selected_color = (0.65, 0.70, 0.75, 0.7)

    def on_press(self):
        # Deseleccionar todos los botones del mismo grupo primero
        parent = self.parent
        if parent:
            for child in parent.children:
                if isinstance(child, ContinentButton):
                    child.deselect()
        
        # Seleccionar este botón
        self.select()
        return super().on_press()

    def select(self):
        self.selected = True
        self.background_color = self.selected_color

    def deselect(self):
        self.selected = False
        self.background_color = self.original_color

    def get_translated_continent(self, continent):
        app = App.get_running_app()
        language = app.language if hasattr(app, 'language') else 'Español'
        continent_map = {
            "América": "north_america",
            "Europa": "europe",
            "África": "africa",
            "Asia": "asia",
            "Oceanía": "oceania"
        }
        continent_key = continent_map.get(continent, continent)
        return TRANSLATIONS[language]['continents'].get(continent_key, continent)

class CountryButton(Button):
    def __init__(self, country, **kwargs):
        super(CountryButton, self).__init__(**kwargs)
        self.country = country
        self.text = self.get_translated_country(country)
        self.size_hint_y = None
        self.height = dp(40)
        self.background_color = (0.85, 0.90, 0.95, 0.5)
        self.color = (1, 1, 1, 1)
        self.font_size = '14sp'
        self.selected = False
        self.original_color = (0.85, 0.90, 0.95, 0.5)
        self.selected_color = (0.65, 0.70, 0.75, 0.7)

    def on_press(self):
        # Deseleccionar todos los botones del mismo grupo primero
        parent = self.parent
        if parent:
            for child in parent.children:
                if isinstance(child, CountryButton):
                    child.deselect()
        
        # Seleccionar este botón
        self.select()
        return super().on_press()

    def select(self):
        self.selected = True
        self.background_color = self.selected_color

    def deselect(self):
        self.selected = False
        self.background_color = self.original_color

    def get_translated_country(self, country):
        app = App.get_running_app()
        language = app.language if hasattr(app, 'language') else 'Español'
        
        for continent_name in TRANSLATIONS[language]['countries_by_continent']:
            countries_dict = TRANSLATIONS[language]['countries_by_continent'][continent_name]
            if country in countries_dict:
                if language == 'Español':
                    return countries_dict[country]
                else:
                    return country
        
        return country

class QuizScreen(Screen):
    country_input = ObjectProperty(None)
    current_question = NumericProperty(0)
    score = NumericProperty(0)
    questions = ListProperty([])
    correct_answers = ListProperty([])
    user_answers = ListProperty([])
    question_results = ListProperty([])
    user_id = NumericProperty(None)
    language = StringProperty('Español')
    
    def __init__(self, **kwargs):
        super(QuizScreen, self).__init__(**kwargs)
        self.language = App.get_running_app().language

        # Fondo
        self.fondo_layout = FloatLayout()
        self.fondo = Image(source="imagen/fondo.png", allow_stretch=True, keep_ratio=False,
                      size_hint=(1, 1), pos_hint={"x": 0, "y": 0})
        self.fondo_layout.add_widget(self.fondo)
        
        # Layout principal
        self.main_layout = FloatLayout()

        # Botón de historial
        self.history_button = Button(
            background_normal='imagen/historial.png',
            size_hint=(None, None),
            size=(dp(45), dp(45)),
            pos_hint={'right': 0.96, 'top': 0.96},
            border=(0, 0, 0, 0)
        )
        self.history_button.bind(on_release=self.show_history)
        self.main_layout.add_widget(self.history_button)
        
        # Botón de volver
        self.back_button = Button(
            background_normal='imagen/flecha.png',
            size_hint=(None, None),
            size=(dp(45), dp(45)),
            pos_hint={'x': 0.04, 'top': 0.96},
            border=(0, 0, 0, 0)
        )
        self.back_button.bind(on_release=self.go_to_menu)
        self.main_layout.add_widget(self.back_button)
        
        # Contenedor de selección
        self.selection_container = BoxLayout(
            orientation='vertical',
            size_hint=(0.9, 0.7),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            spacing=dp(10)
        )
        self.main_layout.add_widget(self.selection_container)
        
        self.show_continent_selection()
        
        self.fondo_layout.add_widget(self.main_layout)
        self.add_widget(self.fondo_layout)
    
    def get_translation(self, key):
        app = App.get_running_app()
        if hasattr(app, 'translate'):
            return app.translate(key)
        return TRANSLATIONS.get(self.language, {}).get(key, key)
    
    def on_enter(self):
        self.language = App.get_running_app().language
        self.update_ui()
    
    def update_ui(self):
        if hasattr(self, 'start_button'):
            self.start_button.text = self.get_translation('start_quiz')
        
        if hasattr(self, 'quiz_container') and self.quiz_container in self.main_layout.children:
            self.show_question()
    
    def show_continent_selection(self):
        self.selection_container.clear_widgets()
        
        title = Label(
            text=self.get_translation('select_continent'),
            size_hint_y=None,
            height=dp(50),
            font_size='20sp',
            bold=True,
            color=(1, 1, 1, 1))
        self.selection_container.add_widget(title)
        
        scroll = ScrollView()
        continents_grid = GridLayout(
            cols=1,
            spacing=dp(10),
            size_hint_y=None)
        continents_grid.bind(minimum_height=continents_grid.setter('height'))
        
        for continent in CONTINENTS.keys():
            btn = ContinentButton(continent)
            btn.bind(on_release=self.show_countries)
            continents_grid.add_widget(btn)
        
        scroll.add_widget(continents_grid)
        self.selection_container.add_widget(scroll)
        
        self.start_button = Button(
            text=self.get_translation('start_quiz'),
            size_hint=(1, None),
            height=dp(50),
            background_color=(0.85, 0.90, 0.95, 1),
            color=(1, 1, 1, 1),
            bold=True)
        self.start_button.bind(on_press=self.start_quiz)
        self.selection_container.add_widget(self.start_button)
    
    def show_countries(self, instance):
        continent = instance.continent
        self.selection_container.clear_widgets()
        
        title_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(50),
            spacing=dp(10))
        
        back_btn = Button(
            text="<--",
            size_hint=(None, 1),
            width=dp(50),
            font_size='20sp',
            background_color=(0.85, 0.90, 0.95, 0))
        back_btn.bind(on_release=lambda x: self.show_continent_selection())
        title_layout.add_widget(back_btn)
        
        title = Label(
            text=f"{self.get_translation('countries_in')} {self.get_translated_continent(continent)}",
            font_size='20sp',
            bold=True,
            color=(1, 1, 1, 1))
        title_layout.add_widget(title)
        self.selection_container.add_widget(title_layout)
        
        scroll = ScrollView()
        countries_grid = GridLayout(
            cols=1,
            spacing=dp(10),
            size_hint_y=None)
        countries_grid.bind(minimum_height=countries_grid.setter('height'))
        
        for country in CONTINENTS[continent]:
            btn = CountryButton(country)
            btn.bind(on_release=self.select_country)
            countries_grid.add_widget(btn)
        
        scroll.add_widget(countries_grid)
        self.selection_container.add_widget(scroll)
        
        self.start_button = Button(
            text=self.get_translation('start_quiz'),
            size_hint=(1, None),
            height=dp(50),
            background_color=(0.85, 0.90, 0.95, 1),
            color=(1, 1, 1, 1),
            bold=True)
        self.start_button.bind(on_press=self.start_quiz)
        self.selection_container.add_widget(self.start_button)
    
    def get_translated_continent(self, continent):
        app = App.get_running_app()
        language = app.language if hasattr(app, 'language') else 'Español'
        continent_map = {
            "América": "north_america",
            "Europa": "europe",
            "África": "africa",
            "Asia": "asia",
            "Oceanía": "oceania"
        }
        continent_key = continent_map.get(continent, continent)
        return TRANSLATIONS[language]['continents'].get(continent_key, continent)
    
    def select_country(self, instance):
        self.selected_country = instance.country
    
    def start_quiz(self, instance):
        # Verificar si hay algún continente seleccionado
        continent_selected = False
        if hasattr(self, 'selection_container'):
            for child in self.selection_container.children:
                if isinstance(child, ScrollView):
                    for grid_child in child.children[0].children:
                        if isinstance(grid_child, ContinentButton) and grid_child.selected:
                            continent_selected = True
                            break
        
        # Verificar si hay algún país seleccionado
        country_selected = hasattr(self, 'selected_country') and self.selected_country
        
        if not continent_selected and not country_selected:
            self.show_message(self.get_translation('error'), self.get_translation('select_country_error'))
            return
        
        country = getattr(self, 'selected_country', '').strip()
            
        if not country:
            self.show_message(self.get_translation('error'), self.get_translation('select_country_error'))
            return
        
        self.main_layout.remove_widget(self.selection_container)
        
        self.quiz_container = BoxLayout(
            orientation='vertical',
            size_hint=(0.9, 0.8),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            spacing=dp(10))
        self.main_layout.add_widget(self.quiz_container)
        
        self.start_button.disabled = True
        self.start_button.text = self.get_translation('generating_questions')
        
        self.quiz_container.clear_widgets()
        self.user_answers = []
        self.question_results = []
        
        loading_label = Label(
            text=f"{self.get_translation('generating_questions_about')} {self.get_translated_country(country)}...",
            size_hint=(1, None),
            height=dp(100),
            font_size='16sp',
            halign='center')
        self.quiz_container.add_widget(loading_label)
        
        Clock.schedule_once(lambda dt: self.generate_questions(country), 0.1)
    
    def get_translated_country(self, country):
        app = App.get_running_app()
        language = app.language if hasattr(app, 'language') else 'Español'
        
        for continent_name in TRANSLATIONS[language]['countries_by_continent']:
            countries_dict = TRANSLATIONS[language]['countries_by_continent'][continent_name]
            if country in countries_dict:
                if language == 'Español':
                    return countries_dict[country]
                else:
                    return country
        
        return country
    
    def generate_questions(self, country):
        try:
            idioma_prompt = "en español" if self.language == "Español" else "in English"
            
            response = client.chat.completions.create(
                model="deepseek/deepseek-r1:free",
                messages=[
                    {
                        "role": "user",
                        "content": f"Genera EXACTAMENTE 10 preguntas variadas sobre {country} {idioma_prompt}. Formato específico: 'Pregunta: ¿...?\nOpciones:\nA) ...\nB) ...\nC) ...\nD) ...\nRespuesta correcta: A/B/C/D'\n\nSolo incluye 10 preguntas completas."
                    }
                ]
            )
        
            raw_text = response.choices[0].message.content
            questions_raw = raw_text.split('Pregunta: ')[1:]
        
            self.questions = []
            self.correct_answers = []
        
            questions_processed = 0
            for q in questions_raw:
                if questions_processed >= 10:
                    break
                
                if not q.strip():
                    continue
                
                parts = q.split('Opciones:')
                if len(parts) < 2:
                    continue
                
                question_text = parts[0].strip()
            
                options_part = parts[1].split('Respuesta correcta:')
                if len(options_part) < 2:
                    continue
                
                options = [opt.strip() for opt in options_part[0].split('\n') if opt.strip() and ')' in opt]
                if len(options) != 4:
                    continue
                
                correct_answer = options_part[1].strip().upper()
                if correct_answer[0] not in ['A', 'B', 'C', 'D']:
                    continue
                
                letter_to_index = {'A': 0, 'B': 1, 'C': 2, 'D': 3}
            
                self.questions.append({
                    'text': question_text,
                    'options': options
                })
                self.correct_answers.append(letter_to_index[correct_answer[0]])
                questions_processed += 1
        
            if len(self.questions) < 10:
                raise ValueError(f"{self.get_translation('only_generated')} {len(self.questions)} {self.get_translation('valid_questions')}")
        
            self.current_question = 0
            self.score = 0
            self.show_question()
        
        except Exception as e:
            self.show_message(self.get_translation('error'), f"{self.get_translation('generate_questions_error')}: {str(e)}")
            self.reset_quiz(None)
        finally:
            self.start_button.disabled = False
            self.start_button.text = self.get_translation('start_quiz')
    
    def show_question(self):
        self.quiz_container.clear_widgets()
        
        if self.current_question >= len(self.questions):
            self.save_quiz_results()
            self.show_results()
            return
        
        question = self.questions[self.current_question]
        question_label = Label(
            text=question['text'],
            size_hint_y=None,
            height=dp(100),
            font_size='16sp',
            halign='center',
            valign='top',
            text_size=(Window.width - dp(40), None),
            padding=(dp(10), dp(10)),
            markup=True
        )
        self.quiz_container.add_widget(question_label)

        progress_label = Label(
            text=f"{self.get_translation('question')} {self.current_question + 1} {self.get_translation('of')} {len(self.questions)}",
            size_hint=(1, None),
            height=dp(30),
            font_size='13sp')
        self.quiz_container.add_widget(progress_label)
        
        score_label = Label(
            text=f"{self.get_translation('score')}: {self.score}",
            size_hint=(1, None),
            height=dp(30),
            font_size='12sp')
        self.quiz_container.add_widget(score_label)
        
        options_grid = GridLayout(cols=1, spacing=dp(10), size_hint=(1, None))
        options_grid.bind(minimum_height=options_grid.setter('height'))
        
        options = question['options']
        for i, option in enumerate(options):
            btn = Button(
                text=option,
                size_hint=(1, None),
                height=dp(50),
                background_color=(0.85, 0.90, 0.95, 0.5),
                color=(1, 1, 1, 1))
            btn.bind(on_press=lambda instance, idx=i: self.check_answer(idx))
            options_grid.add_widget(btn)
        
        scroll = ScrollView(size_hint=(1, 1))
        scroll.add_widget(options_grid)
        self.quiz_container.add_widget(scroll)
    
    def check_answer(self, selected_index):
        question_data = {
            'question': self.questions[self.current_question]['text'],
            'user_answer': selected_index,
            'correct_answer': self.correct_answers[self.current_question],
            'options': self.questions[self.current_question]['options']
        }
        
        if selected_index == self.correct_answers[self.current_question]:
            self.score += 1
            question_data['is_correct'] = True
            self.show_feedback(selected_index, True)
        else:
            question_data['is_correct'] = False
            self.show_feedback(selected_index, False)
        
        self.question_results.append(question_data)
        self.user_answers.append(selected_index)
        
        Clock.schedule_once(lambda dt: self.next_question(), 1.5)
    
    def show_feedback(self, selected_index, is_correct):
        for child in self.quiz_container.children:
            if isinstance(child, ScrollView):
                for grid_child in child.children[0].children:
                    if isinstance(grid_child, Button):
                        if grid_child.text.startswith(chr(65 + selected_index) + ')'):
                            grid_child.background_color = (0, 1, 0, 0.7) if is_correct else (1, 0, 0, 0.7)
                        elif grid_child.text.startswith(chr(65 + self.correct_answers[self.current_question]) + ')'):
                            if not is_correct:
                                grid_child.background_color = (0, 1, 0, 0.7)
    
    def next_question(self):
        self.current_question += 1
        self.show_question()
    
    def save_quiz_results(self):
        if not self.user_id:
            print("Error: No hay user_id definido")
            return
            
        conn = sqlite3.connect('quiz_users.db')
        cursor = conn.cursor()
        
        try:
            approved = 1 if (self.score / len(self.questions)) >= 0.6 else 0
            
            cursor.execute('''
            INSERT INTO quiz_results (user_id, country, score, total_questions, approved)
            VALUES (?, ?, ?, ?, ?)
            ''', (self.user_id, self.selected_country, self.score, len(self.questions), approved))
            
            conn.commit()
        except Exception as e:
            print(f"Error guardando resultados: {e}")
        finally:
            conn.close()
    
    def show_results(self):
        self.quiz_container.clear_widgets()
        
        approved = (self.score / len(self.questions)) >= 0.6
        result_text = f"{self.get_translation('quiz_completed')}!\n{self.get_translation('score')}: {self.score}/{len(self.questions)}\n"
        result_text += f"✅ {self.get_translation('approved')}" if approved else f"❌ {self.get_translation('not_approved')}"
        
        result_label = Label(
            text=result_text,
            size_hint=(1, None),
            height=dp(100),
            font_size='20sp',
            halign='center')
        self.quiz_container.add_widget(result_label)
        
        scroll = ScrollView(size_hint=(1, 1))
        results_layout = GridLayout(cols=1, spacing=dp(15), size_hint_y=None)
        results_layout.bind(minimum_height=results_layout.setter('height'))
        
        for i, result in enumerate(self.question_results):
            question_box = BoxLayout(
                orientation='vertical',
                spacing=dp(5),
                size_hint_y=None)
            question_box.bind(minimum_height=question_box.setter('height'))
            
            question_label = Label(
                text=f"[b]{self.get_translation('question')} {i+1}:[/b] {result['question']}",
                size_hint=(1, None),
                height=dp(60),
                font_size='16sp',
                markup=True,
                halign='left',
                valign='middle')
            question_box.add_widget(question_label)
            
            user_answer = chr(65 + result['user_answer']) + ') ' + result['options'][result['user_answer']].split(') ')[1]
            user_label = Label(
                text=f"{self.get_translation('your_answer')}: [color={'#00FF00' if result['is_correct'] else '#FF0000'}]{user_answer}[/color]",
                size_hint=(1, None),
                height=dp(30),
                font_size='14sp',
                markup=True,
                halign='left')
            question_box.add_widget(user_label)
            
            if not result['is_correct']:
                correct_answer = chr(65 + result['correct_answer']) + ') ' + result['options'][result['correct_answer']].split(') ')[1]
                correct_label = Label(
                    text=f"{self.get_translation('correct_answer')}: [color=#00FF00]{correct_answer}[/color]",
                    size_hint=(1, None),
                    height=dp(30),
                    font_size='14sp',
                    markup=True,
                    halign='left')
                question_box.add_widget(correct_label)
            
            results_layout.add_widget(question_box)
        
        scroll.add_widget(results_layout)
        self.quiz_container.add_widget(scroll)
        
        restart_btn = Button(
            text=self.get_translation('another_quiz'),
            size_hint=(1, None),
            height=dp(50),
            background_color=(0.85, 0.90, 0.95, 0.5),
            color=(1, 1, 1, 1))
        restart_btn.bind(on_press=self.reset_quiz)
        self.quiz_container.add_widget(restart_btn)
    
    def reset_quiz(self, instance):
        # Limpiar completamente el layout principal
        self.main_layout.clear_widgets()
        
        # Restablecer todos los estados y variables
        self.current_question = 0
        self.score = 0
        self.questions = []
        self.correct_answers = []
        self.user_answers = []
        self.question_results = []
        
        # Volver a agregar los botones de navegación
        self.main_layout.add_widget(self.history_button)
        self.main_layout.add_widget(self.back_button)
        
        # Recrear el contenedor de selección
        self.selection_container = BoxLayout(
            orientation='vertical',
            size_hint=(0.9, 0.7),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            spacing=dp(10)
        )
        self.main_layout.add_widget(self.selection_container)
        
        # Mostrar nuevamente la selección de continentes
        self.show_continent_selection()
        
        # Eliminar país seleccionado
        if hasattr(self, 'selected_country'):
            del self.selected_country
    
    def show_history(self, instance):
        if not self.user_id:
            self.show_message(self.get_translation('error'), self.get_translation('no_user_identified'))
            return
            
        conn = sqlite3.connect('quiz_users.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            SELECT country, score, total_questions, approved, completed_at 
            FROM quiz_results
            WHERE user_id = ?
            ORDER BY completed_at DESC
            ''', (self.user_id,))
            
            quizzes = cursor.fetchall()
            
            if not quizzes:
                self.show_message(self.get_translation('history'), self.get_translation('no_completed_quizzes'))
                return
            
            from kivy.uix.popup import Popup
            from kivy.uix.gridlayout import GridLayout
            from kivy.uix.label import Label
            
            content = BoxLayout(orientation='vertical', spacing=dp(10))
            scroll = ScrollView()
            grid = GridLayout(cols=1, spacing=dp(10), size_hint_y=None)
            grid.bind(minimum_height=grid.setter('height'))
            
            headers = GridLayout(cols=5, size_hint_y=None, height=dp(40))
            headers.add_widget(Label(text=self.get_translation('country'), bold=True))
            headers.add_widget(Label(text=self.get_translation('score'), bold=True))
            headers.add_widget(Label(text=self.get_translation('total'), bold=True))
            headers.add_widget(Label(text=self.get_translation('approved'), bold=True))
            headers.add_widget(Label(text=self.get_translation('date'), bold=True))
            grid.add_widget(headers)
            
            for quiz in quizzes:
                row = GridLayout(cols=5, size_hint_y=None, height=dp(40))
                row.add_widget(Label(text=quiz[0]))
                row.add_widget(Label(text=str(quiz[1])))
                row.add_widget(Label(text=str(quiz[2])))
                row.add_widget(Label(text="✅" if quiz[3] else "❌"))
                row.add_widget(Label(text=quiz[4][:19]))
                grid.add_widget(row)
            
            scroll.add_widget(grid)
            content.add_widget(scroll)
            
            close_btn = Button(text=self.get_translation('close'), size_hint=(1, None), height=dp(50))
            content.add_widget(close_btn)
            
            popup = Popup(
                title=self.get_translation('quiz_history'),
                content=content,
                size_hint=(0.9, 0.8))
            close_btn.bind(on_press=popup.dismiss)
            popup.open()
            
        except Exception as e:
            print(f"Error obteniendo historial: {e}")
            self.show_message(self.get_translation('error'), self.get_translation('load_history_error'))
        finally:
            conn.close()
    
    def show_message(self, title, message):
        from kivy.uix.popup import Popup
        from kivy.uix.label import Label
        content = BoxLayout(orientation='vertical')
        content.add_widget(Label(text=message))
        popup = Popup(title=title, content=content, size_hint=(0.7, 0.3))
        popup.open()
        Clock.schedule_once(lambda dt: popup.dismiss(), 1.5)
    
    def go_to_menu(self, instance):
        self.manager.current = 'menu'