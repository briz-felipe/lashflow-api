# Guia de Testes

[← Voltar ao índice](../readme.md)

## Estrutura

```
tests/
├── conftest.py              # fixtures compartilhadas
├── unit/                    # lógica pura, sem DB, sem HTTP
│   ├── test_appointment_service.py
│   ├── test_slot_calculator.py
│   ├── test_payment_service.py
│   ├── test_stock_service.py
│   ├── test_expense_service.py
│   └── test_client_service.py
├── integration/             # repositórios com SQLite :memory:
│   ├── test_user_repository.py
│   ├── test_client_repository.py
│   └── test_expense_repository.py
└── e2e/                     # rotas completas com TestClient
    ├── test_auth.py
    ├── test_clients.py
    ├── test_appointments.py
    ├── test_public.py
    └── test_expenses.py
```

---

## Como executar

### Pré-requisito

```bash
pip install -r requirements-dev.txt
```

### Por camada

```bash
pytest tests/unit/        # lógica pura de domínio — mais rápido
pytest tests/integration/ # repositórios com SQLite :memory:
pytest tests/e2e/         # rotas completas com TestClient
```

### Todos os testes

```bash
pytest
```

### Com verbose e output

```bash
pytest -v                         # nome de cada teste
pytest -v -s                      # inclui prints e logs
pytest --tb=short                 # traceback curto em falhas
```

### Filtrar por nome ou marcador

```bash
pytest -k "test_login"            # todos os testes com "login" no nome
pytest -k "client and not delete" # composição de filtros
pytest tests/e2e/test_auth.py     # arquivo específico
pytest tests/e2e/test_auth.py::TestAuthLogin::test_valid_credentials  # teste específico
```

### Com cobertura

```bash
pip install pytest-cov
pytest --cov=app --cov-report=term-missing
pytest --cov=app --cov-report=html   # gera htmlcov/index.html
```

---

## Fixtures — `tests/conftest.py`

Todas as fixtures estão em `conftest.py` e ficam disponíveis automaticamente em qualquer teste.

### `engine`
Cria um banco SQLite `:memory:` com todas as tabelas. Descartado ao final de cada teste.

### `session`
Abre uma `Session` sobre o engine em memória. Usada nos testes de integração.

### `client_app`
`TestClient` do FastAPI com `dependency_overrides[get_session]` apontando para o banco em memória. Isolado por teste — sem estado persistente entre testes.

### `admin_user`
Cria um `User` com `is_superuser=True` no banco em memória. Depende de `session`.

### `auth_headers`
Faz login com o `admin_user` e retorna `{"Authorization": "Bearer <token>"}`. Depende de `client_app` e `admin_user`.

```python
# Exemplo de uso nas fixtures
def test_meu_endpoint(client_app, auth_headers):
    res = client_app.get("/api/v1/clients", headers=auth_headers)
    assert res.status_code == 200
```

---

## Camada unit — `tests/unit/`

Testa lógica pura dos domain services. **Sem banco, sem HTTP.** Apenas funções e exceções.

```python
# tests/unit/test_appointment_service.py
from app.domain.enums import AppointmentStatus
from app.domain.exceptions import InvalidStatusTransition
from app.domain.services.appointment_service import validate_status_transition

def test_pending_to_confirmed():
    validate_status_transition(AppointmentStatus.pending_approval, AppointmentStatus.confirmed)

def test_completed_is_final():
    with pytest.raises(InvalidStatusTransition):
        validate_status_transition(AppointmentStatus.completed, AppointmentStatus.confirmed)
```

```python
# tests/unit/test_payment_service.py
from app.domain.services.payment_service import calculate_payment_status

def test_fully_paid():
    status = calculate_payment_status(total=25000, paid=25000)
    assert status == PaymentStatus.paid

def test_partial():
    status = calculate_payment_status(total=25000, paid=10000)
    assert status == PaymentStatus.partial
```

### Como adicionar um teste unitário

1. Crie ou edite o arquivo em `tests/unit/test_<service>.py`
2. Importe apenas do `app.domain` — sem imports de `infrastructure` ou `interface`
3. Teste cada função com entradas válidas e inválidas
4. Use `pytest.raises(SuaExcecao)` para exceções de domínio

---

## Camada integration — `tests/integration/`

Testa os repositórios usando um banco SQLite `:memory:` real. Usa a fixture `session`.

```python
# tests/integration/test_client_repository.py
from app.infrastructure.repositories.client_repository import ClientRepository
from app.domain.entities.client import Client
import uuid

def test_create_and_get_client(session):
    professional_id = uuid.uuid4()
    repo = ClientRepository(session)
    client = Client(
        professional_id=professional_id,
        name='Ana Silva',
        phone='11999990000',
    )
    created = repo.create(client)
    found = repo.get_by_id(created.id, professional_id)
    assert found.name == 'Ana Silva'

def test_soft_delete(session):
    professional_id = uuid.uuid4()
    repo = ClientRepository(session)
    client = repo.create(Client(
        professional_id=professional_id,
        name='Test',
        phone='11000000000',
    ))
    repo.soft_delete(client.id, professional_id)
    assert repo.get_by_id(client.id, professional_id) is None
```

### Como adicionar um teste de integração

1. Crie ou edite `tests/integration/test_<entity>_repository.py`
2. Use a fixture `session` — não use `client_app` nem `auth_headers`
3. Crie os objetos necessários diretamente, sem passar pelos endpoints
4. Valide queries complexas: filtros, soft delete, campos calculados

---

## Camada e2e — `tests/e2e/`

Testa as rotas completas via HTTP com `TestClient`. Usa `client_app` e `auth_headers`.

```python
# tests/e2e/test_clients.py
def test_create_client(client_app, auth_headers):
    res = client_app.post(
        '/api/v1/clients',
        json={'name': 'Ana Silva', 'phone': '11999990000'},
        headers=auth_headers,
    )
    assert res.status_code == 201
    data = res.json()
    assert data['name'] == 'Ana Silva'
    assert data['phone'] == '11999990000'

def test_duplicate_phone(client_app, auth_headers):
    payload = {'name': 'Ana', 'phone': '11888880000'}
    client_app.post('/api/v1/clients', json=payload, headers=auth_headers)
    res = client_app.post('/api/v1/clients', json=payload, headers=auth_headers)
    assert res.status_code == 409

def test_requires_auth(client_app):
    res = client_app.get('/api/v1/clients')
    assert res.status_code == 401
```

```python
# tests/e2e/test_auth.py
def test_login_success(client_app, admin_user):
    res = client_app.post(
        '/api/v1/auth/login',
        json={'username': 'admin', 'password': 'admin123'},
    )
    assert res.status_code == 200
    assert 'access_token' in res.json()
    assert 'refresh_token' in res.json()

def test_refresh_token(client_app, admin_user):
    login = client_app.post(
        '/api/v1/auth/login',
        json={'username': 'admin', 'password': 'admin123'},
    ).json()
    res = client_app.post(
        '/api/v1/auth/refresh',
        json={'refresh_token': login['refresh_token']},
    )
    assert res.status_code == 200
    assert 'access_token' in res.json()
```

### Como adicionar um teste e2e

1. Crie ou edite `tests/e2e/test_<dominio>.py`
2. Use `client_app` para requisições HTTP e `auth_headers` para autenticação
3. Sempre teste o caminho feliz **e** casos de erro (401, 404, 409, 422)
4. Não acesse o banco diretamente — use apenas a API HTTP

---

## Rodar testes no CI

Exemplo de GitHub Actions:

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -r requirements-dev.txt
      - run: pytest --tb=short
```
