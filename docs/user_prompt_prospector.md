# Prospector de Palavras-Chave: Arquitetura Orientada a User Prompt

A transição de "cole uma URL" para "digite um prompt exploratório" eleva o sistema de uma simples ferramenta de edição para um **Motor de Busca Semântico e Caçador de Criativos**.

Para que a experiência seja fluida ("Busque vídeos no canal do 'Felipe Franco' onde ele fala a frase 'taxa metabólica basal'"), a arquitetura precisa ser dividida em **Módulos de Intenção e Execução**.

Abaixo, um aprofundamento técnico e estratégico em cada uma das fases, incluindo a capacidade de **Pesquisas Avançadas**.

---

## Passo 0: O NLU (Natural Language Understanding) do Prompt
A magia começa antes mesmo do YouTube. O sistema precisa interpretar a frase do usuário e transformá-la em parâmetros de máquina.

**Exemplo de Prompt do Usuário:**
> *"Busque vídeos recentes no nicho 'Musculação' ou no canal 'Felipe Franco' com mais de 100k views, onde ele explica o conceito de 'taxa metabólica basal'."*

**Ação:** Um micro-agente LLM (gpt-4o-mini rápido ou prompt estruturado via `instructor`/`pydantic`) faz o parsing do texto para um JSON de Query:
```json
{
  "search_target": {
    "type": "channel_and_niche",
    "channel_name": "Felipe Franco",
    "niche": "Musculação"
  },
  "exact_keywords": ["taxa metabólica basal", "metabolismo basal"],
  "semantic_context": "explicação do conceito",
  "filters": {
    "max_age_days": 180,
    "min_views": 100000
  }
}
```

---

## Fase A: Descoberta de Vídeos Leve (Discovery)
O objetivo aqui é puramente encontrar **IDs de vídeos candidatos** que batam com os critérios principais (Canal, Nicho, Views) sem baixar nenhum arquivo pesado.

*   **Técnica:** O sistema usa a YouTube Data API v3 (para buscas exatas em canais) ou o `yt-dlp` com comandos como `ytsearch50:"Felipe Franco musculação"`.
*   **Avançado:** Se houver o filtro "min_views": 100000, já descartamos na etapa de metadados os vídeos irrelevantes, poupando passos futuros.
*   **Resultado do Passo:** Uma lista com 50 a 200 IDs de vídeos (`[ "dQw4w9WgXcQ", ... ]`).

---

## Fase B: Ingestão de Legendas em Massa (O Raspador de VTT)
Baixar 100 vídeos em MP4 mataria a infraestrutura. Baixar 100 legendas `.vtt` demora literalmente **2 a 5 segundos** em paralelo.

*   **Comando Estratégico:** 
    `yt-dlp --skip-download --write-auto-subs --sub-langs pt --dump-json [VIDEO_ID]`
*   **Tratamento do VTT:** Legendas automáticas do YouTube não têm pontuação e quebram a mesma palavra em dois tempos. O sistema precisa de um parser que "costure" as legendas em blocos lógicos de 10 a 15 segundos.
*   **Resultado do Passo:** Um banco de dados local temporário (SQLite ou Redis) com blocos de texto limpos e seus respectivos `start` e `end`.

---

## Fase C: Busca Híbrida Local (A "Mágica" Estilo Filmot)
Com o texto da legenda na mão, como encontramos "taxa metabólica basal" e os contextos em volta de forma avançada?

### 1. Busca Lexical (Exata/Fuzzy FTS5)
Procura exatamente a string `"taxa metabólica"` (ou com leves variações de digitação). Isso é feito no próprio SQLite instanciado com extensão *Full-Text Search* (FTS5). Retornará a linha de legenda exata em milissegundos.

### 2. Busca Semântica (Vector Embeddings) - O Diferencial Advanced
E se o prompt pedisse *"onde ele fala sobre queima calórica passiva"*? As palavras exatas podem não estar na legenda.
Nesse nível avançado, podemos passar os blocos de legenda em um modelo de embedding leve (ex: `text-embedding-3-small` da OpenAI ou modelo local `all-MiniLM-L6-v2`) e colocar num Pinecone/ChromaDB temporário.

*   **Resultado do Passo:** 
    `Vídeo XYZ | Segmento: 04:12 - 04:28 | Texto Real: "Seu metabolismo enquanto você dorme, que é sua taxa metabólica, vai lá pro teto." | Match de Confiança: 98%`

---

## Fase D: Corte Inteligente, Continuidade e Handoff
Encontrar a palavra-chave cravada não basta para um criativo. Se você corta no exato momento que ele fala "taxa", o vídeo fica "seco" e sem contexto.

### 1. Expansão da Janela de Contexto (Context Windowing):
Sabendo que o match ocorreu em `04:12`, o sistema não baixa apenas o segundo 04:12. Ele aplica uma **Margem de Respiro**:
*   *Buffer Antes:* `-15 segundos` (Para pegar a introdução do pensamento).
*   *Buffer Depois:* `+20 segundos` (Para pegar a conclusão).
*   **Novo Corte Alvo:** `03:57 - 04:48`.

### 2. Download Cirúrgico do Vídeo (Partial Segment Download)
Não precisamos baixar 2 horas de podcast. O `yt-dlp` (frequentemente com ajuda do `ffmpeg` por trás) possui comandos para baixar apenas a porção de vídeo requirida caso a plataforma suporte RANGE requests. Contudo, em vídeos live/MPEG-DASH, o HLS permite que baixemos estritamente o fragmento.
*(Se muito complexo, baixa-se a qualidade 480p rapidamente apenas para validar as métricas, ou se for corte de alta qualidade, baixa-se o original de forma temporária e descarta o que não for do corte).*

### 3. Handoff para o Tone Editor (LLM de Ad Quality)
Agora sim, o trecho recortado (`03:57 - 04:48`) é alimentado de volta para o pipeline que você já construía:
*   Passa no Whisper (agora para pontuação perfeita e timestamps milimétricos, pois a legenda auto-gerada original era imperfeita).
*   Entra no GPT para Labeling (Hook, Body, Risco de Compliance).

---

## Resumo dos Critérios de "Pesquisas Avançadas" Suportados (User Prompt)

1. **Filtros por Metadados:**
   - *"Postado nos últimos 30 dias"*
   - *"Acima de 1 Milhão de visualizações"*
   - *"Apenas no YouTube Shorts (vídeos verticais)"*

2. **Filtros Semânticos / Tonais:**
   - *"Trechos onde ele levanta a voz / tem tom enérgico"* (Requereria passar análise de áudio após baixar o trecho).
   - *"Trechos que sirvam de prova social"* (Procura-se no texto por palavras como "depois que eu comecei", "antes eu sofria", "meus alunos").

3. **Busca Multi-Entity:**
   - *"Qualquer médico famoso brasileiro falando sobre tribulus"* -> O NLU descobre listas de canais de médicos famosos, adiciona na queue e projeta.

Com essa arquitetura, a ferramenta não é apenas um "Cutter", mas uma verdadeira **Engenharia de Garimpo em Larga Escala.** O usuário só tem a ideia do ângulo do criativo e o código caça a melhor matéria-prima da internet para validar o Ad.
