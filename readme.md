# LashFlow API

Backend para sistema de gestão de extensão de cílios. Single-tenant, uma conta por profissional.

**Stack:** FastAPI · SQLModel · JWT · SQLite (dev) / PostgreSQL (prod)

---

## Documentacao

| # | Guia | Conteudo |
|---|------|----------|
| 1 | [Setup e Configuracao](docs/01-setup.md) | Instalacao, variaveis de ambiente, Docker, estrutura de pastas |
| 2 | [Autenticacao](docs/02-auth.md) | Fluxo JWT, refresh token, endpoints de auth, integracao Next.js |
| 3 | [Endpoints](docs/03-endpoints.md) | Referencia completa de todos os endpoints com exemplos TypeScript |
| 4 | [Modelo de Dados](docs/04-data-model.md) | Enums, schemas, regras de negocio, segmentacao de clientes |
| 5 | [Testes](docs/05-testing.md) | Como rodar, estrutura por camada, fixtures, exemplos de cada tipo |

---

## Inicio rapido

```bash
# Instalar dependencias
python -m venv env && source env/bin/activate
pip install -r requirements-dev.txt

# Configurar ambiente
cp .env.example .env

# Rodar (SQLite automatico, admin criado no primeiro start)
uvicorn app.main:app --reload
```

Acesse: `http://localhost:8000/docs`

Login inicial: `admin` / `admin` (altere `ADMIN_PASSWORD` no `.env`)

---

## Rodar testes

```bash
pytest tests/unit/        # logica pura de dominio
pytest tests/integration/ # repositorios com SQLite :memory:
pytest tests/e2e/         # rotas completas com TestClient
pytest                    # todos
```

---

## Docker

```bash
# Dev com Postgres + hot reload
docker compose -f docker-compose.local.yml up --build

# Producao
docker compose up --build
```
