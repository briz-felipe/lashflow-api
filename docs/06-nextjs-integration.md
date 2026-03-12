# Integração Next.js — Guia Completo

Base URL da API: `LASHFLOW_API_URL/api/v1`
Todos os endpoints autenticados usam `Authorization: Bearer <token>` **ou** cookie `access_token` (definido automaticamente no login).

---

## Índice

1. [Setup](#1-setup)
2. [Infraestrutura base](#2-infraestrutura-base)
3. [Autenticação](#3-autenticação)
4. [Clientes](#4-clientes)
5. [Agendamentos](#5-agendamentos)
6. [Procedimentos](#6-procedimentos)
7. [Anamneses](#7-anamneses)
8. [Estoque](#8-estoque)
9. [Despesas](#9-despesas)
10. [Pagamentos](#10-pagamentos)
11. [Dashboard](#11-dashboard)
12. [Configurações (horários e bloqueios)](#12-configurações)
13. [Rotas públicas (sem autenticação)](#13-rotas-públicas)

---

## 1. Setup

### LashFlow API — `.env`

```env
OAUTH2_CLIENT_ID=nextjs-app
OAUTH2_CLIENT_SECRET=segredo-compartilhado-forte
COOKIE_SECURE=True         # descomentar em produção (HTTPS)
```

### Next.js — `.env.local`

```env
# Nunca use NEXT_PUBLIC_ — estas vars nunca devem ir ao browser
LASHFLOW_API_URL=http://localhost:8000/api/v1
LASHFLOW_CLIENT_ID=nextjs-app
LASHFLOW_CLIENT_SECRET=segredo-compartilhado-forte
```

### Arquitetura

```
Browser
  │  cookies httpOnly (access_token, refresh_token) — browser não lê, só envia
  ▼
Next.js API Routes  (server-side)
  │  LASHFLOW_CLIENT_ID + LASHFLOW_CLIENT_SECRET ficam aqui — nunca no browser
  │  lê o access_token do cookie e envia como Authorization: Bearer
  ▼
LashFlow API
```

---

## 2. Infraestrutura base

### `lib/lashflow/types.ts`

Tipos TypeScript para todos os recursos da API.

```ts
// ─── Enums ──────────────────────────────────────────────────────────────────

export type AppointmentStatus = 'pending_approval' | 'confirmed' | 'completed' | 'cancelled'
export type PaymentStatus = 'pending' | 'partial' | 'paid'
export type PaymentMethod = 'cash' | 'credit_card' | 'debit_card' | 'pix' | 'bank_transfer' | 'other'
export type StockMovementType = 'IN' | 'OUT'
export type CancelledBy = 'professional' | 'client'

// ─── Auth ────────────────────────────────────────────────────────────────────

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface MeResponse {
  id: string
  username: string
  email: string | null
  is_superuser: boolean
  is_active: boolean
  created_at: string
}

// ─── Paginação ───────────────────────────────────────────────────────────────

export interface Paginated<T> {
  data: T[]
  total: number
  page: number
  per_page: number
}

// ─── Clientes ────────────────────────────────────────────────────────────────

export interface Address {
  street?: string
  neighborhood?: string
  city?: string
  state?: string
  zip_code?: string
}

export interface Client {
  id: string
  name: string
  phone: string
  email?: string
  instagram?: string
  birthday?: string
  notes?: string
  address?: Address
  segments: string[]
  favorite_procedure_id?: string
  total_spent: number          // centavos
  appointments_count: number
  last_appointment_date?: string
  created_at: string
  updated_at: string
}

export interface ClientCreate {
  name: string
  phone: string
  email?: string
  instagram?: string
  birthday?: string
  notes?: string
  address?: Address
}

export interface ClientUpdate extends Partial<ClientCreate> {
  segments?: string[]
}

// ─── Procedimentos ───────────────────────────────────────────────────────────

export interface Procedure {
  id: string
  name: string
  technique: string
  description?: string
  price_in_cents: number
  duration_minutes: number
  is_active: boolean
  image_url?: string
  created_at: string
  updated_at: string
}

export interface ProcedureCreate {
  name: string
  technique: string
  description?: string
  price_in_cents: number
  duration_minutes: number
  image_url?: string
}

export type ProcedureUpdate = Partial<ProcedureCreate>

// ─── Agendamentos ────────────────────────────────────────────────────────────

export interface Appointment {
  id: string
  client_id: string
  procedure_id: string
  payment_id?: string
  service_type?: string
  status: AppointmentStatus
  scheduled_at: string
  duration_minutes: number
  ends_at: string
  price_charged: number       // centavos
  notes?: string
  requested_at: string
  confirmed_at?: string
  cancelled_at?: string
  cancellation_reason?: string
  cancelled_by?: CancelledBy
  created_at: string
  updated_at: string
}

export interface AppointmentCreate {
  client_id: string
  procedure_id: string
  scheduled_at: string        // ISO 8601
  service_type?: string
  price_charged: number       // centavos
  notes?: string
}

export interface AppointmentStatusUpdate {
  status: AppointmentStatus
}

export interface AppointmentCancelRequest {
  reason?: string
  cancelled_by?: CancelledBy
}

export interface AvailableSlotsResponse {
  slots: string[]             // ISO 8601 datetimes
}

// ─── Anamneses ───────────────────────────────────────────────────────────────

export interface LashMapping {
  size?: string
  curve?: string
  thickness?: string
}

export interface Anamnesis {
  id: string
  client_id: string
  has_allergy: boolean
  allergy_details?: string
  had_eye_surgery_last_3_months: boolean
  has_eye_disease: boolean
  eye_disease_details?: string
  uses_eye_drops: boolean
  family_thyroid_history: boolean
  has_glaucoma: boolean
  hair_loss_grade?: string
  prone_to_blepharitis: boolean
  has_epilepsy: boolean
  procedure_type: string
  mapping?: LashMapping
  authorized_photo_publishing: boolean
  signed_at?: string
  notes?: string
  created_at: string
  updated_at: string
}

export interface AnamnesisCreate {
  client_id: string
  procedure_type: string
  has_allergy?: boolean
  allergy_details?: string    // obrigatório se has_allergy=true
  had_eye_surgery_last_3_months?: boolean
  has_eye_disease?: boolean
  eye_disease_details?: string
  uses_eye_drops?: boolean
  family_thyroid_history?: boolean
  has_glaucoma?: boolean
  hair_loss_grade?: string
  prone_to_blepharitis?: boolean
  has_epilepsy?: boolean
  mapping?: LashMapping
  authorized_photo_publishing?: boolean
  signed_at?: string
  notes?: string
}

export type AnamnesisUpdate = Partial<AnamnesisCreate>

// ─── Estoque ─────────────────────────────────────────────────────────────────

export interface Material {
  id: string
  name: string
  category: string
  unit: string
  unit_cost_in_cents: number
  current_stock: number
  minimum_stock: number
  is_active: boolean
  notes?: string
  created_at: string
  updated_at: string
}

export interface MaterialCreate {
  name: string
  category: string
  unit: string
  unit_cost_in_cents: number
  current_stock?: number
  minimum_stock?: number
  notes?: string
}

export type MaterialUpdate = Partial<Omit<MaterialCreate, 'current_stock'>>

export interface StockMovement {
  id: string
  material_id: string
  type: StockMovementType
  quantity: number
  unit_cost_in_cents: number
  total_cost_in_cents: number
  date: string
  notes?: string
  created_at: string
}

export interface StockMovementCreate {
  material_id: string
  type: StockMovementType
  quantity: number
  unit_cost_in_cents: number
  notes?: string
}

export interface StockValueResponse {
  total_value_in_cents: number
}

// ─── Despesas ─────────────────────────────────────────────────────────────────

export type ExpenseRecurrence = 'once' | 'monthly' | 'installment'

export interface Expense {
  id: string
  name: string
  category: string
  amount_in_cents: number
  recurrence: ExpenseRecurrence
  due_day?: number
  is_paid: boolean
  paid_at?: string
  reference_month: string     // YYYY-MM
  notes?: string
  installment_total?: number
  installment_current?: number
  installment_group_id?: string
  created_at: string
  updated_at: string
}

export interface ExpenseCreate {
  name: string
  category: string
  amount_in_cents: number
  recurrence: ExpenseRecurrence
  due_day?: number
  reference_month: string     // YYYY-MM
  notes?: string
  installments?: number       // > 1 gera parcelas
}

export type ExpenseUpdate = Partial<Omit<ExpenseCreate, 'installments'>>

export interface ExpenseSummary {
  month: string
  total_in_cents: number
  paid_in_cents: number
  pending_in_cents: number
  by_category: Record<string, number>
}

export interface ExpenseInstallmentResponse {
  expense: Expense
  installments_created: number
  installment_group_id?: string
}

// ─── Pagamentos ───────────────────────────────────────────────────────────────

export interface PartialPaymentRecord {
  id: string
  amount_in_cents: number
  method: PaymentMethod
  paid_at: string
}

export interface Payment {
  id: string
  appointment_id: string
  client_id: string
  total_amount_in_cents: number
  paid_amount_in_cents: number
  status: PaymentStatus
  method?: PaymentMethod
  paid_at?: string
  notes?: string
  partial_payments: PartialPaymentRecord[]
  created_at: string
  updated_at: string
}

export interface PaymentCreate {
  appointment_id: string
  client_id: string
  total_amount_in_cents: number
  paid_amount_in_cents?: number
  method?: PaymentMethod
  notes?: string
}

export interface PaymentUpdate {
  partial_payment?: { amount_in_cents: number; method: PaymentMethod }
  paid_amount_in_cents?: number
  method?: PaymentMethod
  notes?: string
}

export interface PaymentStats {
  today_in_cents: number
  this_week_in_cents: number
  this_month_in_cents: number
  last_month_in_cents: number
  growth_percent: number
}

export interface MonthlyRevenueItem {
  month: string               // YYYY-MM
  amount_in_cents: number
}

export interface MethodBreakdown {
  cash: number
  credit_card: number
  debit_card: number
  pix: number
  bank_transfer: number
  other: number
}

// ─── Dashboard ────────────────────────────────────────────────────────────────

export interface DashboardStats {
  total_clients: number
  clients_with_upcoming_appointments: number
  today_appointments_count: number
  revenue_stats: PaymentStats
  monthly_revenue: MonthlyRevenueItem[]
  pending_approvals_count: number
}

export interface DashboardToday {
  appointments: Appointment[]
  pending_approvals_count: number
}

// ─── Configurações ────────────────────────────────────────────────────────────

export interface TimeSlot {
  id: string
  day_of_week: number         // 0=Domingo, 6=Sábado
  start_time: string          // HH:MM
  end_time: string            // HH:MM
  is_available: boolean
}

export interface TimeSlotItem {
  day_of_week: number
  start_time: string
  end_time: string
  is_available: boolean
}

export interface BlockedDate {
  id: string
  date: string                // YYYY-MM-DD
  reason?: string
}

export interface BlockedDateCreate {
  date: string
  reason?: string
}
```

---

### `lib/lashflow/client.ts`

Helper central que todas as rotas do Next.js usam para chamar a LashFlow API.

```ts
import { cookies } from 'next/headers'
import { NextRequest } from 'next/server'

const API = process.env.LASHFLOW_API_URL!

export class ApiError extends Error {
  constructor(public status: number, public code: string, message: string) {
    super(message)
  }
}

/** Usado em Server Components e API Routes para chamar a LashFlow com o token do cookie. */
export async function apiServer(path: string, options: RequestInit = {}): Promise<Response> {
  const cookieStore = await cookies()
  const token = cookieStore.get('access_token')?.value

  return fetch(`${API}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers as Record<string, string>),
    },
  })
}

/** Extrai o token do cookie de um NextRequest (para uso em API Routes que recebem req). */
export function tokenFromRequest(req: NextRequest): string | undefined {
  return req.cookies.get('access_token')?.value
}

/** Chama a LashFlow usando o token de um NextRequest específico. */
export async function apiFromRequest(
  req: NextRequest,
  path: string,
  options: RequestInit = {}
): Promise<Response> {
  const token = tokenFromRequest(req)
  return fetch(`${API}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers as Record<string, string>),
    },
  })
}

/** Garante resposta OK ou lança ApiError com o código de erro da API. */
export async function assertOk(res: Response): Promise<void> {
  if (res.ok) return
  let body: { error?: string; detail?: string; message?: string } = {}
  try { body = await res.json() } catch {}
  throw new ApiError(
    res.status,
    body.error ?? 'UNKNOWN',
    body.message ?? body.detail ?? res.statusText
  )
}

/** Wrapper que retorna JSON após assertOk. */
export async function apiJson<T>(res: Response): Promise<T> {
  await assertOk(res)
  return res.json() as Promise<T>
}
```

---

### `lib/lashflow/money.ts`

Utilitário para valores monetários (sempre centavos na API).

```ts
/** Formata centavos como R$ 250,00 */
export function formatMoney(cents: number): string {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(cents / 100)
}

/** Converte string "250,00" ou número 250.00 para centavos */
export function toCents(value: string | number): number {
  if (typeof value === 'number') return Math.round(value * 100)
  return Math.round(parseFloat(value.replace(',', '.')) * 100)
}
```

---

## 3. Autenticação

### `app/api/auth/login/route.ts`

```ts
import { NextRequest, NextResponse } from 'next/server'

const API = process.env.LASHFLOW_API_URL!

export async function POST(req: NextRequest) {
  const { username, password } = await req.json()

  const res = await fetch(`${API}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      username,
      password,
      client_id: process.env.LASHFLOW_CLIENT_ID,
      client_secret: process.env.LASHFLOW_CLIENT_SECRET,
    }),
  })

  if (!res.ok) {
    const err = await res.json()
    return NextResponse.json(
      { error: err.detail ?? 'Credenciais inválidas' },
      { status: 401 }
    )
  }

  const { access_token, refresh_token } = await res.json()

  const response = NextResponse.json({ ok: true })
  const cookieBase = {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax' as const,
    path: '/',
  }
  response.cookies.set('access_token', access_token, { ...cookieBase, maxAge: 60 * 60 * 24 * 7 })
  response.cookies.set('refresh_token', refresh_token, { ...cookieBase, maxAge: 60 * 60 * 24 * 30 })
  return response
}
```

### `app/api/auth/logout/route.ts`

```ts
import { NextResponse } from 'next/server'

export async function POST() {
  const response = NextResponse.json({ ok: true })
  response.cookies.delete('access_token')
  response.cookies.delete('refresh_token')
  return response
}
```

### `app/api/auth/refresh/route.ts`

```ts
import { NextRequest, NextResponse } from 'next/server'

const API = process.env.LASHFLOW_API_URL!

export async function POST(req: NextRequest) {
  const refreshToken = req.cookies.get('refresh_token')?.value
  if (!refreshToken) {
    return NextResponse.json({ error: 'No refresh token' }, { status: 401 })
  }

  const res = await fetch(`${API}/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken }),
  })

  if (!res.ok) {
    const response = NextResponse.json({ error: 'Sessão expirada' }, { status: 401 })
    response.cookies.delete('access_token')
    response.cookies.delete('refresh_token')
    return response
  }

  const { access_token, refresh_token } = await res.json()
  const response = NextResponse.json({ ok: true })
  const cookieBase = {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax' as const,
    path: '/',
  }
  response.cookies.set('access_token', access_token, { ...cookieBase, maxAge: 60 * 60 * 24 * 7 })
  response.cookies.set('refresh_token', refresh_token, { ...cookieBase, maxAge: 60 * 60 * 24 * 30 })
  return response
}
```

### `app/api/auth/me/route.ts`

```ts
import { NextRequest, NextResponse } from 'next/server'
import { apiFromRequest, apiJson } from '@/lib/lashflow/client'
import type { MeResponse } from '@/lib/lashflow/types'

export async function GET(req: NextRequest) {
  try {
    const res = await apiFromRequest(req, '/auth/me')
    const data = await apiJson<MeResponse>(res)
    return NextResponse.json(data)
  } catch {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }
}
```

### `middleware.ts`

Protege todas as rotas de dashboard. Redireciona para `/login` se o token for inválido.

```ts
import { NextRequest, NextResponse } from 'next/server'

const API = process.env.LASHFLOW_API_URL!

export async function middleware(req: NextRequest) {
  const token = req.cookies.get('access_token')?.value

  if (!token) {
    return NextResponse.redirect(new URL('/login', req.url))
  }

  // POST /auth/validate nunca retorna 401 — sempre { valid: true|false }
  const res = await fetch(`${API}/auth/validate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: token }),
  })
  const { valid } = await res.json()

  if (!valid) {
    const response = NextResponse.redirect(new URL('/login', req.url))
    response.cookies.delete('access_token')
    response.cookies.delete('refresh_token')
    return response
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/dashboard/:path*'],
}
```

### `hooks/useAuth.ts`

Hook para componentes React (browser). Chama as API Routes do Next.js — nunca a LashFlow diretamente.

```ts
import { useCallback } from 'react'
import { useRouter } from 'next/navigation'

export function useAuth() {
  const router = useRouter()

  const login = useCallback(async (username: string, password: string) => {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    })
    if (!res.ok) {
      const { error } = await res.json()
      throw new Error(error ?? 'Credenciais inválidas')
    }
    router.push('/dashboard')
  }, [router])

  const logout = useCallback(async () => {
    await fetch('/api/auth/logout', { method: 'POST' })
    router.push('/login')
  }, [router])

  const refresh = useCallback(async (): Promise<boolean> => {
    const res = await fetch('/api/auth/refresh', { method: 'POST' })
    return res.ok
  }, [])

  return { login, logout, refresh }
}
```

---

## 4. Clientes

### API Routes

```ts
// app/api/clients/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { apiFromRequest, apiJson } from '@/lib/lashflow/client'
import type { Paginated, Client, ClientCreate } from '@/lib/lashflow/types'

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url)
  const res = await apiFromRequest(req, `/clients?${searchParams}`)
  return NextResponse.json(await apiJson<Paginated<Client>>(res))
}

export async function POST(req: NextRequest) {
  const body: ClientCreate = await req.json()
  const res = await apiFromRequest(req, '/clients', {
    method: 'POST',
    body: JSON.stringify(body),
  })
  return NextResponse.json(await apiJson<Client>(res), { status: 201 })
}
```

```ts
// app/api/clients/[id]/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { apiFromRequest, apiJson } from '@/lib/lashflow/client'
import type { Client, ClientUpdate } from '@/lib/lashflow/types'

export async function GET(req: NextRequest, { params }: { params: { id: string } }) {
  const res = await apiFromRequest(req, `/clients/${params.id}`)
  return NextResponse.json(await apiJson<Client>(res))
}

export async function PUT(req: NextRequest, { params }: { params: { id: string } }) {
  const body: ClientUpdate = await req.json()
  const res = await apiFromRequest(req, `/clients/${params.id}`, {
    method: 'PUT',
    body: JSON.stringify(body),
  })
  return NextResponse.json(await apiJson<Client>(res))
}

export async function DELETE(req: NextRequest, { params }: { params: { id: string } }) {
  await apiFromRequest(req, `/clients/${params.id}`, { method: 'DELETE' })
  return new NextResponse(null, { status: 204 })
}
```

```ts
// app/api/clients/search/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { apiFromRequest, apiJson } from '@/lib/lashflow/client'
import type { Client } from '@/lib/lashflow/types'

export async function GET(req: NextRequest) {
  const q = new URL(req.url).searchParams.get('q') ?? ''
  const res = await apiFromRequest(req, `/clients/search?q=${encodeURIComponent(q)}`)
  return NextResponse.json(await apiJson<Client[]>(res))
}
```

### Hook

```ts
// hooks/useClients.ts
import { useState, useEffect } from 'react'
import type { Paginated, Client } from '@/lib/lashflow/types'

export function useClients(page = 1, search?: string) {
  const [data, setData] = useState<Paginated<Client> | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const params = new URLSearchParams({ page: String(page), per_page: '20' })
    if (search) params.set('search', search)
    fetch(`/api/clients?${params}`)
      .then(r => r.json())
      .then(setData)
      .finally(() => setLoading(false))
  }, [page, search])

  const deleteClient = async (id: string) => {
    await fetch(`/api/clients/${id}`, { method: 'DELETE' })
    setData(prev => prev ? { ...prev, data: prev.data.filter(c => c.id !== id) } : null)
  }

  return { data, loading, deleteClient }
}
```

---

## 5. Agendamentos

### API Routes

```ts
// app/api/appointments/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { apiFromRequest, apiJson } from '@/lib/lashflow/client'
import type { Appointment, AppointmentCreate } from '@/lib/lashflow/types'

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url)
  const res = await apiFromRequest(req, `/appointments?${searchParams}`)
  return NextResponse.json(await apiJson<Appointment[]>(res))
}

export async function POST(req: NextRequest) {
  const body: AppointmentCreate = await req.json()
  const res = await apiFromRequest(req, '/appointments', {
    method: 'POST',
    body: JSON.stringify(body),
  })
  return NextResponse.json(await apiJson<Appointment>(res), { status: 201 })
}
```

```ts
// app/api/appointments/[id]/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { apiFromRequest, apiJson } from '@/lib/lashflow/client'
import type { Appointment } from '@/lib/lashflow/types'

export async function GET(req: NextRequest, { params }: { params: { id: string } }) {
  const res = await apiFromRequest(req, `/appointments/${params.id}`)
  return NextResponse.json(await apiJson<Appointment>(res))
}
```

```ts
// app/api/appointments/[id]/status/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { apiFromRequest, apiJson } from '@/lib/lashflow/client'
import type { Appointment, AppointmentStatus } from '@/lib/lashflow/types'

export async function PATCH(req: NextRequest, { params }: { params: { id: string } }) {
  const body: { status: AppointmentStatus } = await req.json()
  const res = await apiFromRequest(req, `/appointments/${params.id}/status`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  })
  return NextResponse.json(await apiJson<Appointment>(res))
}
```

```ts
// app/api/appointments/[id]/cancel/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { apiFromRequest, apiJson } from '@/lib/lashflow/client'
import type { Appointment, AppointmentCancelRequest } from '@/lib/lashflow/types'

export async function PATCH(req: NextRequest, { params }: { params: { id: string } }) {
  const body: AppointmentCancelRequest = await req.json()
  const res = await apiFromRequest(req, `/appointments/${params.id}/cancel`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  })
  return NextResponse.json(await apiJson<Appointment>(res))
}
```

```ts
// app/api/appointments/available-slots/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { apiFromRequest, apiJson } from '@/lib/lashflow/client'
import type { AvailableSlotsResponse } from '@/lib/lashflow/types'

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url)
  // Requer: date=YYYY-MM-DD e procedure_id=UUID
  const res = await apiFromRequest(req, `/appointments/available-slots?${searchParams}`)
  return NextResponse.json(await apiJson<AvailableSlotsResponse>(res))
}
```

```ts
// app/api/appointments/today/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { apiFromRequest, apiJson } from '@/lib/lashflow/client'
import type { Appointment } from '@/lib/lashflow/types'

export async function GET(req: NextRequest) {
  const res = await apiFromRequest(req, '/appointments/today')
  return NextResponse.json(await apiJson<Appointment[]>(res))
}
```

```ts
// app/api/appointments/pending-approvals/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { apiFromRequest, apiJson } from '@/lib/lashflow/client'
import type { Appointment } from '@/lib/lashflow/types'

export async function GET(req: NextRequest) {
  const res = await apiFromRequest(req, '/appointments/pending-approvals')
  return NextResponse.json(await apiJson<Appointment[]>(res))
}
```

### Hook

```ts
// hooks/useAppointments.ts
import { useState, useEffect } from 'react'
import type { Appointment, AppointmentStatus } from '@/lib/lashflow/types'

export function useAppointments(filters?: {
  client_id?: string
  status?: AppointmentStatus[]
  from_date?: string
  to_date?: string
}) {
  const [data, setData] = useState<Appointment[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const params = new URLSearchParams()
    if (filters?.client_id) params.set('client_id', filters.client_id)
    if (filters?.from_date) params.set('from_date', filters.from_date)
    if (filters?.to_date) params.set('to_date', filters.to_date)
    filters?.status?.forEach(s => params.append('status', s))

    fetch(`/api/appointments?${params}`)
      .then(r => r.json())
      .then(setData)
      .finally(() => setLoading(false))
  }, [JSON.stringify(filters)])

  const updateStatus = async (id: string, status: AppointmentStatus) => {
    const res = await fetch(`/api/appointments/${id}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status }),
    })
    const updated: Appointment = await res.json()
    setData(prev => prev.map(a => a.id === id ? updated : a))
    return updated
  }

  const cancel = async (id: string, reason?: string) => {
    const res = await fetch(`/api/appointments/${id}/cancel`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reason, cancelled_by: 'professional' }),
    })
    const updated: Appointment = await res.json()
    setData(prev => prev.map(a => a.id === id ? updated : a))
    return updated
  }

  return { data, loading, updateStatus, cancel }
}
```

---

## 6. Procedimentos

### API Routes

```ts
// app/api/procedures/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { apiFromRequest, apiJson } from '@/lib/lashflow/client'
import type { Procedure, ProcedureCreate } from '@/lib/lashflow/types'

export async function GET(req: NextRequest) {
  const active_only = new URL(req.url).searchParams.get('active_only') ?? 'false'
  const res = await apiFromRequest(req, `/procedures?active_only=${active_only}`)
  return NextResponse.json(await apiJson<Procedure[]>(res))
}

export async function POST(req: NextRequest) {
  const body: ProcedureCreate = await req.json()
  const res = await apiFromRequest(req, '/procedures', {
    method: 'POST',
    body: JSON.stringify(body),
  })
  return NextResponse.json(await apiJson<Procedure>(res), { status: 201 })
}
```

```ts
// app/api/procedures/[id]/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { apiFromRequest, apiJson } from '@/lib/lashflow/client'
import type { Procedure, ProcedureUpdate } from '@/lib/lashflow/types'

export async function GET(req: NextRequest, { params }: { params: { id: string } }) {
  const res = await apiFromRequest(req, `/procedures/${params.id}`)
  return NextResponse.json(await apiJson<Procedure>(res))
}

export async function PUT(req: NextRequest, { params }: { params: { id: string } }) {
  const body: ProcedureUpdate = await req.json()
  const res = await apiFromRequest(req, `/procedures/${params.id}`, {
    method: 'PUT',
    body: JSON.stringify(body),
  })
  return NextResponse.json(await apiJson<Procedure>(res))
}

export async function DELETE(req: NextRequest, { params }: { params: { id: string } }) {
  await apiFromRequest(req, `/procedures/${params.id}`, { method: 'DELETE' })
  return new NextResponse(null, { status: 204 })
}
```

```ts
// app/api/procedures/[id]/toggle/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { apiFromRequest, apiJson } from '@/lib/lashflow/client'
import type { Procedure } from '@/lib/lashflow/types'

export async function PATCH(req: NextRequest, { params }: { params: { id: string } }) {
  const res = await apiFromRequest(req, `/procedures/${params.id}/toggle`, { method: 'PATCH' })
  return NextResponse.json(await apiJson<Procedure>(res))
}
```

---

## 7. Anamneses

### API Routes

```ts
// app/api/anamneses/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { apiFromRequest, apiJson } from '@/lib/lashflow/client'
import type { Anamnesis, AnamnesisCreate } from '@/lib/lashflow/types'

export async function GET(req: NextRequest) {
  const client_id = new URL(req.url).searchParams.get('client_id') ?? ''
  const res = await apiFromRequest(req, `/anamneses?client_id=${client_id}`)
  return NextResponse.json(await apiJson<Anamnesis[]>(res))
}

export async function POST(req: NextRequest) {
  const body: AnamnesisCreate = await req.json()
  const res = await apiFromRequest(req, '/anamneses', {
    method: 'POST',
    body: JSON.stringify(body),
  })
  return NextResponse.json(await apiJson<Anamnesis>(res), { status: 201 })
}
```

```ts
// app/api/anamneses/[id]/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { apiFromRequest, apiJson } from '@/lib/lashflow/client'
import type { Anamnesis, AnamnesisUpdate } from '@/lib/lashflow/types'

export async function GET(req: NextRequest, { params }: { params: { id: string } }) {
  const res = await apiFromRequest(req, `/anamneses/${params.id}`)
  return NextResponse.json(await apiJson<Anamnesis>(res))
}

export async function PUT(req: NextRequest, { params }: { params: { id: string } }) {
  const body: AnamnesisUpdate = await req.json()
  const res = await apiFromRequest(req, `/anamneses/${params.id}`, {
    method: 'PUT',
    body: JSON.stringify(body),
  })
  return NextResponse.json(await apiJson<Anamnesis>(res))
}
```

---

## 8. Estoque

### API Routes

```ts
// app/api/stock/materials/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { apiFromRequest, apiJson } from '@/lib/lashflow/client'
import type { Material, MaterialCreate } from '@/lib/lashflow/types'

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url)
  const res = await apiFromRequest(req, `/stock/materials?${searchParams}`)
  return NextResponse.json(await apiJson<Material[]>(res))
}

export async function POST(req: NextRequest) {
  const body: MaterialCreate = await req.json()
  const res = await apiFromRequest(req, '/stock/materials', {
    method: 'POST',
    body: JSON.stringify(body),
  })
  return NextResponse.json(await apiJson<Material>(res), { status: 201 })
}
```

```ts
// app/api/stock/materials/[id]/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { apiFromRequest, apiJson } from '@/lib/lashflow/client'
import type { Material, MaterialUpdate } from '@/lib/lashflow/types'

export async function GET(req: NextRequest, { params }: { params: { id: string } }) {
  const res = await apiFromRequest(req, `/stock/materials/${params.id}`)
  return NextResponse.json(await apiJson<Material>(res))
}

export async function PUT(req: NextRequest, { params }: { params: { id: string } }) {
  const body: MaterialUpdate = await req.json()
  const res = await apiFromRequest(req, `/stock/materials/${params.id}`, {
    method: 'PUT',
    body: JSON.stringify(body),
  })
  return NextResponse.json(await apiJson<Material>(res))
}

export async function DELETE(req: NextRequest, { params }: { params: { id: string } }) {
  await apiFromRequest(req, `/stock/materials/${params.id}`, { method: 'DELETE' })
  return new NextResponse(null, { status: 204 })
}
```

```ts
// app/api/stock/movements/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { apiFromRequest, apiJson } from '@/lib/lashflow/client'
import type { StockMovement, StockMovementCreate } from '@/lib/lashflow/types'

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url)
  const res = await apiFromRequest(req, `/stock/movements?${searchParams}`)
  return NextResponse.json(await apiJson<StockMovement[]>(res))
}

export async function POST(req: NextRequest) {
  const body: StockMovementCreate = await req.json()
  const res = await apiFromRequest(req, '/stock/movements', {
    method: 'POST',
    body: JSON.stringify(body),
  })
  return NextResponse.json(await apiJson<StockMovement>(res), { status: 201 })
}
```

```ts
// app/api/stock/value/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { apiFromRequest, apiJson } from '@/lib/lashflow/client'
import type { StockValueResponse } from '@/lib/lashflow/types'

export async function GET(req: NextRequest) {
  const res = await apiFromRequest(req, '/stock/value')
  return NextResponse.json(await apiJson<StockValueResponse>(res))
}
```

```ts
// app/api/stock/alerts/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { apiFromRequest, apiJson } from '@/lib/lashflow/client'
import type { Material } from '@/lib/lashflow/types'

export async function GET(req: NextRequest) {
  const res = await apiFromRequest(req, '/stock/materials/alerts')
  return NextResponse.json(await apiJson<Material[]>(res))
}
```

---

## 9. Despesas

### API Routes

```ts
// app/api/expenses/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { apiFromRequest, apiJson } from '@/lib/lashflow/client'
import type { Expense, ExpenseCreate, ExpenseInstallmentResponse } from '@/lib/lashflow/types'

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url)
  const res = await apiFromRequest(req, `/expenses?${searchParams}`)
  return NextResponse.json(await apiJson<Expense[]>(res))
}

export async function POST(req: NextRequest) {
  const body: ExpenseCreate = await req.json()
  const res = await apiFromRequest(req, '/expenses', {
    method: 'POST',
    body: JSON.stringify(body),
  })
  return NextResponse.json(await apiJson<ExpenseInstallmentResponse>(res), { status: 201 })
}
```

```ts
// app/api/expenses/[id]/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { apiFromRequest, apiJson } from '@/lib/lashflow/client'
import type { Expense, ExpenseUpdate } from '@/lib/lashflow/types'

export async function GET(req: NextRequest, { params }: { params: { id: string } }) {
  const res = await apiFromRequest(req, `/expenses/${params.id}`)
  return NextResponse.json(await apiJson<Expense>(res))
}

export async function PUT(req: NextRequest, { params }: { params: { id: string } }) {
  const body: ExpenseUpdate = await req.json()
  const res = await apiFromRequest(req, `/expenses/${params.id}`, {
    method: 'PUT',
    body: JSON.stringify(body),
  })
  return NextResponse.json(await apiJson<Expense>(res))
}

export async function DELETE(req: NextRequest, { params }: { params: { id: string } }) {
  await apiFromRequest(req, `/expenses/${params.id}`, { method: 'DELETE' })
  return new NextResponse(null, { status: 204 })
}
```

```ts
// app/api/expenses/[id]/pay/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { apiFromRequest, apiJson } from '@/lib/lashflow/client'
import type { Expense } from '@/lib/lashflow/types'

export async function PATCH(req: NextRequest, { params }: { params: { id: string } }) {
  const res = await apiFromRequest(req, `/expenses/${params.id}/pay`, { method: 'PATCH' })
  return NextResponse.json(await apiJson<Expense>(res))
}
```

```ts
// app/api/expenses/summary/route.ts
// Query: ?month=YYYY-MM
import { NextRequest, NextResponse } from 'next/server'
import { apiFromRequest, apiJson } from '@/lib/lashflow/client'
import type { ExpenseSummary } from '@/lib/lashflow/types'

export async function GET(req: NextRequest) {
  const month = new URL(req.url).searchParams.get('month') ?? ''
  const res = await apiFromRequest(req, `/expenses/summary?month=${month}`)
  return NextResponse.json(await apiJson<ExpenseSummary>(res))
}
```

---

## 10. Pagamentos

### API Routes

```ts
// app/api/payments/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { apiFromRequest, apiJson } from '@/lib/lashflow/client'
import type { Payment, PaymentCreate } from '@/lib/lashflow/types'

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url)
  const res = await apiFromRequest(req, `/payments?${searchParams}`)
  return NextResponse.json(await apiJson<Payment[]>(res))
}

export async function POST(req: NextRequest) {
  const body: PaymentCreate = await req.json()
  const res = await apiFromRequest(req, '/payments', {
    method: 'POST',
    body: JSON.stringify(body),
  })
  return NextResponse.json(await apiJson<Payment>(res), { status: 201 })
}
```

```ts
// app/api/payments/[id]/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { apiFromRequest, apiJson } from '@/lib/lashflow/client'
import type { Payment, PaymentUpdate } from '@/lib/lashflow/types'

export async function GET(req: NextRequest, { params }: { params: { id: string } }) {
  const res = await apiFromRequest(req, `/payments/${params.id}`)
  return NextResponse.json(await apiJson<Payment>(res))
}

export async function PATCH(req: NextRequest, { params }: { params: { id: string } }) {
  const body: PaymentUpdate = await req.json()
  const res = await apiFromRequest(req, `/payments/${params.id}`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  })
  return NextResponse.json(await apiJson<Payment>(res))
}
```

```ts
// app/api/payments/stats/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { apiFromRequest, apiJson } from '@/lib/lashflow/client'
import type { PaymentStats } from '@/lib/lashflow/types'

export async function GET(req: NextRequest) {
  const res = await apiFromRequest(req, '/payments/stats')
  return NextResponse.json(await apiJson<PaymentStats>(res))
}
```

```ts
// app/api/payments/by-appointment/[appointmentId]/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { apiFromRequest, apiJson } from '@/lib/lashflow/client'
import type { Payment } from '@/lib/lashflow/types'

export async function GET(req: NextRequest, { params }: { params: { appointmentId: string } }) {
  const res = await apiFromRequest(req, `/payments/by-appointment/${params.appointmentId}`)
  return NextResponse.json(await apiJson<Payment>(res))
}
```

```ts
// app/api/payments/method-breakdown/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { apiFromRequest, apiJson } from '@/lib/lashflow/client'
import type { MethodBreakdown } from '@/lib/lashflow/types'

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url)
  const res = await apiFromRequest(req, `/payments/method-breakdown?${searchParams}`)
  return NextResponse.json(await apiJson<MethodBreakdown>(res))
}
```

---

## 11. Dashboard

### API Routes

```ts
// app/api/dashboard/stats/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { apiFromRequest, apiJson } from '@/lib/lashflow/client'
import type { DashboardStats } from '@/lib/lashflow/types'

export async function GET(req: NextRequest) {
  const res = await apiFromRequest(req, '/dashboard/stats')
  return NextResponse.json(await apiJson<DashboardStats>(res))
}
```

```ts
// app/api/dashboard/today/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { apiFromRequest, apiJson } from '@/lib/lashflow/client'
import type { DashboardToday } from '@/lib/lashflow/types'

export async function GET(req: NextRequest) {
  const res = await apiFromRequest(req, '/dashboard/today')
  return NextResponse.json(await apiJson<DashboardToday>(res))
}
```

### Hook

```ts
// hooks/useDashboard.ts
import { useState, useEffect } from 'react'
import type { DashboardStats, DashboardToday } from '@/lib/lashflow/types'

export function useDashboardStats() {
  const [data, setData] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/api/dashboard/stats')
      .then(r => r.json())
      .then(setData)
      .finally(() => setLoading(false))
  }, [])

  return { data, loading }
}

export function useDashboardToday() {
  const [data, setData] = useState<DashboardToday | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/api/dashboard/today')
      .then(r => r.json())
      .then(setData)
      .finally(() => setLoading(false))
  }, [])

  return { data, loading }
}
```

---

## 12. Configurações

### API Routes

```ts
// app/api/settings/time-slots/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { apiFromRequest, apiJson } from '@/lib/lashflow/client'
import type { TimeSlot, TimeSlotItem } from '@/lib/lashflow/types'

export async function GET(req: NextRequest) {
  const res = await apiFromRequest(req, '/settings/time-slots')
  return NextResponse.json(await apiJson<TimeSlot[]>(res))
}

export async function PUT(req: NextRequest) {
  const body: { slots: TimeSlotItem[] } = await req.json()
  const res = await apiFromRequest(req, '/settings/time-slots', {
    method: 'PUT',
    body: JSON.stringify(body),
  })
  return NextResponse.json(await apiJson<TimeSlot[]>(res))
}
```

```ts
// app/api/settings/blocked-dates/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { apiFromRequest, apiJson } from '@/lib/lashflow/client'
import type { BlockedDate, BlockedDateCreate } from '@/lib/lashflow/types'

export async function GET(req: NextRequest) {
  const res = await apiFromRequest(req, '/settings/blocked-dates')
  return NextResponse.json(await apiJson<BlockedDate[]>(res))
}

export async function POST(req: NextRequest) {
  const body: BlockedDateCreate = await req.json()
  const res = await apiFromRequest(req, '/settings/blocked-dates', {
    method: 'POST',
    body: JSON.stringify(body),
  })
  return NextResponse.json(await apiJson<BlockedDate>(res), { status: 201 })
}
```

```ts
// app/api/settings/blocked-dates/[id]/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { apiFromRequest } from '@/lib/lashflow/client'

export async function DELETE(req: NextRequest, { params }: { params: { id: string } }) {
  await apiFromRequest(req, `/settings/blocked-dates/${params.id}`, { method: 'DELETE' })
  return new NextResponse(null, { status: 204 })
}
```

---

## 13. Rotas públicas

**Não requerem autenticação.** Usadas pela página de agendamento do cliente.

```ts
// app/api/public/procedures/route.ts
import { NextResponse } from 'next/server'
import type { Procedure } from '@/lib/lashflow/types'

const API = process.env.LASHFLOW_API_URL!

export async function GET() {
  const res = await fetch(`${API}/public/procedures`)
  return NextResponse.json(await res.json() as Procedure[])
}
```

```ts
// app/api/public/available-slots/route.ts
// Query: ?date=YYYY-MM-DD&procedure_id=UUID
import { NextRequest, NextResponse } from 'next/server'
import type { AvailableSlotsResponse } from '@/lib/lashflow/types'

const API = process.env.LASHFLOW_API_URL!

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url)
  const res = await fetch(`${API}/public/available-slots?${searchParams}`)
  return NextResponse.json(await res.json() as AvailableSlotsResponse)
}
```

```ts
// app/api/public/appointments/route.ts
import { NextRequest, NextResponse } from 'next/server'
import type { Appointment } from '@/lib/lashflow/types'

const API = process.env.LASHFLOW_API_URL!

export async function POST(req: NextRequest) {
  const body = await req.json()
  // body: { procedure_id, scheduled_at, client: { name, phone }, notes? }
  const res = await fetch(`${API}/public/appointments`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  return NextResponse.json(await res.json() as Appointment, { status: 201 })
}
```

---

## Referência rápida

### Erros da API

```ts
// lib/lashflow/errors.ts
export const ERROR_MESSAGES: Record<string, string> = {
  INVALID_TRANSITION: 'Transição de status inválida',
  SLOT_UNAVAILABLE: 'Horário indisponível',
  INSUFFICIENT_STOCK: 'Estoque insuficiente',
  DUPLICATE_PHONE: 'Telefone já cadastrado',
  ALLERGY_DETAIL_REQUIRED: 'Detalhes da alergia são obrigatórios',
}
```

### Tratamento de erro nos hooks

```ts
async function safeFetch<T>(url: string, options?: RequestInit): Promise<T | null> {
  const res = await fetch(url, options)
  if (res.status === 401) {
    // Tenta refresh automático
    const refreshed = await fetch('/api/auth/refresh', { method: 'POST' })
    if (!refreshed.ok) {
      window.location.href = '/login'
      return null
    }
    // Retry
    const retried = await fetch(url, options)
    if (!retried.ok) return null
    return retried.json()
  }
  if (!res.ok) return null
  return res.json()
}
```

### Valores monetários

```
Sempre centavos (int):  25000 = R$ 250,00
formatMoney(25000)   → "R$ 250,00"
toCents("250,00")    → 25000
toCents(250.00)      → 25000
```

### Paginação

```ts
// Parâmetros: page (default 1) e per_page (default 20, max 100)
// Resposta: { data: T[], total: number, page: number, per_page: number }
fetch('/api/clients?page=2&per_page=20')
```
