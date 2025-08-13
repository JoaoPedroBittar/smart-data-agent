import streamlit as st
import plotly.express as px
import pandas as pd
from typing import Optional

class FormattingAgent:
    """
    Agente responsável por formatar e apresentar os resultados obtidos
    do Agente 2 de forma amigável para o usuário final.
    
    Este é o "Agente 3" do fluxo de orquestração:
      - Entrada: DataFrame + tipo de visualização (opcional)
      - Saída: Exibição no Streamlit (tabela, métrica ou gráfico interativo)
    """

    @staticmethod
    def format_response(df: pd.DataFrame, visualization: Optional[str] = None):
        """
        Formata a resposta com base no DataFrame e no tipo de visualização.
        
        - Se o DataFrame estiver vazio → mostra aviso.
        - Se houver 1 linha e 1 coluna → mostra como métrica.
        - Caso contrário → exibe tabela e, se solicitado, gera visualização.
        
        Args:
            df (pd.DataFrame): Dados retornados do Agente 2
            visualization (Optional[str]): Tipo de visualização (pie, bar, line, etc.)
        """
        # Verifica se o DataFrame está vazio, se sim, exibe aviso e retorna
        if df.empty:
            st.warning("Nenhum resultado encontrado")
            return

        # Caso especial: se o DataFrame tem apenas 1 linha e 1 coluna, mostra métrica simples
        if df.shape == (1, 1):
            valor = df.iloc[0, 0]  # pega o único valor
            st.metric("Resultado", f"{valor:,}")  # formata número com vírgulas e exibe
            return

        # Ajuste de nome de coluna, caso específico para "total_reclamacoes"
        if "total_reclamacoes" in df.columns:
            df = df.rename(columns={"total_reclamacoes": "Total de Reclamações"})
        
        # Exibe os dados completos dentro de um expansor (seção recolhível)
        with st.expander("📋 Dados Completos", expanded=True):
            st.dataframe(df, use_container_width=True)  # tabela responsiva

        # Se um tipo de visualização foi passado, gera o gráfico correspondente
        if visualization:
            FormattingAgent._generate_visualization(df, visualization)

    @staticmethod
    def _generate_visualization(df: pd.DataFrame, vis_type: str):
        """
        Gera visualização interativa com Plotly de acordo com o tipo informado.
        
        - Atualmente implementado: gráfico de pizza.
        - Pode ser expandido para barras, linhas, etc.
        
        Args:
            df (pd.DataFrame): Dados já tratados
            vis_type (str): Tipo de visualização (ex: 'pie')
        """
        try:
            if vis_type == "pie":
                # Validação: gráfico de pizza requer pelo menos 2 colunas (categoria e valor)
                if len(df.columns) < 2:
                    st.error("""
                    **Dados insuficientes para gráfico de pizza**
                    - Necessário: 1 coluna de categorias + 1 coluna numérica
                    - Exemplo SQL correto:
                    ```sql
                    SELECT canal, COUNT(*) as total 
                    FROM suporte 
                    WHERE resolvido = 0 
                    GROUP BY canal
                    ```
                    """)
                    return

                # Cria o gráfico de pizza tipo "donut" com Plotly Express
                fig = px.pie(
                    df,
                    names=df.columns[0],       # coluna para categorias (labels)
                    values=df.columns[1],      # coluna para valores numéricos
                    title="Reclamações Não Resolvidas por Canal",
                    hole=0.3,                  # cria um donut (buraco no centro)
                    hover_data=[df.columns[1]] # mostra valor ao passar o mouse
                )

                # Personaliza o texto dentro do gráfico e o tooltip
                fig.update_traces(
                    textinfo='percent+label',  # mostra % e nome da categoria
                    hovertemplate="<b>%{label}</b><br>%{value} reclamações (%{percent})"
                )

                # Exibe o gráfico dentro do Streamlit responsivamente
                st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            # Se houver erro ao gerar o gráfico, mostra mensagem de erro
            st.error(f"Erro ao gerar visualização: {str(e)}")
