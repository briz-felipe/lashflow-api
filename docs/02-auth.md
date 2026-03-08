# Autenticação

[← Voltar ao índice](../readme.md)

## Como funciona

O sistema usa **JWT stateless** com dois tokens:

| Token | Duração padrão | Uso |
|-------|---------------|-----|
| `access_token` | 7 dias | Enviado em todas as requisições autenticadas |
| `refresh_token` | 30 dias | Usado apenas para obter novo par de tokens |

Todos os tokens carregam `{ sub: user_id, exp: timestamp, type: "access"|"refresh" }`.

---

## Fluxo completo

```
1. POST /api/v1/auth/login
   → { access_token, refresh_token }

2. Requisições autenticadas:
   Header: Authorization: Bearer <access_token>

3. Token expirado (resposta 401):
   POST /api/v1/auth/refresh { refresh_token }
   → { access_token, refresh_token }  (novo par)

4. Verificar se ainda autenticado (SSR / middleware):
   POST /api/v1/auth/validate { refresh_token: "<qualquer token>" }
   → { valid: true|false, ... }
```

---

## Endpoints

### `POST /api/v1/auth/login`

```json
// Request
{ "username": "admin", "password": "admin" }

// Response 200
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}

// Response 401
{ "detail": "Invalid credentials" }
```

---

### `POST /api/v1/auth/refresh`

```json
// Request
{ "refresh_token": "eyJ..." }

// Response 200
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}

// Response 401 — token inválido ou expirado
{ "detail": "Invalid refresh token" }

// Response 401 — enviou access token em vez de refresh
{ "detail": "Invalid token type" }
```

---

### `GET /api/v1/auth/validate`

Valida o access token no header Bearer. Retorna 401 se inválido.

```
Header: Authorization: Bearer <access_token>

// Response 200
{
  "valid": true,
  "user_id": "uuid",
  "username": "admin"
}
```

---

### `POST /api/v1/auth/validate`

Valida qualquer token no body. **Sempre retorna 200** (nunca 401) — útil para SSR.

```json
// Request
{ "refresh_token": "<qualquer token>" }

// Response 200 — token válido
{
  "valid": true,
  "user_id": "uuid",
  "username": "admin",
  "expires_at": "2025-04-07T00:00:00Z"
}

// Response 200 — token inválido
{ "valid": false }
```

---

### `GET /api/v1/auth/me`

Retorna dados do usuário autenticado.

```
Header: Authorization: Bearer <access_token>

// Response 200
{
  "id": "uuid",
  "username": "admin",
  "email": null,
  "is_superuser": true,
  "is_active": true,
  "created_at": "2025-03-07T..."
}
```

---

### `POST /api/v1/auth/register`

Cria um novo usuário. **Requer superuser.**

```json
// Request
{
  "username": "nova_profissional",
  "password": "senha123",
  "email": "nova@email.com"   // opcional
}

// Response 201 — MeResponse
```

---

## Gerenciamento de tokens no frontend

### Armazenamento básico

```ts
// lib/auth.ts
export function saveTokens(access: string, refresh: string) {
  localStorage.setItem('access_token', access)
  localStorage.setItem('refresh_token', refresh)
}

export function clearTokens() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
}
```

### Refresh automático com interceptor

```ts
// lib/api.ts
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1'

export async function apiFetch(path: string, options: RequestInit = {}): Promise<Response> {
  let token = localStorage.getItem('access_token')

  let res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  })

  // Token expirado — tenta refresh automático uma vez
  if (res.status === 401) {
    const refreshToken = localStorage.getItem('refresh_token')
    if (!refreshToken) {
      clearTokens()
      window.location.href = '/login'
      return res
    }

    const refreshRes = await fetch(`${API_URL}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    })

    if (!refreshRes.ok) {
      clearTokens()
      window.location.href = '/login'
      return res
    }

    const { access_token, refresh_token } = await refreshRes.json()
    saveTokens(access_token, refresh_token)

    // Retry com novo token
    res = await fetch(`${API_URL}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${access_token}`,
        ...options.headers,
      },
    })
  }

  return res
}
```

### Middleware Next.js (App Router)

```ts
// middleware.ts
import { NextRequest, NextResponse } from 'next/server'

export async function middleware(req: NextRequest) {
  const token = req.cookies.get('access_token')?.value
  if (!token) return NextResponse.redirect(new URL('/login', req.url))

  const res = await fetch(`${process.env.API_URL}/api/v1/auth/validate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: token }),
  })
  const data = await res.json()

  if (!data.valid) return NextResponse.redirect(new URL('/login', req.url))
  return NextResponse.next()
}

export const config = {
  matcher: ['/dashboard/:path*'],
}
```

### Hook de autenticação (React)

```ts
// hooks/useAuth.ts
import { useCallback } from 'react'
import { useRouter } from 'next/navigation'

export function useAuth() {
  const router = useRouter()

  const login = useCallback(async (username: string, password: string) => {
    const res = await fetch('/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    })
    if (!res.ok) throw new Error('Credenciais inválidas')
    const { access_token, refresh_token } = await res.json()
    localStorage.setItem('access_token', access_token)
    localStorage.setItem('refresh_token', refresh_token)
    router.push('/dashboard')
  }, [router])

  const logout = useCallback(() => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    router.push('/login')
  }, [router])

  return { login, logout }
}
```
