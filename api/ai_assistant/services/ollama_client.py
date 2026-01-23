"""
Cliente HTTP para comunicação com Ollama.

Envia prompts estruturados e recebe respostas em linguagem natural.
"""
import os
import logging
from typing import Dict, Any, List, Optional

import requests
from requests.exceptions import RequestException, Timeout


logger = logging.getLogger(__name__)


class OllamaClient:
    """
    Cliente para API do Ollama.

    Usa o endpoint /api/chat para gerar respostas em linguagem natural.
    """

    DEFAULT_HOST = 'http://localhost:11434'
    DEFAULT_MODEL = 'llama3.2'
    DEFAULT_TIMEOUT = 120  # segundos

    def __init__(
        self,
        host: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None
    ):
        """
        Inicializa o cliente Ollama.

        Args:
            host: URL do servidor Ollama (default: localhost:11434)
            model: Modelo a ser usado (default: llama3.2)
            timeout: Timeout em segundos (default: 120)
        """
        self.host = host or os.getenv('OLLAMA_HOST', self.DEFAULT_HOST)
        self.model = model or os.getenv('OLLAMA_MODEL', self.DEFAULT_MODEL)
        self.timeout = timeout or int(os.getenv('OLLAMA_TIMEOUT', self.DEFAULT_TIMEOUT))

    def generate_response(
        self,
        query_description: str,
        data: List[Dict[str, Any]],
        display_type: str,
        module: str
    ) -> str:
        """
        Gera resposta em linguagem natural usando Ollama.

        Args:
            query_description: Descrição do que foi consultado
            data: Dados retornados pela query
            display_type: Tipo de exibição (text, table, list, currency, password)
            module: Módulo consultado

        Returns:
            Resposta em português brasileiro
        """
        prompt = self._build_prompt(query_description, data, display_type, module)

        try:
            response = requests.post(
                f'{self.host}/api/chat',
                json={
                    'model': self.model,
                    'messages': [
                        {
                            'role': 'system',
                            'content': self._get_system_prompt()
                        },
                        {
                            'role': 'user',
                            'content': prompt
                        }
                    ],
                    'stream': False,
                    'options': {
                        'temperature': 0.7,
                        'num_predict': 500,
                    }
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()

            return result.get('message', {}).get('content', 'Não foi possível gerar uma resposta.')

        except Timeout:
            logger.error(f"Ollama timeout after {self.timeout}s")
            return self._fallback_response(query_description, data, display_type)
        except RequestException as e:
            logger.error(f"Ollama request error: {e}")
            return self._fallback_response(query_description, data, display_type)
        except Exception as e:
            logger.error(f"Ollama unexpected error: {e}")
            return self._fallback_response(query_description, data, display_type)

    def _get_system_prompt(self) -> str:
        """Retorna o prompt de sistema para o Ollama."""
        return """Você é um assistente financeiro pessoal amigável e prestativo.
Suas respostas devem ser:
- Em português brasileiro
- Naturais e conversacionais
- Concisas mas informativas
- Formatadas de forma clara

Para valores monetários:
- Use o formato R$ X.XXX,XX
- Arredonde para 2 casas decimais
- Destaque valores importantes

Para datas:
- Use formato brasileiro (DD/MM/AAAA)
- Mencione "hoje", "ontem", "esta semana" quando apropriado

Para listas e tabelas:
- Organize de forma clara
- Use bullet points quando apropriado
- Destaque itens importantes

Nunca invente dados. Use apenas as informações fornecidas.
Se não houver dados, diga que não encontrou registros."""

    def _build_prompt(
        self,
        query_description: str,
        data: List[Dict[str, Any]],
        display_type: str,
        module: str
    ) -> str:
        """Constrói o prompt estruturado com XML tags."""
        # Formata os dados de acordo com o tipo
        if not data:
            data_str = "Nenhum registro encontrado."
        elif display_type == 'currency':
            # Para valores monetários, formata como moeda
            data_str = self._format_currency_data(data)
        elif display_type == 'password':
            # Para senhas, formata de forma segura
            data_str = self._format_password_data(data)
        else:
            # Para outros tipos, formata como lista/tabela
            data_str = self._format_general_data(data)

        return f"""<context>
O usuário fez uma pergunta sobre {self._get_module_description(module)}.
Consulta realizada: {query_description}
</context>

<data>
{data_str}
</data>

<instruction>
Transforme os dados acima em uma resposta natural e amigável em português.
{"Formate valores monetários como R$ X.XXX,XX." if display_type == 'currency' else ""}
{"IMPORTANTE: Não revele senhas completas diretamente. Apenas confirme que encontrou a credencial." if display_type == 'password' else ""}
Se não houver dados, informe educadamente que não encontrou registros.
</instruction>"""

    def _get_module_description(self, module: str) -> str:
        """Retorna descrição amigável do módulo."""
        descriptions = {
            'revenues': 'receitas e faturamento',
            'expenses': 'despesas e gastos',
            'accounts': 'contas bancárias e saldos',
            'credit_cards': 'cartões de crédito',
            'loans': 'empréstimos',
            'library': 'biblioteca pessoal e leituras',
            'personal_planning': 'planejamento pessoal e tarefas',
            'security': 'senhas e credenciais',
            'vaults': 'cofres e reservas',
            'transfers': 'transferências',
            'unknown': 'dados gerais'
        }
        return descriptions.get(module, 'dados gerais')

    def _format_currency_data(self, data: List[Dict[str, Any]]) -> str:
        """Formata dados monetários."""
        if not data:
            return "Nenhum valor encontrado."

        lines = []
        for item in data:
            parts = []
            for key, value in item.items():
                if isinstance(value, (int, float)):
                    # Formata como moeda brasileira
                    formatted = f"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                    parts.append(f"{key}: {formatted}")
                else:
                    parts.append(f"{key}: {value}")
            lines.append(" | ".join(parts))

        return "\n".join(lines)

    def _format_password_data(self, data: List[Dict[str, Any]]) -> str:
        """Formata dados de senhas (ocultando parcialmente)."""
        if not data:
            return "Nenhuma credencial encontrada."

        lines = []
        for item in data:
            titulo = item.get('titulo', item.get('title', 'N/A'))
            usuario = item.get('usuario', item.get('username', 'N/A'))
            site = item.get('site', 'N/A')
            senha = item.get('senha', '')

            # Mascara a senha parcialmente
            if senha and len(senha) > 4:
                senha_masked = senha[:2] + '*' * (len(senha) - 4) + senha[-2:]
            elif senha:
                senha_masked = '*' * len(senha)
            else:
                senha_masked = '***'

            lines.append(f"- {titulo}: usuário={usuario}, site={site}, senha={senha_masked}")

        return "\n".join(lines)

    def _format_general_data(self, data: List[Dict[str, Any]]) -> str:
        """Formata dados gerais como lista."""
        if not data:
            return "Nenhum registro encontrado."

        lines = []
        for i, item in enumerate(data, 1):
            parts = []
            for key, value in item.items():
                if value is not None:
                    if isinstance(value, (int, float)) and 'valor' in key.lower():
                        formatted = f"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                        parts.append(f"{key}: {formatted}")
                    else:
                        parts.append(f"{key}: {value}")
            lines.append(f"{i}. " + " | ".join(parts))

        return "\n".join(lines)

    def _fallback_response(
        self,
        query_description: str,
        data: List[Dict[str, Any]],
        display_type: str
    ) -> str:
        """
        Resposta de fallback quando Ollama não está disponível.

        Gera uma resposta básica sem IA.
        """
        if not data:
            return f"Não encontrei registros para: {query_description}"

        if display_type == 'currency':
            # Tenta extrair o valor total
            for item in data:
                for key, value in item.items():
                    if 'total' in key.lower() or 'saldo' in key.lower():
                        if isinstance(value, (int, float)):
                            formatted = f"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                            return f"{query_description}: {formatted}"

        if display_type == 'password':
            count = len(data)
            return f"Encontrei {count} credencial(is) correspondente(s). Por segurança, acesse o módulo de Segurança para ver os detalhes."

        # Resposta genérica
        count = len(data)
        return f"{query_description}: encontrados {count} registro(s)."

    def check_health(self) -> bool:
        """
        Verifica se o Ollama está disponível.

        Returns:
            True se Ollama está respondendo, False caso contrário
        """
        try:
            response = requests.get(f'{self.host}/api/tags', timeout=5)
            return response.status_code == 200
        except Exception:
            return False
