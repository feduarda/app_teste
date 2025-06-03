import logging
from datetime import datetime

from kivy.app import App
from kivy.uix.screenmanager import Screen


class AddProjectScreen(Screen):
    def on_pre_enter(self):
        data_hoje = datetime.now().strftime("%d/%m/%Y")
        hora_agora = datetime.now().strftime("%H:%M")
        self.ids.data.text = data_hoje
        self.ids.hora.text = hora_agora

    def mostrar_campos_segmento(self):
        segmento = self.ids.segmento.text

        geografia_ids = [
            "geologia",
            "uso_solo",
            "hidrografia",
            "erosao",
            "compactacao_solo",
            "vegetacao",
            "observacoes_geografia",
        ]
        # Campos que SEMPRE aparecem quando o segmento for Agricultura
        agricultura_ids = [
            "pulverizacao",
            "cultura",
            "estagio",
            "ndvi",
            "anomalia",
            "observacoes_agricultura",
        ]
        topografia_ids = [
            "tipo_voo",
            "inclinacao",
            "altitude",
            "datum",
            "observacoes_topografia",
        ]

        def set_visibilidade(campos, mostrar):
            for campo in campos:
                widget = self.ids[campo]
                widget.opacity = 1 if mostrar else 0
                widget.disabled = not mostrar
                widget.height = 40 if mostrar else 0

        set_visibilidade(geografia_ids, segmento == "Geografia")
        set_visibilidade(agricultura_ids, segmento == "Agricultura")
        set_visibilidade(topografia_ids, segmento == "Topografia")

    def get_text_safe(self, ids_container, campo):
        """Obtém o texto do campo de forma segura, evitando erros se o campo não existir"""
        try:
            return getattr(ids_container, campo).text
        except:
            return ""

    def salvar_projeto(self):
        logging.debug("Iniciando processo de salvar projeto")
        try:
            ids = self.ids

            # Coletar dados comuns
            dados = {
                "nome_projeto": ids.nome_projeto.text,
                "responsavel": ids.tecnico.text,
                "contato": ids.contato.text,
                "plataforma": ids.plataforma.text,
                "payload": ids.payload.text,
                "recobrimento_lateral": ids.recobrimento_lateral.text,
                "recobrimento_longitudinal": ids.recobrimento_longitudinal.text,
                "vlos": ids.vlos.text,
                "data": ids.data.text,
                "hora": ids.hora.text,
                "localizacao": ids.localizacao.text,
                "latitude": ids.latitude.text,
                "longitude": ids.longitude.text,
                "acuracia": ids.acuracia.text,
                "coordenadas": ids.coordenadas.text,
                "extensao": ids.extensao.text,
                "altura": ids.altura.text,
                "duracao": ids.duracao.text,
                "clima": ids.clima.text,
                "segmento": ids.segmento.text,
            }

            # Mapear campos específicos por segmento
            campos_por_segmento = {
                "Geografia": {
                    "direct": ["geologia", "uso_solo", "hidrografia"],
                    "safe": [
                        "erosao",
                        "compactacao_solo",
                        "vegetacao",
                        "observacoes_geografia",
                    ],
                },
                "Agricultura": {
                    "direct": ["pulverizacao", "cultura", "estagio"],
                    "safe": ["ndvi", "anomalia", "observacoes_agricultura"],
                    "pulverizacao": ["cauda", "adjuvante", "ativo"],
                },
                "Topografia": {
                    "direct": ["tipo_voo", "inclinacao", "altitude"],
                    "safe": ["datum", "observacoes_topografia"],
                },
            }

            # Adicionar campos específicos do segmento selecionado
            segmento = dados["segmento"]
            if segmento in campos_por_segmento:
                campos = campos_por_segmento[segmento]

                # Adicionar campos com acesso direto
                for campo in campos.get("direct", []):
                    dados[campo] = getattr(ids, campo).text

                # Adicionar campos com acesso seguro
                for campo in campos.get("safe", []):
                    dados[campo] = self.get_text_safe(ids, campo)

                # Caso especial para agricultura com pulverização
                if segmento == "Agricultura" and dados["pulverizacao"] == "Sim":
                    for campo in campos.get("pulverizacao", []):
                        dados[campo] = getattr(ids, campo).text

            # Obter a instância do aplicativo
            app = App.get_running_app()

            # Salvar dados do projeto
            sucesso, mensagem = app.project_manager.salvar_projeto_json(dados)
            if sucesso:
                app.mostrar_mensagem("Salvar Projeto", mensagem)
                app.mudar_para_ver_projetos()
            else:
                app.mostrar_mensagem("Erro", mensagem)
        except Exception as e:
            logging.exception("Erro ao salvar projeto")
            app = App.get_running_app()
            app.mostrar_mensagem(
                "Erro",
                "Falha ao salvar o projeto. Verifique os dados e tente novamente.",
            )