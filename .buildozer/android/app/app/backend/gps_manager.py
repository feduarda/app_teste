import logging
from time import time

from kivy.clock import mainthread
from kivy.utils import platform
from plyer import gps


class GPSManager:
    def __init__(self, app):
        self.app = app
        self.gps_running = False

    def configure_gps(self):
        """Configura o GPS da aplicação."""
        try:
            gps.configure(on_location=self.on_location, on_status=self.on_status)
        except NotImplementedError:
            logging.warning("GPS não implementado para esta plataforma")

    def capturar_coordenadas(self):
        try:
            logging.info("Iniciando captura de coordenadas GPS")

            if platform == "android":
                from jnius import autoclass

                Context = autoclass("android.content.Context")
                LocationManager = autoclass("android.location.LocationManager")
                PythonActivity = autoclass("org.kivy.android.PythonActivity")
                activity = PythonActivity.mActivity
                lm = activity.getSystemService(Context.LOCATION_SERVICE)

                if not lm.isProviderEnabled(LocationManager.GPS_PROVIDER):
                    self.app.mostrar_mensagem(
                        "GPS Desativado", "Ative o GPS e tente novamente."
                    )
                    return

            self.app.mostrar_mensagem("GPS", "Buscando sua localização. Aguarde...")

            self._best_fix = None
            self._start_ts = time()
            # TODO Verificar minTime
            gps.start(minTime=0, minDistance=0)
            self.gps_running = True

        except NotImplementedError:
            self.app.mostrar_mensagem("Erro", "GPS não disponível neste dispositivo")
        except Exception as e:
            logging.exception("Erro ao iniciar GPS")
            self.app.mostrar_mensagem("Erro", f"Falha ao iniciar GPS: {e}")
            if self.gps_running:
                gps.stop()
                self.gps_running = False

    def stop_gps(self):
        """Para o serviço de GPS."""
        if self.gps_running:
            gps.stop()
            self.gps_running = False

    @mainthread
    def on_location(self, **kw):
        """Recebe cada fix; após 2s escolhe o de melhor acurácia."""
        try:
            acc = kw.get("accuracy", 9999)
            logging.info(f"Fix recebido: {kw}")

            if getattr(self, "_best_fix", None) is None or acc < self._best_fix.get(
                "accuracy", 9999
            ):
                self._best_fix = kw

            if time() - self._start_ts < 2:  # warm‑up de 2 s
                return

            best = self._best_fix or kw
            add_scr = self.app.root.get_screen("add_project")
            add_scr.ids.latitude.text = str(best.get("lat", ""))
            add_scr.ids.longitude.text = str(best.get("lon", ""))
            add_scr.ids.acuracia.text = str(best.get("accuracy", ""))

            # Define o campo coordenadas como Grau Decimal (DD) automaticamente
            add_scr.ids.coordenadas.text = "Geográfica (DD)"
            self.stop_gps()
            self.app.mostrar_mensagem(
                "GPS", "Localização capturada com sucesso!", fechar_em=1
            )

        except Exception as e:
            logging.exception("Erro ao processar localização GPS")
            self.app.mostrar_mensagem("Erro", f"Falha ao processar localização: {e}")

    @mainthread
    def on_status(self, stype, status):
        logging.info(f"Status do GPS alterado: type={stype}, status={status}")
