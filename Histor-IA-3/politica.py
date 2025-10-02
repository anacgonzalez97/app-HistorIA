from kivy.uix.screenmanager import Screen
from kivy.app import App
from kivy.lang import Builder

Builder.load_file('style/politica.kv')

class PoliticaScreen(Screen):
    def on_enter(self):
        self.update_ui()

    def update_ui(self):
        self.ids.politica_label.text = App.get_running_app().translate("politica_text")

    def go_to_menu(self):
        self.manager.current = 'menu'
