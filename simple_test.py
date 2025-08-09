#!/usr/bin/env python3
"""
Teste simplificado do D&D 5e Offline Indexer.
"""

import sys
import time
from pathlib import Path

# Adiciona src ao path para imports
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_basic_functionality():
    """Testa funcionalidades básicas."""
    print("🎲 Teste Básico do D&D 5e Offline Indexer")
    print("=" * 50)

    # Teste 1: Consulta em português
    print("\n📝 Teste 1: Consulta em português")
    try:
        from query_engine import QueryEngine
        query_engine = QueryEngine()

        start_time = time.time()
        result = query_engine.query("Como criar um personagem?")
        end_time = time.time()

        print(f"✅ Tempo de resposta: {end_time - start_time:.2f}s")
        print(f"✅ Idioma detectado: {result.query_language}")
        print(f"✅ Confiança: {result.confidence:.1f}%")
        print(f"✅ Resultados encontrados: {result.found_results}")
        print(f"✅ Fontes utilizadas: {len(result.sources)}")
        print(f"✅ Resposta (primeiros 200 chars): {result.answer[:200]}...")

    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

    # Teste 2: Consulta em inglês
    print("\n📝 Teste 2: Consulta em inglês")
    try:
        start_time = time.time()
        result = query_engine.query("What are spell slots?")
        end_time = time.time()

        print(f"✅ Tempo de resposta: {end_time - start_time:.2f}s")
        print(f"✅ Idioma detectado: {result.query_language}")
        print(f"✅ Confiança: {result.confidence:.1f}%")
        print(f"✅ Resultados encontrados: {result.found_results}")
        print(f"✅ Fontes utilizadas: {len(result.sources)}")
        print(f"✅ Resposta (primeiros 200 chars): {result.answer[:200]}...")

    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

    # Teste 3: Verificar índice
    print("\n📝 Teste 3: Verificação do índice")
    try:
        total_docs = query_engine.indexer.get_document_count()
        print(f"✅ Total de documentos indexados: {total_docs}")

        # Verificar idiomas disponíveis
        languages = query_engine.indexer.get_available_languages()
        print(f"✅ Idiomas disponíveis: {languages}")

    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

    print("\n🎉 Todos os testes básicos foram executados com sucesso!")
    print("\n📋 Sistema pronto para uso:")
    print("  • Interface CLI: python src/query.py search \"sua pergunta\"")
    print("  • Interface web: python run.py web")
    print("  • Status: python run.py status")

    return True


if __name__ == "__main__":
    success = test_basic_functionality()
    sys.exit(0 if success else 1)
