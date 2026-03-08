# Setup e Configuração

[← Voltar ao índice](../readme.md)

## Requisitos

- Python 3.12+
- pip

---

## Instalação local

```bash
git clone <repo>
cd lashflow-api

# Criar e ativar virtualenv
python -m venv env
source env/bin/activate       # Linux/Mac
env\Scripts\activate          # Windows

# Instalar dependências de dev
pip install -r requirements-dev.txt

# Copiar e configurar variáveis de ambiente
cp .env.example .env
```

---

## Variáveis de Ambiente

Arquivo `.env` na raiz do projeto:

| Variável | Padrão | Obrigatória em prod | Descrição |
|----------|--------|---------------------|-----------|
| `DATABASE_URL` | `sqlite:///./lashflow.db` | Sim | URL do banco. SQLite para dev, Postgres para prod |
| `SECRET_KEY` | `dev-secret-key-...` | **Sim** | Chave de assinatura JWT. Gere com `openssl rand -hex 32` |
| `ALGORITHM` | `HS256` | Não | Algoritmo JWT |
| `JWT_EXPIRE_DAYS` | `7` | Não | Validade do access token em dias |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `30` | Não | Validade do refresh token em dias |
| `ADMIN_USERNAME` | `admin` | Não | Username do admin criado no primeiro startup |
| `ADMIN_PASSWORD` | `admin` | **Sim** | Senha do admin. Troque em produção |
| `ADMIN_EMAIL` | *(vazio)* | Não | Email do admin inicial |

### Exemplo `.env` para produção

```env
DATABASE_URL=postgresql+psycopg2://lashflow:senha_forte@db:5432/lashflow
SECRET_KEY=c3d1e2f4a5b6...  # openssl rand -hex 32
JWT_EXPIRE_DAYS=7
REFRESH_TOKEN_EXPIRE_DAYS=30
ADMIN_USERNAME=admin
ADMIN_PASSWORD=senha_muito_forte_aqui
ADMIN_EMAIL=admin@seudominio.com
```

### URL do banco

```
# SQLite (local, sem instalar nada)
DATABASE_URL=sqlite:///./lashflow.db

# PostgreSQL
DATABASE_URL=postgresql+psycopg2://usuario:senha@host:5432/nome_banco

# PostgreSQL via Docker Compose
DATABASE_URL=postgresql+psycopg2://lashflow:lashflow@db:5432/lashflow
```

---

## Rodando o Projeto

### Dev local (SQLite automático)

```bash
uvicorn app.main:app --reload
# API disponível em http://localhost:8000
# Swagger UI em  http://localhost:8000/docs
```

Na primeira execução, o backend cria as tabelas e o usuário admin com os valores do `.env`.

### Docker — dev com Postgres

```bash
# Subir (Postgres + app com hot reload)
docker compose -f docker-compose.local.yml up --build

# Parar
docker compose -f docker-compose.local.yml down

# Ver logs do app
docker compose -f docker-compose.local.yml logs -f app
```

### Docker — produção / staging

```bash
docker compose up --build
docker compose down
docker compose logs -f app
```

---

## Debug no VSCode

O arquivo `.vscode/launch.json` já está configurado. Pressione `F5` para iniciar o servidor em modo debug com breakpoints.

---

## Estrutura de Pastas

```
lashflow-api/
├── app/
│   ├── main.py                    # factory, lifespan, routers, exception handlers
│   ├── domain/
│   │   ├── enums.py               # todos os enums do sistema
│   │   ├── exceptions.py          # exceções de domínio (não HTTP)
│   │   ├── entities/              # SQLModel table classes
│   │   └── services/              # lógica pura de negócio (sem DB)
│   ├── infrastructure/
│   │   ├── settings.py            # Settings via pydantic-settings
│   │   ├── database.py            # engine, get_session
│   │   └── repositories/         # todas as queries ficam aqui
│   └── interface/
│       ├── dependencies.py        # get_current_user, JWT utils
│       ├── schemas/               # Pydantic request/response
│       └── routers/               # endpoints FastAPI
├── tests/
│   ├── conftest.py
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── docs/                          # esta pasta
├── Dockerfile
├── docker-compose.yml
├── docker-compose.local.yml
├── requirements.txt
├── requirements-dev.txt
└── .env.example
```

---

## Regras de Importação entre Camadas

| Camada | Pode importar | NÃO pode importar |
|--------|--------------|-------------------|
| `domain/entities` | `enums` | repositories, services, routers |
| `domain/services` | `entities`, `enums`, `exceptions` | repositories, HTTP |
| `infrastructure/repositories` | `entities`, `database` | `domain/services`, routers |
| `interface/routers` | `schemas`, `repositories`, `domain/services`, `dependencies` | — |

Repositories **nunca** importam domain services. Domain services **nunca** importam repositories.
