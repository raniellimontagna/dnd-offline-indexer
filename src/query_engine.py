from text_processor import TextProcessor
from indexer import DnDIndexer
from ai_response_generator import AIResponseGenerator
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import logging
from pathlib import Path
import json
from datetime import datetime
import os

# Desabilitar telemetria do ChromaDB
os.environ["ANONYMIZED_TELEMETRY"] = "False"

# Importa nossos módulos

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class QueryResponse:
    """Estrutura de resposta para consultas."""
    answer: str
    confidence: float
    sources: List[Dict]
    query_language: str
    processing_time: float
    found_results: int


class QueryEngine:
    """Motor de consultas inteligente para documentos de D&D."""

    def __init__(self, index_dir: str = "index", enable_ai: bool = True):
        self.indexer = DnDIndexer(index_dir)
        self.processor = TextProcessor()

        # Inicializa gerador IA se solicitado
        self.ai_generator = None
        if enable_ai:
            try:
                self.ai_generator = AIResponseGenerator()
                logger.info(f"IA habilitada: {self.ai_generator.available}")
            except Exception as e:
                logger.warning(f"Erro ao inicializar IA: {e}")

        # Templates de resposta por idioma
        self.response_templates = {
            'pt': {
                'no_results': "Desculpe, não encontrei informações sobre '{query}' nos documentos de D&D disponíveis.",
                'low_confidence': "Encontrei algumas informações que podem ser relacionadas à sua pergunta sobre '{query}', mas não tenho certeza se respondem completamente:",
                'good_confidence': "Com base nos documentos de D&D, posso responder sobre '{query}':",
                'sources_intro': "\n\n**Fontes consultadas:**",
                'source_format': "• {book} (página {page})"
            },
            'en': {
                'no_results': "Sorry, I couldn't find information about '{query}' in the available D&D documents.",
                'low_confidence': "I found some information that might be related to your question about '{query}', but I'm not sure if it fully answers it:",
                'good_confidence': "Based on the D&D documents, I can answer about '{query}':",
                'sources_intro': "\n\n**Sources consulted:**",
                'source_format': "• {book} (page {page})"
            }
        }

    def detect_query_intent(self, query: str) -> Dict[str, any]:
        """
        Analisa a intenção da consulta.

        Args:
            query: Pergunta do usuário

        Returns:
            Dicionário com análise da intenção
        """
        query_lower = query.lower()

        # Detecta idioma
        language = self.processor.detect_language(query)

        # Detecta tipo de pergunta
        intent = {
            'language': language,
            'query_type': 'general',
            'book_preference': None,
            'specific_terms': [],
            'question_words': []
        }

        # Palavras de pergunta por idioma
        question_words = {
            'pt': ['como', 'o que', 'qual', 'quando', 'onde', 'por que', 'quanto'],
            'en': ['how', 'what', 'which', 'when', 'where', 'why', 'how much', 'how many']
        }

        # Identifica palavras de pergunta
        for word in question_words.get(language, []):
            if word in query_lower:
                intent['question_words'].append(word)

        # Detecta tipos específicos de consulta
        if any(term in query_lower for term in ['regra', 'regras', 'rule', 'rules']):
            intent['query_type'] = 'rules'
        elif any(term in query_lower for term in ['truques', 'cantrips', 'cantrip', 'magia de nível 0', '0-level']):
            intent['query_type'] = 'cantrips'
        elif any(term in query_lower for term in ['magia', 'spell', 'conjuração', 'casting', 'feitiço']):
            intent['query_type'] = 'spells'
        elif any(term in query_lower for term in ['personagem', 'character', 'classe', 'class']):
            intent['query_type'] = 'character'
        elif any(term in query_lower for term in ['combate', 'combat', 'ataque', 'attack']):
            intent['query_type'] = 'combat'
        elif any(term in query_lower for term in ['monstro', 'monster', 'criatura', 'creature']):
            intent['query_type'] = 'monsters'

        # Detecta preferência por tipo de livro
        if any(term in query_lower for term in ['mestre', 'master', 'dm', 'dungeon']):
            intent['book_preference'] = 'dungeon_masters_guide'
        elif any(term in query_lower for term in ['jogador', 'player', 'phb']):
            intent['book_preference'] = 'players_handbook'

        # Extrai termos específicos de D&D
        dnd_terms = [
            # Português
            'vantagem', 'desvantagem', 'ca', 'classe de armadura', 'pv', 'pontos de vida',
            'teste de resistência', 'cd', 'rolagem', 'dado', 'd20', 'iniciativa',
            # Inglês
            'advantage', 'disadvantage', 'ac', 'armor class', 'hp', 'hit points',
            'saving throw', 'dc', 'roll', 'dice', 'd20', 'initiative'
        ]

        for term in dnd_terms:
            if term in query_lower:
                intent['specific_terms'].append(term)

        return intent

    def enhance_query(self, query: str, intent: Dict) -> str:
        """
        Melhora a consulta baseada na intenção detectada.

        Args:
            query: Consulta original
            intent: Análise da intenção

        Returns:
            Consulta melhorada
        """
        enhanced = query

        # Adiciona sinônimos e termos relacionados
        synonyms = {
            'pt': {
                'truques': ['truques', 'cantrips', 'magias de nível 0', 'cantrip', 'magia menor'],
                'vantagem': ['vantagem', 'advantage', 'benefício'],
                'desvantagem': ['desvantagem', 'disadvantage', 'penalidade'],
                'ca': ['ca', 'classe de armadura', 'armor class', 'ac'],
                'pv': ['pv', 'pontos de vida', 'hit points', 'hp', 'vida'],
                'magia': ['magia', 'spell', 'conjuração', 'feitiço', 'encantamento'],
                'personagem': ['personagem', 'character', 'pc', 'jogador'],
                'mago': ['mago', 'wizard', 'bruxo', 'feiticeiro', 'sorcerer', 'warlock'],
                'classe': ['classe', 'class', 'arquétipo'],
                'combate': ['combate', 'combat', 'luta', 'batalha', 'fight'],
                'rolagem': ['rolagem', 'roll', 'teste', 'jogada']
            },
            'en': {
                'cantrips': ['cantrips', 'truques', '0-level spells', 'cantrip', 'minor spells'],
                'advantage': ['advantage', 'vantagem', 'benefit'],
                'disadvantage': ['disadvantage', 'desvantagem', 'penalty'],
                'ac': ['ac', 'armor class', 'ca', 'classe de armadura'],
                'hp': ['hp', 'hit points', 'pv', 'pontos de vida', 'health'],
                'spell': ['spell', 'magia', 'conjuração', 'casting', 'magic'],
                'character': ['character', 'personagem', 'pc', 'player'],
                'wizard': ['wizard', 'mago', 'sorcerer', 'feiticeiro', 'warlock', 'bruxo'],
                'class': ['class', 'classe', 'archetype'],
                'combat': ['combat', 'combate', 'fight', 'battle'],
                'roll': ['roll', 'rolagem', 'test', 'check']
            }
        }

        # Expande consulta com sinônimos mais inteligentemente
        query_words = query.lower().split()
        lang_synonyms = synonyms.get(intent['language'], {})

        # Identifica termos que têm sinônimos e adiciona apenas os mais relevantes
        expanded_terms = []
        for word in query_words:
            if word in lang_synonyms:
                # Adiciona apenas os 3 sinônimos mais importantes
                expanded_terms.extend(lang_synonyms[word][:3])

        if expanded_terms:
            enhanced += f" {' '.join(expanded_terms)}"

        return enhanced

    def generate_response(self, query: str, results: List[Dict], intent: Dict) -> QueryResponse:
        """
        Gera resposta baseada nos resultados da busca usando IA quando disponível.

        Args:
            query: Consulta original
            results: Resultados da busca
            intent: Análise da intenção

        Returns:
            Resposta estruturada
        """
        start_time = datetime.now()

        language = intent['language']
        templates = self.response_templates[language]

        if not results:
            return QueryResponse(
                answer=templates['no_results'].format(query=query),
                confidence=0.0,
                sources=[],
                query_language=language,
                processing_time=0.0,
                found_results=0
            )

        # Calcula confiança baseada nos scores dos resultados
        if not results:
            confidence = 0.0
        else:
            # Usa uma média ponderada que favorece os melhores resultados
            top_scores = [r['score'] for r in results[:3]]  # Top 3 resultados
            avg_top_score = sum(top_scores) / len(top_scores)

            # Aplica fator de boost baseado na qualidade dos resultados
            # Se o melhor resultado é muito bom (>0.7), aumenta confiança
            if results[0]['score'] > 0.7:
                confidence = min(avg_top_score * 1.3, 1.0)
            elif results[0]['score'] > 0.5:
                confidence = min(avg_top_score * 1.1, 1.0)
            else:
                confidence = avg_top_score

        # Prepara fontes
        sources = []
        seen_sources = set()

        for result in results[:5]:  # Mostra até 5 fontes
            metadata = result['metadata']
            book_name = metadata['book_filename'].replace('.pdf', '')
            page_num = metadata['page_number']

            source_key = f"{book_name}_{page_num}"
            if source_key not in seen_sources:
                sources.append({
                    'book': book_name,
                    'page': page_num,
                    'score': result['score'],
                    'language': result['language']
                })
                seen_sources.add(source_key)

        # Gera resposta usando IA se disponível
        if self.ai_generator and self.ai_generator.available:
            logger.info("Gerando resposta com IA...")
            ai_answer = self.ai_generator.generate_response(
                query, results, language)

            # Adiciona informações sobre fontes à resposta IA
            if sources:
                source_lines = [templates['sources_intro']]
                for source in sources:
                    source_line = templates['source_format'].format(
                        book=source['book'],
                        page=source['page']
                    )
                    source_lines.append(source_line)

                ai_answer += '\n\n' + '\n'.join(source_lines)

            answer = ai_answer
        else:
            # Fallback para resposta tradicional
            logger.info("Gerando resposta tradicional (IA não disponível)")
            answer = self._generate_traditional_response(
                query, results, intent, templates, sources)

        processing_time = (datetime.now() - start_time).total_seconds()

        return QueryResponse(
            answer=answer,
            confidence=confidence,
            sources=sources,
            query_language=language,
            processing_time=processing_time,
            found_results=len(results)
        )

    def _generate_traditional_response(self, query: str, results: List[Dict],
                                       intent: Dict, templates: Dict, sources: List[Dict]) -> str:
        """Gera resposta tradicional quando IA não está disponível."""
        answer_parts = []

        # Seleciona melhores resultados para a resposta
        top_results = results[:3]  # Usa os 3 melhores
        confidence = min(sum(r['score']
                         for r in results) / len(results) * 1.2, 1.0)

        if confidence < 0.3:
            answer_parts.append(
                templates['low_confidence'].format(query=query))
        else:
            answer_parts.append(
                templates['good_confidence'].format(query=query))

        # Combina informações dos melhores resultados
        seen_content = set()
        for result in top_results:
            content = result['text']

            # Evita duplicação de conteúdo muito similar
            content_key = content[:100].lower().strip()
            if content_key not in seen_content:
                # Limita tamanho do texto para evitar respostas muito longas
                if len(content) > 300:
                    content = content[:297] + "..."

                answer_parts.append(f"\n{content}")
                seen_content.add(content_key)

        # Adiciona fontes à resposta
        if sources:
            answer_parts.append(templates['sources_intro'])
            for source in sources:
                source_line = templates['source_format'].format(
                    book=source['book'],
                    page=source['page']
                )
                answer_parts.append(source_line)

        return '\n'.join(answer_parts)

    def query(self, question: str, max_results: int = 10,
              book_type: str = None, book_filename: str = None) -> QueryResponse:
        """
        Processa uma consulta completa.

        Args:
            question: Pergunta do usuário
            max_results: Número máximo de resultados da busca
            book_type: Filtrar por tipo de livro
            book_filename: Filtrar por arquivo específico

        Returns:
            Resposta estruturada
        """
        logger.info(f"Processando consulta: '{question}'")

        # Analisa intenção
        intent = self.detect_query_intent(question)
        logger.info(f"Intenção detectada: {intent}")

        # Melhora consulta
        enhanced_query = self.enhance_query(question, intent)

        # Determina filtros baseados na intenção
        search_book_type = book_type or intent.get('book_preference')

        # Realiza busca
        results = self.indexer.search(
            query=enhanced_query,
            language=intent['language'],
            n_results=max_results,
            book_type=search_book_type,
            book_filename=book_filename
        )

        # Se não encontrou resultados no idioma detectado, tenta no outro
        if not results and intent['language'] == 'pt':
            logger.info("Tentando busca em inglês...")
            results = self.indexer.search(
                query=enhanced_query,
                language='en',
                n_results=max_results,
                book_type=search_book_type,
                book_filename=book_filename
            )
        elif not results and intent['language'] == 'en':
            logger.info("Tentando busca em português...")
            results = self.indexer.search(
                query=enhanced_query,
                language='pt',
                n_results=max_results,
                book_type=search_book_type,
                book_filename=book_filename
            )

        # Se ainda não encontrou resultados satisfatórios, tenta busca mais ampla
        if not results or (results and results[0]['score'] < 0.3):
            logger.info("Tentando busca mais ampla...")
            broader_query = question  # Usa consulta original sem expansão
            broader_results = self.indexer.search(
                query=broader_query,
                language=None,  # Busca em ambos idiomas
                n_results=max_results * 2,  # Busca mais resultados
                book_type=search_book_type,
                book_filename=book_filename
            )

            # Se a busca ampla trouxe resultados melhores, usa ela
            if broader_results and (not results or broader_results[0]['score'] > results[0]['score']):
                results = broader_results[:max_results]

        # Gera resposta
        response = self.generate_response(question, results, intent)

        logger.info(f"Resposta gerada - Confiança: {response.confidence:.2f}, "
                    f"Resultados: {response.found_results}, "
                    f"Tempo: {response.processing_time:.2f}s")

        return response

    def get_available_books(self) -> List[Dict]:
        """
        Retorna lista de livros disponíveis.

        Returns:
            Lista de livros indexados
        """
        return self.indexer.get_books_list()

    def get_stats(self) -> Dict:
        """
        Retorna estatísticas do sistema.

        Returns:
            Estatísticas das coleções
        """
        stats = self.indexer.get_collection_stats()

        # Adiciona informações sobre IA
        if self.ai_generator:
            stats['ai_status'] = self.ai_generator.get_status()
        else:
            stats['ai_status'] = {"available": False,
                                  "reason": "IA desabilitada"}

        return stats

    def get_ai_status(self) -> Dict:
        """
        Retorna status específico da IA.

        Returns:
            Status da IA
        """
        if self.ai_generator:
            return self.ai_generator.get_status()
        else:
            return {"available": False, "reason": "IA não inicializada"}

# Função de conveniência para consultas rápidas


def quick_query(question: str, index_dir: str = "index") -> str:
    """
    Função de conveniência para consultas rápidas.

    Args:
        question: Pergunta
        index_dir: Diretório do índice

    Returns:
        Resposta em texto
    """
    engine = QueryEngine(index_dir)
    response = engine.query(question)
    return response.answer


if __name__ == "__main__":
    # Teste do motor de consultas
    print("=== TESTE DO MOTOR DE CONSULTAS ===")

    engine = QueryEngine()

    # Verifica se há livros indexados
    books = engine.get_available_books()
    if not books:
        print("Nenhum livro indexado encontrado! Execute primeiro o indexer.py")
        exit(1)

    print(f"Livros disponíveis: {len(books)}")
    for book in books:
        print(f"  📖 {book['filename']} ({book['language']})")

    # Estatísticas
    stats = engine.get_stats()
    print(f"\nEstatísticas:")
    for lang, stat in stats.items():
        print(f"  {lang.upper()}: {stat['total_documents']} documentos")

    # Consultas de teste
    test_queries = [
        "Como funciona vantagem e desvantagem?",
        "What is armor class?",
        "Regras de conjuração de magias",
        "How do saving throws work?",
        "O que é iniciativa em combate?",
        "Spellcasting rules for wizards",
        "Como criar um personagem?",
        "Character creation steps"
    ]

    print(f"\n=== TESTE DE CONSULTAS ===")

    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Pergunta: '{query}'")
        print("-" * 50)

        response = engine.query(query)

        print(f"Idioma detectado: {response.query_language}")
        print(f"Confiança: {response.confidence:.2f}")
        print(f"Resultados encontrados: {response.found_results}")
        print(f"Tempo de processamento: {response.processing_time:.2f}s")
        print(f"\nResposta:")
        print(response.answer)

        if i < len(test_queries):
            input("\nPressione Enter para continuar...")

    # Modo interativo
    print(f"\n=== MODO INTERATIVO ===")
    print("Digite suas perguntas sobre D&D 5e (digite 'sair' para terminar):")

    while True:
        try:
            question = input("\n🎲 Sua pergunta: ").strip()

            if question.lower() in ['sair', 'exit', 'quit', '']:
                break

            response = engine.query(question)

            print(f"\n🎯 Resposta (confiança: {response.confidence:.2f}):")
            print(response.answer)

        except KeyboardInterrupt:
            print("\n\nSaindo...")
            break
        except Exception as e:
            print(f"Erro: {e}")

    print("Obrigado por usar o sistema D&D 5e!")
