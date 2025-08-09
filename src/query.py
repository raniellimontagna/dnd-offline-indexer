#!/usr/bin/env python3
"""
Interface de linha de comando para o D&D 5e Offline Indexer.
"""

import argparse
import sys
import logging
from pathlib import Path
from typing import Optional

# Importa nossos módulos
try:
    from query_engine import QueryEngine
    from pdf_extractor import extract_all_pdfs
    from text_processor import process_books
    from indexer import DnDIndexer
except ImportError as e:
    print(f"Erro ao importar módulos: {e}")
    print("Certifique-se de que todos os pacotes estão instalados:")
    print("pip install -r requirements.txt")
    sys.exit(1)

# Configuração de logging
logging.basicConfig(
    level=logging.WARNING,  # Reduz verbosidade na linha de comando
    format='%(levelname)s: %(message)s'
)


def setup_logging(verbose: bool):
    """Configura nível de logging baseado na verbosidade."""
    if verbose:
        logging.getLogger().setLevel(logging.INFO)
    else:
        logging.getLogger().setLevel(logging.WARNING)


def build_index_command(args):
    """Comando para construir/reconstruir o índice."""
    print("🔧 Construindo índice dos documentos D&D 5e...")

    # Verifica se existem PDFs
    books_dir = Path(args.books_dir)
    if not books_dir.exists():
        print(f"❌ Diretório {books_dir} não encontrado!")
        return False

    pdf_files = list(books_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"❌ Nenhum arquivo PDF encontrado em {books_dir}")
        return False

    print(f"📚 Encontrados {len(pdf_files)} arquivos PDF")

    try:
        # 1. Extração
        print("1️⃣ Extraindo texto dos PDFs...")
        books_data = extract_all_pdfs(str(books_dir))

        if not books_data:
            print("❌ Falha na extração de PDFs")
            return False

        print(f"✅ Extraídos {len(books_data)} livros")

        # 2. Processamento
        print("2️⃣ Processando e dividindo texto...")
        processed_books = process_books(books_data)

        if not processed_books:
            print("❌ Falha no processamento de texto")
            return False

        total_chunks = sum(book['total_chunks'] for book in processed_books)
        print(f"✅ Processados {total_chunks} chunks de texto")

        # 3. Indexação
        print("3️⃣ Construindo índice de busca...")
        indexer = DnDIndexer(args.index_dir)
        stats = indexer.index_multiple_books(processed_books)

        if stats['success'] == 0:
            print("❌ Falha na indexação")
            return False

        print(f"✅ Índice construído com sucesso!")
        print(f"   📖 Livros indexados: {stats['success']}")
        print(f"   📄 Total de chunks: {stats['total_chunks']}")

        # Estatísticas por idioma
        collection_stats = indexer.get_collection_stats()
        print(f"   🌐 Documentos por idioma:")
        for lang, stat in collection_stats.items():
            print(
                f"      {lang.upper()}: {stat['total_documents']} documentos")

        return True

    except Exception as e:
        print(f"❌ Erro durante a construção do índice: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return False


def query_command(args):
    """Comando para fazer consultas."""
    try:
        engine = QueryEngine(args.index_dir)

        if args.query:
            # Consulta única
            response = engine.query(
                question=args.query,
                max_results=args.max_results,
                book_type=args.book_type,
                book_filename=args.book_filename
            )

            print_response(response, args.show_sources)

        else:
            # Modo interativo
            print("🎲 D&D 5e Offline Indexer - Modo Interativo")
            print("Digite suas perguntas sobre D&D 5e (digite 'sair' para terminar)")
            print("-" * 60)

            while True:
                try:
                    question = input("\n🎯 Sua pergunta: ").strip()

                    if question.lower() in ['sair', 'exit', 'quit', '']:
                        break

                    response = engine.query(
                        question=question,
                        max_results=args.max_results,
                        book_type=args.book_type,
                        book_filename=args.book_filename
                    )

                    print_response(response, args.show_sources)

                except KeyboardInterrupt:
                    print("\n\nSaindo...")
                    break
                except Exception as e:
                    print(f"❌ Erro: {e}")

        return True

    except Exception as e:
        print(f"❌ Erro ao inicializar motor de consultas: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return False


def print_response(response, show_sources: bool = True):
    """Imprime uma resposta formatada."""
    print(f"\n📋 Resposta:")
    print("-" * 40)

    # Confiança
    confidence_emoji = "🟢" if response.confidence >= 0.7 else "🟡" if response.confidence >= 0.4 else "🔴"
    print(f"{confidence_emoji} Confiança: {response.confidence:.0%}")

    # Metadados
    print(f"🌐 Idioma: {response.query_language.upper()}")
    print(f"⏱️ Tempo: {response.processing_time:.2f}s")
    print(f"🔍 Resultados: {response.found_results}")

    print(f"\n{response.answer}")

    # Fontes
    if show_sources and response.sources:
        print(f"\n📚 Fontes:")
        for i, source in enumerate(response.sources[:5], 1):
            print(
                f"  {i}. {source['book'].replace('.pdf', '')} (página {source['page']}) - {source['score']:.0%}")


def status_command(args):
    """Comando para mostrar status do sistema."""
    try:
        engine = QueryEngine(args.index_dir)

        print("📊 Status do D&D 5e Offline Indexer")
        print("=" * 50)

        # Estatísticas das coleções
        stats = engine.get_stats()
        total_docs = sum(stat.get('total_documents', 0)
                         for stat in stats.values())

        print(f"📄 Total de documentos: {total_docs}")
        print(f"🌐 Idiomas disponíveis:")
        for lang, stat in stats.items():
            print(f"   {lang.upper()}: {stat['total_documents']} documentos")

        # Lista de livros
        books = engine.get_available_books()
        print(f"\n📚 Livros indexados ({len(books)}):")

        books_by_type = {}
        for book in books:
            book_type = book['book_type']
            if book_type not in books_by_type:
                books_by_type[book_type] = []
            books_by_type[book_type].append(book)

        for book_type, type_books in books_by_type.items():
            print(f"\n  📖 {book_type.replace('_', ' ').title()}:")
            for book in type_books:
                print(
                    f"     • {book['filename'].replace('.pdf', '')} ({book['language'].upper()})")

        return True

    except Exception as e:
        print(f"❌ Erro ao obter status: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return False


def list_books_command(args):
    """Comando para listar livros disponíveis."""
    try:
        engine = QueryEngine(args.index_dir)
        books = engine.get_available_books()

        if not books:
            print("📚 Nenhum livro indexado encontrado")
            print("Execute: python query.py build-index")
            return True

        print(f"📚 Livros Indexados ({len(books)})")
        print("=" * 50)

        for i, book in enumerate(books, 1):
            print(f"{i:2d}. {book['filename'].replace('.pdf', '')}")
            print(f"     Tipo: {book['book_type'].replace('_', ' ').title()}")
            print(f"     Idioma: {book['language'].upper()}")
            print(
                f"     Indexado: {book['indexed_at'].split('T')[0] if 'T' in book['indexed_at'] else book['indexed_at']}")
            print()

        return True

    except Exception as e:
        print(f"❌ Erro ao listar livros: {e}")
        return False


def main():
    """Função principal."""
    parser = argparse.ArgumentParser(
        description="D&D 5e Offline Indexer - Sistema de consultas em documentos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:

  # Construir índice
  python query.py build-index

  # Fazer uma consulta
  python query.py search "Como funciona vantagem?"

  # Modo interativo
  python query.py search

  # Consulta com filtros
  python query.py search "regras de magia" --book-type players_handbook

  # Status do sistema
  python query.py status
        """
    )

    # Argumentos globais
    parser.add_argument(
        "--index-dir",
        default="index",
        help="Diretório do índice (padrão: index)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Modo verboso"
    )

    # Subcomandos
    subparsers = parser.add_subparsers(
        dest="command", help="Comandos disponíveis")

    # Comando build-index
    build_parser = subparsers.add_parser(
        "build-index",
        help="Constrói/reconstrói o índice dos documentos"
    )
    build_parser.add_argument(
        "--books-dir",
        default="data/books",
        help="Diretório com os PDFs (padrão: data/books)"
    )

    # Comando search
    search_parser = subparsers.add_parser(
        "search",
        help="Faz consultas nos documentos"
    )
    search_parser.add_argument(
        "query",
        nargs="?",
        help="Pergunta (se omitida, entra em modo interativo)"
    )
    search_parser.add_argument(
        "--max-results",
        type=int,
        default=10,
        help="Número máximo de resultados (padrão: 10)"
    )
    search_parser.add_argument(
        "--book-type",
        choices=["players_handbook", "dungeon_masters_guide",
                 "monster_manual", "supplement"],
        help="Filtrar por tipo de livro"
    )
    search_parser.add_argument(
        "--book-filename",
        help="Filtrar por arquivo específico"
    )
    search_parser.add_argument(
        "--no-sources",
        action="store_true",
        help="Não mostrar fontes das respostas"
    )

    # Comando status
    status_parser = subparsers.add_parser(
        "status",
        help="Mostra status do sistema"
    )

    # Comando list-books
    list_parser = subparsers.add_parser(
        "list-books",
        help="Lista livros indexados"
    )

    args = parser.parse_args()

    # Configurações
    setup_logging(args.verbose)

    # Se nenhum comando foi especificado, mostra ajuda
    if not args.command:
        parser.print_help()
        return 1

    # Executa comando
    success = False

    if args.command == "build-index":
        success = build_index_command(args)
    elif args.command == "search":
        args.show_sources = not args.no_sources
        success = query_command(args)
    elif args.command == "status":
        success = status_command(args)
    elif args.command == "list-books":
        success = list_books_command(args)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
