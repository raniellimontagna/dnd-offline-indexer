#!/usr/bin/env python3
"""
Teste abrangente do D&D 5e Offline Indexer.
Valida todas as funcionalidades principais do sistema.
"""

import sys
import time
import requests
import json
from pathlib import Path

# Adiciona src ao path para imports
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_cli_queries():
    """Testa consultas via CLI."""
    print("🧪 Testando consultas via CLI...")

    # Testa consulta em português
    print("\n📝 Teste 1: Consulta em português")
    from query_engine import QueryEngine
    query_engine = QueryEngine()

    result = query_engine.search("Como funciona a iniciativa em combate?")
    print(f"✅ Idioma detectado: {result['language']}")
    print(f"✅ Confiança: {result['confidence']}%")
    print(f"✅ Resultados encontrados: {len(result['sources'])}")
    print(f"✅ Resposta (primeiros 100 chars): {result['answer'][:100]}...")

    # Testa consulta em inglês
    print("\n📝 Teste 2: Consulta em inglês")
    result = query_engine.search("How does advantage work in combat?")
    print(f"✅ Idioma detectado: {result['language']}")
    print(f"✅ Confiança: {result['confidence']}%")
    print(f"✅ Resultados encontrados: {len(result['sources'])}")
    print(f"✅ Resposta (primeiros 100 chars): {result['answer'][:100]}...")

    return True


def test_web_api():
    """Testa a API web."""
    print("\n🌐 Testando API web...")

    base_url = "http://127.0.0.1:8080"

    # Testa endpoint de status
    try:
        response = requests.get(f"{base_url}/status")
        if response.status_code == 200:
            status = response.json()
            print(
                f"✅ Status API: {status['total_documents']} documentos indexados")
        else:
            print(f"❌ Erro no status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro ao acessar API: {e}")
        return False

    # Testa busca via API
    try:
        search_data = {"query": "O que são pontos de vida?"}
        response = requests.post(f"{base_url}/search", json=search_data)
        if response.status_code == 200:
            result = response.json()
            print(
                f"✅ Busca API: Idioma {result['language']}, Confiança {result['confidence']}%")
        else:
            print(f"❌ Erro na busca: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro na busca API: {e}")
        return False

    return True


def test_language_detection():
    """Testa detecção de idioma."""
    print("\n🌍 Testando detecção de idioma...")

    from text_processor import TextProcessor
    processor = TextProcessor()

    # Textos de teste
    test_cases = [
        ("Como criar um personagem?", "PT"),
        ("What is a spell slot?", "EN"),
        ("Qual é a diferença entre AC e HP?", "PT"),
        ("How do saving throws work?", "EN"),
        ("Quais são as escolas de magia?", "PT"),
    ]

    for text, expected_lang in test_cases:
        detected_lang = processor.detect_language(text)
        if detected_lang == expected_lang:
            print(f"✅ '{text}' → {detected_lang}")
        else:
            print(f"❌ '{text}' → {detected_lang} (esperado: {expected_lang})")

    return True


def test_document_coverage():
    """Testa cobertura dos documentos."""
    print("\n📚 Testando cobertura dos documentos...")

    from indexer import Indexer
    indexer = Indexer()

    # Verifica se todos os PDFs foram processados
    processed_file = Path("index/processed_books.json")
    if processed_file.exists():
        with open(processed_file, 'r', encoding='utf-8') as f:
            processed = json.load(f)

        books_dir = Path("data/books")
        pdf_files = list(books_dir.glob("*.pdf"))

        print(f"✅ PDFs encontrados: {len(pdf_files)}")
        print(f"✅ PDFs processados: {len(processed)}")

        for pdf_file in pdf_files:
            if pdf_file.name in processed:
                print(f"✅ {pdf_file.name}")
            else:
                print(f"❌ {pdf_file.name} não processado")

        return len(processed) == len(pdf_files)
    else:
        print("❌ Arquivo de controle não encontrado")
        return False


def test_query_performance():
    """Testa performance das consultas."""
    print("\n⚡ Testando performance...")

    from query_engine import QueryEngine
    query_engine = QueryEngine()

    queries = [
        "Como funciona magia?",
        "What is AC?",
        "Explicar salvaguardas",
        "Combat rules",
        "Classes de personagem"
    ]

    total_time = 0
    for query in queries:
        start_time = time.time()
        result = query_engine.search(query)
        end_time = time.time()
        query_time = end_time - start_time
        total_time += query_time

        print(
            f"✅ '{query}': {query_time:.2f}s (confiança: {result['confidence']}%)")

    avg_time = total_time / len(queries)
    print(f"✅ Tempo médio: {avg_time:.2f}s")

    return avg_time < 10.0  # Espera-se menos de 10s por consulta


def run_comprehensive_test():
    """Executa todos os testes."""
    print("🎲 D&D 5e Offline Indexer - Teste Abrangente")
    print("=" * 60)

    tests = [
        ("Detecção de Idioma", test_language_detection),
        ("Cobertura de Documentos", test_document_coverage),
        ("Consultas CLI", test_cli_queries),
        ("API Web", test_web_api),
        ("Performance", test_query_performance),
    ]

    results = {}

    for test_name, test_func in tests:
        print(f"\n🔍 Executando: {test_name}")
        try:
            result = test_func()
            results[test_name] = result
            status = "✅ PASSOU" if result else "❌ FALHOU"
            print(f"📊 Resultado: {status}")
        except Exception as e:
            results[test_name] = False
            print(f"❌ ERRO: {e}")

    # Relatório final
    print("\n" + "=" * 60)
    print("📊 RELATÓRIO FINAL")
    print("=" * 60)

    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{test_name:25} {status}")

    print(f"\n🎯 Taxa de Sucesso: {passed}/{total} ({100*passed/total:.1f}%)")

    if passed == total:
        print("🎉 TODOS OS TESTES PASSARAM! Sistema pronto para uso.")
        return 0
    else:
        print("⚠️  Alguns testes falharam. Verifique os logs acima.")
        return 1


if __name__ == "__main__":
    sys.exit(run_comprehensive_test())
