import ollama
import logging
from typing import List, Dict, Optional
import json

logger = logging.getLogger(__name__)


class AIResponseGenerator:
    """Gerador de respostas usando IA local (Ollama) para melhorar as respostas do sistema D&D."""

    def __init__(self, model_name: str = "llama3.2:3b"):
        """
        Inicializa o gerador de respostas IA.

        Args:
            model_name: Nome do modelo Ollama (padrão: llama3.2:3b - modelo leve e rápido)
        """
        self.model_name = model_name
        self.available = self._check_ollama_availability()

    def _check_ollama_availability(self) -> bool:
        """Verifica se o Ollama está disponível e funcionando."""
        try:
            # Tenta listar os modelos disponíveis
            models = ollama.list()
            models_list = models.get('models', [])
            logger.info(f"Ollama disponível com {len(models_list)} modelos")
            return True
        except Exception as e:
            logger.warning(f"Ollama não disponível: {e}")
            return False

    def _ensure_model_available(self) -> bool:
        """Garante que o modelo necessário está disponível."""
        try:
            models = ollama.list()
            models_list = models.get('models', [])
            model_names = []

            for model in models_list:
                # Tenta diferentes estruturas de resposta
                if isinstance(model, dict):
                    name = model.get('name') or model.get(
                        'model') or model.get('id')
                    if name:
                        model_names.append(name)
                elif isinstance(model, str):
                    model_names.append(model)

            if self.model_name in model_names:
                return True

            # Tenta baixar o modelo se não estiver disponível
            logger.info(f"Baixando modelo {self.model_name}...")
            ollama.pull(self.model_name)
            logger.info(f"Modelo {self.model_name} baixado com sucesso")
            return True

        except Exception as e:
            logger.error(f"Erro ao garantir modelo disponível: {e}")
            return False

    def generate_response(self, query: str, search_results: List[Dict], language: str = "pt") -> str:
        """
        Gera uma resposta elaborada usando IA baseada nos resultados da busca.

        Args:
            query: Pergunta original do usuário
            search_results: Resultados da busca semântica
            language: Idioma da resposta (pt/en)

        Returns:
            Resposta elaborada pela IA ou fallback se IA não disponível
        """
        if not self.available:
            return self._generate_fallback_response(search_results, language)

        if not self._ensure_model_available():
            return self._generate_fallback_response(search_results, language)

        try:
            prompt = self._build_prompt(query, search_results, language)

            response = ollama.chat(
                model=self.model_name,
                messages=[{
                    'role': 'user',
                    'content': prompt
                }],
                options={
                    'temperature': 0.3,  # Respostas mais consistentes
                    'top_p': 0.8,
                    'max_tokens': 1000
                }
            )

            ai_response = response['message']['content'].strip()
            logger.info(
                f"Resposta IA gerada com sucesso ({len(ai_response)} chars)")
            return ai_response

        except Exception as e:
            logger.error(f"Erro ao gerar resposta IA: {e}")
            return self._generate_fallback_response(search_results, language)

    def _build_prompt(self, query: str, search_results: List[Dict], language: str) -> str:
        """Constrói o prompt para a IA baseado na consulta e resultados."""

        # Prepara os trechos encontrados
        context_pieces = []
        # Máximo 5 resultados
        for i, result in enumerate(search_results[:5], 1):
            metadata = result.get('metadata', {})
            text = result.get('text', '')
            score = result.get('score', 0)

            book_filename = metadata.get('book_filename', 'Livro desconhecido')
            page_number = metadata.get('page_number', '?')

            # Remove extensão .pdf do nome do livro
            book = book_filename.replace(
                '.pdf', '') if book_filename else 'Livro desconhecido'

            context_pieces.append(f"""
Trecho {i} (relevância: {score:.2f}):
Fonte: {book}, página {page_number}
Conteúdo: {text}
""")

        context = "\n".join(context_pieces)

        if language == "pt":
            prompt = f"""Você é um assistente especialista em Dungeons & Dragons 5ª edição. Analise os trechos fornecidos e responda à pergunta do usuário.

PERGUNTA: {query}

TRECHOS DOS LIVROS D&D 5E:
{context}

INSTRUÇÕES CRÍTICAS:
1. Se perguntarem sobre TRUQUES/CANTRIPS de uma classe:
   - Procure por listas de magias de nível 0
   - Liste CADA truque encontrado em formato numerado
   - Inclua escola de magia se mencionada
   - Inclua descrição básica se disponível

2. Se perguntarem sobre MAGIAS:
   - Liste nome, nível, escola, componentes, alcance, duração
   - Use formato numerado sempre

3. Se perguntarem sobre REGRAS:
   - Cite valores exatos (CA, PV, dano, CD)
   - Mencione modificadores específicos

4. SEMPRE baseie-se EXCLUSIVAMENTE nos trechos fornecidos
5. Se não encontrar a informação específica, diga: "Nos trechos disponíveis não encontrei uma lista completa de [assunto]"
6. Use linguagem técnica de D&D 5e
7. Responda em português brasileiro

EXEMPLO DE RESPOSTA PARA TRUQUES:
"Truques do Mago encontrados nos trechos:
1. [Nome do Truque] - [Escola] - [Descrição breve]
2. [Nome do Truque] - [Escola] - [Descrição breve]"

RESPOSTA:"""
        else:
            prompt = f"""You are a D&D 5th edition expert assistant. Analyze the provided excerpts and answer the user's question.

QUESTION: {query}

D&D 5E BOOK EXCERPTS:
{context}

CRITICAL INSTRUCTIONS:
1. If asked about CANTRIPS for a class:
   - Look for 0-level spell lists
   - List EACH cantrip found in numbered format
   - Include school of magic if mentioned
   - Include basic description if available

2. If asked about SPELLS:
   - List name, level, school, components, range, duration
   - Always use numbered format

3. If asked about RULES:
   - Cite exact values (AC, HP, damage, DC)
   - Mention specific modifiers

4. ALWAYS base answers EXCLUSIVELY on provided excerpts
5. If specific information not found, say: "In the available excerpts I didn't find a complete list of [topic]"
6. Use technical D&D 5e language
7. Answer in English

EXAMPLE RESPONSE FOR CANTRIPS:
"Wizard Cantrips found in excerpts:
1. [Cantrip Name] - [School] - [Brief description]
2. [Cantrip Name] - [School] - [Brief description]"

ANSWER:"""

        return prompt

    def _generate_fallback_response(self, search_results: List[Dict], language: str) -> str:
        """Gera uma resposta simples quando IA não está disponível."""
        if not search_results:
            if language == "pt":
                return "Não encontrei informações relevantes nos livros indexados."
            else:
                return "I couldn't find relevant information in the indexed books."

        # Pega o melhor resultado
        best_result = search_results[0]
        text = best_result.get('text', '')
        source = best_result.get('metadata', {})
        book = source.get('book', 'Livro desconhecido')
        page = source.get('page', '?')

        if language == "pt":
            return f"""Encontrei esta informação relevante:

{text[:800]}{'...' if len(text) > 800 else ''}

**Fonte:** {book} (página {page})

*Nota: Para respostas mais elaboradas, instale e configure o Ollama.*"""
        else:
            return f"""I found this relevant information:

{text[:800]}{'...' if len(text) > 800 else ''}

**Source:** {book} (page {page})

*Note: For more elaborate answers, install and configure Ollama.*"""

    def get_status(self) -> Dict:
        """Retorna status do sistema IA."""
        status = {
            "available": self.available,
            "model": self.model_name
        }

        if self.available:
            try:
                models = ollama.list()
                models_list = models.get('models', [])
                model_names = []

                for model in models_list:
                    if isinstance(model, dict):
                        name = model.get('name') or model.get(
                            'model') or model.get('id')
                        if name:
                            model_names.append(name)
                    elif isinstance(model, str):
                        model_names.append(model)

                status["installed_models"] = model_names
            except:
                status["installed_models"] = []

        return status
