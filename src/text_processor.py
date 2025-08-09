import re
import nltk
from langdetect import detect
from typing import List, Dict, Tuple
import logging
from pathlib import Path
import json

# Baixa recursos do NLTK se necessário
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TextProcessor:
    """Processa e divide texto extraído de PDFs para indexação eficiente."""

    def __init__(self):
        self.stop_words_en = set(stopwords.words('english'))
        self.stop_words_pt = set(stopwords.words('portuguese'))

        # Termos específicos de D&D que não devem ser removidos
        self.dnd_terms = {
            'en': {'ac', 'hp', 'dc', 'dm', 'pc', 'npc', 'cr', 'xp', 'gp', 'sp', 'cp'},
            'pt': {'ca', 'pv', 'cd', 'mestre', 'jogador', 'xp', 'po', 'pp', 'pc'}
        }

    def detect_language(self, text: str) -> str:
        """
        Detecta o idioma do texto.

        Args:
            text: Texto para análise

        Returns:
            Código do idioma ('pt' ou 'en')
        """
        try:
            # Remove números e caracteres especiais para melhor detecção
            clean_text = re.sub(
                r'[^a-zA-ZáàâãéèêíîóôõúçÁÀÂÃÉÈÊÍÎÓÔÕÚÇ\s]', '', text)

            if len(clean_text.strip()) < 20:
                return 'en'  # Default para inglês se texto muito curto

            detected = detect(clean_text)

            # Mapeia códigos de idioma
            if detected in ['pt', 'pt-br']:
                return 'pt'
            else:
                return 'en'

        except Exception:
            # Se não conseguir detectar, tenta por palavras-chave
            portuguese_indicators = ['que', 'não', 'com',
                                     'uma', 'para', 'por', 'são', 'da', 'do', 'em']
            english_indicators = ['the', 'and', 'you',
                                  'are', 'with', 'for', 'have', 'this', 'that']

            text_lower = text.lower()
            pt_count = sum(
                1 for word in portuguese_indicators if word in text_lower)
            en_count = sum(
                1 for word in english_indicators if word in text_lower)

            return 'pt' if pt_count > en_count else 'en'

    def split_into_chunks(self, text: str, max_chunk_size: int = 1000, overlap: int = 200) -> List[Dict]:
        """
        Divide texto em chunks com sobreposição para preservar contexto.

        Args:
            text: Texto para dividir
            max_chunk_size: Tamanho máximo do chunk em caracteres
            overlap: Sobreposição entre chunks

        Returns:
            Lista de chunks com metadados
        """
        # Detecta idioma do texto
        language = self.detect_language(text)

        # Divide em sentenças
        sentences = sent_tokenize(
            text, language='portuguese' if language == 'pt' else 'english')

        chunks = []
        current_chunk = ""
        current_sentences = []

        for sentence in sentences:
            # Verifica se adicionar a sentença excederia o limite
            if len(current_chunk) + len(sentence) > max_chunk_size and current_chunk:
                # Adiciona o chunk atual
                chunks.append({
                    'text': current_chunk.strip(),
                    'sentences': current_sentences,
                    'language': language,
                    'word_count': len(current_chunk.split()),
                    'char_count': len(current_chunk)
                })

                # Inicia novo chunk com sobreposição
                if overlap > 0 and current_sentences:
                    # Calcula quantas sentenças manter para sobreposição
                    overlap_text = ""
                    overlap_sentences = []

                    for sent in reversed(current_sentences):
                        if len(overlap_text) + len(sent) <= overlap:
                            overlap_text = sent + " " + overlap_text
                            overlap_sentences.insert(0, sent)
                        else:
                            break

                    current_chunk = overlap_text
                    current_sentences = overlap_sentences
                else:
                    current_chunk = ""
                    current_sentences = []

            # Adiciona sentença atual
            current_chunk += sentence + " "
            current_sentences.append(sentence)

        # Adiciona último chunk se não estiver vazio
        if current_chunk.strip():
            chunks.append({
                'text': current_chunk.strip(),
                'sentences': current_sentences,
                'language': language,
                'word_count': len(current_chunk.split()),
                'char_count': len(current_chunk)
            })

        return chunks

    def extract_keywords(self, text: str, language: str) -> List[str]:
        """
        Extrai palavras-chave relevantes do texto.

        Args:
            text: Texto para análise
            language: Idioma do texto

        Returns:
            Lista de palavras-chave
        """
        # Tokeniza em palavras
        words = word_tokenize(
            text.lower(), language='portuguese' if language == 'pt' else 'english')

        # Remove stopwords e mantém termos de D&D
        stop_words = self.stop_words_pt if language == 'pt' else self.stop_words_en
        dnd_terms = self.dnd_terms.get(language, set())

        keywords = []
        for word in words:
            # Remove pontuação e números
            clean_word = re.sub(
                r'[^a-zA-ZáàâãéèêíîóôõúçÁÀÂÃÉÈÊÍÎÓÔÕÚÇ]', '', word)

            if (len(clean_word) > 2 and
                (clean_word not in stop_words or clean_word in dnd_terms) and
                    not clean_word.isdigit()):
                keywords.append(clean_word)

        # Remove duplicatas mantendo ordem
        seen = set()
        unique_keywords = []
        for keyword in keywords:
            if keyword not in seen:
                seen.add(keyword)
                unique_keywords.append(keyword)

        return unique_keywords

    def process_book_data(self, book_data: Dict) -> Dict:
        """
        Processa dados de um livro completo.

        Args:
            book_data: Dados extraídos do PDF

        Returns:
            Dados processados com chunks e metadados
        """
        logger.info(f"Processando livro: {book_data['filename']}")

        processed_chunks = []
        total_chunks = 0

        for page_data in book_data['pages']:
            page_text = page_data['text']

            if not page_text.strip():
                continue

            # Divide página em chunks
            chunks = self.split_into_chunks(page_text)

            for i, chunk in enumerate(chunks):
                # Extrai palavras-chave
                keywords = self.extract_keywords(
                    chunk['text'], chunk['language'])

                # Adiciona metadados
                processed_chunk = {
                    'id': f"{book_data['filename']}_page_{page_data['page_number']}_chunk_{i}",
                    'book_filename': book_data['filename'],
                    'book_type': book_data['book_type'],
                    'page_number': page_data['page_number'],
                    'chunk_index': i,
                    'text': chunk['text'],
                    'language': chunk['language'],
                    'word_count': chunk['word_count'],
                    'char_count': chunk['char_count'],
                    'keywords': keywords,
                    'sentences_count': len(chunk['sentences'])
                }

                processed_chunks.append(processed_chunk)
                total_chunks += 1

        # Detecta idioma principal do livro
        languages = [chunk['language'] for chunk in processed_chunks]
        main_language = max(
            set(languages), key=languages.count) if languages else 'en'

        processed_book = {
            'filename': book_data['filename'],
            'book_type': book_data['book_type'],
            'title': book_data['title'],
            'author': book_data['author'],
            'total_pages': book_data['total_pages'],
            'total_chunks': total_chunks,
            'main_language': main_language,
            'language_distribution': {lang: languages.count(lang) for lang in set(languages)},
            'chunks': processed_chunks,
            'total_words': sum(chunk['word_count'] for chunk in processed_chunks),
            'avg_chunk_size': sum(chunk['word_count'] for chunk in processed_chunks) / total_chunks if total_chunks > 0 else 0
        }

        logger.info(
            f"Processado: {total_chunks} chunks, idioma principal: {main_language}")

        return processed_book

    def process_multiple_books(self, books_data: List[Dict]) -> List[Dict]:
        """
        Processa múltiplos livros.

        Args:
            books_data: Lista de dados extraídos dos PDFs

        Returns:
            Lista de dados processados
        """
        processed_books = []

        for book_data in books_data:
            try:
                processed_book = self.process_book_data(book_data)
                processed_books.append(processed_book)
            except Exception as e:
                logger.error(f"Erro ao processar {book_data['filename']}: {e}")

        return processed_books

    def save_processed_data(self, processed_books: List[Dict], output_path: str):
        """
        Salva dados processados em arquivo JSON.

        Args:
            processed_books: Dados processados
            output_path: Caminho do arquivo de saída
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(processed_books, f, ensure_ascii=False, indent=2)

        logger.info(f"Dados processados salvos em: {output_file}")

# Função de conveniência


def process_books(books_data: List[Dict]) -> List[Dict]:
    """
    Função de conveniência para processar livros.

    Args:
        books_data: Dados extraídos dos PDFs

    Returns:
        Dados processados
    """
    processor = TextProcessor()
    return processor.process_multiple_books(books_data)


if __name__ == "__main__":
    # Teste do processamento
    from pdf_extractor import extract_all_pdfs

    print("Extraindo PDFs...")
    books_data = extract_all_pdfs()

    if books_data:
        print("Processando texto...")
        processed_books = process_books(books_data)

        print(f"\n=== RESUMO DO PROCESSAMENTO ===")
        print(f"Total de livros processados: {len(processed_books)}")

        for book in processed_books:
            print(f"\n📚 {book['filename']}")
            print(f"   Idioma principal: {book['main_language']}")
            print(f"   Total de chunks: {book['total_chunks']}")
            print(f"   Palavras totais: {book['total_words']:,}")
            print(
                f"   Tamanho médio do chunk: {book['avg_chunk_size']:.1f} palavras")
            print(
                f"   Distribuição de idiomas: {book['language_distribution']}")

        # Salva dados processados
        processor = TextProcessor()
        processor.save_processed_data(
            processed_books, "index/processed_books.json")
    else:
        print("Nenhum livro encontrado para processar.")
