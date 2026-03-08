# Schemas, Tipos e Modelo de Dados

[← Voltar ao índice](../readme.md)

## Enums

```ts
type AppointmentStatus = 'pending_approval' | 'confirmed' | 'in_progress' | 'completed' | 'cancelled' | 'no_show'
type PaymentStatus     = 'pending' | 'paid' | 'partial' | 'refunded' | 'failed'
type PaymentMethod     = 'cash' | 'credit_card' | 'debit_card' | 'pix' | 'bank_transfer' | 'other'
type LashTechnique     = 'classic' | 'volume' | 'hybrid' | 'mega_volume' | 'wispy' | 'wet_look' | 'other'
type LashServiceType   = 'application' | 'maintenance' | 'removal' | 'lash_lifting' | 'permanent'
type ClientSegment     = 'volume' | 'classic' | 'hybrid' | 'vip' | 'recorrente' | 'inativa'
type MaterialCategory  = 'essenciais' | 'acessorios' | 'descartaveis' | 'quimicos' | 'opcionais'
type MaterialUnit      = 'un' | 'pacote' | 'caixa' | 'ml' | 'g' | 'par' | 'rolo' | 'kit'
type StockMovementType = 'purchase' | 'usage' | 'adjustment'
type ExpenseRecurrence = 'one_time' | 'monthly' | 'weekly' | 'yearly'
```

---

## Convenções gerais

| Campo | Formato |
|-------|---------|
| Valores monetários | Sempre **centavos** (int). `25000 = R$ 250,00` |
| Datas com hora | ISO 8601: `"2025-04-10T09:00:00-03:00"` |
| Mês de referência | `"YYYY-MM"`: `"2025-04"` |
| Data simples | `"YYYY-MM-DD"`: `"2025-04-10"` |
| Telefone | Apenas dígitos: `"11999990000"` (o backend normaliza) |
| IDs | UUID v4 |

---

## Entidades e soft delete

| Entidade | Soft delete | Observação |
|----------|-------------|------------|
| `Client` | `deleted_at` | Preserva histórico de agendamentos e pagamentos |
| `Procedure` | `is_active: false` | Nunca deletar — use `PATCH /:id/toggle` |
| `Material` | `is_active: false` | Nunca deletar — use `DELETE` que desativa |
| `Appointment` | Hard delete | |
| `Payment` | Hard delete | |
| `Expense` | Hard delete | Deleta apenas a parcela individual, não o grupo |

---

## Campos calculados do Client

Calculados via query no repository — **não armazenados** na coluna:

| Campo | Cálculo |
|-------|---------|
| `total_spent` | Soma de `Payment.paid_amount_in_cents` do cliente |
| `appointments_count` | Contagem de appointments com `status = completed` |
| `last_appointment_date` | Máximo `scheduled_at` com `status = completed` |
| `favorite_procedure_id` | `procedure_id` mais frequente em appointments `completed` |

---

## Segmentação de clientes

Um cliente pode ter múltiplos segmentos simultaneamente:

| Segmento | Critério |
|----------|----------|
| `vip` | `appointments_count >= 5` OU `total_spent >= R$1.000` |
| `recorrente` | Último agendamento há menos de 45 dias E `appointments_count >= 2` |
| `inativa` | Sem agendamento há mais de 60 dias (ou nunca teve) |
| `volume` | Técnica mais usada é `volume` ou `mega_volume` |
| `classic` | Técnica mais usada é `classic` |
| `hybrid` | Técnica mais usada é `hybrid` |

---

## Algoritmo de slots disponíveis

```
1. Data está em BlockedDates? → retorna []
2. Existe TimeSlot para o dia da semana com is_available = true? → senão retorna []
3. Gerar candidatos de 30 em 30 min entre startTime e endTime
4. Filtrar: candidato + duration_minutes <= endTime
5. Filtrar: não conflita com appointments ativos (cancelled e no_show não bloqueiam)
6. Filtrar: não está no passado
```

---

## Parcelamento de despesas

Ao criar com `installments > 1`:

- Backend gera N registros com mesmo `installment_group_id`
- `reference_month` é incrementado mês a mês
- `recurrence` é forçado para `monthly`
- `DELETE /expenses/:id` deleta apenas aquela parcela (não o grupo)

---

## Status de pagamento (calculado automaticamente)

| Condição | Status |
|----------|--------|
| `paid_amount = 0` | `pending` |
| `0 < paid_amount < total_amount` | `partial` |
| `paid_amount >= total_amount` | `paid` |

Nunca envie `status` no body — ele é calculado pelo backend via `payment_service.calculate_status()`.

---

## Isolamento por profissional

Toda entidade tem `professional_id` vinculado ao JWT do usuário autenticado. O campo é **sempre extraído do token** — nunca do body da requisição. Todas as queries filtram automaticamente por `professional_id`.
