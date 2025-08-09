#!/usr/bin/env python3
"""
Script de configuração e instalação do D&D 5e Offline Indexer.
"""

import subprocess
import sys
import os
from pathlib import Path
import platform


def run_command(command, description, check=True):
    """Executa um comando e mostra o resultado."""
    print(f"📦 {description}...")
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=check,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"✅ {description} - Concluído")
            return True
        else:
            print(f"❌ {description} - Erro:")
            print(result.stderr)
            return False
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - Erro:")
        print(e.stderr)
        return False


def check_python_version():
    """Verifica se a versão do Python é adequada."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(
            f"❌ Python 3.8+ é necessário. Versão atual: {version.major}.{version.minor}")
        return False

    print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
    return True


def install_requirements():
    """Instala dependências Python."""
    requirements_file = Path("requirements.txt")

    if not requirements_file.exists():
        print("❌ Arquivo requirements.txt não encontrado!")
        return False

    # Atualiza pip
    run_command(
        f"{sys.executable} -m pip install --upgrade pip",
        "Atualizando pip",
        check=False
    )

    # Instala dependências
    success = run_command(
        f"{sys.executable} -m pip install -r requirements.txt",
        "Instalando dependências Python"
    )

    return success


def download_nltk_data():
    """Baixa dados necessários do NLTK."""
    print("📚 Baixando recursos do NLTK...")

    try:
        import nltk

        # Lista de recursos necessários
        resources = [
            'punkt',
            'stopwords'
        ]

        for resource in resources:
            try:
                nltk.data.find(f'tokenizers/{resource}')
                print(f"✅ NLTK {resource} - Já instalado")
            except LookupError:
                print(f"📥 Baixando NLTK {resource}...")
                nltk.download(resource, quiet=True)
                print(f"✅ NLTK {resource} - Baixado")

        return True

    except ImportError:
        print("❌ NLTK não instalado. Execute primeiro a instalação das dependências.")
        return False
    except Exception as e:
        print(f"❌ Erro ao baixar recursos NLTK: {e}")
        return False


def create_directories():
    """Cria estrutura de diretórios necessária."""
    directories = [
        "data/books",
        "index",
        "templates",
        "src"
    ]

    print("📁 Criando estrutura de diretórios...")

    for directory in directories:
        dir_path = Path(directory)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"✅ Criado: {directory}")
        else:
            print(f"✅ Já existe: {directory}")

    return True


def check_pdfs():
    """Verifica se existem PDFs na pasta books."""
    books_dir = Path("data/books")
    pdf_files = list(books_dir.glob("*.pdf"))

    print(f"📚 Verificando PDFs em {books_dir}...")
    print(f"✅ Encontrados {len(pdf_files)} arquivos PDF")

    if pdf_files:
        for pdf in pdf_files:
            print(f"   📖 {pdf.name}")
    else:
        print("ℹ️  Coloque seus PDFs de D&D 5e na pasta data/books/")

    return len(pdf_files) > 0


def test_imports():
    """Testa se todas as dependências podem ser importadas."""
    print("🧪 Testando importações...")

    imports_to_test = [
        ("fitz", "PyMuPDF"),
        ("langdetect", "langdetect"),
        ("sklearn", "scikit-learn"),
        ("nltk", "NLTK"),
        ("numpy", "NumPy"),
        ("pandas", "Pandas"),
        ("sentence_transformers", "sentence-transformers"),
        ("chromadb", "ChromaDB"),
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn")
    ]

    all_good = True

    for module, package in imports_to_test:
        try:
            __import__(module)
            print(f"✅ {package} - OK")
        except ImportError:
            print(f"❌ {package} - Não encontrado")
            all_good = False

    return all_good


def show_next_steps():
    """Mostra próximos passos para o usuário."""
    print("\n" + "="*60)
    print("🎯 PRÓXIMOS PASSOS")
    print("="*60)

    print("\n1. 📚 Adicione seus PDFs de D&D 5e:")
    print("   Coloque os arquivos PDF na pasta: data/books/")
    print("   Formatos suportados: Livro do Jogador, Guia do Mestre, etc.")

    print("\n2. 🔧 Construa o índice:")
    print("   python src/query.py build-index")

    print("\n3. 🔍 Faça consultas:")
    print("   # Modo interativo")
    print("   python src/query.py search")
    print("   ")
    print("   # Consulta única")
    print("   python src/query.py search \"Como funciona vantagem?\"")

    print("\n4. 🌐 Interface web:")
    print("   python src/app.py")
    print("   Acesse: http://localhost:8000")

    print("\n5. 📊 Verificar status:")
    print("   python src/query.py status")

    print("\n" + "="*60)


def main():
    """Função principal do setup."""
    print("🎲 D&D 5e Offline Indexer - Setup")
    print("="*50)

    # Verifica versão do Python
    if not check_python_version():
        return 1

    # Cria diretórios
    if not create_directories():
        return 1

    # Instala dependências
    if not install_requirements():
        print("❌ Falha na instalação das dependências")
        return 1

    # Baixa recursos NLTK
    if not download_nltk_data():
        print("⚠️  Aviso: Recursos NLTK não baixados completamente")

    # Testa importações
    if not test_imports():
        print("❌ Algumas dependências não estão funcionando corretamente")
        return 1

    # Verifica PDFs
    has_pdfs = check_pdfs()

    print("\n✅ Setup concluído com sucesso!")

    if not has_pdfs:
        print("⚠️  Não esqueça de adicionar seus PDFs à pasta data/books/")

    show_next_steps()

    return 0


if __name__ == "__main__":
    sys.exit(main())
