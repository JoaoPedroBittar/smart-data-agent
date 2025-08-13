import sqlite3
import pandas as pd
import streamlit as st
from config import DB_PATH
from typing import Optional
import hashlib
import time

class DataConsultantAgent:
    """
    Agente responsável por executar a query SQL gerada pelo Agente 1
    no banco SQLite e retornar os dados tratados.

    Este é o "Agente 2" do fluxo de orquestração:
      - Entrada: Query SQL
      - Saída: DataFrame pronto para visualização ou análise
    """

    # Cache simples para armazenar resultados de queries recentes
    _query_cache = {}

    @staticmethod
    def run_query(query: str, visualization: Optional[str] = None) -> pd.DataFrame:
        """
        Executa a consulta SQL no banco e retorna um DataFrame processado.
        Inclui:
          - Tratamento especial para gráficos de pizza
          - Conversão robusta de valores numéricos
          - Filtragem de valores nulos/zerados
          - Cache simples para acelerar consultas repetidas
          - Validação básica para evitar queries destrutivas sem filtro

        Args:
            query (str): Instrução SQL a ser executada
            visualization (Optional[str]): Tipo de visualização (ex: 'pie', 'bar')

        Returns:
            pd.DataFrame: Resultado da consulta tratado
        """
        # Validação inicial para evitar queries inválidas ou vazias
        if not isinstance(query, str) or not query.strip():
            st.error("Consulta inválida: deve ser uma string não vazia")
            return pd.DataFrame()

        # Validação básica para prevenir execução de queries perigosas sem filtro
        forbidden_statements = ['DROP ', 'DELETE ', 'UPDATE ']
        lowered_query = query.strip().upper()
        for stmt in forbidden_statements:
            if lowered_query.startswith(stmt) and 'WHERE' not in lowered_query:
                st.error(f"Query potencialmente perigosa detectada: '{stmt.strip()}' sem cláusula WHERE. Execução abortada.")
                return pd.DataFrame()

        # Check no cache antes de executar a query
        query_hash = hashlib.md5(query.encode('utf-8')).hexdigest()
        if query_hash in DataConsultantAgent._query_cache:
            st.info("Resultado retornado do cache.")
            return DataConsultantAgent._query_cache[query_hash]

        try:
            # Conexão segura com o banco SQLite
            conn = sqlite3.connect(DB_PATH)
            df = pd.read_sql_query(query, conn)
            conn.close()

            # Se não houver resultados, retorna DataFrame vazio
            if df.empty:
                return df

            # Tratamento para gráficos (mantido + incrementado)
            if visualization == "pie" and len(df.columns) == 2:
                df = DataConsultantAgent._prepare_pie_chart_data(df)
            elif visualization:  # Novo tratamento genérico
                df = DataConsultantAgent._prepare_visualization_data(df, visualization)

            # Conversão numérica (mantido + incrementado)
            df = DataConsultantAgent._convert_numeric_columns(df)
            df = DataConsultantAgent._enhance_numeric_conversion(df)

            # Armazena resultado no cache
            DataConsultantAgent._query_cache[query_hash] = df

            return df

        except sqlite3.Error as e:
            # Erros relacionados ao banco de dados são exibidos junto da query gerada
            st.error(f"Erro no banco de dados: {str(e)}")
            st.code(query, language='sql')
            return pd.DataFrame()
        except Exception as e:
            # Erros genéricos são tratados para não quebrar a aplicação
            st.error(f"Erro inesperado: {str(e)}")
            return pd.DataFrame()

    @staticmethod
    def _prepare_pie_chart_data(df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepara dados para exibição em gráfico de pizza.
        - Garante que as colunas sejam 'categoria' e 'valor'
        - Remove linhas com valores zerados ou nulos
        - Converte strings numéricas (incluindo formatos como '1.5k') para float
        - Ordena em ordem decrescente pelo valor
        """
        # Renomeia as colunas para nomes padrão
        df.columns = ['categoria', 'valor']

        # Remove caracteres não numéricos, converte 'k' para milhar, e transforma em float
        df['valor'] = (
            df['valor'].astype(str)
            .str.replace('[^\\d.,kK]', '', regex=True)
            .replace({'k': '*1e3', 'K': '*1e3'}, regex=True)
            .map(pd.eval)
            .astype(float)
        )

        # Mantém apenas valores positivos e ordena do maior para o menor
        df = df[df['valor'] > 0].sort_values('valor', ascending=False)

        return df

    @staticmethod
    def _prepare_visualization_data(df: pd.DataFrame, vis_type: str) -> pd.DataFrame:
        """
        Novo método: Prepara dados para vários tipos de visualização
        """
        if len(df.columns) < 2:
            return df

        # Padroniza nomes para gráficos
        if len(df.columns) == 2:
            df.columns = ['categoria', 'valor']

        # Conversão numérica genérica
        if 'valor' in df.columns:
            try:
                df['valor'] = pd.to_numeric(
                    df['valor'].astype(str)
                    .str.replace('[^\\d.,]', '', regex=True)
                    .str.replace(',', '.', regex=False),
                    errors='coerce'
                )
                df = df[df['valor'].notna()]
            except:
                pass

        return df

    @staticmethod
    def _convert_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
        """
        Converte para numérico todas as colunas que parecem conter valores quantitativos.
        Critério: nome da coluna contém 'valor', 'total', 'count' ou 'soma'.
        """
        for col in df.columns:
            if any(key in col.lower() for key in ['valor', 'total', 'count', 'soma']):
                try:
                    # Tentativa de conversão direta
                    df[col] = pd.to_numeric(df[col], errors='raise')
                except:
                    # Caso falhe, aplica limpeza mais profunda
                    try:
                        df[col] = (
                            df[col].astype(str)
                            .str.replace('[^\\d.,]', '', regex=True)
                            .str.replace(',', '.', regex=False)
                            .pipe(pd.to_numeric, errors='coerce')
                        )
                    except:
                        continue

        return df

    @staticmethod
    def _enhance_numeric_conversion(df: pd.DataFrame) -> pd.DataFrame:
        """
        Novo método: Complementa a conversão numérica para mais padrões
        """
        numeric_patterns = ['valor', 'total', 'count', 'sum', 'amount', 'quant', 'soma', 'qtd', 'num']

        for col in df.columns:
            if any(pat in col.lower() for pat in numeric_patterns):
                try:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                except:
                    continue

        return df
