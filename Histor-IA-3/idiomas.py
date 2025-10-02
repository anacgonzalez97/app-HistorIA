from kivy.uix.screenmanager import Screen
from kivy.app import App
from kivy.lang import Builder
import json

IDIOMA_PATH = "config_idioma.json"

Builder.load_file('style/idiomas.kv')

TRANSLATIONS = {
    'Español': {
        'select_language': 'Selecciona un idioma:',
        'back': 'Guardar y volver',
        'spanish': 'Español',
        'english': 'Inglés'
    },
    'English': {
        'select_language': 'Select a language:',
        'back': 'Save and go back',
        'spanish': 'Spanish',
        'english': 'English'
    }
}

class IdiomasScreen(Screen):

    def on_enter(self):
        self.update_ui()

    def on_language_selected(self, language):
        app = App.get_running_app()
        app.set_language(language)
        self.guardar_idioma(language)
        self.update_ui()

    def guardar_idioma(self, language):
        with open(IDIOMA_PATH, "w") as f:
            json.dump({"idioma": language}, f)

    def guardar_y_volver(self):
        self.manager.current = 'login'

    def update_ui(self):
        lang = App.get_running_app().language
        self.ids.language_label.text = TRANSLATIONS[lang]['select_language']
        self.ids.btn_volver.text = TRANSLATIONS[lang]['back']
     