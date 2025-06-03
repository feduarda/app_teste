import logging

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.screenmanager import Screen
from kivy_garden.mapview import MapMarker, MapView


class MapScreen(Screen):
    def __init__(self, **kwargs):
        super(MapScreen, self).__init__(**kwargs)
        self.current_marker = None
        self.centralization_attempts = 0
        self.max_attempts = 4  # Número máximo de tentativas

    def on_enter(self):
        """Chamado quando a tela é exibida"""
        # Resetar contador de tentativas
        self.centralization_attempts = 0
        # Iniciar tentativas de centralização
        Clock.schedule_once(self.try_center_on_gps, 0.5)

    def try_center_on_gps(self, dt=None):
        """Tenta centralizar o mapa e agenda novas tentativas se necessário"""
        # Incrementar contador de tentativas
        self.centralization_attempts += 1
        logging.info(f"Tentativa {self.centralization_attempts} de centralizar o mapa")

        # Tentar centralizar
        success = self.center_map_on_gps()

        # Se não teve sucesso e ainda não atingiu o máximo de tentativas, tenta novamente
        if not success and self.centralization_attempts < self.max_attempts:
            # Cada nova tentativa ocorre em intervalos maiores
            delay = 1.0 * self.centralization_attempts
            logging.info(f"Agendando nova tentativa em {delay} segundos")
            Clock.schedule_once(self.try_center_on_gps, delay)

    def center_map_on_gps(self, dt=None):
        """Centraliza o mapa na localização GPS atual"""
        try:
            app = App.get_running_app()
            mapview = self.ids.mapview

            # Tentar obter as coordenadas da tela de projeto
            add_project_screen = app.root.get_screen("add_project")
            lat_text = add_project_screen.ids.latitude.text
            lon_text = add_project_screen.ids.longitude.text

            # Verificar se as coordenadas existem e são válidas
            if lat_text and lon_text and lat_text.strip() and lon_text.strip():
                try:
                    lat = float(lat_text)
                    lon = float(lon_text)

                    # Verificar se são coordenadas válidas
                    if lat != 0 and lon != 0:
                        logging.info(f"Centralizando mapa em: {lat}, {lon}")
                        # Definir zoom apropriado para visualização
                        mapview.zoom = 15
                        # Centralizar o mapa
                        mapview.center_on(lat, lon)
                        # Atualizar o marcador
                        self.update_marker(lat, lon)
                        return True
                except ValueError:
                    logging.warning("Coordenadas inválidas")

            # Se chegou aqui, não conseguiu centralizar
            logging.info("Não há coordenadas válidas disponíveis ainda")
            return False

        except Exception as e:
            logging.exception(f"Erro ao centralizar mapa: {e}")
            return False

    def update_marker(self, lat, lon):
        """Atualiza o marcador no mapa"""
        try:
            mapview = self.ids.mapview

            # Remover marcador anterior, se existir
            if self.current_marker:
                mapview.remove_marker(self.current_marker)

            # Adicionar novo marcador
            self.current_marker = MapMarker(lat=lat, lon=lon)
            mapview.add_marker(self.current_marker)
            logging.info(f"Marcador adicionado em: {lat}, {lon}")
        except Exception as e:
            logging.exception(f"Erro ao atualizar marcador: {e}")

    def update_location(self, *args):
        """Método seguro para atualizar a localização via botão"""
        try:
            app = App.get_running_app()
            # Iniciar a captura de coordenadas GPS
            app.gps_manager.capturar_coordenadas()
            # Agendar a atualização do mapa após o tempo do warm-up do GPS (2s + margem)
            Clock.schedule_once(self.try_center_on_gps, 3)
        except Exception as e:
            logging.exception("Erro ao atualizar localização")
            app = App.get_running_app()
            app.mostrar_mensagem("Erro", f"Falha ao atualizar localização: {e}")
