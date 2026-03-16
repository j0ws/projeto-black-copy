# Projeto Black Copy

Este repositório contém o backend (e futuramente frontend) da aplicação **Caçador de Criativos (Black Copy)**.

## ⚠️ Regras de Operação e Custos

**IMPORTANTE:** Como este projeto integra serviços de terceiros (como Apify e OpenAI) que consomem saldo financeiro ou créditos:
1. **Nenhum teste automatizado ou execução que envolva consumo de créditos/dinheiro real deve ser realizado sem a prévia e explícita autorização do usuário.**
2. O sistema foi projetado para rodar a lógica real sempre que um endpoint for acionado (sem mecanismos restritivos de "_dry-run_" mascarando chamadas), então o cuidado no consumo deve ser prévio à execução.
3. Se um script for testar rotas que geram cobranças, pergunte antes de prosseguir!

## Estrutura Atual
- `backend/`: FastAPI + SQLAlchemy + Integrações (Apify, etc).

---

## Projeto Conceitual

A ideia central do projeto é automatizar a extração e o recorte de vídeos virais para acelerar o fluxo criativo e a construção de novos vídeos com ganchos validados.
O sistema é dividido nas seguintes frentes:

### 1º Módulo: [Modulo Miner tts] (TikTok Shop)
Integração com uma API de scraper (Apify) para pesquisar semanalmente os vídeos do TikTok Shop mais virais dos últimos 7 dias referentes a um nicho ou produto (ex: "*testo hard*"). O objetivo aqui é ter um radar passivo e constante do que está retendo a atenção no TikTok e convertendo em vendas.

### 2º Módulo: [Modulo Miner yt] (YouTube)
Ferramenta ativa para pesquisa de clipes no YouTube com base em filtros, tags e palavras-chave. Através dela, é possível encontrar o "timestamp" (segundo exato) onde a palavra é dita, visualizar um preview e **baixar em lote** (recortes precisos limitados por tempo, ex: 10~20s) para já ter no computador diferentes opções de "gancho e corpo" prontos para edição no funil de vendas.
