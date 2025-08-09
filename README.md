# D&D 5e Offline Indexer

Sistema pessoal para responder dúvidas sobre Dungeons & Dragons 5e usando livros oficiais em PDF.

**⚠️ Aviso Legal**: Este é um projeto educacional para demonstrar técnicas de processamento de texto e busca semântica. Certifique-se de que possui os direitos legais para indexar e consultar qualquer documento que utilizar com este sistema.

## Características

- Extração e processamento de conteúdo de PDFs
- Detecção automática de idioma (português/inglês)
- Busca semântica inteligente
- Respostas baseadas exclusivamente no conteúdo dos PDFs
- Interface web para consultas
- Fácil adição de novos PDFs

## Instalação

### Com ambiente virtual (recomendado)

```bash
# Criar e ativar ambiente virtual
python3 -m venv .venv
source .venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
python -m nltk.downloader punkt stopwords
```

### Instalação direta (não recomendada em sistemas com gerenciamento externo)

```bash
pip install -r requirements.txt
python -m nltk.downloader punkt stopwords
```

## Estrutura dos Dados

Coloque seus PDFs na pasta `data/books/`:

- Livros em português: detectados automaticamente
- Livros em inglês: detectados automaticamente

**Nota**: Os PDFs dos livros oficiais não são incluídos no repositório. Você deve adicionar seus próprios livros (com os quais possui direitos legais de uso) na pasta `data/books/`.

## Uso

### 1. Indexar os PDFs

```bash
# Ativar ambiente virtual
source .venv/bin/activate

# Criar índice dos PDFs
python src/indexer.py
```

### 2. Iniciar o servidor web

```bash
# Ativar ambiente virtual (se não estiver ativo)
source .venv/bin/activate

# Iniciar servidor web
python src/app.py
```

### 3. Usar via linha de comando

```bash
# Ativar ambiente virtual
source .venv/bin/activate

# Exemplos de consultas D&D
python src/query.py search "Como funciona o sistema de vantagem?"
python src/query.py search "Como calcular modificadores de atributo?"
python src/query.py search "Quais são as ações em combate?"
python src/query.py search "What is the spell save DC formula?"

# Comandos úteis
python src/query.py status          # Ver status do sistema
python src/query.py list-books      # Listar livros indexados
```

## API

- `GET /` - Interface web
- `POST /query` - Consulta via API
- `GET /books` - Lista de livros indexados

## Configuração

### Telemetria

O sistema está configurado para **não enviar telemetria**, garantindo privacidade total e operação offline. Isso elimina avisos de conexão que poderiam aparecer durante o uso.

### Ambiente Virtual

Sempre use o ambiente virtual para garantir que as dependências estejam corretas:

```bash
source .venv/bin/activate
```

### Estrutura de Pastas
```
dnd-offline-indexer/
├── data/
│   └── books/          # ← Seus livros de D&D aqui
│       ├── players-handbook.pdf
│       ├── dungeon-masters-guide.pdf
│       ├── monster-manual.pdf
│       └── ...
├── index/              # ← Criado automaticamente
├── src/                # ← Código do sistema
└── ...
```

## Dicas de Uso

- **Privacidade**: Todos os dados ficam locais, nada é enviado online
- **Idiomas**: Suporta livros em português e inglês automaticamente
- **Performance**: Primeira indexação pode demorar, consultas são rápidas
- **Backup**: Faça backup da pasta `index/` após indexar
- **Consultas**: Use termos específicos de D&D para melhores resultados
- **Fontes**: O sistema mostra exatamente de qual livro e página veio a informação
- **Livros**: Funciona melhor com livros oficiais que têm texto selecionável

## Arquivos Principais

- `src/pdf_extractor.py` - Extração de texto dos PDFs
- `src/text_processor.py` - Processamento e divisão do texto
- `src/indexer.py` - Criação do índice de busca
- `src/query_engine.py` - Motor de busca e respostas
- `src/app.py` - Interface web
- `src/query.py` - Interface de linha de comando
