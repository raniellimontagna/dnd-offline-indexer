# Pasta para livros de D&D 5e

Coloque aqui os PDFs dos livros oficiais de D&D 5e que você deseja indexar.

## Importante

- Este sistema indexa o **conteúdo** dos livros de D&D 5e
- Certifique-se de ter **direitos legais** para usar os livros (ter comprado fisicamente ou digitalmente)
- Livros em **português** e **inglês** são detectados automaticamente

## Livros suportados

Exemplos de livros que funcionam bem:

- Player's Handbook / Livro do Jogador
- Dungeon Master's Guide / Guia do Mestre
- Monster Manual / Manual dos Monstros
- Xanathar's Guide to Everything
- Tasha's Cauldron of Everything
- E outros livros oficiais de D&D 5e

## Estrutura recomendada

```
books/
├── core/
│   ├── players-handbook.pdf
│   ├── dungeon-masters-guide.pdf
│   └── monster-manual.pdf
├── supplements/
│   ├── xanathars-guide.pdf
│   └── tashas-cauldron.pdf
└── adventures/
    └── curse-of-strahd.pdf
```

## Formatos suportados

- ✅ PDF com texto selecionável dos livros oficiais
- ❌ PDFs apenas com imagens (precisariam de OCR)
- ❌ PDFs protegidos por senha
- ❌ Conteúdo pirata ou não licenciado

## Após adicionar livros

Execute o indexador para processar os livros de D&D:

```bash
source .venv/bin/activate
python src/indexer.py
```

## Exemplos de consultas

Depois de indexar, você poderá fazer perguntas como:

- "Como funciona o sistema de vantagem?"
- "Quais são as escolas de magia?"
- "Como calcular Classe de Armadura?"
- "What is the spell slot progression for wizards?"
