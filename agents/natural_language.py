import time
from typing import Tuple, Optional
from openai import OpenAI
from config import OLLAMA_BASE_URL, LLM_MODEL, REQUEST_TIMEOUT
import re
import sqlite3

# Inicializa o cliente da API OpenAI (compatível com Ollama API)
client = OpenAI(
    base_url=OLLAMA_BASE_URL,
    api_key="ollama",
    timeout=REQUEST_TIMEOUT
)

class NaturalLanguageAgent:
    """
    Agente responsável por interpretar comandos em linguagem natural
    e convertê-los em consultas SQL prontas para execução no banco SQLite.
    
    Este é o "Agente 1" do fluxo de orquestração:
      - Entrada: Texto do usuário (linguagem natural)
      - Saída: Query SQL + tipo de visualização (se detectado)
    """

    @staticmethod
    def get_most_recent_year() -> str:
        from config import DB_PATH
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(strftime('%Y', data_compra)) FROM compras;")
            result = cursor.fetchone()[0]
            conn.close()
            return result if result else '2025'
        except:
            return '2025'

    @staticmethod
    def extract_month_from_command(command: str) -> Optional[str]:
        meses = {
            "janeiro": "01", "fevereiro": "02", "março": "03", "abril": "04",
            "maio": "05", "junho": "06", "julho": "07", "agosto": "08",
            "setembro": "09", "outubro": "10", "novembro": "11", "dezembro": "12"
        }
        command = command.lower()
        for nome, numero in meses.items():
            if nome in command:
                return numero

        match = re.search(r'm[eê]s\s*(\d{1,2})', command)
        if match:
            m = int(match.group(1))
            if 1 <= m <= 12:
                return f"{m:02d}"

        return None

    @staticmethod
    def interpret_command(user_command: str) -> Tuple[str, Optional[str]]:
        user_cmd = user_command.lower()
        
        # Detecta tipo de visualização
        vis_type = None
        if "gráfico" in user_cmd or "grafico" in user_cmd:
            if "pizza" in user_cmd: vis_type = "pie"
            elif "barras" in user_cmd: vis_type = "bar"
            elif "linha" in user_cmd: vis_type = "line"

        # Detecta mês e ano
        mes = NaturalLanguageAgent.extract_month_from_command(user_command)
        ano = NaturalLanguageAgent.get_most_recent_year()

        # DETECÇÃO DE TABELA AUTOMÁTICA E MÉDIAS
        tabela = None
        data_col = None
        where_cond = "1=1"
        group_by = None
        calcular_media_por_cliente = False

        if any(palavra in user_cmd for palavra in ["reclamaç", "não resolvid", "ticket"]):
            tabela = "suporte"
            data_col = "data_contato"
            where_cond = "resolvido = 0"
            group_by = "canal"
        elif any(palavra in user_cmd for palavra in ["venda", "compra", "produto"]):
            tabela = "compras"
            data_col = "data_compra"
            group_by = "categoria"
            if "média" in user_cmd or "media" in user_cmd:
                calcular_media_por_cliente = True

        # Se tabela foi detectada
        if tabela:
            if calcular_media_por_cliente:
                # Query para média de compras por cliente por categoria
                sql_query = f"""
SELECT categoria, ROUND(AVG(contagem_cliente), 2) AS media_compras_por_cliente
FROM (
    SELECT cliente_id, categoria, COUNT(*) AS contagem_cliente
    FROM {tabela}
    WHERE 1=1
"""
                if mes: sql_query += f" AND strftime('%m', {data_col}) = '{mes}'"
                if ano: sql_query += f" AND strftime('%Y', {data_col}) = '{ano}'"
                sql_query += f"""
    GROUP BY cliente_id, categoria
) AS sub
GROUP BY categoria
ORDER BY media_compras_por_cliente DESC;
                """.strip()
            else:
                # Query simples (total por grupo)
                sql_query = f"SELECT {group_by}, COUNT(*) AS total FROM {tabela} AS t WHERE {where_cond}"
                if mes: sql_query += f" AND strftime('%m', t.{data_col}) = '{mes}'"
                if ano: sql_query += f" AND strftime('%Y', t.{data_col}) = '{ano}'"
                sql_query += f"\nGROUP BY {group_by};"

            return sql_query, vis_type

        # Prompt enviado ao LLM como fallback
        prompt = f"""
[INST] <<SYS>>
Você é um especialista em SQLite. Converta a solicitação do usuário para uma query SQL válida.

TABELAS DISPONÍVEIS:
- clientes(id, nome, email, idade, cidade, estado, profissao, genero)
- compras(id, cliente_id, data_compra, valor, categoria, canal)
- suporte(id, cliente_id, data_contato, tipo_contato, resolvido, canal)
- campanhas_marketing(id, cliente_id, nome_campanha, data_envio, interagiu, canal)

Pedido: {user_command}
[/INST]
"""

        try:
            response = client.chat.completions.create(
                model=LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=500
            )

            sql_query = response.choices[0].message.content.strip()

            if "```sql" in sql_query:
                sql_query = sql_query.split("```sql")[-1].split("```")[0].strip()
            elif "```" in sql_query:
                sql_query = sql_query.split("```")[-1].split("```")[0].strip()

            # Corrigir possíveis alias
            def corrigir_query(query: str) -> str:
                query = re.sub(r'\bFROM\s+s\b', 'FROM suporte AS s', query, flags=re.IGNORECASE)
                query = re.sub(r'\bFROM\s+c\b', 'FROM clientes AS c', query, flags=re.IGNORECASE)
                if 'FROM suporte AS s' in query:
                    query = re.sub(r'\bc\.canal\b', 's.canal', query, flags=re.IGNORECASE)
                return query

            sql_query = corrigir_query(sql_query)

            if not sql_query.strip() or sql_query.strip() == "SELECT 1":
                sql_query = "SELECT 1"

            return sql_query, vis_type
        
        except Exception as e:
            fallback_sql = "SELECT 1"
            return fallback_sql, vis_type
