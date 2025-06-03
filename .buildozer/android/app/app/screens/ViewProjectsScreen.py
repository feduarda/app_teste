import logging

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen


class ProjetoCard(BoxLayout):
    def __init__(self, projeto, **kwargs):
        super().__init__(**kwargs)
        # Armazenar projeto para uso nos eventos de botão
        self.projeto = projeto

        # Atualizar as labels com os dados do projeto
        self.ids.label_nome.text = f"Projeto: {projeto.get('nome_projeto', 'N/A')}"
        self.ids.label_responsavel.text = (
            f"Responsável: {projeto.get('responsavel', 'N/A')}"
        )
        self.ids.label_data_hora.text = (
            f"Data: {projeto.get('data', 'N/A')} | Hora: {projeto.get('hora', 'N/A')}"
        )

    def download_pdf(self, instance):
        """Método simplificado para download direto como PDF"""
        try:
            app = App.get_running_app()
            app.exportar_projeto_pdf(self.projeto)
        except Exception as e:
            logging.exception("Erro ao fazer download do projeto como PDF")
            app = App.get_running_app()
            app.mostrar_mensagem("Erro", f"Falha ao exportar o projeto: {str(e)}")

    def delete_projeto(self, instance):
        box = BoxLayout(orientation="vertical", padding=10, spacing=10)
        box.add_widget(Label(text="Tem certeza que deseja excluir este projeto?"))

        btns = BoxLayout(size_hint_y=None, height=40, spacing=10)
        btn_confirmar = Button(text="Sim", background_color=(1, 0, 0, 1))
        btn_cancelar = Button(text="Cancelar")

        popup = Popup(title="Confirmar Exclusão", content=box, size_hint=(0.8, 0.4))
        btns.add_widget(btn_cancelar)
        btns.add_widget(btn_confirmar)
        box.add_widget(btns)

        def confirmar_exclusao(_):
            app = App.get_running_app()
            nome = self.projeto.get("nome_projeto")  # ou use um ID, se houver
            sucesso, msg = app.project_manager.excluir_projeto(nome)
            popup.dismiss()

            if sucesso:
                app.mostrar_mensagem("Projeto Excluído", msg)
                app.mudar_para_ver_projetos()
            else:
                app.mostrar_mensagem("Erro", msg)

        btn_confirmar.bind(on_press=confirmar_exclusao)
        btn_cancelar.bind(on_press=lambda _: popup.dismiss())
        popup.open()


class ViewProjectsScreen(Screen):
    def on_enter(self):
        """Método chamado automaticamente quando a tela é exibida"""
        self.atualizar_lista_projetos()

    def atualizar_lista_projetos(self):
        """Atualiza a lista de projetos na interface"""
        try:
            # Limpa o container de projetos
            container = self.ids.projetos_container
            container.clear_widgets()

            # Obtém a referência do aplicativo e acessa a lista de projetos
            app = App.get_running_app()
            projetos = app.project_manager.projetos

            if not projetos:
                # Se não houver projetos cadastrados
                container.add_widget(
                    Label(text="Nenhum projeto cadastrado", size_hint_y=None, height=40)
                )
                return

            # Adiciona cada projeto à lista
            for projeto in projetos:
                container.add_widget(ProjetoCard(projeto))

        except Exception as e:
            logging.exception("Erro ao atualizar lista de projetos")
            app = App.get_running_app()
            app.mostrar_mensagem(
                "Erro", f"Falha ao carregar a lista de projetos: {str(e)}"
            )
