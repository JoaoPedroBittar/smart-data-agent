import streamlit as st
from agents.natural_language import NaturalLanguageAgent  # Agente que interpreta comandos em linguagem natural e gera SQL
from agents.data_consultant import DataConsultantAgent    # Agente que executa queries SQL e retorna dados
from agents.formatting import FormattingAgent             # Agente que formata e exibe dados (tabelas, gráficos)
from utils.ollama import check_ollama_connection          # Função para verificar se o servidor Ollama está ativo

# Função para ajustar dinamicamente a altura da text_area conforme número de linhas
def get_text_area_height(text, line_height=24, min_lines=3, max_lines=15):
    lines = text.count('\n') + 1
    lines = max(min_lines, min(lines, max_lines))
    return lines * line_height

# Configurações iniciais da página Streamlit
st.set_page_config(
    page_title="Painel Inteligente de Análise de Dados",  # Título da aba do navegador
    page_icon="🤖",                                       # Ícone da página
    layout="wide"                                         # Layout em largura total
)

def main():
    # Verifica se o servidor Ollama está rodando, se não exibe erro e para execução
    if not check_ollama_connection():
        st.error("Servidor Ollama não está respondendo. Execute: ollama serve")
        st.stop()

    # Título principal da aplicação
    st.title("🤖 Painel Inteligente de Análise de Dados")

    # Inicializa variáveis de estado da sessão caso não existam
    if "history" not in st.session_state:
        st.session_state.history = []      # Histórico de consultas feitas
    if "last_sql" not in st.session_state:
        st.session_state.last_sql = ""     # Última query SQL gerada
    if "last_df" not in st.session_state:
        st.session_state.last_df = None    # Último DataFrame resultante da consulta
    if "last_vis_type" not in st.session_state:
        st.session_state.last_vis_type = None  # Tipo de visualização para exibir o resultado
    if "user_command" not in st.session_state:
        st.session_state.user_command = ""

    # Cria a barra lateral (sidebar)
    with st.sidebar:
        st.header("📌 Exemplos Prontos")  # Cabeçalho para exemplos de consultas
        # Dicionário com exemplos para facilitar o uso
        examples = {
            "Estados com mais clientes via app em maio": "Liste os 5 estados com maior número de clientes que compraram via app em maio. Retorne a lista em formato de tabela.",
            "Clientes que interagiram com campanhas WhatsApp em 2024": "Quantos clientes interagiram com campanhas de WhatsApp em 2024?",
            "Categorias com maior média de compras por cliente": "Quais categorias de produto tiveram o maior número de compras em média por cliente?",
            "Número de reclamações não resolvidas por canal": "Qual o número de reclamações não resolvidas por canal? Retorne um gráfico de pizza."
        }
        # Cria botões para cada exemplo, ao clicar preenche o campo de consulta
        for name, query in examples.items():
            if st.button(name, help=query, use_container_width=True):
                st.session_state.user_command = query

        st.markdown("---")  # Linha separadora

        # Dicas para o usuário melhorar os comandos
        st.header("💡 Dicas para escrever comandos")
        st.markdown(
            """
            - Seja específico no que deseja saber (ex: período, canal, tipo de dado).
            - Use palavras como “gráfico de pizza”, “lista em tabela”, “top 5”, para ajudar na visualização.
            """
        )

        st.markdown("---")

        # Histórico das últimas consultas feitas pelo usuário
        st.header("🕘 Histórico de Consultas")
        if st.session_state.history:
            # Mostra as últimas 10 consultas, da mais recente para a mais antiga
            for i, item in enumerate(reversed(st.session_state.history[-10:]), 1):
                st.write(f"{i}. {item}")
        else:
            st.write("Nenhuma consulta realizada ainda.")

    # Calcula altura dinâmica da caixa de texto com base no texto atual
    height = get_text_area_height(st.session_state.get("user_command", ""))

    # Campo principal para o usuário digitar sua consulta em linguagem natural, altura dinâmica
    query = st.text_area(
        "Digite sua consulta:",
        placeholder="Ex: Total de vendas por categoria em 2024 como gráfico de pizza",
        key="user_command",
        height=height
    )

    # Botão para processar a consulta
    if st.button("▶️ Calcular e Visualizar", type="primary"):
        with st.spinner("Processando sua consulta..."):  # Exibe indicador de processamento
            # Interpreta a consulta em linguagem natural para SQL e tipo de visualização
            sql, vis_type = NaturalLanguageAgent.interpret_command(query)

            # Executa a query SQL e retorna os dados
            df = DataConsultantAgent.run_query(sql)

            # Armazena os resultados e query no estado da sessão
            st.session_state.last_sql = sql
            st.session_state.last_df = df
            st.session_state.last_vis_type = vis_type

            # Salva o texto da consulta no histórico, se não vazio
            if query.strip():
                st.session_state.history.append(query.strip())

    # Exibe os resultados da última consulta
    if st.session_state.last_df is not None:
        with st.expander("🔍 Consulta SQL Gerada", expanded=False):
            # Exibe a query SQL gerada para transparência
            st.code(st.session_state.last_sql, language="sql")

        # Caso o resultado seja vazio, avisa o usuário
        if st.session_state.last_df.empty:
            st.warning("Nenhum resultado encontrado para a consulta.")
        else:
            # Formata e exibe o resultado (tabela, gráfico etc.)
            FormattingAgent.format_response(st.session_state.last_df, st.session_state.last_vis_type)

            # Gera CSV para download dos dados
            csv = st.session_state.last_df.to_csv(index=False, decimal=",")
            st.download_button(
                "📤 Exportar CSV",
                data=csv,
                file_name="resultado.csv",
                mime="text/csv"
            )

# Executa a função principal quando o script é chamado
if __name__ == "__main__":
    main()
