import requests
from config import OLLAMA_PORT

def check_ollama_connection() -> bool:
    """
    Função para verificar se o servidor Ollama (responsável pelo LLM local)
    está respondendo corretamente na porta configurada.

    Returns:
        bool: True se o servidor responder com status 200 (OK), False caso contrário.
    """
    try:
        # Faz uma requisição GET simples para a URL base do servidor Ollama
        # O timeout de 10 segundos evita que a aplicação trave caso o servidor esteja desligado ou inacessível
        response = requests.get(f"http://localhost:{OLLAMA_PORT}", timeout=10)

        # Retorna True se o servidor respondeu com status HTTP 200 (OK)
        return response.status_code == 200

    except Exception:
        # Qualquer exceção (ex: erro de conexão, timeout, etc.) será tratada aqui e retorna False
        return False


