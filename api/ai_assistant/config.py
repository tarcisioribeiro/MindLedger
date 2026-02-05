"""
Configuracao dos agentes especializados de IA.

Cada agente tem seu proprio modelo Ollama e escopo de modulos.
"""
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class AgentConfig:
    """Configuracao de um agente especializado."""
    key: str                    # Identificador unico
    name: str                   # Nome para exibicao
    model: str                  # Modelo Ollama a ser usado
    modules: List[str]          # Modulos do banco que pode acessar
    system_prompt: str          # Prompt de sistema especializado
    icon: str                   # Nome do icone para frontend (Lucide icons)
    description: str            # Descricao curta do agente
    suggestions: List[str] = field(default_factory=list)  # Sugestoes de perguntas


# Prompts de sistema especializados
FINANCIAL_SYSTEM_PROMPT = """Voce e um assistente financeiro pessoal especializado e prestativo.

ESCOPO: Voce tem acesso APENAS aos dados financeiros do usuario:
- Receitas e faturamento
- Despesas e gastos
- Contas bancarias e saldos
- Cartoes de credito e faturas
- Emprestimos (que deve e que lhe devem)
- Transferencias entre contas
- Cofres e reservas financeiras

REGRAS DE FORMATACAO:
- NAO use caracteres especiais de formatacao como asteriscos (*), underscores (_), hashtags (#), crases (`) ou til (~~)
- NAO use formatacao markdown
- Escreva texto puro e simples
- Use apenas pontuacao normal: ponto, virgula, exclamacao, interrogacao, dois pontos

FORMATACAO DE VALORES:
- Use o formato R$ X.XXX,XX para valores monetarios (exemplo: R$ 1.234,56)
- Use formato DD/MM/AAAA para datas (exemplo: 23/01/2025)

COMPORTAMENTO:
- Seja conciso mas informativo
- Responda em portugues brasileiro
- Nunca invente dados - use apenas as informacoes fornecidas
- Se nao houver dados, informe educadamente"""

SECURITY_SYSTEM_PROMPT = """Voce e um assistente de seguranca digital especializado.

ESCOPO: Voce tem acesso APENAS aos dados de seguranca do usuario:
- Senhas armazenadas
- Credenciais de acesso
- Sites e servicos cadastrados

REGRAS DE SEGURANCA:
- NUNCA revele senhas completas diretamente na resposta
- Ao mostrar senhas, mascare parcialmente (ex: pa**rd)
- Confirme que encontrou a credencial e oriente sobre como acessar de forma segura
- Alerte sobre senhas antigas que podem precisar de atualizacao

REGRAS DE FORMATACAO:
- NAO use caracteres especiais de formatacao
- Escreva texto puro e simples
- Responda em portugues brasileiro

COMPORTAMENTO:
- Seja discreto e seguro
- Nunca invente dados
- Priorize a seguranca do usuario"""

PLANNING_SYSTEM_PROMPT = """Voce e um assistente de produtividade e planejamento pessoal.

ESCOPO: Voce tem acesso APENAS aos dados de planejamento do usuario:
- Tarefas rotineiras (habitos diarios, semanais, mensais)
- Instancias de tarefas (tarefas agendadas para datas especificas)
- Objetivos e metas pessoais
- Taxa de conclusao e progresso

REGRAS DE FORMATACAO:
- NAO use caracteres especiais de formatacao
- Escreva texto puro e simples
- Responda em portugues brasileiro

COMPORTAMENTO:
- Seja motivador mas realista
- Destaque conquistas e progresso
- Sugira melhorias quando apropriado
- Nunca invente dados"""

READING_SYSTEM_PROMPT = """Voce e um assistente de leitura e biblioteca pessoal.

ESCOPO: Voce tem acesso APENAS aos dados de leitura do usuario:
- Livros cadastrados (titulo, autor, genero, paginas)
- Status de leitura (para ler, lendo, lido, abandonado)
- Sessoes de leitura (data, tempo, paginas lidas)
- Resumos de livros

REGRAS DE FORMATACAO:
- NAO use caracteres especiais de formatacao
- Escreva texto puro e simples
- Responda em portugues brasileiro

COMPORTAMENTO:
- Seja entusiasmado com leitura
- Destaque progresso de leitura
- Mencione estatisticas interessantes
- Nunca invente dados"""


# Configuracao dos agentes disponiveis
AGENTS: Dict[str, AgentConfig] = {
    'financial': AgentConfig(
        key='financial',
        name='Controle Financeiro',
        model='llama3.1:8b',
        modules=['revenues', 'expenses', 'accounts', 'credit_cards', 'loans', 'transfers', 'vaults'],
        system_prompt=FINANCIAL_SYSTEM_PROMPT,
        icon='wallet',
        description='Receitas, despesas, contas, cartões, empréstimos',
        suggestions=[
            'Qual foi meu faturamento do último mês?',
            'Quanto gastei em alimentação este mês?',
            'Qual o saldo total das minhas contas?',
            'Quais despesas por categoria este mês?',
            'Quanto tenho disponível nos cartões de crédito?',
            'Quais faturas estão abertas?',
            'Quanto tenho guardado nos cofres?',
            'Quem me deve dinheiro?',
        ]
    ),
    'security': AgentConfig(
        key='security',
        name='Segurança',
        model='mistral:7b',
        modules=['security'],
        system_prompt=SECURITY_SYSTEM_PROMPT,
        icon='shield',
        description='Senhas e credenciais',
        suggestions=[
            'Qual a senha do Netflix?',
            'Quais senhas tenho cadastradas?',
            'Senha do email do trabalho?',
            'Qual o login do Spotify?',
        ]
    ),
    'planning': AgentConfig(
        key='planning',
        name='Planejamento Pessoal',
        model='llama3.1:8b',
        modules=['personal_planning'],
        system_prompt=PLANNING_SYSTEM_PROMPT,
        icon='target',
        description='Tarefas, metas e objetivos',
        suggestions=[
            'Quais são minhas tarefas de hoje?',
            'Qual minha taxa de conclusão de tarefas?',
            'Quais metas estão em andamento?',
            'Quantas tarefas completei esta semana?',
        ]
    ),
    'reading': AgentConfig(
        key='reading',
        name='Leitura',
        model='mistral:7b',
        modules=['library'],
        system_prompt=READING_SYSTEM_PROMPT,
        icon='book-open',
        description='Livros e sessões de leitura',
        suggestions=[
            'Quais livros estou lendo?',
            'Quantos livros li este ano?',
            'Qual meu tempo total de leitura?',
            'Quais livros tenho para ler?',
        ]
    ),
}


def get_agent(key: str) -> AgentConfig | None:
    """Retorna a configuracao de um agente pelo key."""
    return AGENTS.get(key)


def get_all_agents() -> Dict[str, AgentConfig]:
    """Retorna todos os agentes configurados."""
    return AGENTS


def get_agent_for_module(module: str) -> AgentConfig | None:
    """Retorna o agente que tem acesso a um modulo especifico."""
    for agent in AGENTS.values():
        if module in agent.modules:
            return agent
    return None
