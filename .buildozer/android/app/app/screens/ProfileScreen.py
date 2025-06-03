import webbrowser

from kivy.uix.screenmanager import Screen


class ProfileScreen(Screen):
    def mudar_para_abrir_link(self):
        webbrowser.open(
            "https://docs.google.com/forms/d/e/1FAIpQLSdb5CwD9a3_Ew7fCARI7T6OdXu3sKmV3PmHb3HqlOnKjsDGgw/viewform?usp=sharing"
        )

    pass
