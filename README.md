# Projeto Black Copy

Este repositório contém o backend (e futuramente frontend) da aplicação **Caçador de Criativos (Black Copy)**.

## ⚠️ Regras de Operação e Custos

**IMPORTANTE:** Como este projeto integra serviços de terceiros (como Apify e OpenAI) que consomem saldo financeiro ou créditos:
1. **Nenhum teste automatizado ou execução que envolva consumo de créditos/dinheiro real deve ser realizado sem a prévia e explícita autorização do usuário.**
2. O sistema foi projetado para rodar a lógica real sempre que um endpoint for acionado (sem mecanismos restritivos de "_dry-run_" mascarando chamadas), então o cuidado no consumo deve ser prévio à execução.
3. Se um script for testar rotas que geram cobranças, pergunte antes de prosseguir!

## Estrutura Atual
- `backend/`: FastAPI + SQLAlchemy + Integrações (Apify, etc).
