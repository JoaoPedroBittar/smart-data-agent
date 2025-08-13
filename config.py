from pathlib import Path

# Configurações do Ollama (LLM local)

# Porta padrão onde o servidor Ollama está rodando localmente
OLLAMA_PORT = "11434"

# URL base para fazer requisições à API do Ollama
# Usei o localhost na porta configurada, com versão da API v1
OLLAMA_BASE_URL = f"http://localhost:{OLLAMA_PORT}/v1"

# Nome do modelo LLM padrão usado para gerar queries SQL
LLM_MODEL = "llama3"

OLLAMA_GPU_LAYERS = 10  #Ruduzindo camadas da GPU

# Tempo máximo (em segundos) para aguardar resposta do modelo LLM antes de timeout
REQUEST_TIMEOUT = 300

# Configuração do Banco de Dados SQLite

# Caminho absoluto para o arquivo do banco de dados SQLite local
# Usei pathlib.Path para maior portabilidade e evitar problemas com separadores
DB_PATH = Path(r"C:\Users\Acer\OneDrive\Documentos\desafio-automacao\utils\clientes_completo.db")

# Verifica se o arquivo do banco realmente existe antes de continuar a execução
# Isso evita erros futuros caso o banco não esteja presente ou o caminho esteja errado
if not DB_PATH.exists():
    raise FileNotFoundError(f"Arquivo do banco de dados não encontrado em: {DB_PATH}")

# Exporta o caminho como string para uso direto em funções que exigem path string
DB_PATH_STR = str(DB_PATH)
