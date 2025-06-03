import logging
import os
from datetime import datetime

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager
from kivy.utils import platform
from kivy_garden.mapview import MapView, MapMarker


from app.backend.exporters.pdf_exporter import PDFExporter
from app.backend.gps_manager import GPSManager
from app.project_manager import ProjectManager
from app.screens.AddProjectScreen import AddProjectScreen
from app.screens.MapScreen import MapScreen
from app.screens.ProfileScreen import ProfileScreen
from app.screens.ViewProjectsScreen import ViewProjectsScreen
from app.screens.WelcomeScreen import WelcomeScreen

# Constante de request code
CREATE_PDF = 1001

# Configuração do logger
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)


class MyApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.project_manager = ProjectManager()
        self.pdf_exporter = PDFExporter()
        self.gps_manager = GPSManager(self)
        self.add_project = AddProjectScreen()
        self._pending_pdf = None  # Guarda tupla (bytes, nome)

    def on_start(self):
        # Verificar permissões ao iniciar o app
        caminho_json = os.path.join(self.user_data_dir, "projetos_salvos.json")
        self.project_manager.carregar_projetos(caminho_json)

        if platform == "android":
            from android import activity

            activity.bind(on_activity_result=self.on_activity_result)
            self.request_android_permissions()

    def build(self):
        try:
            Builder.load_file("telas.kv")
            self.enable_swipe = False
            sm = ScreenManager()
            sm.add_widget(WelcomeScreen(name="welcome"))
            sm.add_widget(ProfileScreen(name="profile"))
            sm.add_widget(AddProjectScreen(name="add_project"))
            sm.add_widget(ViewProjectsScreen(name="view_projects"))
            sm.add_widget(MapScreen(name="mapa"))

            # Configure GPS como no exemplo oficial
            try:
                # Configure GPS
                self.gps_manager.configure_gps()
            except NotImplementedError:
                logging.warning("GPS não implementado para esta plataforma")

            return sm
        except Exception as e:
            logging.exception("Erro ao construir o aplicativo")
            raise

    def request_android_permissions(self):
        """Request location permissions for Android"""
        if platform == "android":
            from android.permissions import Permission, request_permissions

            def callback(permissions, results):
                if all([res for res in results]):
                    logging.info("Location permissions granted.")
                else:
                    logging.warning("Some location permissions refused.")

            request_permissions(
                [
                    Permission.ACCESS_COARSE_LOCATION,
                    Permission.ACCESS_FINE_LOCATION,
                    Permission.CAMERA,
                ],
                callback,
            )

    def entrar(self):
        logging.debug("Mudando para tela de perfil")
        self.root.current = "profile"

    def mudar_para_welcome(self):
        logging.debug("Mudando para tela welcome")
        self.root.current = "welcome"

    def mudar_para_perfil(self):
        logging.debug("Mudando para tela de perfil")
        self.root.current = "profile"

    def mudar_para_add_projeto(self):
        logging.debug("Mudando para tela de adicionar projeto")
        self.root.current = "add_project"

    def mudar_para_ver_projetos(self):
        logging.debug("Mudando para tela de ver projetos")
        try:
            self.root.current = "view_projects"
            view_projects_screen = self.root.get_screen("view_projects")
            view_projects_screen.atualizar_lista_projetos()

        except Exception as e:
            logging.exception("Erro ao mudar para tela de ver projetos")

    def sair(self):
        logging.info("Saindo do aplicativo")
        self.stop()

    def mostrar_mensagem(self, titulo, mensagem, fechar_em=None):
        """
        Mostra (ou atualiza) um popup.
        - fechar_em: segundos para fechar automaticamente; se None, fica aberto.
        """
        try:
            # Se já existe, só atualiza título e texto --------------------------
            if hasattr(self, "_popup") and self._popup:
                self._popup.title = titulo
                self._label.text = mensagem
            else:
                # Cria popup apenas uma vez -------------------------------------
                layout = BoxLayout(orientation="vertical", spacing=10, padding=10)
                self._label = Label(text=mensagem, size_hint_y=0.7)
                btn_fechar = Button(text="OK", size_hint_y=0.3)

                self._popup = Popup(
                    title=titulo,
                    content=layout,
                    size_hint=(0.8, 0.4),
                    auto_dismiss=False,
                )

                btn_fechar.bind(on_release=self._popup.dismiss)
                layout.add_widget(self._label)
                layout.add_widget(btn_fechar)
                self._popup.open()

            # Fechamento automático (opcional) ----------------------------------
            if fechar_em is not None:
                # cancela agendamento anterior, se houver
                if hasattr(self, "_popup_ev") and self._popup_ev:
                    self._popup_ev.cancel()
                self._popup_ev = Clock.schedule_once(
                    lambda *_: self._fechar_popup(), fechar_em
                )

        except Exception:
            logging.exception("Erro ao exibir popup de mensagem")

    def _fechar_popup(self, *args):
        if hasattr(self, "_popup") and self._popup:
            self._popup.dismiss()
            self._popup = None

    def get_text_safe(self, ids, nome):
        widget = getattr(ids, nome, None)
        return widget.text if widget else ""

    def capturar_coordenadas(self):
        self.gps_manager.capturar_coordenadas()

    def on_location(self, **kwargs):
        self.gps_manager.on_location(**kwargs)

    def on_status(self, stype, status):
        self.gps_manager.on_status(stype, status)

    def on_pause(self):
        self.gps_manager.stop_gps()
        return True

    def on_resume(self):
        # Se quiser retomar, descomente e ajuste para o método certo:
        self.gps_manager.capturar_coordenadas()
        pass

    def salvar_projeto(self):
        add_project_screen = self.root.get_screen("add_project")
        add_project_screen.salvar_projeto()

    def exportar_projeto_pdf(self, projeto):
        """
        Gera PDF em memória e abre picker ACTION_CREATE_DOCUMENT
        para o usuário escolher onde salvar.
        """
        if platform == "android":
            from android import activity
            from jnius import autoclass

            # Gerar bytes do PDF
            pdf_bytes = self.pdf_exporter.export_bytes(projeto)
            if not pdf_bytes:
                self.mostrar_mensagem("Erro", "Falha ao gerar PDF")
                return

            # Prepara intent para salvar via SAF
            nome = f"{projeto.get('nome_projeto','projeto')}_{datetime.now():%Y%m%d_%H%M%S}.pdf"
            Intent = autoclass("android.content.Intent")
            intent = Intent(Intent.ACTION_CREATE_DOCUMENT)
            intent.addCategory(Intent.CATEGORY_OPENABLE)
            intent.setType("application/pdf")
            intent.putExtra(Intent.EXTRA_TITLE, nome)

            # Guarda dados para escrever após o retorno
            self._pending_pdf = (pdf_bytes, nome)

            # Dispara picker
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            activity = PythonActivity.mActivity
            activity.startActivityForResult(intent, CREATE_PDF)

            return

        self.mostrar_mensagem("Erro", "Função disponível apenas no Android")
        return None

    def on_activity_result(self, requestCode, resultCode, intent):
        """
        Captura o URI selecionado e grava o PDF via ContentResolver.openOutputStream(uri).
        """
        if platform == "android":
            from android import activity
            from jnius import autoclass

            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            Activity = autoclass("android.app.Activity")
            if requestCode == CREATE_PDF and resultCode == Activity.RESULT_OK:
                uri = intent.getData()
                if uri and self._pending_pdf:
                    pdf_bytes, nome = self._pending_pdf
                    try:
                        resolver = PythonActivity.mActivity.getContentResolver()
                        out = resolver.openOutputStream(uri)
                        out.write(pdf_bytes)
                        out.close()
                        self.mostrar_mensagem("sucesso", f"PDF salvo como {nome}")
                    except Exception as e:
                        logging.exception("Erro ao gravar PDF via SAF")
                        self.mostrar_mensagem("Erro", f"Falha ao salvar o PDF: {e}")
                self._pending_pdf = None

    # Add these methods to the MyApp class
    def mudar_para_mapa(self):
        """Navega para a tela de mapa"""
        try:
            # Capturar coordenadas GPS atuais antes de mostrar o mapa
            self.gps_manager.capturar_coordenadas()

            # Mudar para a tela de mapa
            self.root.current = "mapa"
        except Exception as e:
            logging.exception("Erro ao abrir mapa")
            self.mostrar_mensagem("Erro", f"Falha ao abrir mapa: {e}")


if __name__ == "__main__":
    try:
        MyApp().run()
    except Exception as e:
        logging.exception("Erro fatal ao iniciar o aplicativo")
