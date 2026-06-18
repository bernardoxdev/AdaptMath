# AdaptMath (CaseOrbi)

Plataforma de apoio ao estudo de Matemática/ENEM com:
- Teste de aptidão (questões geradas/selecionadas e corrigidas)
- Exercícios e gestão de questões (salvas, reportes, etc.)
- Assistente de IA para dicas e chat
- Relatórios e insights de desempenho

> Este repositório é uma aplicação web **backend Flask** com **frontend estático** (templates e assets servidos pelo Flask) e armazenamento em **PostgreSQL + Redis**.

## Visão geral da arquitetura

- **Backend (Flask)**
  - Define rotas HTML (landing, login, dashboard) e rotas JSON (API para o frontend).
  - Autenticação com **JWT (access + refresh)** guardados na **sessão Flask**.
  - Sessões: `Flask-Session` usando armazenamento em disco (`SESSION_TYPE=filesystem`).

- **Banco de dados (PostgreSQL)**
  - Persistência de usuários e dados acadêmicos (ex.: questões, respostas, testes, conversas/mensagens).
  - O setup inicial cria tabelas e importa/classifica questões.

- **Cache/estado (Redis)**
  - Armazena estado temporário do teste de aptidão (lista de questões por usuário), reduzindo round-trips ao banco.

- **IA local (Transformers / PyTorch)**
  - Geração de **dica** e de **respostas** do chat no backend.
  - Modelo utilizado no código: **Qwen/Qwen2.5-0.5B-Instruct**.

## Premissas e decisões

1. **IA executa localmente no container**
   - Vantagem: simplifica arquitetura (sem provedores externos de LLM para dicas/chat).
   - Tradeoff: maior consumo de CPU/GPU e tempo de inicialização; exige ambiente preparado para inferência.

2. **Setup automatizado na inicialização do container**
   - O `docker-compose` sobe o Postgres, e o backend roda `setup_database` antes do `gunicorn`.
   - Tradeoff: primeira inicialização é mais lenta.

3. **Separação de responsabilidades**
   - Postgres: dados persistentes.
   - Redis: dados temporários/estado do teste.

## Tradeoffs (o que pode ser melhorado)

- **Reinicialização/reaquisição de modelo**: o modelo é carregado no módulo (ao importar). Isso pode aumentar o tempo de start e memória.
- **Sem fila para inferência**: requests de IA concorrem diretamente com a carga web.
- **Streaming ausente**: respostas não são emitidas em streaming.
- **Observabilidade**: logs e métricas ainda são limitados.
- **Segurança**: há chaves via `.env`/variáveis; faltam hardening adicional (ex.: rotação de chaves, controles de abuso).

## Uso de IA

### 1) Dica para questões
- Endpoint (exemplo no backend): `/api/questoes/dica/<numero>`
- O backend monta um prompt em PT-BR instruindo o modelo a:
  - dar **apenas 1 dica**
  - **não revelar** alternativa correta nem resolver completamente

### 2) Chat e relatórios
- Chat:
  - Criação de conversa: `/api/chat/conversa`
  - Listagem de conversas: `/api/chat/conversas`
  - Envio de mensagem: `/api/chat/mensagem`
- Relatórios:
  - Insights automáticos: `/api/relatorio/insights`
  - Análise detalhada por IA: `/api/relatorio/analise`

## Variáveis de ambiente (principais)

Defina no arquivo `.env` (o `docker-compose.yml` usa `env_file: .env`):

- `DATABASE_URL` (ex.: `postgresql://case:case123@db:5432/case_db`)
- `POSTGRES_PASSWORD` (usado pelo serviço `db`)
- `SECRET_KEY` (chave de sessão e JWT)
- `ACCESS_TOKEN_EXPIRE_MINUTES` (expiração do access token)
- `REFRESH_TOKEN_EXPIRE_DAYS` (expiração do refresh token)
- `HF_TOKEN` (token para login no Hugging Face; necessário para downloads do modelo/artefatos)
- `REDIS_HOST` / `REDIS_PORT` / `REDIS_DB` (padrão: `redis`, `6379`, `0`)

## Setup e inicialização (com Docker Compose)

### 1) Criar/ajustar o `.env`

Crie um arquivo `.env` na raiz do projeto com as variáveis exigidas acima.

### 2) Subir a aplicação

```bash
docker compose up --build
```

- Postgres sobe na porta **5433** do host (-> 5432 no container).
- Backend sobe na porta **5000** do host.

### 3) Acessar

- Frontend/rotas HTML: `http://localhost:5000`

## Assunções e limitações conhecidas

- A primeira execução pode ser lenta por:
  - criação de tabelas
  - import/classificação de questões
  - download do modelo Hugging Face e inicialização do Transformer

- O token Hugging Face (`HF_TOKEN`) pode ser necessário dependendo do acesso do modelo no seu ambiente.

## O que eu melhoraria com mais tempo e recursos

- **Pipeline de inferência** (fila/worker): separar geração de IA da carga web.
- **Streaming** de respostas do LLM.
- **Quantização/cache de modelo** (ex.: GGUF, vLLM ou alternativas) para reduzir memória e tempo.
- **Rate limit e proteção anti-abuso** nos endpoints de IA.
- **Atualização e migração de schema** com ferramentas (Alembic) e migrations versionadas.
- **Testes automatizados** (unit/integration) e validação de contratos API.
- **Correções de bugs/consistência de rotas**: há duplicidades no código (ex.: endpoints DELETE repetidos) que devem ser eliminadas.
- **Observabilidade**: logs estruturados, métricas (Prometheus) e tracing.

