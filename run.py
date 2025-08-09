#!/usr/bin/env python3
"""
Script principal para executar o D&D 5e Offline Indexer.
"""

import sys
import os
import argparse
from pathlib import Path

# Adiciona src ao path para imports
sys.path.insert(0, str(Path(__file__).parent / "src"))


def run_setup():
    """Executa o setup inicial."""
    print("🔧 Executando setup inicial...")
    exec(open("setup.py").read())


def run_indexer():
    """Executa a indexação dos documentos."""
    try:
        from query import main as query_main
        # Simula argumentos para build-index
        old_argv = sys.argv
        sys.argv = ["query.py", "build-index"]
        result = query_main()
        sys.argv = old_argv
        return result == 0
    except Exception as e:
        print(f"❌ Erro na indexação: {e}")
        return False


def run_query_interactive():
    """Executa modo interativo de consultas."""
    try:
        from query import main as query_main
        # Simula argumentos para search interativo
        old_argv = sys.argv
        sys.argv = ["query.py", "search"]
        result = query_main()
        sys.argv = old_argv
        return result == 0
    except Exception as e:
        print(f"❌ Erro nas consultas: {e}")
        return False


def run_web_server(host="0.0.0.0", port=8000):
    """Executa o servidor web."""
    try:
        from app import run_server
        print(f"🌐 Iniciando servidor web em http://{host}:{port}")
        print("Pressione Ctrl+C para parar")
        run_server(host=host, port=port)
        return True
    except KeyboardInterrupt:
        print("\n🛑 Servidor parado pelo usuário")
        return True
    except Exception as e:
        print(f"❌ Erro no servidor web: {e}")
        return False


def check_status():
    """Verifica status do sistema."""
    try:
        from query import main as query_main
        # Simula argumentos para status
        old_argv = sys.argv
        sys.argv = ["query.py", "status"]
        result = query_main()
        sys.argv = old_argv
        return result == 0
    except Exception as e:
        print(f"❌ Erro ao verificar status: {e}")
        return False


def main():
    """Função principal."""
    parser = argparse.ArgumentParser(
        description="D&D 5e Offline Indexer - Sistema completo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Comandos disponíveis:

  setup     - Configura e instala dependências
  index     - Constrói índice dos documentos
  search    - Modo interativo de consultas
  web       - Inicia servidor web
  status    - Verifica status do sistema
  
Fluxo recomendado:
  1. python run.py setup
  2. Adicione PDFs em data/books/
  3. python run.py index
  4. python run.py web OU python run.py search
        """
    )

    parser.add_argument(
        "command",
        choices=["setup", "index", "search", "web", "status"],
        help="Comando a executar"
    )

    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host para servidor web (padrão: 0.0.0.0)"
    )

    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Porta para servidor web (padrão: 8000)"
    )

    args = parser.parse_args()

    print("🎲 D&D 5e Offline Indexer")
    print("=" * 40)

    success = False

    if args.command == "setup":
        success = True
        run_setup()

    elif args.command == "index":
        success = run_indexer()

    elif args.command == "search":
        success = run_query_interactive()

    elif args.command == "web":
        success = run_web_server(args.host, args.port)

    elif args.command == "status":
        success = check_status()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
