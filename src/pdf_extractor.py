import fitz  # PyMuPDF
import os
import re
from typing import List, Dict, Tuple
from pathlib import Path
import logging
import warnings

# Suprimir avisos do MuPDF sobre perfis de cor
warnings.filterwarnings("ignore", category=UserWarning, module="fitz")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDFExtractor:
    """Extrai texto de PDFs de D&D 5e mantendo estrutura e metadados."""

    def __init__(self, books_dir: str = "data/books"):
        self.books_dir = Path(books_dir)

    def extract_from_file(self, pdf_path: Path) -> Dict:
        """
        Extrai texto de um arquivo PDF específico.

        Args:
            pdf_path: Caminho para o arquivo PDF

        Returns:
            Dict com texto extraído e metadados
        """
        logger.info(f"Extraindo texto de: {pdf_path.name}")

        try:
            doc = fitz.open(pdf_path)

            # Metadados do documento
            metadata = doc.metadata

            pages_content = []

            for page_num in range(len(doc)):
                page = doc[page_num]

                # Extrai texto da página
                text = page.get_text()

                # Remove quebras de linha desnecessárias e limpa o texto
                text = self._clean_text(text)

                if text.strip():  # Só adiciona páginas com conteúdo
                    pages_content.append({
                        'page_number': page_num + 1,
                        'text': text,
                        'word_count': len(text.split())
                    })

            doc.close()

            # Detecta o tipo de livro baseado no nome do arquivo
            book_type = self._detect_book_type(pdf_path.name)

            return {
                'filename': pdf_path.name,
                'filepath': str(pdf_path),
                'title': metadata.get('title', pdf_path.stem),
                'author': metadata.get('author', 'Wizards of the Coast'),
                'book_type': book_type,
                'total_pages': len(pages_content),
                'pages': pages_content,
                'total_words': sum(page['word_count'] for page in pages_content)
            }

        except Exception as e:
            logger.error(f"Erro ao extrair PDF {pdf_path}: {e}")
            return None

    def extract_all_books(self) -> List[Dict]:
        """
        Extrai texto de todos os PDFs na pasta de livros.

        Returns:
            Lista de dicionários com dados extraídos
        """
        books_data = []

        if not self.books_dir.exists():
            logger.error(f"Pasta {self.books_dir} não encontrada!")
            return books_data

        # Busca todos os arquivos PDF
        pdf_files = list(self.books_dir.glob("*.pdf"))

        if not pdf_files:
            logger.warning(
                f"Nenhum arquivo PDF encontrado em {self.books_dir}")
            return books_data

        logger.info(f"Encontrados {len(pdf_files)} arquivos PDF")

        for pdf_file in pdf_files:
            book_data = self.extract_from_file(pdf_file)
            if book_data:
                books_data.append(book_data)
                logger.info(
                    f"Extraído: {book_data['filename']} - {book_data['total_pages']} páginas, {book_data['total_words']} palavras")

        return books_data

    def _clean_text(self, text: str) -> str:
        """
        Limpa e normaliza o texto extraído.

        Args:
            text: Texto bruto extraído

        Returns:
            Texto limpo
        """
        # Remove caracteres de controle
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)

        # Normaliza espaços em branco
        text = re.sub(r'\s+', ' ', text)

        # Remove linhas muito curtas (provavelmente números de página ou artefatos)
        lines = text.split('\n')
        cleaned_lines = []

        for line in lines:
            line = line.strip()
            if len(line) > 10:  # Mantém apenas linhas com conteúdo substancial
                cleaned_lines.append(line)

        return '\n'.join(cleaned_lines)

    def _detect_book_type(self, filename: str) -> str:
        """
        Detecta o tipo de livro baseado no nome do arquivo.

        Args:
            filename: Nome do arquivo

        Returns:
            Tipo do livro
        """
        filename_lower = filename.lower()

        # Livro do Jogador
        if any(term in filename_lower for term in ['player', 'jogador', 'phb']):
            return 'players_handbook'

        # Guia do Mestre
        elif any(term in filename_lower for term in ['master', 'mestre', 'dmg', 'dungeon']):
            return 'dungeon_masters_guide'

        # Manual dos Monstros
        elif any(term in filename_lower for term in ['monster', 'monstro', 'mm']):
            return 'monster_manual'

        # Outros suplementos
        elif any(term in filename_lower for term in ['xanathar', 'volo', 'mordenkainen', 'tasha']):
            return 'supplement'

        else:
            return 'unknown'

# Função de conveniência para uso direto


def extract_all_pdfs(books_dir: str = "data/books") -> List[Dict]:
    """
    Função de conveniência para extrair todos os PDFs.

    Args:
        books_dir: Diretório com os PDFs

    Returns:
        Lista com dados extraídos
    """
    extractor = PDFExtractor(books_dir)
    return extractor.extract_all_books()


if __name__ == "__main__":
    # Teste da extração
    books_data = extract_all_pdfs()

    print(f"\n=== RESUMO DA EXTRAÇÃO ===")
    print(f"Total de livros processados: {len(books_data)}")

    for book in books_data:
        print(f"\n📖 {book['filename']}")
        print(f"   Tipo: {book['book_type']}")
        print(f"   Páginas: {book['total_pages']}")
        print(f"   Palavras: {book['total_words']:,}")

        # Mostra uma amostra do conteúdo
        if book['pages']:
            sample_text = book['pages'][0]['text'][:200]
            print(f"   Amostra: {sample_text}...")
