# Referência de Endpoints

[← Voltar ao índice](../readme.md)

**Base URL:** `/api/v1`
**Autenticação:** `Authorization: Bearer <access_token>` em todas as rotas exceto `/public/*` e `/auth/login`.

---

## Paginação

```json
// Response (onde aplicável)
{
  "data": [...],
  "total": 142,
  "page": 1,
  "per_page": 20
}
```

## Erros padrão

```json
{ "error": "SLOT_UNAVAILABLE", "message": "Horário já ocupado", "status_code": 409 }
```

| Status | Significado |
|--------|-------------|
| `400` | Validação de input |
| `401` | Não autenticado |
| `403` | Sem permissão |
| `404` | Não encontrado |
| `409` | Conflito (slot ocupado, telefone duplicado) |
| `422` | Regra de negócio violada (estoque insuficiente, transição inválida) |

---

## Clientes — `/clients`

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/clients?search=&page=1&per_page=20` | Lista paginada |
| `GET` | `/clients/search?q=` | Busca rápida (sem paginação) |
| `GET` | `/clients/:id` | Detalhe + stats calculados |
| `POST` | `/clients` | Criar |
| `PUT` | `/clients/:id` | Atualizar |
| `DELETE` | `/clients/:id` | Soft delete |

```ts
// Criar cliente
const res = await apiFetch('/clients', {
  method: 'POST',
  body: JSON.stringify({
    name: 'Ana Silva',
    phone: '11999990000',           // apenas dígitos (o backend normaliza)
    email: 'ana@email.com',         // opcional
    instagram: '@anasilva',         // opcional
    birthday: '1995-04-22',         // opcional, "YYYY-MM-DD"
    notes: 'Prefere volume russo',  // opcional
    address: {                      // opcional
      street: 'Rua das Flores, 123',
      neighborhood: 'Centro',
      city: 'São Paulo',
      state: 'SP',
      zip_code: '01001000',
    },
  }),
})

// Response 201
{
  "id": "uuid",
  "name": "Ana Silva",
  "phone": "11999990000",
  "email": "ana@email.com",
  "segments": [],
  "total_spent": 0,               // centavos, calculado
  "appointments_count": 0,        // calculado
  "last_appointment_date": null,  // calculado
  "favorite_procedure_id": null,  // calculado
  "created_at": "...",
  "updated_at": "..."
}

// Busca rápida
const res = await apiFetch('/clients/search?q=Ana')
// Response: Client[]
```

---

## Procedimentos — `/procedures`

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/procedures?activeOnly=true` | Lista |
| `GET` | `/procedures/:id` | Detalhe |
| `POST` | `/procedures` | Criar |
| `PUT` | `/procedures/:id` | Atualizar |
| `DELETE` | `/procedures/:id` | Deletar |
| `PATCH` | `/procedures/:id/toggle` | Ativar/desativar |

```ts
await apiFetch('/procedures', {
  method: 'POST',
  body: JSON.stringify({
    name: 'Volume Russo',
    technique: 'volume',        // ver enum LashTechnique
    price_in_cents: 25000,      // R$ 250,00
    duration_minutes: 120,
    description: 'Descrição',   // opcional
    image_url: 'https://...',   // opcional
  }),
})
```

---

## Agendamentos — `/appointments`

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/appointments?clientId=&status=&from=&to=` | Lista |
| `GET` | `/appointments/available-slots?date=YYYY-MM-DD&procedureId=uuid` | Slots disponíveis |
| `GET` | `/appointments/pending-approvals` | Aguardando aprovação |
| `GET` | `/appointments/today` | Agendamentos de hoje |
| `GET` | `/appointments/:id` | Detalhe |
| `POST` | `/appointments` | Criar |
| `PATCH` | `/appointments/:id/status` | Atualizar status |
| `PATCH` | `/appointments/:id/cancel` | Cancelar |

```ts
// Buscar slots disponíveis
const res = await apiFetch('/appointments/available-slots?date=2025-04-10&procedureId=uuid')
// Response: { "slots": ["2025-04-10T09:00:00", "2025-04-10T09:30:00", ...] }

// Criar agendamento
await apiFetch('/appointments', {
  method: 'POST',
  body: JSON.stringify({
    client_id: 'uuid',
    procedure_id: 'uuid',
    scheduled_at: '2025-04-10T09:00:00-03:00',
    service_type: 'application',  // opcional
    price_charged: 25000,
    notes: 'Primeira vez',        // opcional
  }),
})

// Aprovar
await apiFetch(`/appointments/${id}/status`, {
  method: 'PATCH',
  body: JSON.stringify({ status: 'confirmed' }),
})

// Cancelar
await apiFetch(`/appointments/${id}/cancel`, {
  method: 'PATCH',
  body: JSON.stringify({
    reason: 'Cliente desmarcou',
    cancelled_by: 'client',   // "client" | "professional"
  }),
})
```

**Transições de status válidas:**
```
pending_approval → confirmed | cancelled
confirmed        → in_progress | cancelled | no_show
in_progress      → completed | cancelled
completed        → (estado final)
cancelled        → (estado final)
no_show          → (estado final)
```

---

## Pagamentos — `/payments`

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/payments?from=&to=` | Lista |
| `GET` | `/payments/stats` | Estatísticas de receita |
| `GET` | `/payments/monthly-revenue?months=6` | Receita mensal |
| `GET` | `/payments/method-breakdown?from=&to=` | Por método de pagamento |
| `GET` | `/payments/cash-flow?from=&to=` | Extrato |
| `GET` | `/payments/by-appointment/:appointmentId` | Por agendamento |
| `GET` | `/payments/:id` | Detalhe |
| `POST` | `/payments` | Criar |
| `PATCH` | `/payments/:id` | Atualizar / adicionar pagamento parcial |

```ts
// Criar pagamento simples
await apiFetch('/payments', {
  method: 'POST',
  body: JSON.stringify({
    appointment_id: 'uuid',
    client_id: 'uuid',
    total_amount_in_cents: 25000,
    paid_amount_in_cents: 25000,
    method: 'pix',   // "cash"|"credit_card"|"debit_card"|"pix"|"bank_transfer"|"other"
  }),
})
// status calculado automaticamente: pending | partial | paid

// Adicionar pagamento parcial (pagamento misto)
await apiFetch(`/payments/${id}`, {
  method: 'PATCH',
  body: JSON.stringify({
    partial_payment: {
      amount_in_cents: 12000,
      method: 'pix',
    },
  }),
})

// GET /payments/stats
// → { today_in_cents, this_week_in_cents, this_month_in_cents, last_month_in_cents, growth_percent }

// GET /payments/monthly-revenue?months=6
// → [{ month: "2025-01", amount_in_cents: 980000 }, ...]

// GET /payments/method-breakdown
// → { pix: 580000, credit_card: 320000, cash: 150000, ... }
```

---

## Anamneses — `/anamneses`

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/anamneses?clientId=uuid` | Lista por cliente (mais recente primeiro) |
| `GET` | `/anamneses/:id` | Detalhe |
| `POST` | `/anamneses` | Criar |
| `PUT` | `/anamneses/:id` | Atualizar |

```ts
await apiFetch('/anamneses', {
  method: 'POST',
  body: JSON.stringify({
    client_id: 'uuid',
    procedure_type: 'extension',    // "extension"|"permanent"|"lash_lifting"
    has_allergy: true,
    allergy_details: 'Látex',       // obrigatório se has_allergy = true
    had_eye_surgery_last_3_months: false,
    has_eye_disease: false,
    uses_eye_drops: false,
    family_thyroid_history: false,
    has_glaucoma: false,
    prone_to_blepharitis: false,
    has_epilepsy: false,
    authorized_photo_publishing: true,
    mapping: {                      // opcional
      size: '13mm',
      curve: 'C',
      thickness: '0.07',
    },
  }),
})
```

---

## Estoque — `/stock`

### Materiais

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/stock/materials?category=&search=&lowStock=` | Lista |
| `GET` | `/stock/materials/alerts` | Abaixo do mínimo |
| `GET` | `/stock/value` | Valor total do estoque |
| `GET` | `/stock/monthly-costs?months=6` | Custos mensais |
| `GET` | `/stock/materials/:id` | Detalhe |
| `POST` | `/stock/materials` | Criar |
| `PUT` | `/stock/materials/:id` | Atualizar |
| `DELETE` | `/stock/materials/:id` | Desativar (soft) |

### Movimentações

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/stock/movements?materialId=&from=&to=` | Lista |
| `POST` | `/stock/movements` | Registrar movimentação |

```ts
// Criar material
await apiFetch('/stock/materials', {
  method: 'POST',
  body: JSON.stringify({
    name: 'Cola Preta',
    category: 'quimicos',
    unit: 'ml',
    unit_cost_in_cents: 4990,
    current_stock: 10,
    minimum_stock: 3,
  }),
})

// Registrar movimentação
await apiFetch('/stock/movements', {
  method: 'POST',
  body: JSON.stringify({
    material_id: 'uuid',
    type: 'purchase',    // "purchase" | "usage" | "adjustment"
    quantity: 5,
    unit_cost_in_cents: 4990,
    notes: 'Compra fornecedor X',
  }),
})
// purchase   → currentStock += quantity
// usage      → currentStock -= quantity (422 se negativo)
// adjustment → currentStock = quantity (valor absoluto)
```

---

## Despesas — `/expenses`

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/expenses?month=YYYY-MM&category=&isPaid=` | Lista |
| `GET` | `/expenses/summary?month=YYYY-MM` | Resumo do mês |
| `GET` | `/expenses/monthly-totals?months=6` | Totais mensais |
| `GET` | `/expenses/:id` | Detalhe |
| `POST` | `/expenses` | Criar (com suporte a parcelamento) |
| `PUT` | `/expenses/:id` | Atualizar |
| `DELETE` | `/expenses/:id` | Deletar parcela individual |
| `PATCH` | `/expenses/:id/pay` | Marcar como paga |

```ts
// Despesa simples
await apiFetch('/expenses', {
  method: 'POST',
  body: JSON.stringify({
    name: 'Aluguel',
    category: 'aluguel',
    amount_in_cents: 150000,
    recurrence: 'monthly',
    due_day: 5,
    reference_month: '2025-04',
  }),
})

// Despesa parcelada (gera N registros automaticamente)
await apiFetch('/expenses', {
  method: 'POST',
  body: JSON.stringify({
    name: 'Cadeira Reclinável',
    category: 'material',
    amount_in_cents: 25000,   // valor de cada parcela
    recurrence: 'monthly',
    reference_month: '2025-04',
    installments: 6,
  }),
})
// Response: { expense, installments_created: 6, installment_group_id: "uuid" }

// GET /expenses/summary?month=2025-04
// → { month, total_in_cents, paid_in_cents, pending_in_cents, by_category: { aluguel: 150000 } }
```

---

## Configurações de Agenda — `/settings`

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/settings/time-slots` | Horários por dia da semana |
| `PUT` | `/settings/time-slots` | Atualizar horários (substitui todos) |
| `GET` | `/settings/blocked-dates` | Datas bloqueadas |
| `POST` | `/settings/blocked-dates` | Bloquear data |
| `DELETE` | `/settings/blocked-dates/:id` | Desbloquear |

```ts
// Configurar horários
await apiFetch('/settings/time-slots', {
  method: 'PUT',
  body: JSON.stringify({
    slots: [
      { day_of_week: 1, start_time: '09:00', end_time: '18:00', is_available: true },  // Segunda
      { day_of_week: 2, start_time: '09:00', end_time: '18:00', is_available: true },
      { day_of_week: 6, start_time: '09:00', end_time: '14:00', is_available: true },  // Sábado
      // 0 = Domingo, 1 = Segunda, ..., 6 = Sábado
    ],
  }),
})

// Bloquear data
await apiFetch('/settings/blocked-dates', {
  method: 'POST',
  body: JSON.stringify({ date: '2025-12-25', reason: 'Natal' }),
})
```

---

## Dashboard — `/dashboard`

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/dashboard/stats` | Resumo geral |
| `GET` | `/dashboard/today` | Agenda de hoje + pendências |

```ts
// GET /dashboard/stats
{
  "total_clients": 142,
  "clients_with_upcoming_appointments": 18,
  "today_appointments_count": 4,
  "revenue_stats": {
    "today_in_cents": 75000,
    "this_week_in_cents": 320000,
    "this_month_in_cents": 1250000,
    "last_month_in_cents": 1100000,
    "growth_percent": 13.6
  },
  "monthly_revenue": [
    { "month": "2025-01", "amount_in_cents": 980000 }
  ],
  "pending_approvals_count": 2
}
```

---

## Agendamento Público — `/public` *(sem autenticação)*

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/public/procedures` | Procedimentos ativos |
| `GET` | `/public/available-slots?date=&procedureId=` | Slots disponíveis |
| `POST` | `/public/appointments` | Solicitar agendamento |

```ts
// Fluxo de booking público

// 1. Carregar procedimentos
const procedures = await fetch('/api/v1/public/procedures').then(r => r.json())

// 2. Carregar slots
const { slots } = await fetch(
  `/api/v1/public/available-slots?date=2025-04-10&procedureId=${procedureId}`
).then(r => r.json())

// 3. Confirmar agendamento
const res = await fetch('/api/v1/public/appointments', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    procedure_id: 'uuid',
    scheduled_at: '2025-04-10T09:00:00-03:00',
    client: {
      name: 'Ana Paula',
      phone: '11988887777',  // o backend normaliza e busca/cria o cliente
    },
    notes: 'Prefiro técnica natural',  // opcional
  }),
})
// → Appointment com status "pending_approval"
// → Profissional aprova via PATCH /appointments/:id/status { status: "confirmed" }
```
