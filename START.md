# START (Como ligar e usar)

Este documento descreve como iniciar o AdaptMath localmente usando **Docker Compose**.

## 1) Pré-requisitos

- Docker + Docker Compose instalados
- Espaço em disco para download do modelo (Transformers)

## 2) Configurar variáveis de ambiente

Na raiz do projeto, verifique/crie o arquivo `.env`.

Variáveis utilizadas pelo sistema:
- `DATABASE_URL` (conexão com o Postgres)
- `POSTGRES_PASSWORD` (senha do Postgres no serviço `db`)
- `SECRET_KEY` (segredo para sessões/JWT)
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `REFRESH_TOKEN_EXPIRE_DAYS`
- `HF_TOKEN` (token do Hugging Face para baixar artefatos do modelo)

Opcional (mas usado pelo código/compose):
- `REDIS_HOST` / `REDIS_PORT` / `REDIS_DB`

## 3) Subir a aplicação

Na pasta do projeto (mesma do `docker-compose.yml`):

```bash
docker compose up --build
```

Durante o boot:
- Postgres inicia e passa no healthcheck
- o backend roda `python -m backend.database.setup_database` (cria tabelas e prepara/importa questões)
- em seguida inicia o `gunicorn` na porta **5000**

## 4) Acessar o sistema

Abra no navegador:

- `http://localhost:5000`

## 5) Fluxo de uso (resumo)

1. Acesse a landing e vá para **Login**.
2. Se necessário, crie uma conta em **Registro**.
3. No **Dashboard**, inicie o **teste de aptidão** quando quiser.
4. Use a área de **questões** (filtros, salvas, reportes).
5. Para IA:
   - solicite **dica** por questão
   - abra/continue conversas no chat
6. Em **Relatórios**, consulte insights e análise detalhada.

## 6) Troubleshooting rápido

- **Erro ao conectar no Postgres**:
  - confirme `DATABASE_URL` e se `POSTGRES_PASSWORD` em `.env` bate com o compose
- **Falha no download do modelo**:
  - garanta que `HF_TOKEN` está correto e com permissões
- **Demora na primeira execução**:
  - é esperado: import/classificação + download do modelo

## 7) Encerrar

```bash
docker compose down
```

> As volumes do Postgres e Redis permanecem conforme a configuração do compose (há `postgres_data` e `redis_data`).