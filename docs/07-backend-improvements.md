# Backend — Melhorias e Novos Endpoints

> Documento de referência para desenvolvimento do backend LashFlow, baseado na análise do frontend atual.
> Tudo que está descrito aqui é necessário para o frontend funcionar completamente sem mock data.

---

## 🔴 Crítico — Frontend travado em mock sem isso

### 1. Convenção de nomenclatura: snake_case ↔ camelCase

O FastAPI retorna snake_case por padrão, mas o frontend usa camelCase em todas as entidades.
**Solução recomendada:** configurar Pydantic para aceitar input em camelCase e retornar camelCase.

```python
# app/infrastructure/settings.py ou app/main.py
from pydantic import ConfigDict
from pydantic.alias_generators import to_camel

# Em cada schema de response:
class ClientResponse(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: str
    name: str
    total_spent: int        # exposto como "totalSpent"
    appointments_count: int # exposto como "appointmentsCount"
    created_at: datetime    # exposto como "createdAt"
    # ...
```

Ou configurar globalmente no `app/main.py`:
```python
app = FastAPI()
# Todos os modelos que herdam de um BaseModel com alias_generator=to_camel
# já respondem em camelCase automaticamente.
```

**Mapeamento completo necessário:**

| Frontend (camelCase) | Backend (snake_case) |
|---|---|
| `clientId` | `client_id` |
| `procedureId` | `procedure_id` |
| `scheduledAt` | `scheduled_at` |
| `durationMinutes` | `duration_minutes` |
| `endsAt` | `ends_at` |
| `priceCharged` | `price_charged` |
| `serviceType` | `service_type` |
| `requestedAt` | `requested_at` |
| `confirmedAt` | `confirmed_at` |
| `cancelledAt` | `cancelled_at` |
| `cancellationReason` | `cancellation_reason` |
| `cancelledBy` | `cancelled_by` |
| `paymentId` | `payment_id` |
| `createdAt` | `created_at` |
| `updatedAt` | `updated_at` |
| `totalSpent` | `total_spent` |
| `appointmentsCount` | `appointments_count` |
| `lastAppointmentDate` | `last_appointment_date` |
| `favoriteProcedureId` | `favorite_procedure_id` |
| `zipCode` | `zip_code` |
| `amountInCents` | `amount_in_cents` |
| `referenceMonth` | `reference_month` |
| `dueDay` | `due_day` |
| `isPaid` | `is_paid` |
| `paidAt` | `paid_at` |
| `installmentTotal` | `installment_total` |
| `installmentCurrent` | `installment_current` |
| `installmentGroupId` | `installment_group_id` |
| `priceInCents` | `price_in_cents` |
| `durationMinutes` | `duration_minutes` |
| `imageUrl` | `image_url` |
| `isActive` | `is_active` |
| `totalAmountInCents` | `total_amount_in_cents` |
| `paidAmountInCents` | `paid_amount_in_cents` |
| `appointmentId` | `appointment_id` |
| `currentStock` | `current_stock` |
| `minimumStock` | `minimum_stock` |
| `unitCostInCents` | `unit_cost_in_cents` |
| `materialId` | `material_id` |
| `dayOfWeek` | `day_of_week` |
| `startTime` | `start_time` |
| `endTime` | `end_time` |
| `isAvailable` | `is_available` |
| `isSuperuser` | `is_superuser` |

---

### 2. Settings — Service completo novo

A página de configurações (`/configuracoes`) está 100% hardcoded em mock data.
Nenhum dos endpoints de settings está sendo chamado.

#### `GET /api/v1/settings/time-slots`

Retorna os horários de atendimento por dia da semana.

```json
// Response 200
[
  { "id": "uuid", "dayOfWeek": 1, "startTime": "09:00", "endTime": "18:00", "isAvailable": true },
  { "id": "uuid", "dayOfWeek": 2, "startTime": "09:00", "endTime": "18:00", "isAvailable": true },
  { "id": "uuid", "dayOfWeek": 6, "startTime": "09:00", "endTime": "14:00", "isAvailable": true }
  // Dias não listados = fechado
]
```

#### `PUT /api/v1/settings/time-slots`

Substitui todos os horários (upsert).

```json
// Request
{
  "slots": [
    { "dayOfWeek": 1, "startTime": "09:00", "endTime": "18:00", "isAvailable": true },
    { "dayOfWeek": 6, "startTime": "09:00", "endTime": "14:00", "isAvailable": true }
  ]
}
// Response 200 — lista atualizada
```

#### `GET /api/v1/settings/blocked-dates`

```json
// Response 200
[
  { "id": "uuid", "date": "2025-12-25", "reason": "Natal" },
  { "id": "uuid", "date": "2025-01-01", "reason": "Ano Novo" }
]
```

#### `POST /api/v1/settings/blocked-dates`

```json
// Request
{ "date": "2025-12-25", "reason": "Natal" }
// Response 201
{ "id": "uuid", "date": "2025-12-25", "reason": "Natal" }
```

#### `DELETE /api/v1/settings/blocked-dates/:id`

```
Response 204 No Content
```

---

### 3. Booking público — `/public/procedures`

A página de agendamento público (`/agendar`) usa `mockProcedures` para listar os procedimentos.
O endpoint já existe no backend mas o frontend não está chamando.

**Confirmação necessária:** `GET /api/v1/public/procedures` deve retornar apenas procedimentos com `is_active = true`, sem autenticação. Sem campos sensíveis de custo/margem.

```json
// Response 200
[
  {
    "id": "uuid",
    "name": "Volume Russo",
    "technique": "volume",
    "priceInCents": 25000,
    "durationMinutes": 120,
    "description": "...",
    "imageUrl": null
  }
]
```

---

## 🟡 Alto — Feature incompleta

### 4. Dashboard — Endpoints de agregação

O `useDashboard` faz **5 chamadas paralelas** (clients, revenue stats, monthly revenue, today appointments, pending approvals). O backend já tem endpoints de agregação que devem ser usados.

#### `GET /api/v1/dashboard/stats`

```json
// Response 200
{
  "totalClients": 142,
  "clientsWithUpcomingAppointments": 18,
  "todayAppointmentsCount": 4,
  "revenueStats": {
    "todayInCents": 75000,
    "thisWeekInCents": 320000,
    "thisMonthInCents": 1250000,
    "lastMonthInCents": 1100000,
    "growthPercent": 13.6
  },
  "monthlyRevenue": [
    { "month": "2025-01", "amountInCents": 980000 }
  ],
  "pendingApprovalsCount": 2
}
```

#### `GET /api/v1/dashboard/today`

```json
// Response 200
{
  "appointments": [
    {
      "id": "uuid",
      "clientId": "uuid",
      "procedureId": "uuid",
      "scheduledAt": "2025-04-10T09:00:00-03:00",
      "endsAt": "2025-04-10T11:00:00-03:00",
      "status": "confirmed",
      "priceCharged": 25000
    }
  ],
  "pendingApprovals": [...]
}
```

---

### 5. Agendamento — campos obrigatórios no response

O frontend referencia os seguintes campos nos agendamentos que devem estar presentes no response:

```typescript
// O que o frontend usa e precisa estar no response:
{
  "id": "uuid",
  "clientId": "uuid",
  "procedureId": "uuid",
  "paymentId": "uuid | null",       // Vincula pagamento ao agendamento
  "serviceType": "application",      // application|maintenance|removal|lash_lifting|permanent
  "status": "confirmed",
  "scheduledAt": "2025-04-10T09:00:00-03:00",
  "durationMinutes": 120,
  "endsAt": "2025-04-10T11:00:00-03:00",  // Calculado: scheduledAt + durationMinutes
  "priceCharged": 25000,             // Preço cobrado naquele agendamento especificamente
  "notes": "...",
  "requestedAt": "...",
  "confirmedAt": "...",
  "cancelledAt": "...",
  "cancellationReason": "...",
  "cancelledBy": "professional | client",
  "createdAt": "...",
  "updatedAt": "..."
}
```

**Campos que precisam de atenção:**

- `endsAt`: deve ser calculado pelo backend (`scheduled_at + duration_minutes`) e retornado no response. O frontend não calcula.
- `priceCharged`: deve ser o preço cobrado **no momento do agendamento**, não o preço atual do procedimento (que pode ter mudado).
- `paymentId`: vincula o agendamento ao pagamento gerado. Deve ser preenchido quando o pagamento for criado.
- `durationMinutes`: deve vir do procedimento associado no momento da criação, não recalculado a cada request.

#### `POST /api/v1/appointments` — Request esperado

```json
{
  "clientId": "uuid",
  "procedureId": "uuid",
  "scheduledAt": "2025-04-10T09:00:00-03:00",
  "serviceType": "application",     // opcional, default: "application"
  "priceCharged": 25000,            // opcional, default: procedure.price_in_cents
  "notes": "Primeira vez"           // opcional
}
```

#### `GET /api/v1/appointments` — Filtros necessários

```
GET /appointments?clientId=uuid&status=confirmed,pending_approval&from=2025-04-01&to=2025-04-30
```

O frontend usa `from` e `to` para filtrar por intervalo de datas (ex: agenda semanal). O `to` precisa estar implementado no backend.

---

### 6. Cancelamento de agendamento — body snake_case

O frontend envia:
```json
{ "reason": "Cliente desmarcou", "cancelled_by": "client" }
```

Confirmar que o backend aceita `cancelled_by` (snake_case) em `PATCH /appointments/:id/cancel`.

---

## 🟢 Médio — Melhorias de experiência

### 7. Despesas — Categorias customizadas

O frontend permite criar categorias de despesa além do enum padrão.
Atualmente salvo em `localStorage` — não persiste entre dispositivos.

**Opção A (recomendada):** Adicionar suporte a string livre no campo `category` de expense, não só os valores do enum. O backend valida se é string não vazia.

**Opção B:** Novo endpoint de categorias customizadas:

```
GET  /expenses/categories          → lista categorias do enum + customizadas
POST /expenses/categories          → { "name": "Minha Categoria" }
DELETE /expenses/categories/:id    → remove categoria customizada
```

---

### 8. Pagamentos — Campos no response

O frontend (`/financeiro`) exibe a tabela de fluxo de caixa com:
- Nome do cliente
- Nome do procedimento
- Valor
- Método
- Status
- Data

O endpoint `GET /payments/cash-flow` precisa retornar esses campos populados (com join no client e appointment/procedure), não apenas IDs:

```json
// Response esperado de GET /payments/cash-flow
[
  {
    "id": "uuid",
    "appointmentId": "uuid",
    "clientId": "uuid",
    "clientName": "Ana Silva",           // join necessário
    "procedureName": "Volume Russo",     // join necessário
    "totalAmountInCents": 25000,
    "paidAmountInCents": 25000,
    "method": "pix",
    "status": "paid",
    "createdAt": "2025-04-10T..."
  }
]
```

---

### 9. Clientes — Response com campos calculados

O frontend exibe na tela de cliente (`/clientes/:id`):
- `totalSpent` — soma de pagamentos pagos
- `appointmentsCount` — contagem de agendamentos concluídos
- `lastAppointmentDate` — data do último agendamento concluído
- `favoriteProcedureId` — procedimento mais frequente
- `segments` — array calculado automaticamente

Esses campos já estão documentados como calculados no backend (`docs/04-data-model.md`), mas precisam estar **sempre presentes** no response de `GET /clients/:id` e `GET /clients`.

---

### 10. Stock — Response de movimentações com dados do material

O frontend no estoque exibe o histórico de movimentações com nome do material. O endpoint `GET /stock/movements` deve retornar o nome do material junto:

```json
[
  {
    "id": "uuid",
    "materialId": "uuid",
    "materialName": "Cola Preta",   // join necessário
    "type": "purchase",
    "quantity": 5,
    "unitCostInCents": 4990,
    "notes": "...",
    "createdAt": "..."
  }
]
```

---

### 11. Booking público — Lookup de cliente por telefone

O frontend envia na criação de agendamento público:

```json
{
  "procedureId": "uuid",
  "scheduledAt": "2025-04-10T09:00:00-03:00",
  "client": {
    "name": "Ana Paula",
    "phone": "11988887777"
  },
  "notes": "..."
}
```

O backend deve:
1. Normalizar o telefone (remover formatação)
2. Buscar cliente existente por telefone
3. Se não encontrar, criar o cliente automaticamente
4. Criar o agendamento com `status = pending_approval`
5. Retornar o agendamento criado

O `professional_id` deve vir do contexto da aplicação (configuração do studio), não do JWT (booking é público, sem autenticação).

**Questão em aberto:** como identificar o `professional_id` no booking público? Opções:
- A. URL com identificador único do studio: `GET /public/:studioSlug/procedures`
- B. Domínio customizado (mais complexo)
- C. Apenas um profissional por instância (mais simples, recomendado para MVP)

---

## 📋 Resumo de prioridades

| # | Item | Impacto | Esforço |
|---|---|---|---|
| 1 | camelCase nos responses (alias_generator) | 🔴 Bloqueia tudo | Baixo |
| 2 | Settings (time-slots + blocked-dates) | 🔴 Página vazia | Médio |
| 3 | `/public/procedures` confirmado | 🔴 Booking público quebrado | Baixo |
| 4 | `endsAt` calculado no agendamento | 🔴 Frontend não calcula | Baixo |
| 5 | Dashboard `/dashboard/stats` e `/today` | 🟡 Otimização | Médio |
| 6 | Filtro `to` em `GET /appointments` | 🟡 Agenda semanal incompleta | Baixo |
| 7 | `clientName` + `procedureName` em cash-flow | 🟡 Tabela financeiro vazia | Baixo |
| 8 | `materialName` em stock movements | 🟡 Histórico sem nome | Baixo |
| 9 | Categorias customizadas de despesa | 🟢 Workaround existe | Alto |
| 10 | Booking público — resolução de professional_id | 🟢 Só em multi-tenant | Alto |
