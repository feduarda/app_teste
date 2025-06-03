import json
import logging
import os

from kivy.app import App
from kivy.event import EventDispatcher
from kivy.properties import ListProperty

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)


class ProjectManager(EventDispatcher):
    projetos = ListProperty([])

    def salvar_projeto_json(self, dados):
        try:
            self._validar_dados(dados)

            # Atualiza em memória
            self.projetos.append(dados.copy())

            # Salva no JSON
            caminho_json = os.path.join(
                App.get_running_app().user_data_dir, "projetos_salvos.json"
            )
            self._salvar_em_arquivo(dados, caminho_json)

            return True, "Projeto salvo com sucesso!"
        except ValueError as e:
            return False, str(e)
        except Exception as e:
            logging.exception("Erro ao salvar projeto no JSON")
            return False, "Erro ao salvar projeto no dispositivo."

    def _salvar_em_arquivo(self, dados, caminho_json):
        projetos = []

        if os.path.exists(caminho_json):
            with open(caminho_json, "r", encoding="utf-8") as f:
                try:
                    projetos = json.load(f)
                except json.JSONDecodeError:
                    logging.warning("Arquivo JSON inválido, começando do zero.")

        projetos.append(dados)

        with open(caminho_json, "w", encoding="utf-8") as f:
            json.dump(projetos, f, ensure_ascii=False, indent=4)
            logging.info(f"Projeto salvo no JSON: {caminho_json}")

    def carregar_projetos(self, caminho_json):
        if os.path.exists(caminho_json):
            try:
                with open(caminho_json, "r", encoding="utf-8") as f:
                    self.projetos = json.load(f)
                    logging.info(f"{len(self.projetos)} projetos carregados")
            except json.JSONDecodeError:
                logging.warning("Arquivo de projetos corrompido")
                self.projetos = []
        else:
            self.projetos = []

    def _validar_dados(self, dados):
        if not dados.get("nome_projeto"):
            raise ValueError("Nome do projeto é obrigatório")

        if len(dados.get("responsavel", "")) < 3:
            raise ValueError("Responsável deve ter pelo menos 3 caracteres")

        # Valida campos obrigatórios com base no segmento
        segmento = dados.get("segmento", "")
        if segmento == "Geografia":
            if not dados.get("geologia"):
                raise ValueError(
                    "Campo Geologia é obrigatório para o segmento Geografia"
                )
        elif segmento == "Agricultura":
            if not dados.get("cultura"):
                raise ValueError(
                    "Campo Cultura é obrigatório para o segmento Agricultura"
                )
        elif segmento == "Topografia":
            if not dados.get("tipo_voo"):
                raise ValueError(
                    "Campo Tipo de Voo é obrigatório para o segmento Topografia"
                )

    def excluir_projeto(self, id_projeto):
        """
        Remove o projeto da lista e atualiza o JSON.
        Aceita índice (int) ou nome_projeto (str).
        """
        try:
            # Caminho do JSON
            caminho_json = os.path.join(
                App.get_running_app().user_data_dir, "projetos_salvos.json"
            )

            # Carrega projetos atuais do JSON
            projetos = []
            if os.path.exists(caminho_json):
                with open(caminho_json, "r", encoding="utf-8") as f:
                    projetos = json.load(f)

            # Define critério: por índice ou por nome
            if isinstance(id_projeto, int):
                if 0 <= id_projeto < len(projetos):
                    projetos.pop(id_projeto)
                else:
                    return False, "Índice inválido."
            elif isinstance(id_projeto, str):
                projetos = [p for p in projetos if p.get("nome_projeto") != id_projeto]
            else:
                return False, "Identificador de projeto inválido."

            # Salva a lista atualizada
            with open(caminho_json, "w", encoding="utf-8") as f:
                json.dump(projetos, f, ensure_ascii=False, indent=4)

            # Atualiza a lista em memória
            self.projetos = projetos

            return True, "Projeto excluído com sucesso!"
        except Exception as e:
            logging.exception("Erro ao excluir projeto")
            return False, "Erro ao excluir o projeto."
