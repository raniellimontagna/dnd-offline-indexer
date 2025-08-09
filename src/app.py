from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import logging
from typing import Optional
import json
from pathlib import Path

# Importa nossos módulos
from query_engine import QueryEngine, QueryResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuração da aplicação
app = FastAPI(
    title="D&D 5e Offline Indexer",
    description="Sistema pessoal para consultas em documentos de D&D 5e",
    version="1.0.0"
)

# Templates
templates = Jinja2Templates(directory="templates")

# Motor de consultas
query_engine = None


def initialize_query_engine():
    """Inicializa o motor de consultas."""
    global query_engine
    try:
        query_engine = QueryEngine()
        logger.info("Motor de consultas inicializado com sucesso")
        return True
    except Exception as e:
        logger.error(f"Erro ao inicializar motor de consultas: {e}")
        return False


@app.on_event("startup")
async def startup_event():
    """Evento de inicialização da aplicação."""
    if not initialize_query_engine():
        logger.warning("Aplicação iniciada sem motor de consultas funcional")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Página inicial da aplicação."""
    # Verifica se o sistema está funcionando
    system_status = {
        'engine_ready': query_engine is not None,
        'books_count': 0,
        'total_documents': 0
    }

    if query_engine:
        try:
            books = query_engine.get_available_books()
            stats = query_engine.get_stats()

            system_status['books_count'] = len(books)
            system_status['total_documents'] = sum(
                stat.get('total_documents', 0) for stat in stats.values()
            )
            system_status['books'] = books
            system_status['stats'] = stats
        except Exception as e:
            logger.error(f"Erro ao obter status do sistema: {e}")

    return templates.TemplateResponse(
        "index.html",
        {"request": request, "system_status": system_status}
    )


@app.post("/query")
async def query_documents(
    query: str = Form(...),
    book_type: Optional[str] = Form(None),
    book_filename: Optional[str] = Form(None),
    max_results: int = Form(default=10)
):
    """
    Endpoint para consultas aos documentos.

    Args:
        query: Pergunta do usuário
        book_type: Filtro por tipo de livro (opcional)
        book_filename: Filtro por arquivo específico (opcional)
        max_results: Número máximo de resultados

    Returns:
        Resposta estruturada da consulta
    """
    if not query_engine:
        raise HTTPException(
            status_code=503,
            detail="Motor de consultas não inicializado"
        )

    if not query.strip():
        raise HTTPException(
            status_code=400,
            detail="Consulta não pode estar vazia"
        )

    try:
        # Processa consulta
        response = query_engine.query(
            question=query.strip(),
            max_results=max_results,
            book_type=book_type if book_type and book_type != "all" else None,
            book_filename=book_filename if book_filename and book_filename != "all" else None
        )

        # Converte para dicionário
        response_dict = {
            'answer': response.answer,
            'confidence': response.confidence,
            'sources': response.sources,
            'query_language': response.query_language,
            'processing_time': response.processing_time,
            'found_results': response.found_results,
            'query': query
        }

        return JSONResponse(content=response_dict)

    except Exception as e:
        logger.error(f"Erro ao processar consulta '{query}': {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno: {str(e)}"
        )


@app.get("/api/query")
async def api_query(
    q: str,
    book_type: Optional[str] = None,
    book_filename: Optional[str] = None,
    max_results: int = 10
):
    """
    Endpoint GET para consultas via API.

    Args:
        q: Pergunta do usuário
        book_type: Filtro por tipo de livro (opcional)
        book_filename: Filtro por arquivo específico (opcional)
        max_results: Número máximo de resultados

    Returns:
        Resposta estruturada da consulta
    """
    if not query_engine:
        raise HTTPException(
            status_code=503,
            detail="Motor de consultas não inicializado"
        )

    if not q.strip():
        raise HTTPException(
            status_code=400,
            detail="Parâmetro 'q' (consulta) é obrigatório"
        )

    try:
        response = query_engine.query(
            question=q.strip(),
            max_results=max_results,
            book_type=book_type,
            book_filename=book_filename
        )

        return {
            'answer': response.answer,
            'confidence': response.confidence,
            'sources': response.sources,
            'query_language': response.query_language,
            'processing_time': response.processing_time,
            'found_results': response.found_results,
            'query': q
        }

    except Exception as e:
        logger.error(f"Erro ao processar consulta API '{q}': {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno: {str(e)}"
        )


@app.get("/books")
async def get_books():
    """
    Retorna lista de livros disponíveis.

    Returns:
        Lista de livros indexados
    """
    if not query_engine:
        raise HTTPException(
            status_code=503,
            detail="Motor de consultas não inicializado"
        )

    try:
        books = query_engine.get_available_books()
        return {"books": books}

    except Exception as e:
        logger.error(f"Erro ao obter lista de livros: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno: {str(e)}"
        )


@app.get("/stats")
async def get_stats():
    """
    Retorna estatísticas do sistema.

    Returns:
        Estatísticas das coleções
    """
    if not query_engine:
        raise HTTPException(
            status_code=503,
            detail="Motor de consultas não inicializado"
        )

    try:
        stats = query_engine.get_stats()
        books = query_engine.get_available_books()

        return {
            "collection_stats": stats,
            "books_count": len(books),
            "total_documents": sum(
                stat.get('total_documents', 0) for stat in stats.values()
            )
        }

    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """
    Verifica saúde da aplicação.

    Returns:
        Status da aplicação
    """
    return {
        "status": "healthy" if query_engine else "degraded",
        "engine_ready": query_engine is not None,
        "message": "Sistema funcionando" if query_engine else "Motor de consultas não inicializado"
    }

# Função para executar o servidor


def run_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """
    Executa o servidor web.

    Args:
        host: Endereço do host
        port: Porta do servidor
        reload: Recarregamento automático
    """
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="D&D 5e Offline Indexer Web Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host address")
    parser.add_argument("--port", type=int, default=8000, help="Port number")
    parser.add_argument("--reload", action="store_true",
                        help="Enable auto-reload")

    args = parser.parse_args()

    print("=== D&D 5e Offline Indexer ===")
    print(f"Iniciando servidor em http://{args.host}:{args.port}")
    print("Pressione Ctrl+C para parar")

    run_server(host=args.host, port=args.port, reload=args.reload)
