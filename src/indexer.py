import chromadb
from sentence_transformers import SentenceTransformer
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional
import uuid
from datetime import datetime
import os

# Desabilitar telemetria do ChromaDB
os.environ["ANONYMIZED_TELEMETRY"] = "False"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DnDIndexer:
    """Sistema de indexação para documentos de D&D usando embeddings semânticos."""

    def __init__(self, index_dir: str = "index", model_name: str = "all-MiniLM-L6-v2"):
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(exist_ok=True)

        # Inicializa ChromaDB
        self.client = chromadb.PersistentClient(
            path=str(self.index_dir / "chroma_db"))

        # Carrega modelo de embeddings
        logger.info(f"Carregando modelo de embeddings: {model_name}")
        self.embedding_model = SentenceTransformer(model_name)

        # Coleções separadas por idioma
        self.collection_pt = self.client.get_or_create_collection(
            name="dnd_documents_pt",
            metadata={"description": "Documentos D&D em Português"}
        )

        self.collection_en = self.client.get_or_create_collection(
            name="dnd_documents_en",
            metadata={"description": "Documentos D&D em Inglês"}
        )

        self.collections = {
            'pt': self.collection_pt,
            'en': self.collection_en
        }

    def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Cria embeddings para uma lista de textos.

        Args:
            texts: Lista de textos

        Returns:
            Lista de embeddings
        """
        logger.info(f"Criando embeddings para {len(texts)} textos...")
        embeddings = self.embedding_model.encode(texts, show_progress_bar=True)
        return embeddings.tolist()

    def index_book(self, processed_book: Dict) -> bool:
        """
        Indexa um livro processado.

        Args:
            processed_book: Dados do livro processado

        Returns:
            True se indexado com sucesso
        """
        logger.info(f"Indexando livro: {processed_book['filename']}")

        try:
            chunks = processed_book['chunks']

            if not chunks:
                logger.warning(
                    f"Nenhum chunk encontrado em {processed_book['filename']}")
                return False

            # Agrupa chunks por idioma
            chunks_by_language = {}
            for chunk in chunks:
                lang = chunk['language']
                if lang not in chunks_by_language:
                    chunks_by_language[lang] = []
                chunks_by_language[lang].append(chunk)

            # Indexa cada idioma separadamente
            for language, lang_chunks in chunks_by_language.items():
                if language not in self.collections:
                    logger.warning(
                        f"Idioma {language} não suportado, pulando...")
                    continue

                collection = self.collections[language]

                # Prepara dados para indexação
                texts = [chunk['text'] for chunk in lang_chunks]
                ids = [chunk['id'] for chunk in lang_chunks]

                # Cria metadados
                metadatas = []
                for chunk in lang_chunks:
                    metadata = {
                        'book_filename': chunk['book_filename'],
                        'book_type': chunk['book_type'],
                        'page_number': chunk['page_number'],
                        'chunk_index': chunk['chunk_index'],
                        'language': chunk['language'],
                        'word_count': chunk['word_count'],
                        'char_count': chunk['char_count'],
                        'sentences_count': chunk['sentences_count'],
                        'keywords': json.dumps(chunk['keywords'], ensure_ascii=False),
                        'indexed_at': datetime.now().isoformat()
                    }
                    metadatas.append(metadata)

                # Cria embeddings
                embeddings = self.create_embeddings(texts)

                # Remove documentos existentes do mesmo livro
                existing_docs = collection.get(
                    where={"book_filename": processed_book['filename']}
                )

                if existing_docs['ids']:
                    logger.info(
                        f"Removendo {len(existing_docs['ids'])} documentos existentes de {processed_book['filename']}")
                    collection.delete(ids=existing_docs['ids'])

                # Adiciona novos documentos
                collection.add(
                    documents=texts,
                    embeddings=embeddings,
                    metadatas=metadatas,
                    ids=ids
                )

                logger.info(
                    f"Indexados {len(lang_chunks)} chunks em {language} para {processed_book['filename']}")

            return True

        except Exception as e:
            logger.error(f"Erro ao indexar {processed_book['filename']}: {e}")
            return False

    def index_multiple_books(self, processed_books: List[Dict]) -> Dict[str, int]:
        """
        Indexa múltiplos livros.

        Args:
            processed_books: Lista de livros processados

        Returns:
            Estatísticas da indexação
        """
        stats = {'success': 0, 'failed': 0, 'total_chunks': 0}

        for book in processed_books:
            if self.index_book(book):
                stats['success'] += 1
                stats['total_chunks'] += book['total_chunks']
            else:
                stats['failed'] += 1

        logger.info(
            f"Indexação concluída: {stats['success']} sucessos, {stats['failed']} falhas, {stats['total_chunks']} chunks totais")

        return stats

    def search(self, query: str, language: str = None, n_results: int = 10,
               book_type: str = None, book_filename: str = None) -> List[Dict]:
        """
        Busca documentos relevantes.

        Args:
            query: Consulta de busca
            language: Idioma preferido ('pt' ou 'en', None para ambos)
            n_results: Número máximo de resultados
            book_type: Filtrar por tipo de livro
            book_filename: Filtrar por arquivo específico

        Returns:
            Lista de documentos relevantes
        """
        # Determina idiomas para busca
        if language and language in self.collections:
            search_languages = [language]
        else:
            search_languages = ['pt', 'en']

        all_results = []

        for lang in search_languages:
            collection = self.collections[lang]

            # Constrói filtro
            where_filter = {}
            if book_type:
                where_filter['book_type'] = book_type
            if book_filename:
                where_filter['book_filename'] = book_filename

            try:
                # Realiza busca
                results = collection.query(
                    query_texts=[query],
                    n_results=n_results,
                    where=where_filter if where_filter else None
                )

                # Processa resultados
                if results['documents'] and results['documents'][0]:
                    for i in range(len(results['documents'][0])):
                        distance = results['distances'][0][i]
                        # Converte distância em score de similaridade (0-1)
                        # ChromaDB usa distância euclidiana normalizada, então convertemos para similaridade
                        # Sempre positivo, 0-1
                        score = max(0.0, 1.0 / (1.0 + distance))

                        result = {
                            'id': results['ids'][0][i],
                            'text': results['documents'][0][i],
                            'distance': distance,
                            'score': score,
                            'language': lang,
                            'metadata': results['metadatas'][0][i]
                        }

                        # Parse keywords de volta para lista
                        if 'keywords' in result['metadata']:
                            try:
                                result['metadata']['keywords'] = json.loads(
                                    result['metadata']['keywords'])
                            except:
                                result['metadata']['keywords'] = []

                        all_results.append(result)

            except Exception as e:
                logger.error(f"Erro na busca em {lang}: {e}")

        # Ordena por score e retorna os melhores resultados
        all_results.sort(key=lambda x: x['score'], reverse=True)

        return all_results[:n_results]

    def get_collection_stats(self) -> Dict:
        """
        Retorna estatísticas das coleções.

        Returns:
            Estatísticas das coleções
        """
        stats = {}

        for lang, collection in self.collections.items():
            try:
                count = collection.count()
                stats[lang] = {
                    'total_documents': count,
                    'collection_name': collection.name
                }
            except Exception as e:
                logger.error(f"Erro ao obter stats de {lang}: {e}")
                stats[lang] = {'total_documents': 0, 'error': str(e)}

        return stats

    def get_books_list(self) -> List[Dict]:
        """
        Retorna lista de livros indexados.

        Returns:
            Lista de livros com metadados
        """
        books = []
        seen_books = set()

        for lang, collection in self.collections.items():
            try:
                # Obtém todos os documentos
                results = collection.get()

                for metadata in results['metadatas']:
                    book_key = (metadata['book_filename'],
                                metadata['book_type'])

                    if book_key not in seen_books:
                        books.append({
                            'filename': metadata['book_filename'],
                            'book_type': metadata['book_type'],
                            'language': metadata['language'],
                            'indexed_at': metadata.get('indexed_at', 'Unknown')
                        })
                        seen_books.add(book_key)

            except Exception as e:
                logger.error(f"Erro ao listar livros de {lang}: {e}")

        return books

    def delete_book(self, book_filename: str) -> bool:
        """
        Remove um livro do índice.

        Args:
            book_filename: Nome do arquivo do livro

        Returns:
            True se removido com sucesso
        """
        success = True

        for lang, collection in self.collections.items():
            try:
                # Busca documentos do livro
                existing_docs = collection.get(
                    where={"book_filename": book_filename}
                )

                if existing_docs['ids']:
                    collection.delete(ids=existing_docs['ids'])
                    logger.info(
                        f"Removidos {len(existing_docs['ids'])} documentos de {book_filename} em {lang}")

            except Exception as e:
                logger.error(f"Erro ao remover {book_filename} de {lang}: {e}")
                success = False

        return success

# Função de conveniência para indexação completa


def build_index(processed_books_path: str = "index/processed_books.json",
                index_dir: str = "index") -> bool:
    """
    Constrói índice completo a partir de dados processados.

    Args:
        processed_books_path: Caminho para dados processados
        index_dir: Diretório do índice

    Returns:
        True se indexado com sucesso
    """
    try:
        # Carrega dados processados
        with open(processed_books_path, 'r', encoding='utf-8') as f:
            processed_books = json.load(f)

        # Cria indexador
        indexer = DnDIndexer(index_dir)

        # Indexa livros
        stats = indexer.index_multiple_books(processed_books)

        logger.info(f"Índice construído: {stats}")
        return stats['success'] > 0

    except Exception as e:
        logger.error(f"Erro ao construir índice: {e}")
        return False


if __name__ == "__main__":
    # Teste da indexação
    from pdf_extractor import extract_all_pdfs
    from text_processor import process_books

    print("=== CONSTRUINDO ÍNDICE ===")

    # Extrai PDFs
    print("1. Extraindo PDFs...")
    books_data = extract_all_pdfs()

    if not books_data:
        print("Nenhum PDF encontrado!")
        exit(1)

    # Processa texto
    print("2. Processando texto...")
    processed_books = process_books(books_data)

    # Constrói índice
    print("3. Construindo índice...")
    indexer = DnDIndexer()
    stats = indexer.index_multiple_books(processed_books)

    print(f"\n=== ÍNDICE CONSTRUÍDO ===")
    print(f"Livros indexados: {stats['success']}")
    print(f"Total de chunks: {stats['total_chunks']}")

    # Estatísticas das coleções
    collection_stats = indexer.get_collection_stats()
    print(f"\nEstatísticas das coleções:")
    for lang, stat in collection_stats.items():
        print(f"  {lang.upper()}: {stat['total_documents']} documentos")

    # Lista livros indexados
    books_list = indexer.get_books_list()
    print(f"\nLivros no índice:")
    for book in books_list:
        print(
            f"  📖 {book['filename']} ({book['language']}) - {book['book_type']}")

    # Teste de busca
    print(f"\n=== TESTE DE BUSCA ===")
    test_queries = [
        "Como funciona vantagem e desvantagem?",
        "What is armor class?",
        "Regras de conjuração",
        "How to create a character?"
    ]

    for query in test_queries:
        print(f"\nBusca: '{query}'")
        results = indexer.search(query, n_results=3)

        if results:
            for i, result in enumerate(results, 1):
                print(
                    f"  {i}. [{result['language'].upper()}] Score: {result['score']:.3f}")
                print(f"     Livro: {result['metadata']['book_filename']}")
                print(f"     Página: {result['metadata']['page_number']}")
                print(f"     Texto: {result['text'][:100]}...")
        else:
            print("  Nenhum resultado encontrado.")
