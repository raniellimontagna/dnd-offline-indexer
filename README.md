# D&D 5e Offline Indexer

> [!WARNING]
> **Discontinued.** This proof of concept is no longer maintained and the repository is archived (read-only).

Sistema pessoal para responder dúvidas sobre Dungeons & Dragons 5e usando livros oficiais em PDF.

**⚠️ Aviso Legal**: Este é um projeto educacional para demonstrar técnicas de processamento de texto e busca semântica. Certifique-se de que possui os direitos legais para indexar e consultar qualquer documento que utilizar com este sistema.

## Características

- Extração e processamento de conteúdo de PDFs
- Detecção automática de idioma (português/inglês)
- Busca semântica inteligente
- Respostas inteligentes com IA local (Ollama)
- Respostas baseadas exclusivamente no conteúdo dos PDFs
- Interface web para consultas
- Fácil adição de novos PDFs
- Privacidade total - tudo funciona offline

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

### 2. Configurar IA (Opcional - Recomendado)

Para obter respostas mais elaboradas e naturais:

```bash
# Ativar ambiente virtual
source .venv/bin/activate

# Configurar IA automaticamente
python src/query.py ai-setup

# Ou configurar com modelo específico
python src/query.py ai-setup --model llama3.2:1b --test
```

**Nota**: A IA funciona totalmente offline. Se não configurada, o sistema usa respostas tradicionais baseadas nos trechos encontrados.

### 3. Iniciar o servidor web

```bash
# Ativar ambiente virtual (se não estiver ativo)
source .venv/bin/activate

# Iniciar servidor web
python src/app.py
```

### 4. Usar via linha de comando

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

## 🤖 Sistema de IA

### Configuração da IA

O sistema inclui um gerador de respostas inteligente usando **Ollama** (IA local):

```bash
# Verificar status da IA
python src/query.py status

# Configurar IA pela primeira vez
python src/query.py ai-setup

# Configurar com modelo específico
python src/query.py ai-setup --model llama3.2:1b

# Testar IA após configuração
python src/query.py ai-setup --model llama3.2:3b --test
```

### Vantagens da IA

- **🔒 Totalmente offline** - Seus dados nunca saem do computador
- **📚 Respostas elaboradas** - Processa e explica informações dos livros
- **🎯 Contextual** - Usa apenas conteúdo dos livros indexados
- **⚡ Rápida** - Responde em poucos segundos
- **🌐 Multilíngue** - Funciona em português e inglês

### Exemplos de Respostas

**Sem IA:**

```
COMBATENTE MONTADO Você é um oponente perigoso...
```

**Com IA:**

```
O sistema de vantagem é uma ferramenta importante no jogo, que pode ser
usada para influenciar os resultados de testes de habilidade, jogadas de
ataque e resistência. Quando você tem vantagem, joga dois d20 e usa o
maior resultado...
```

### Modelos Recomendados

- **llama3.2:1b** - Mais leve, mais rápido (1GB)
- **llama3.2:3b** - Equilibrado (padrão) (2GB)
- **llama3.1:8b** - Mais elaborado (4.7GB)

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

- **🔒 Privacidade**: Todos os dados ficam locais, nada é enviado online
- **🌐 Idiomas**: Suporta livros em português e inglês automaticamente
- **⚡ Performance**: Primeira indexação pode demorar, consultas são rápidas
- **💾 Backup**: Faça backup da pasta `index/` após indexar
- **🎯 Consultas**: Use termos específicos de D&D para melhores resultados
- **📖 Fontes**: O sistema mostra exatamente de qual livro e página veio a informação
- **📚 Livros**: Funciona melhor com livros oficiais que têm texto selecionável
- **🤖 IA**: Para melhores respostas, configure a IA com `python src/query.py ai-setup`
- **⚠️ Avisos**: Avisos sobre "format error" do MuPDF são normais e não afetam o funcionamento

## Arquivos Principais

- `src/pdf_extractor.py` - Extração de texto dos PDFs
- `src/text_processor.py` - Processamento e divisão do texto
- `src/indexer.py` - Criação do índice de busca
- `src/query_engine.py` - Motor de busca e respostas
- `src/ai_response_generator.py` - Gerador de respostas IA
- `src/app.py` - Interface web
- `src/query.py` - Interface de linha de comando

## FAQ - Perguntas Frequentes

### 🤖 Como ativar as respostas inteligentes?

1. Execute: `python src/query.py ai-setup`
2. Aguarde o download do modelo (pode demorar)
3. Pronto! Suas consultas terão respostas elaboradas

### ⚠️ Vejo erros "MuPDF format error" - é normal?

Sim! São apenas avisos sobre perfis de cor dos PDFs. Não afetam a extração de texto.

### 🐌 Por que a primeira indexação demora?

O sistema precisa:

- Extrair texto de todos os PDFs
- Processar e dividir o conteúdo
- Criar embeddings para busca semântica
- Tudo isso roda apenas uma vez

### 🔍 As consultas não encontram nada relevante

Tente:

- Usar termos específicos de D&D
- Fazer perguntas mais diretas
- Verificar se os livros foram indexados: `python src/query.py list-books`

### 💻 Como instalar o Ollama?

```bash
# Linux/Mac
curl -fsSL https://ollama.ai/install.sh | sh

# Windows
# Baixe de: https://ollama.ai/download

# Depois execute
ollama serve
```

### 🔒 Meus dados são enviados para algum lugar?

**Não!** Tudo funciona offline:

- ✅ PDFs ficam no seu computador
- ✅ Índice criado localmente
- ✅ IA roda localmente (Ollama)
- ✅ Nenhum dado é enviado para internet
