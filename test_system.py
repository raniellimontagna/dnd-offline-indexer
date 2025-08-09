#!/usr/bin/env python3
"""
Script de teste para verificar se o sistema está funcionando corretamente.
"""

import sys
import os
from pathlib import Path

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_imports():
    """Testa importações básicas."""
    print("🧪 Testando importações...")

    try:
        import fitz
        print("✅ PyMuPDF - OK")
    except ImportError as e:
        print(f"❌ PyMuPDF - {e}")
        return False

    try:
        import langdetect
        print("✅ langdetect - OK")
    except ImportError as e:
        print(f"❌ langdetect - {e}")
        return False

    try:
        import nltk
        print("✅ NLTK - OK")
    except ImportError as e:
        print(f"❌ NLTK - {e}")
        return False

    try:
        import sentence_transformers
        print("✅ sentence-transformers - OK")
    except ImportError as e:
        print(f"❌ sentence-transformers - {e}")
        return False

    try:
        import chromadb
        print("✅ ChromaDB - OK")
    except ImportError as e:
        print(f"❌ ChromaDB - {e}")
        return False

    try:
        import fastapi
        print("✅ FastAPI - OK")
    except ImportError as e:
        print(f"❌ FastAPI - {e}")
        return False

    return True


def test_custom_modules():
    """Testa nossos módulos customizados."""
    print("\n🔧 Testando módulos customizados...")

    try:
        from pdf_extractor import PDFExtractor
        print("✅ pdf_extractor - OK")
    except ImportError as e:
        print(f"❌ pdf_extractor - {e}")
        return False

    try:
        from text_processor import TextProcessor
        print("✅ text_processor - OK")
    except ImportError as e:
        print(f"❌ text_processor - {e}")
        return False

    try:
        from indexer import DnDIndexer
        print("✅ indexer - OK")
    except ImportError as e:
        print(f"❌ indexer - {e}")
        return False

    try:
        from query_engine import QueryEngine
        print("✅ query_engine - OK")
    except ImportError as e:
        print(f"❌ query_engine - {e}")
        return False

    return True


def check_files():
    """Verifica se os arquivos necessários existem."""
    print("\n📁 Verificando estrutura de arquivos...")

    required_files = [
        "src/pdf_extractor.py",
        "src/text_processor.py",
        "src/indexer.py",
        "src/query_engine.py",
        "src/app.py",
        "src/query.py",
        "templates/index.html",
        "requirements.txt",
        "config.json"
    ]

    missing_files = []

    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path}")
            missing_files.append(file_path)

    return len(missing_files) == 0


def check_directories():
    """Verifica se os diretórios necessários existem."""
    print("\n📂 Verificando diretórios...")

    required_dirs = [
        "data/books",
        "index",
        "templates",
        "src"
    ]

    for dir_path in required_dirs:
        dir_obj = Path(dir_path)
        if dir_obj.exists() and dir_obj.is_dir():
            print(f"✅ {dir_path}/")
        else:
            print(f"❌ {dir_path}/")
            dir_obj.mkdir(parents=True, exist_ok=True)
            print(f"✅ Criado: {dir_path}/")


def check_pdfs():
    """Verifica PDFs disponíveis."""
    print("\n📚 Verificando PDFs...")

    books_dir = Path("data/books")
    pdf_files = list(books_dir.glob("*.pdf"))

    print(f"Pasta: {books_dir}")
    print(f"PDFs encontrados: {len(pdf_files)}")

    if pdf_files:
        for pdf in pdf_files:
            size_mb = pdf.stat().st_size / (1024 * 1024)
            print(f"  📖 {pdf.name} ({size_mb:.1f} MB)")
    else:
        print("  ℹ️  Nenhum PDF encontrado")
        print("  💡 Dica: Coloque seus PDFs de D&D 5e na pasta data/books/")

    return len(pdf_files) > 0


def test_language_detection():
    """Testa detecção de idiomas."""
    print("\n🌐 Testando detecção de idiomas...")

    try:
        from text_processor import TextProcessor
        processor = TextProcessor()

        # Testes em português
        pt_text = "Como funciona o sistema de vantagem e desvantagem em D&D?"
        detected = processor.detect_language(pt_text)
        print(f"✅ Português: '{pt_text}' → {detected}")

        # Testes em inglês
        en_text = "How does the advantage and disadvantage system work in D&D?"
        detected = processor.detect_language(en_text)
        print(f"✅ Inglês: '{en_text}' → {detected}")

        return True

    except Exception as e:
        print(f"❌ Erro na detecção de idiomas: {e}")
        return False


def main():
    """Função principal do teste."""
    print("🎲 D&D 5e Offline Indexer - Teste do Sistema")
    print("=" * 60)

    all_tests_passed = True

    # Teste 1: Importações básicas
    if not test_imports():
        print("\n❌ Falha nas importações básicas")
        all_tests_passed = False

    # Teste 2: Módulos customizados
    if not test_custom_modules():
        print("\n❌ Falha nos módulos customizados")
        all_tests_passed = False

    # Teste 3: Estrutura de arquivos
    if not check_files():
        print("\n❌ Alguns arquivos estão faltando")
        all_tests_passed = False

    # Teste 4: Diretórios
    check_directories()

    # Teste 5: PDFs
    has_pdfs = check_pdfs()

    # Teste 6: Detecção de idiomas
    if not test_language_detection():
        print("\n❌ Falha na detecção de idiomas")
        all_tests_passed = False

    # Resultado final
    print("\n" + "=" * 60)

    if all_tests_passed:
        print("✅ TODOS OS TESTES PASSARAM!")
        print("\n🚀 Próximos passos:")

        if has_pdfs:
            print("1. Construir índice: python src/query.py build-index")
            print("2. Iniciar interface web: python src/app.py")
            print("3. Ou usar linha de comando: python src/query.py search")
        else:
            print("1. Adicione seus PDFs de D&D à pasta data/books/")
            print("2. Execute: python src/query.py build-index")
            print("3. Inicie interface web: python src/app.py")

    else:
        print("❌ ALGUNS TESTES FALHARAM")
        print("Verifique os erros acima e execute novamente.")

    return 0 if all_tests_passed else 1


if __name__ == "__main__":
    sys.exit(main())
