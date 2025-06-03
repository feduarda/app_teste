# backend/exporters/pdf_exporter.py

import logging
from datetime import datetime

from fpdf import FPDF


class PDFExporter:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(
            level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
        )

    def export_bytes(self, projeto):
        """
        Gera o PDF em memória e retorna os bytes.
        Usa FPDF.output(dest='S') para obter o conteúdo como string.
        """
        try:
            # Definição explícita do formato A4 com margens reduzidas
            pdf = FPDF(format="A4")
            pdf.set_margins(10, 10, 10)  # Margens de 1cm em todos os lados
            pdf.add_page()

            # Cabeçalho com design melhorado
            self._adicionar_cabecalho(pdf, projeto)

            # Organiza os dados para exibir em duas colunas
            campos_agrupados = self._agrupar_campos(projeto)

            # Renderiza os campos em duas colunas
            self._renderizar_dados_em_colunas(pdf, campos_agrupados)

            # Adiciona rodapé
            self._adicionar_rodape(pdf)

            # Retorna bytes do PDF
            pdf_data = pdf.output(dest="S").encode("latin-1")
            self.logger.debug("PDF gerado em memória com layout em duas colunas")
            return pdf_data

        except Exception as e:
            self.logger.error(f"Erro ao gerar PDF em memória: {e}")
            return None

    def _adicionar_cabecalho(self, pdf, projeto):
        """Adiciona cabeçalho do relatório com estilo melhorado"""
        # Cabeçalho
        pdf.set_font("Helvetica", "B", 16)
        pdf.set_text_color(0, 51, 102)  # Azul escuro para o título
        pdf.cell(0, 10, f"Relatório do Projeto", 0, 1, "C")

        # Nome do projeto em destaque
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(51, 51, 51)  # Cinza escuro
        pdf.cell(0, 8, f"{projeto.get('nome_projeto', 'Sem nome')}", 0, 1, "C")

        # Data do relatório
        pdf.set_font("Helvetica", "I", 10)
        pdf.set_text_color(128, 128, 128)  # Cinza médio
        data_atual = datetime.now().strftime("%d/%m/%Y %H:%M")
        pdf.cell(0, 6, f"Gerado em: {data_atual}", 0, 1, "R")

        # Linha separadora
        pdf.set_draw_color(200, 200, 200)  # Cinza claro
        pdf.line(10, pdf.get_y() + 3, pdf.w - 10, pdf.get_y() + 3)
        pdf.ln(10)

    def _agrupar_campos(self, projeto):
        """Organiza os campos em grupos para melhor apresentação em colunas"""
        # Definir grupos de campos relacionados
        grupos = {
            "Informações Gerais": ["responsavel", "contato", "data", "hora", "clima"],
            "Especificações Técnicas": [
                "plataforma",
                "payload",
                "vlos",
                "extensao",
                "altura",
                "duracao",
            ],
            "Parâmetros de Voo": ["recobrimento_lateral", "recobrimento_longitudinal"],
            "Localização": [
                "localizacao",
                "latitude",
                "longitude",
                "acuracia",
                "coordenadas",
            ],
        }

        # Adicionar grupos específicos por segmento
        segmento = projeto.get("segmento", "")
        if segmento == "Geografia":
            grupos["Dados Geográficos"] = [
                "geologia",
                "uso_solo",
                "hidrografia",
                "erosao",
                "compactacao_solo",
                "vegetacao",
                "observacoes_geografia",
            ]
        elif segmento == "Agricultura":
            grupos["Dados Agrícolas"] = [
                "cultura",
                "estagio",
                "ndvi",
                "anomalia",
                "pulverizacao",
            ]
            if projeto.get("pulverizacao") == "Sim":
                grupos["Dados de Pulverização"] = ["cauda", "adjuvante", "ativo"]
            grupos["Observações"] = ["observacoes_agricultura"]
        elif segmento == "Topografia":
            grupos["Dados Topográficos"] = [
                "tipo_voo",
                "inclinacao",
                "altitude",
                "datum",
                "observacoes_topografia",
            ]

        # Preencher com os dados do projeto
        campos_agrupados = {}
        for titulo_grupo, campos in grupos.items():
            dados_grupo = {}
            for campo in campos:
                if campo in projeto and projeto[campo]:
                    # Formatar o nome do campo para apresentação
                    nome_formatado = campo.replace("_", " ").title()
                    dados_grupo[nome_formatado] = projeto[campo]

            if dados_grupo:
                campos_agrupados[titulo_grupo] = dados_grupo

        # Dividir em duas colunas equilibradas
        coluna1 = {}
        coluna2 = {}

        grupos_nomes = list(campos_agrupados.keys())
        total_grupos = len(grupos_nomes)

        # Dividir os grupos entre as duas colunas de forma balanceada
        for i, grupo in enumerate(grupos_nomes):
            if i < total_grupos / 2:
                coluna1[grupo] = campos_agrupados[grupo]
            else:
                coluna2[grupo] = campos_agrupados[grupo]

        return {"coluna1": coluna1, "coluna2": coluna2}

    def _renderizar_dados_em_colunas(self, pdf, campos_agrupados):
        """Renderiza os dados em duas colunas separadas"""
        # Configurações de coluna - ajustadas para formato A4 com margens de 1cm
        page_width = (
            pdf.w - 20
        )  # Largura total disponível (A4 = 210mm - 20mm de margens)
        col_width = (page_width / 2) - 5  # Largura de uma coluna com espaço entre elas

        # Posição inicial
        y_start = pdf.get_y()

        # Renderizar coluna 1
        x_col1 = 10  # Margem esquerda reduzida para 1cm
        pdf.set_xy(x_col1, y_start)
        y_max = self._renderizar_coluna(
            pdf, campos_agrupados["coluna1"], x_col1, col_width
        )

        # Renderizar coluna 2
        x_col2 = x_col1 + col_width + 10  # Posição X da segunda coluna
        pdf.set_xy(x_col2, y_start)
        y_max_col2 = self._renderizar_coluna(
            pdf, campos_agrupados["coluna2"], x_col2, col_width
        )

        # Ajustar posição Y final para o maior valor entre as duas colunas
        pdf.set_y(max(y_max, y_max_col2) + 5)

    def _renderizar_coluna(self, pdf, grupos, x_pos, col_width):
        """Renderiza os dados de uma coluna e retorna a posição Y final"""
        y_start = pdf.get_y()
        current_y = y_start

        for grupo, campos in grupos.items():
            # Definir posição para o título do grupo
            pdf.set_xy(x_pos, current_y)

            # Título do grupo
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(0, 51, 102)  # Azul escuro
            pdf.set_fill_color(240, 240, 245)  # Fundo cinza claro
            pdf.cell(col_width, 8, grupo, 0, 1, "L", True)

            current_y = pdf.get_y()

            # Campos do grupo
            pdf.set_text_color(0, 0, 0)  # Preto para texto normal
            for campo, valor in campos.items():
                # Tratamento especial para campos com nomes longos como "Recobrimento Lateral"
                campo_width = pdf.get_string_width(campo + ": ")

                # Se o nome do campo for muito longo ou o valor for longo
                if campo_width > (col_width * 0.4) or len(str(valor)) > 20:
                    # Nome do campo em uma linha separada
                    pdf.set_xy(x_pos, current_y)
                    pdf.set_font("Helvetica", "B", 10)
                    pdf.cell(col_width, 6, campo + ":", 0, 1)
                    current_y = pdf.get_y()

                    # Valor com recuo em linha separada
                    pdf.set_xy(x_pos + 5, current_y)  # Recuo para hierarquia visual
                    pdf.set_font("Helvetica", "", 10)
                    pdf.multi_cell(col_width - 5, 5, str(valor))
                    current_y = pdf.get_y() + 2  # Adiciona pequeno espaço após valor
                else:
                    # Formato padrão para campos curtos
                    pdf.set_xy(x_pos, current_y)
                    pdf.set_font("Helvetica", "B", 10)
                    pdf.cell(col_width * 0.4, 6, campo + ":", 0, 0)

                    pdf.set_font("Helvetica", "", 10)
                    pdf.cell(col_width * 0.6, 6, str(valor), 0, 1)
                    current_y = pdf.get_y()

            # Espaço entre grupos
            current_y += 3
            pdf.set_y(current_y)

        return pdf.get_y()

    def _adicionar_rodape(self, pdf):
        """Adiciona rodapé ao documento"""
        pdf.set_y(-15)
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(128, 128, 128)  # Cinza para o rodapé

        # Linha divisória
        pdf.set_draw_color(200, 200, 200)  # Cinza claro
        pdf.line(10, pdf.h - 15, pdf.w - 10, pdf.h - 15)

        # Texto do rodapé
        pdf.cell(pdf.w / 2 - 10, 10, "DataVANT - Relatório de Projeto", 0, 0, "L")
        pdf.cell(pdf.w / 2 - 10, 10, f"Página {pdf.page_no()}", 0, 0, "R")
