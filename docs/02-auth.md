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

## Arquitetura com Next.js (padrão BFF)

O padrão recomendado é **Backend for Frontend (BFF)**: o browser nunca fala diretamente com a API LashFlow. Todo tráfego passa pelas API Routes do Next.js, que ficam no servidor.

```
Browser (React)
    │
    │  cookie httpOnly (access_token, refresh_token)
    ▼
Next.js API Routes  ──────────────────────────────────────────────────────
    │  server-side                                                        │
    │  LASHFLOW_CLIENT_ID + LASHFLOW_CLIENT_SECRET (nunca vão ao browser)│
    ▼                                                                     │
LashFlow API  ◄───────────────────────────────────────────────────────────
    Authorization: Bearer <access_token>
    + client_id / client_secret (no login)
```

**Por que BFF?**
- `OAUTH2_CLIENT_ID` e `OAUTH2_CLIENT_SECRET` ficam **apenas no servidor** Next.js — nunca expostos ao browser
- Tokens JWT ficam em **cookies httpOnly** — imunes a XSS
- O browser não sabe onde está a API LashFlow

---

## Configuração

### LashFlow API — `.env`

```env
# Habilita validação de client credentials em /auth/login e /auth/token
# Deixe comentado para dev local / Swagger (sem validação)
OAUTH2_CLIENT_ID=nextjs-app
OAUTH2_CLIENT_SECRET=sua-senha-super-secreta-aqui
```

### Next.js — `.env.local`

```env
# URL da API (nunca NEXT_PUBLIC_ — não deve ir ao browser)
LASHFLOW_API_URL=http://localhost:8000/api/v1

# Deve ser igual ao configurado no LashFlow API
LASHFLOW_CLIENT_ID=nextjs-app
LASHFLOW_CLIENT_SECRET=sua-senha-super-secreta-aqui
```

---

## Implementação no Next.js

### 1. Rota de login — `app/api/auth/login/route.ts`

Recebe username/password do browser, chama a API com as client credentials, devolve cookies httpOnly.

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
    return NextResponse.json({ error: err.detail ?? 'Credenciais inválidas' }, { status: 401 })
  }

  const { access_token, refresh_token } = await res.json()

  const response = NextResponse.json({ ok: true })
  response.cookies.set('access_token', access_token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    path: '/',
    maxAge: 60 * 60 * 24 * 7, // 7 dias
  })
  response.cookies.set('refresh_token', refresh_token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    path: '/',
    maxAge: 60 * 60 * 24 * 30, // 30 dias
  })
  return response
}
```

### 2. Rota de logout — `app/api/auth/logout/route.ts`

```ts
import { NextResponse } from 'next/server'

export async function POST() {
  const response = NextResponse.json({ ok: true })
  response.cookies.delete('access_token')
  response.cookies.delete('refresh_token')
  return response
}
```

### 3. Rota de refresh — `app/api/auth/refresh/route.ts`

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
    const response = NextResponse.json({ error: 'Session expired' }, { status: 401 })
    response.cookies.delete('access_token')
    response.cookies.delete('refresh_token')
    return response
  }

  const { access_token, refresh_token } = await res.json()

  const response = NextResponse.json({ ok: true })
  response.cookies.set('access_token', access_token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    path: '/',
    maxAge: 60 * 60 * 24 * 7,
  })
  response.cookies.set('refresh_token', refresh_token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    path: '/',
    maxAge: 60 * 60 * 24 * 30,
  })
  return response
}
```

### 4. Helper de fetch server-side — `lib/api-server.ts`

Usado nas API Routes do Next.js para chamar a LashFlow API com o token do cookie.

```ts
import { cookies } from 'next/headers'

const API = process.env.LASHFLOW_API_URL!

export async function apiServer(
  path: string,
  options: RequestInit = {}
): Promise<Response> {
  const cookieStore = await cookies()
  const token = cookieStore.get('access_token')?.value

  return fetch(`${API}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  })
}
```

### 5. Exemplo de API Route proxy — `app/api/clients/route.ts`

O browser chama `/api/clients`, o Next.js chama a LashFlow com o token.

```ts
import { NextRequest, NextResponse } from 'next/server'
import { apiServer } from '@/lib/api-server'

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url)
  const res = await apiServer(`/clients?${searchParams}`)

  if (res.status === 401) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const data = await res.json()
  return NextResponse.json(data)
}
```

### 6. Middleware — `middleware.ts`

Protege todas as rotas de dashboard. Valida o token server-side sem expô-lo.

```ts
import { NextRequest, NextResponse } from 'next/server'

const API = process.env.LASHFLOW_API_URL!

export async function middleware(req: NextRequest) {
  const token = req.cookies.get('access_token')?.value

  if (!token) {
    return NextResponse.redirect(new URL('/login', req.url))
  }

  // Valida o token na API (POST /auth/validate nunca lança 401 — sempre retorna { valid })
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

### 7. Hook de login no browser — `hooks/useAuth.ts`

O browser chama as API Routes do Next.js — nunca a LashFlow diretamente.

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

  return { login, logout }
}
```

---

## Fluxo completo — passo a passo

```
1. Usuário preenche login no browser
   POST /api/auth/login  →  Next.js API Route
   Next.js  →  POST /api/v1/auth/login  (com client_id + client_secret)
   LashFlow  →  { access_token, refresh_token }
   Next.js  →  Set-Cookie: access_token=...; HttpOnly  (browser nunca vê o token)

2. Navegação protegida
   Browser  →  GET /dashboard
   Middleware lê cookie access_token → valida em POST /api/v1/auth/validate
   Token válido → deixa passar | inválido → redireciona /login

3. Chamada de dados
   Browser  →  GET /api/clients (Next.js API Route)
   Next.js lê cookie access_token → Authorization: Bearer <token>
   Next.js  →  GET /api/v1/clients  →  LashFlow
   LashFlow  →  { data: [...] }
   Next.js  →  repassa ao browser

4. Token expirado
   Next.js recebe 401 da LashFlow
   Next.js  →  POST /api/v1/auth/refresh  (com refresh_token do cookie)
   LashFlow  →  novo par de tokens
   Next.js  →  atualiza cookies  →  retry automático da requisição
```

---

## Endpoints da API LashFlow

### `POST /api/v1/auth/login`

JSON — usado pelo Next.js BFF.

```json
// Request
{
  "username": "admin",
  "password": "admin",
  "client_id": "nextjs-app",        // obrigatório se OAUTH2_CLIENT_ID estiver configurado
  "client_secret": "senha-secreta"  // obrigatório se OAUTH2_CLIENT_SECRET estiver configurado
}

// Response 200
{ "access_token": "eyJ...", "refresh_token": "eyJ...", "token_type": "bearer" }

// Response 401 — credenciais do usuário inválidas
{ "detail": "Invalid credentials" }

// Response 401 — client_id/secret errado ou ausente
{ "detail": "Invalid client credentials" }
```

### `POST /api/v1/auth/token`

Form-data OAuth2 — alternativa ao /login, compatível com Swagger UI.

```
POST /api/v1/auth/token
Content-Type: application/x-www-form-urlencoded

username=admin&password=admin&client_id=nextjs-app&client_secret=senha-secreta
```

### `POST /api/v1/auth/refresh`

```json
// Request
{ "refresh_token": "eyJ..." }

// Response 200
{ "access_token": "eyJ...", "refresh_token": "eyJ...", "token_type": "bearer" }

// Response 401 — token inválido ou expirado
{ "detail": "Invalid refresh token" }
```

### `POST /api/v1/auth/validate`

**Sempre retorna 200** — nunca 401. Útil para middleware SSR.

```json
// Request
{ "refresh_token": "<qualquer token>" }

// Response 200 — token válido
{ "valid": true, "user_id": "uuid", "username": "admin", "expires_at": "2025-04-07T00:00:00Z" }

// Response 200 — token inválido
{ "valid": false }
```

### `GET /api/v1/auth/me`

```
Header: Authorization: Bearer <access_token>

// Response 200
{ "id": "uuid", "username": "admin", "email": null, "is_superuser": true, "is_active": true, "created_at": "..." }
```

### `POST /api/v1/auth/register`

Cria usuário. **Requer superuser.**

```json
{ "username": "nova_profissional", "password": "senha123", "email": "nova@email.com" }
// Response 201 — MeResponse
```
