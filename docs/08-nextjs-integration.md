# Next.js — Guia de Integração com a API LashFlow

> Arquitetura: **Next.js → LashFlow API diretamente** (sem BFF).
> O Next.js se comunica com o backend via fetch a partir dos Client/Server Components.
> A autenticação usa **cookies httpOnly** setados pelo backend no login.

---

## Configuração do ambiente

### Backend — `.env`

```env
# Adicionar origem do Next.js (dev e prod separados por vírgula)
CORS_ORIGINS=http://localhost:3000,https://app.lashflow.com.br
```

### Next.js — `.env.local`

```env
# URL base da API — acessível em Server Components e Route Handlers
API_URL=http://localhost:8000

# Repetir com prefixo NEXT_PUBLIC_ para Client Components (browser)
NEXT_PUBLIC_API_URL=http://localhost:8000
```

> **Produção:** `API_URL=https://api.lashflow.com.br`

---

## Autenticação

### Fluxo

O backend seta **cookies httpOnly** (`access_token`, `refresh_token`) automaticamente na resposta de login. O browser os envia de volta em todas as requisições subsequentes — nenhuma lógica extra de armazenamento necessária no frontend.

```
1. POST /api/v1/auth/login  →  backend seta cookies httpOnly
2. Todas as requests seguintes  →  browser envia cookies automaticamente
3. POST /api/v1/auth/logout  →  backend limpa os cookies
4. POST /api/v1/auth/refresh  →  renova access_token via refresh_token (cookie ou body)
```

### Requisitos cross-origin (dev)

Como Next.js (`:3000`) e a API (`:8000`) estão em origens diferentes em desenvolvimento, todas as requisições autenticadas precisam de `credentials: 'include'`:

```ts
fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/clients/`, {
  credentials: "include",  // envia cookies cross-origin
})
```

Em produção com mesmo domínio (reverse proxy), `credentials: 'include'` ainda é necessário se forem subdomínios diferentes.

### Login

```ts
// POST /api/v1/auth/login
const resp = await fetch(`${API_URL}/api/v1/auth/login`, {
  method: "POST",
  credentials: "include",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ username, password }),
})
const data = await resp.json()
// data.accessToken — JWT (também disponível via cookie httpOnly)
// data.refreshToken
// data.tokenType — "bearer"
```

### Logout

```ts
await fetch(`${API_URL}/api/v1/auth/logout`, {
  method: "POST",
  credentials: "include",
})
```

### Verificar sessão (Server Component)

```ts
import { cookies } from "next/headers"

async function getMe() {
  const cookieStore = cookies()
  const token = cookieStore.get("access_token")?.value
  if (!token) return null

  const resp = await fetch(`${process.env.API_URL}/api/v1/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  })
  if (!resp.ok) return null
  return resp.json()
}
```

---

## Convenções da API

### camelCase

Todos os responses usam **camelCase**. Os bodies de request também aceitam camelCase (e snake_case por compatibilidade).

```json
// Response
{ "clientId": "uuid", "scheduledAt": "2025-04-10T09:00:00Z", "priceCharged": 25000 }

// Request — aceita camelCase OU snake_case
{ "clientId": "uuid", "scheduledAt": "...", "priceCharged": 25000 }
{ "client_id": "uuid", "scheduled_at": "...", "price_charged": 25000 }  // também funciona
```

### Valores monetários

Sempre em **centavos (int)**. Conversão no frontend:

```ts
const reais = (centavos: number) => (centavos / 100).toLocaleString("pt-BR", {
  style: "currency",
  currency: "BRL",
})
reais(25000) // "R$ 250,00"
```

### Datas

ISO 8601 com timezone: `"2025-04-10T09:00:00-03:00"` ou UTC `"2025-04-10T12:00:00Z"`.

### Paginação

Endpoints de listagem retornam:

```json
{ "data": [...], "total": 142, "page": 1, "perPage": 20 }
```

Query params: `?page=1&per_page=20`.

### Erros de domínio

```json
{ "error": "SLOT_UNAVAILABLE", "message": "...", "statusCode": 422 }
```

| `error` | HTTP | Situação |
|---|---|---|
| `INVALID_TRANSITION` | 422 | Transição de status inválida |
| `SLOT_UNAVAILABLE` | 409 | Horário já ocupado |
| `INSUFFICIENT_STOCK` | 422 | Estoque insuficiente |
| `DUPLICATE_PHONE` | 409 | Telefone já cadastrado |
| `ALLERGY_DETAIL_REQUIRED` | 422 | Alergia sem detalhes |

---

## Tipos TypeScript

```ts
// Enums
type AppointmentStatus = "pending_approval" | "confirmed" | "in_progress" | "completed" | "cancelled" | "no_show"
type PaymentStatus = "pending" | "paid" | "partial" | "refunded" | "failed"
type PaymentMethod = "cash" | "credit_card" | "debit_card" | "pix" | "bank_transfer" | "other"
type LashTechnique = "classic" | "volume" | "hybrid" | "mega_volume" | "wispy" | "wet_look" | "other"
type LashServiceType = "application" | "maintenance" | "removal" | "lash_lifting" | "permanent"
type ExpenseRecurrence = "one_time" | "monthly" | "weekly" | "yearly"
type StockMovementType = "purchase" | "usage" | "adjustment"

// Entidades
interface Client {
  id: string
  name: string
  phone: string
  email?: string
  instagram?: string
  birthday?: string
  notes?: string
  address?: Address
  segments: string[]
  favoriteProcedureId?: string
  totalSpent: number        // centavos
  appointmentsCount: number
  lastAppointmentDate?: string
  createdAt: string
  updatedAt: string
}

interface Address {
  street?: string
  neighborhood?: string
  city?: string
  state?: string
  zipCode?: string
}

interface Appointment {
  id: string
  clientId: string
  procedureId: string
  paymentId?: string
  serviceType?: LashServiceType
  status: AppointmentStatus
  scheduledAt: string
  durationMinutes: number
  endsAt: string            // calculado pelo backend
  priceCharged: number      // centavos
  notes?: string
  requestedAt: string
  confirmedAt?: string
  cancelledAt?: string
  cancellationReason?: string
  cancelledBy?: "professional" | "client"
  createdAt: string
  updatedAt: string
}

interface Procedure {
  id: string
  name: string
  technique: LashTechnique
  description?: string
  priceInCents: number
  durationMinutes: number
  isActive: boolean
  imageUrl?: string
  createdAt: string
  updatedAt: string
}

interface Payment {
  id: string
  appointmentId: string
  clientId: string
  totalAmountInCents: number
  paidAmountInCents: number
  status: PaymentStatus
  method?: PaymentMethod
  paidAt?: string
  notes?: string
  partialPayments: PartialPaymentRecord[]
  createdAt: string
  updatedAt: string
}

interface PartialPaymentRecord {
  id: string
  amountInCents: number
  method: PaymentMethod
  paidAt: string
}

interface CashFlowItem {
  id: string
  appointmentId?: string
  clientId: string
  clientName?: string
  procedureName?: string
  totalAmountInCents: number
  paidAmountInCents: number
  method?: PaymentMethod
  status: PaymentStatus
  createdAt: string
}

interface Expense {
  id: string
  name: string
  category: string
  amountInCents: number
  recurrence: ExpenseRecurrence
  dueDay?: number
  isPaid: boolean
  paidAt?: string
  referenceMonth: string    // "YYYY-MM"
  notes?: string
  installmentTotal?: number
  installmentCurrent?: number
  installmentGroupId?: string
  createdAt: string
  updatedAt: string
}

interface Material {
  id: string
  name: string
  category: string
  unit: string
  unitCostInCents: number
  currentStock: number
  minimumStock: number
  isActive: boolean
  notes?: string
  createdAt: string
  updatedAt: string
}

interface StockMovement {
  id: string
  materialId: string
  materialName?: string
  type: StockMovementType
  quantity: number
  unitCostInCents: number
  totalCostInCents: number
  date: string
  notes?: string
  createdAt: string
}

interface TimeSlot {
  id: string
  dayOfWeek: number         // 0=Dom, 1=Seg, ..., 6=Sáb
  startTime: string         // "HH:MM"
  endTime: string           // "HH:MM"
  isAvailable: boolean
}

interface BlockedDate {
  id: string
  date: string              // "YYYY-MM-DD"
  reason?: string
}

interface DashboardStats {
  totalClients: number
  clientsWithUpcomingAppointments: number
  todayAppointmentsCount: number
  revenueStats: RevenueStats
  monthlyRevenue: MonthlyRevenueItem[]
  pendingApprovalsCount: number
}

interface RevenueStats {
  todayInCents: number
  thisWeekInCents: number
  thisMonthInCents: number
  lastMonthInCents: number
  growthPercent: number
}

interface MonthlyRevenueItem {
  month: string             // "YYYY-MM"
  amountInCents: number
}

interface PaginatedResponse<T> {
  data: T[]
  total: number
  page: number
  perPage: number
}
```

---

## Referência de endpoints

Base: `http://localhost:8000/api/v1`

### Auth

| Método | Endpoint | Descrição |
|---|---|---|
| `POST` | `/auth/login` | Login com username + password |
| `POST` | `/auth/logout` | Limpa cookies de sessão |
| `POST` | `/auth/refresh` | Renova access token via refresh token |
| `GET` | `/auth/me` | Retorna usuário autenticado |
| `GET` | `/auth/validate` | Valida o token atual |
| `POST` | `/auth/register` | Cria novo usuário (requer superuser) |

**Login request:**
```json
{ "username": "admin", "password": "senha" }
```

**Login response:**
```json
{ "accessToken": "eyJ...", "refreshToken": "eyJ...", "tokenType": "bearer" }
```

---

### Dashboard (requer auth)

| Método | Endpoint | Descrição |
|---|---|---|
| `GET` | `/dashboard/stats` | Estatísticas gerais + receita + pendentes |
| `GET` | `/dashboard/today` | Agendamentos de hoje + pendentes |

---

### Clientes (requer auth)

| Método | Endpoint | Descrição |
|---|---|---|
| `GET` | `/clients/` | Lista paginada (`?search=&page=&per_page=`) |
| `POST` | `/clients/` | Cria cliente |
| `GET` | `/clients/{id}` | Detalhe com campos calculados |
| `PATCH` | `/clients/{id}` | Atualiza parcialmente |
| `DELETE` | `/clients/{id}` | Soft delete |

**Create request:**
```json
{ "name": "Ana Silva", "phone": "(11) 99999-0000", "email": "...", "instagram": "@ana" }
```

---

### Procedimentos (requer auth)

| Método | Endpoint | Descrição |
|---|---|---|
| `GET` | `/procedures/` | Lista procedimentos ativos |
| `POST` | `/procedures/` | Cria procedimento |
| `PUT` | `/procedures/{id}` | Atualiza procedimento |
| `DELETE` | `/procedures/{id}` | Desativa (soft delete via `isActive`) |

**Create request:**
```json
{
  "name": "Volume Russo",
  "technique": "volume",
  "priceInCents": 25000,
  "durationMinutes": 120,
  "description": "...",
  "imageUrl": null
}
```

---

### Agendamentos (requer auth)

| Método | Endpoint | Descrição |
|---|---|---|
| `GET` | `/appointments/` | Lista com filtros |
| `POST` | `/appointments/` | Cria agendamento |
| `GET` | `/appointments/{id}` | Detalhe |
| `PATCH` | `/appointments/{id}/status` | Transição de status |
| `PATCH` | `/appointments/{id}/cancel` | Cancelar com motivo |
| `GET` | `/appointments/today` | Agendamentos de hoje |
| `GET` | `/appointments/pending-approvals` | Aguardando confirmação |
| `GET` | `/appointments/available-slots` | Horários disponíveis |

**Filtros da listagem:**
```
GET /appointments/?clientId=uuid&status=confirmed&from=2025-04-01&to=2025-04-30
```

**Create request:**
```json
{
  "clientId": "uuid",
  "procedureId": "uuid",
  "scheduledAt": "2025-04-10T09:00:00-03:00",
  "serviceType": "application",
  "priceCharged": 25000,
  "notes": "..."
}
```

**Cancel request:**
```json
{ "reason": "Cliente desmarcou", "cancelledBy": "client" }
```

**Slots disponíveis:**
```
GET /appointments/available-slots?date=2025-04-10&procedure_id=uuid
```
```json
{ "slots": ["09:00", "09:30", "10:00"] }
```

---

### Pagamentos (requer auth)

| Método | Endpoint | Descrição |
|---|---|---|
| `GET` | `/payments/cash-flow` | Fluxo de caixa com clientName e procedureName |
| `GET` | `/payments/stats` | Receita hoje/semana/mês |
| `GET` | `/payments/monthly-revenue` | Receita mensal (últimos N meses) |
| `GET` | `/payments/method-breakdown` | Breakdown por método de pagamento |
| `GET` | `/payments/by-appointment/{id}` | Pagamento de um agendamento |
| `POST` | `/payments/` | Cria pagamento |
| `PATCH` | `/payments/{id}` | Adiciona pagamento parcial |

**Create request:**
```json
{
  "appointmentId": "uuid",
  "clientId": "uuid",
  "totalAmountInCents": 25000,
  "paidAmountInCents": 25000,
  "method": "pix"
}
```

---

### Finanças — Despesas (requer auth)

| Método | Endpoint | Descrição |
|---|---|---|
| `GET` | `/expenses/` | Lista por mês (`?month=2025-04`) |
| `POST` | `/expenses/` | Cria despesa (com `installments` > 1 gera parcelamento) |
| `PATCH` | `/expenses/{id}` | Atualiza |
| `PATCH` | `/expenses/{id}/pay` | Marca como pago |
| `DELETE` | `/expenses/{id}` | Remove |
| `GET` | `/expenses/summary` | Resumo do mês (`?month=2025-04`) |

**Resumo response:**
```json
{
  "month": "2025-04",
  "totalInCents": 500000,
  "paidInCents": 300000,
  "pendingInCents": 200000,
  "byCategory": { "aluguel": 200000, "material": 300000 }
}
```

---

### Estoque (requer auth)

| Método | Endpoint | Descrição |
|---|---|---|
| `GET` | `/stock/materials` | Lista materiais (`?category=&low_stock=true`) |
| `POST` | `/stock/materials` | Cria material |
| `PUT` | `/stock/materials/{id}` | Atualiza |
| `DELETE` | `/stock/materials/{id}` | Desativa |
| `GET` | `/stock/materials/alerts` | Materiais com estoque baixo |
| `GET` | `/stock/movements` | Histórico com `materialName` |
| `POST` | `/stock/movements` | Registra entrada/saída/ajuste |
| `GET` | `/stock/value` | Valor total do estoque |
| `GET` | `/stock/monthly-costs` | Custo mensal do estoque |

---

### Configurações (requer auth)

| Método | Endpoint | Descrição |
|---|---|---|
| `GET` | `/settings/time-slots` | Horários por dia da semana |
| `PUT` | `/settings/time-slots` | Substitui todos os horários (upsert) |
| `GET` | `/settings/blocked-dates` | Datas bloqueadas |
| `POST` | `/settings/blocked-dates` | Bloqueia uma data |
| `DELETE` | `/settings/blocked-dates/{id}` | Desbloqueia |

**PUT time-slots request:**
```json
{
  "slots": [
    { "dayOfWeek": 1, "startTime": "09:00", "endTime": "18:00", "isAvailable": true },
    { "dayOfWeek": 6, "startTime": "09:00", "endTime": "14:00", "isAvailable": true }
  ]
}
```

> `dayOfWeek`: 0=Domingo, 1=Segunda, 2=Terça, ..., 6=Sábado (padrão JS).
> Dias não listados = fechado.

---

### Rotas públicas (sem auth)

| Método | Endpoint | Descrição |
|---|---|---|
| `GET` | `/public/procedures` | Procedimentos ativos (sem campos de custo) |
| `GET` | `/public/available-slots` | Horários livres por data |
| `POST` | `/public/appointments` | Agendamento público (cria cliente se não existir) |

**Agendamento público request:**
```json
{
  "procedureId": "uuid",
  "scheduledAt": "2025-04-10T09:00:00-03:00",
  "client": { "name": "Ana Paula", "phone": "(11) 98888-7777" },
  "notes": "Primeira vez"
}
```

O backend normaliza o telefone e reusa o cliente existente caso o telefone já esteja cadastrado.

---

### Anamnese (requer auth)

| Método | Endpoint | Descrição |
|---|---|---|
| `GET` | `/anamneses/` | Lista (`?clientId=uuid`) |
| `POST` | `/anamneses/` | Cria anamnese |
| `GET` | `/anamneses/{id}` | Detalhe |
| `PATCH` | `/anamneses/{id}` | Atualiza |
| `DELETE` | `/anamneses/{id}` | Remove |

---

## Utilitários de fetch

```ts
// lib/api.ts

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

async function apiFetch<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const resp = await fetch(`${BASE}/api/v1${path}`, {
    ...init,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  })

  if (!resp.ok) {
    const error = await resp.json().catch(() => ({}))
    throw Object.assign(new Error(error.message ?? "API error"), {
      status: resp.status,
      code: error.error,
    })
  }

  if (resp.status === 204) return undefined as T
  return resp.json() as Promise<T>
}

// Helpers
export const api = {
  get: <T>(path: string) => apiFetch<T>(path),
  post: <T>(path: string, body: unknown) =>
    apiFetch<T>(path, { method: "POST", body: JSON.stringify(body) }),
  patch: <T>(path: string, body: unknown) =>
    apiFetch<T>(path, { method: "PATCH", body: JSON.stringify(body) }),
  put: <T>(path: string, body: unknown) =>
    apiFetch<T>(path, { method: "PUT", body: JSON.stringify(body) }),
  delete: <T = void>(path: string) => apiFetch<T>(path, { method: "DELETE" }),
}
```

### Uso

```ts
// Client components
import { api } from "@/lib/api"

const clients = await api.get<PaginatedResponse<Client>>("/clients/?page=1&per_page=20")
const appt = await api.post<Appointment>("/appointments/", { clientId, procedureId, scheduledAt, priceCharged })
await api.delete(`/clients/${id}`)
```

### Server Components (passa o cookie do browser)

```ts
import { cookies } from "next/headers"
import { cache } from "react"

const BASE = process.env.API_URL!

export const getServerData = cache(async <T>(path: string): Promise<T> => {
  const cookieStore = cookies()
  const token = cookieStore.get("access_token")?.value

  const resp = await fetch(`${BASE}/api/v1${path}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    cache: "no-store",
  })

  if (!resp.ok) throw new Error(`${resp.status}`)
  return resp.json()
})

// Uso em um Server Component
const stats = await getServerData<DashboardStats>("/dashboard/stats")
```

---

## Checklist de configuração

- [ ] Backend `.env`: `CORS_ORIGINS=http://localhost:3000`
- [ ] Next.js `.env.local`: `NEXT_PUBLIC_API_URL=http://localhost:8000` e `API_URL=http://localhost:8000`
- [ ] Todas as requisições do browser com `credentials: "include"`
- [ ] Server Components usando cookie `access_token` via `cookies()` do Next.js
- [ ] Produção: `COOKIE_SECURE=true` no backend e HTTPS obrigatório
