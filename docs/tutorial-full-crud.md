# Tutorial: Full CRUD API

!!! tip "Prerequisites"
    Complete the [Getting Started](getting-started.md) guide first. This tutorial
    assumes you are familiar with `@component`, `@configured`, and `pico_boot.init()`.

    You can also scaffold this project instantly with
    [pico-initializer](https://dperezcabrera.github.io/pico-initializer/) — select
    **fastapi**, **sqlalchemy**, **pydantic**, and **auth**, then enable the
    **Products CRUD** example.

This tutorial walks through building a production-ready **Products API** using the
pico ecosystem. The example is a versioned REST API (`/api/v1/`) that
manages a product catalog — creation, listing, search, pagination, partial
updates, soft and hard deletion — secured with JWT and role-based access control.

The goal is to show how the different pico packages fit together as a cohesive
stack, and how each one takes responsibility for a distinct layer:

- **pico-boot** wires everything together with zero boilerplate
- **pico-client-auth** protects all routes by default; you opt individual ones out
- **pico-pydantic** guards the service contract regardless of how the service is called
- **pico-sqlalchemy** handles transactions and queries declaratively
- **pico-fastapi** keeps controllers thin — pure HTTP mapping, no business logic

By the end you will have a working API where an invalid JWT, a missing role, a
malformed request body, and a domain constraint violation each fail fast at their
own layer, with the right HTTP status and without leaking details across layers.

---

## Stack

| Library | Role |
|---------|------|
| `pico-boot` | Bootstrap, plugin auto-discovery, config loading |
| `pico-ioc` | IoC container, constructor injection |
| `pico-fastapi` | HTTP controllers with `@controller` |
| `pico-sqlalchemy` | Repositories, transactions, declarative queries |
| `pico-pydantic` | AOP validation in the service layer with `@validate` |
| `pico-client-auth` | JWT authentication, RBAC, `SecurityContext` |
| `pydantic` | HTTP schemas (input/output DTOs) |

---

## Installation

```bash
pip install \
  pico-boot \
  pico-fastapi \
  pico-sqlalchemy \
  pico-pydantic \
  pico-client-auth \
  aiosqlite \
  pydantic \
  uvicorn
```

> Replace `aiosqlite` with `asyncpg` for PostgreSQL.

---

## Database model

The example uses a single `products` table. `active` enables soft-deletion — deactivated products disappear from all queries without being physically removed.

<svg width="100%" viewBox="0 0 680 310" xmlns="http://www.w3.org/2000/svg">
<defs><style>.db-t{font:400 14px system-ui,sans-serif;fill:#2c2c2a}.db-ts{font:400 12px system-ui,sans-serif;fill:#5f5e5a}.db-th{font:500 14px system-ui,sans-serif;fill:#2c2c2a}.db-m{font:400 12px ui-monospace,monospace;fill:#185fa5}@media(prefers-color-scheme:dark){.db-t{fill:#c2c0b6}.db-ts{fill:#9c9a92}.db-th{fill:#c2c0b6}.db-m{fill:#85b7eb}}</style></defs>
<rect x="140" y="20" width="400" height="270" rx="10" fill="none" stroke="rgba(0,0,0,.12)" stroke-width="1"/>
<rect x="140" y="20" width="400" height="42" rx="10" fill="#185fa5"/>
<rect x="140" y="42" width="400" height="20" fill="#185fa5"/>
<text class="db-th" x="340" y="47" text-anchor="middle" fill="#fff">products</text>
<rect x="140" y="62" width="400" height="28" fill="rgba(0,0,0,.04)"/>
<text class="db-ts" x="168" y="80">column</text>
<text class="db-ts" x="320" y="80">type</text>
<text class="db-ts" x="430" y="80">constraints</text>
<line x1="140" y1="90" x2="540" y2="90" stroke="rgba(0,0,0,.08)" stroke-width="1"/>
<rect x="140" y="90" width="400" height="30" fill="#fff"/>
<circle cx="164" cy="105" r="5" fill="#EF9F27" stroke="#BA7517" stroke-width="1"/>
<text class="db-th" x="180" y="110">id</text>
<text class="db-m" x="320" y="110">INTEGER</text>
<text class="db-ts" x="430" y="110">PK · autoincrement</text>
<line x1="140" y1="120" x2="540" y2="120" stroke="rgba(0,0,0,.05)" stroke-width="1"/>
<rect x="140" y="120" width="400" height="30" fill="#f8f7f4"/>
<text class="db-t" x="180" y="139">name</text>
<text class="db-m" x="320" y="139">VARCHAR(100)</text>
<text class="db-ts" x="430" y="139">NOT NULL</text>
<line x1="140" y1="150" x2="540" y2="150" stroke="rgba(0,0,0,.05)" stroke-width="1"/>
<rect x="140" y="150" width="400" height="30" fill="#fff"/>
<text class="db-t" x="180" y="169">description</text>
<text class="db-m" x="320" y="169">VARCHAR(500)</text>
<text class="db-ts" x="430" y="169">nullable</text>
<line x1="140" y1="180" x2="540" y2="180" stroke="rgba(0,0,0,.05)" stroke-width="1"/>
<rect x="140" y="180" width="400" height="30" fill="#f8f7f4"/>
<text class="db-t" x="180" y="199">price</text>
<text class="db-m" x="320" y="199">FLOAT</text>
<text class="db-ts" x="430" y="199">NOT NULL</text>
<line x1="140" y1="210" x2="540" y2="210" stroke="rgba(0,0,0,.05)" stroke-width="1"/>
<rect x="140" y="210" width="400" height="30" fill="#fff"/>
<text class="db-t" x="180" y="229">stock</text>
<text class="db-m" x="320" y="229">INTEGER</text>
<text class="db-ts" x="430" y="229">NOT NULL · default 0</text>
<line x1="140" y1="240" x2="540" y2="240" stroke="rgba(0,0,0,.05)" stroke-width="1"/>
<rect x="140" y="240" width="400" height="30" fill="#f8f7f4"/>
<text class="db-t" x="180" y="259">active</text>
<text class="db-m" x="320" y="259">BOOLEAN</text>
<text class="db-ts" x="430" y="259">NOT NULL · default true</text>
<line x1="140" y1="270" x2="540" y2="270" stroke="rgba(0,0,0,.06)" stroke-width="1"/>
<text class="db-ts" x="164" y="287">PK</text>
<circle cx="178" cy="283" r="4" fill="#EF9F27" stroke="#BA7517" stroke-width="1"/>
<text class="db-ts" x="188" y="287">primary key     soft-delete via active = false</text>
</svg>

---

## Layer architecture

Each pico package owns exactly one layer. The IoC container resolves constructor dependencies automatically — no manual wiring between layers.

<svg width="100%" viewBox="0 0 680 560" xmlns="http://www.w3.org/2000/svg">
<defs>
<style>.la-ts{font:400 12px system-ui,sans-serif;fill:#5f5e5a}.la-th{font:500 14px system-ui,sans-serif}@media(prefers-color-scheme:dark){.la-ts{fill:#9c9a92}}</style>
<marker id="la-arr" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M2 1L8 5L2 9" fill="none" stroke="context-stroke" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></marker>
</defs>

<!-- Band 1: HTTP — height 108, y=16..124 -->
<rect x="20" y="16" width="640" height="108" rx="10" fill="#E6F1FB" stroke="#B5D4F4" stroke-width="0.5"/>
<text class="la-ts" x="36" y="33" fill="#0C447C">HTTP layer — pico-fastapi · pico-client-auth</text>
<!-- 3 boxes: w=186, gap=20  3×186+2×20=598, left=40+1=41 -->
<rect x="40" y="42" width="186" height="68" rx="7" fill="#185fa5" stroke="#0C447C" stroke-width="0.5"/>
<text class="la-th" x="133" y="72" text-anchor="middle" dominant-baseline="central" fill="#fff">ProductController</text>
<text class="la-ts" x="133" y="96" text-anchor="middle" fill="#B5D4F4">@controller · /api/v1/products</text>
<rect x="246" y="42" width="186" height="68" rx="7" fill="#185fa5" stroke="#0C447C" stroke-width="0.5"/>
<text class="la-th" x="339" y="72" text-anchor="middle" dominant-baseline="central" fill="#fff">JWT middleware</text>
<text class="la-ts" x="339" y="96" text-anchor="middle" fill="#B5D4F4">validates Bearer token</text>
<rect x="452" y="42" width="186" height="68" rx="7" fill="#185fa5" stroke="#0C447C" stroke-width="0.5"/>
<text class="la-th" x="545" y="72" text-anchor="middle" dominant-baseline="central" fill="#fff">RoleResolver</text>
<text class="la-ts" x="545" y="96" text-anchor="middle" fill="#B5D4F4">extracts roles from claims</text>

<!-- Band 2: Service — y=148..256 -->
<rect x="20" y="148" width="640" height="108" rx="10" fill="#EAF3DE" stroke="#C0DD97" stroke-width="0.5"/>
<text class="la-ts" x="36" y="165" fill="#27500A">Service layer — pico-ioc · pico-pydantic</text>
<rect x="40" y="174" width="186" height="68" rx="7" fill="#3B6D11" stroke="#27500A" stroke-width="0.5"/>
<text class="la-th" x="133" y="204" text-anchor="middle" dominant-baseline="central" fill="#fff">ProductService</text>
<text class="la-ts" x="133" y="228" text-anchor="middle" fill="#C0DD97">@validate · @transactional</text>
<rect x="246" y="174" width="186" height="68" rx="7" fill="#3B6D11" stroke="#27500A" stroke-width="0.5"/>
<text class="la-th" x="339" y="204" text-anchor="middle" dominant-baseline="central" fill="#fff">SecurityContext</text>
<text class="la-ts" x="339" y="228" text-anchor="middle" fill="#C0DD97">request-scoped ContextVar</text>
<rect x="452" y="174" width="186" height="68" rx="7" fill="#3B6D11" stroke="#27500A" stroke-width="0.5"/>
<text class="la-th" x="545" y="204" text-anchor="middle" dominant-baseline="central" fill="#fff">ValidationInterceptor</text>
<text class="la-ts" x="545" y="228" text-anchor="middle" fill="#C0DD97">AOP — pico-pydantic</text>

<!-- Band 3: Data — y=280..388 -->
<rect x="20" y="280" width="640" height="108" rx="10" fill="#FAEEDA" stroke="#FAC775" stroke-width="0.5"/>
<text class="la-ts" x="36" y="297" fill="#633806">Data layer — pico-sqlalchemy</text>
<!-- 2 boxes centred: w=270, gap=40  total 580, left=50 -->
<rect x="50" y="306" width="270" height="68" rx="7" fill="#854F0B" stroke="#633806" stroke-width="0.5"/>
<text class="la-th" x="185" y="336" text-anchor="middle" dominant-baseline="central" fill="#fff">ProductRepository</text>
<text class="la-ts" x="185" y="360" text-anchor="middle" fill="#FAC775">@repository · @query (declarative)</text>
<rect x="360" y="306" width="270" height="68" rx="7" fill="#854F0B" stroke="#633806" stroke-width="0.5"/>
<text class="la-th" x="495" y="336" text-anchor="middle" dominant-baseline="central" fill="#fff">SessionManager</text>
<text class="la-ts" x="495" y="360" text-anchor="middle" fill="#FAC775">async engine · implicit commit</text>

<!-- Band 4: Infra — y=412..520 -->
<rect x="20" y="412" width="640" height="108" rx="10" fill="#F1EFE8" stroke="#D3D1C7" stroke-width="0.5"/>
<text class="la-ts" x="36" y="429" fill="#444441">Infrastructure</text>
<rect x="50" y="438" width="270" height="68" rx="7" fill="#888780" stroke="#5F5E5A" stroke-width="0.5"/>
<text class="la-th" x="185" y="468" text-anchor="middle" dominant-baseline="central" fill="#fff">Database</text>
<text class="la-ts" x="185" y="492" text-anchor="middle" fill="#D3D1C7">SQLite · PostgreSQL</text>
<rect x="360" y="438" width="270" height="68" rx="7" fill="#888780" stroke="#5F5E5A" stroke-width="0.5"/>
<text class="la-th" x="495" y="468" text-anchor="middle" dominant-baseline="central" fill="#fff">JWKS endpoint</text>
<text class="la-ts" x="495" y="492" text-anchor="middle" fill="#D3D1C7">RSA public keys · TTL cache</text>

<!-- Arrows HTTP  Service (col centres: 133, 339, 545) -->
<line x1="133" y1="110" x2="133" y2="174" stroke="#378ADD" stroke-width="1.2" marker-end="url(#la-arr)"/>
<line x1="339" y1="110" x2="339" y2="174" stroke="#378ADD" stroke-width="1.2" marker-end="url(#la-arr)"/>
<line x1="545" y1="110" x2="545" y2="174" stroke="#378ADD" stroke-width="1.2" marker-end="url(#la-arr)"/>

<!-- Arrows Service  Data (L-bends to stay clear of band borders) -->
<path d="M133 242 L133 264 L185 264 L185 306" stroke="#639922" stroke-width="1.2" fill="none" marker-end="url(#la-arr)"/>
<path d="M339 242 L339 264 L495 264 L495 306" stroke="#639922" stroke-width="1" stroke-dasharray="5 3" fill="none" marker-end="url(#la-arr)"/>

<!-- Arrows Data  Infra -->
<line x1="185" y1="374" x2="185" y2="438" stroke="#BA7517" stroke-width="1.2" marker-end="url(#la-arr)"/>
<line x1="495" y1="374" x2="495" y2="438" stroke="#BA7517" stroke-width="1.2" marker-end="url(#la-arr)"/>

<!-- Legend -->
<line x1="250" y1="540" x2="290" y2="540" stroke="#5F5E5A" stroke-width="1.2" marker-end="url(#la-arr)"/>
<text class="la-ts" x="298" y="544">constructor injection</text>
<line x1="420" y1="540" x2="460" y2="540" stroke="#5F5E5A" stroke-width="1" stroke-dasharray="5 3" marker-end="url(#la-arr)"/>
<text class="la-ts" x="468" y="544">reads / wraps</text>
</svg>

---

## Auth server separation

The Products API and the Auth server run as **independent processes**. The API never stores credentials — it validates JWTs using only the public keys from the Auth server's JWKS endpoint, cached locally with a configurable TTL.

<svg width="100%" viewBox="0 0 680 400" xmlns="http://www.w3.org/2000/svg">
<defs><style>.as-t{font:400 14px system-ui,sans-serif;fill:#2c2c2a}.as-ts{font:400 12px system-ui,sans-serif;fill:#5f5e5a}.as-th{font:500 14px system-ui,sans-serif;fill:#2c2c2a}.as-b{font:500 10px system-ui,sans-serif}@media(prefers-color-scheme:dark){.as-t{fill:#c2c0b6}.as-ts{fill:#9c9a92}.as-th{fill:#c2c0b6}}</style>
<marker id="as-arr" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M2 1L8 5L2 9" fill="none" stroke="context-stroke" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></marker>
</defs>
<!-- Client process -->
<rect x="20" y="60" width="140" height="200" rx="10" fill="#F1EFE8" stroke="#888780" stroke-width="0.8"/>
<text class="as-b" x="90" y="80" text-anchor="middle" fill="#444441">CLIENT</text>
<rect x="38" y="90" width="104" height="36" rx="6" fill="#888780" stroke="#5F5E5A" stroke-width="0.5"/>
<text class="as-th" x="90" y="112" text-anchor="middle" fill="#fff">Browser / App</text>
<text class="as-ts" x="90" y="152">1. POST /login</text>
<text class="as-ts" x="90" y="170">2. Receives JWT</text>
<text class="as-ts" x="90" y="188">3. Calls API</text>
<text class="as-ts" x="90" y="206">   with Bearer</text>
<!-- Auth server process -->
<rect x="258" y="20" width="164" height="290" rx="10" fill="#EEEDFE" stroke="#534AB7" stroke-width="0.8"/>
<text class="as-b" x="340" y="42" text-anchor="middle" fill="#3C3489">AUTH SERVER</text>
<text class="as-ts" x="340" y="58" text-anchor="middle" fill="#534AB7">separate process</text>
<rect x="276" y="68" width="128" height="36" rx="6" fill="#534AB7" stroke="#3C3489" stroke-width="0.5"/>
<text class="as-th" x="340" y="90" text-anchor="middle" fill="#fff">Login endpoint</text>
<rect x="276" y="116" width="128" height="36" rx="6" fill="#534AB7" stroke="#3C3489" stroke-width="0.5"/>
<text class="as-th" x="340" y="138" text-anchor="middle" fill="#fff">JWT issuer</text>
<rect x="276" y="164" width="128" height="36" rx="6" fill="#7F77DD" stroke="#534AB7" stroke-width="0.5"/>
<text class="as-th" x="340" y="183" text-anchor="middle" fill="#fff">JWKS endpoint</text>
<text class="as-b" x="340" y="198" text-anchor="middle" fill="#EEEDFE">GET /jwks.json</text>
<rect x="276" y="212" width="128" height="48" rx="6" fill="#3C3489" stroke="#26215C" stroke-width="0.5"/>
<text class="as-th" x="340" y="232" text-anchor="middle" fill="#fff">RSA key pair</text>
<text class="as-b" x="340" y="250" text-anchor="middle" fill="#AFA9EC">private signs · public verifies</text>
<!-- Products API process -->
<rect x="498" y="60" width="162" height="290" rx="10" fill="#E1F5EE" stroke="#0F6E56" stroke-width="0.8"/>
<text class="as-b" x="579" y="80" text-anchor="middle" fill="#085041">PRODUCTS API</text>
<text class="as-ts" x="579" y="96" text-anchor="middle" fill="#0F6E56">separate process</text>
<rect x="516" y="106" width="126" height="36" rx="6" fill="#0F6E56" stroke="#085041" stroke-width="0.5"/>
<text class="as-th" x="579" y="128" text-anchor="middle" fill="#fff">JWT middleware</text>
<rect x="516" y="154" width="126" height="44" rx="6" fill="#0F6E56" stroke="#085041" stroke-width="0.5"/>
<text class="as-th" x="579" y="174" text-anchor="middle" fill="#fff">JWKS cache</text>
<text class="as-b" x="579" y="190" text-anchor="middle" fill="#9FE1CB">TTL 300s</text>
<rect x="516" y="210" width="126" height="36" rx="6" fill="#0F6E56" stroke="#085041" stroke-width="0.5"/>
<text class="as-th" x="579" y="232" text-anchor="middle" fill="#fff">SecurityContext</text>
<rect x="516" y="258" width="126" height="36" rx="6" fill="#0F6E56" stroke="#085041" stroke-width="0.5"/>
<text class="as-th" x="579" y="280" text-anchor="middle" fill="#fff">ProductController</text>
<rect x="516" y="330" width="126" height="36" rx="6" fill="#888780" stroke="#5F5E5A" stroke-width="0.5"/>
<text class="as-th" x="579" y="352" text-anchor="middle" fill="#fff">Database</text>
<line x1="579" y1="294" x2="579" y2="330" stroke="#0F6E56" stroke-width="1.2" marker-end="url(#as-arr)" fill="none"/>
<!-- Login flow -->
<path d="M160 104 L258 104" stroke="#534AB7" stroke-width="1.2" marker-end="url(#as-arr)" fill="none"/>
<text class="as-ts" x="209" y="98" text-anchor="middle" fill="#534AB7">POST /login</text>
<path d="M258 140 L160 140" stroke="#534AB7" stroke-width="1.2" marker-end="url(#as-arr)" fill="none"/>
<text class="as-ts" x="209" y="134" text-anchor="middle" fill="#534AB7">JWT token</text>
<!-- Client  API with Bearer -->
<path d="M160 196 L300 360 L498 196" stroke="#0F6E56" stroke-width="1.2" marker-end="url(#as-arr)" fill="none"/>
<text class="as-ts" x="300" y="384" text-anchor="middle" fill="#0F6E56">Bearer &lt;jwt&gt;</text>
<!-- API  JWKS (cached fetch) -->
<path d="M516 172 L422 182" stroke="#7F77DD" stroke-width="1.2" stroke-dasharray="5 3" marker-end="url(#as-arr)" fill="none"/>
<text class="as-ts" x="468" y="162" text-anchor="middle" fill="#7F77DD">GET /jwks.json</text>
<text class="as-ts" x="468" y="176" text-anchor="middle" fill="#9c9a92">cached · TTL 300s</text>
<!-- Private key signs JWT (internal) -->
<line x1="340" y1="164" x2="340" y2="152" stroke="#AFA9EC" stroke-width="1" stroke-dasharray="3 3" marker-end="url(#as-arr)" fill="none"/>
<!-- Security note -->
<rect x="160" y="306" width="300" height="46" rx="8" fill="rgba(227,68,49,.06)" stroke="rgba(227,68,49,.2)" stroke-width="0.8"/>
<text class="as-b" x="310" y="326" text-anchor="middle" fill="#993C1D">CREDENTIALS NEVER REACH THE API</text>
<text class="as-ts" x="310" y="342" text-anchor="middle" fill="#993C1D">only the public key (JWKS) is shared</text>
</svg>

---

## Project structure

```
├── application.yaml         # all configuration — one file for the whole stack
├── main.py                  # 5 lines — full bootstrap
└── myapp/
    ├── __init__.py
    ├── database.py          # DatabaseConfigurer — auto-creates tables on startup
    ├── models.py            # SQLAlchemy entity — tables only, no logic
    ├── schemas.py           # Pydantic schemas — HTTP DTOs + domain contract
    ├── repositories.py      # database access — declarative queries, no session boilerplate
    ├── services.py          # business logic — transactions, validation, domain rules
    ├── controllers.py       # HTTP routes — thin mapping layer, no business logic
    └── auth.py              # custom RoleResolver (optional — only if your IdP is non-standard)
```

The `pico-ioc` scanner is **recursive**: declaring `"myapp"` in `init()` is
enough to discover everything in any subpackage. No explicit imports between
layers are needed for wiring — the IoC container resolves constructor
dependencies by type.

---

## Configuration — `application.yaml`

All configuration for all plugins in a single file:

```yaml
# Database — read by pico-sqlalchemy
database:
  url: sqlite+aiosqlite:///./products.db
  echo: false

# FastAPI — read by pico-fastapi
fastapi:
  title: Products API
  version: 1.0.0

# JWT auth — read by pico-client-auth
auth_client:
  issuer: https://auth.example.com   # required — fails at startup if missing
  audience: my-api                   # required — fails at startup if missing
  jwks_ttl_seconds: 300
  accepted_algorithms:
    - RS256
```

Each package reads its own section. There is no configuration code anywhere
in the application components.

Environment variables override any YAML value:

```bash
DATABASE__URL=postgresql+asyncpg://user:pass@db/prod \
AUTH_CLIENT__ISSUER=https://auth.prod.com \
uvicorn main:app
```

---

## Bootstrap — `main.py`

```python
from pico_boot import init
from pico_ioc import configuration, YamlTreeSource, EnvSource
from fastapi import FastAPI

container = init(
    modules=["myapp"],
    config=configuration(YamlTreeSource("application.yaml"), EnvSource()),
)

app = container.get(FastAPI)
```

That's it. `pico-boot` discovers all installed plugins via entry points
(`pico-fastapi`, `pico-sqlalchemy`, `pico-pydantic`, `pico-client-auth`)
and initializes them in the correct order. There is no explicit mention of
those packages anywhere in the code.

```bash
uvicorn main:app --reload
# Swagger at http://localhost:8000/docs
```

---

## Request flow

```
POST /api/v1/products/  Authorization: Bearer <jwt>
         │
         ▼
pico-client-auth (automatic middleware)
  ├─ validates JWT signature against JWKS
  ├─ checks iss, aud, exp
  ├─ resolves roles via RoleResolver
  └─ populates SecurityContext            401 if token invalid/missing
         │
         ▼
@requires_role("product-manager")        403 if insufficient permissions
         │
         ▼
ProductController.create_product(body: ProductCreate)
  └─ FastAPI validates the body           422 if HTTP data invalid
         │
         ▼
ProductService.create(data: ProductData)
  └─ pico-pydantic @validate              ValidationFailedError if contract broken
         │
         ▼
@transactional opens async session
         │
         ▼
ProductRepository.save(product)
  └─ flush() + automatic commit
         │
         ▼
HTTP 201  {"id": 1, "name": "Laptop Pro", ...}
```

Three independent validation layers, each in the right place: auth before
touching any code, HTTP data at the HTTP boundary, domain contract inside
the service.

---

## 1. Entity — `myapp/models.py`

```python
from sqlalchemy import Integer, String, Float, Boolean
from pico_sqlalchemy import AppBase, Mapped, mapped_column


class Product(AppBase):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
```

`AppBase` is the declarative base from `pico-sqlalchemy`. Entity subclasses are
discovered automatically, but table creation requires a `DatabaseConfigurer`
component.

---

## 1b. Table setup — `myapp/database.py`

```python
import asyncio

from pico_ioc import component
from pico_sqlalchemy import DatabaseConfigurer, AppBase


@component
class SchemaSetup(DatabaseConfigurer):
    def __init__(self, base: AppBase):
        self.base = base

    @property
    def priority(self) -> int:
        return 0

    def configure_database(self, engine) -> None:
        async def _create():
            async with engine.begin() as conn:
                await conn.run_sync(self.base.metadata.create_all)
        asyncio.run(_create())
```

This component is auto-discovered by the IoC scanner. On startup,
`pico-sqlalchemy` calls `configure_database()` and the tables are created.

---

## 2. Schemas — `myapp/schemas.py`

Two types of schemas with distinct purposes:

- **HTTP schemas** (`ProductCreate`, `ProductUpdate`, `ProductResponse`): define
  the REST API contract. FastAPI uses them to validate and serialize at the HTTP
  boundary.
- **Domain schema** (`ProductData`): defines the internal service contract.
  `pico-pydantic` enforces it on every call to the service, regardless of
  origin — HTTP, Celery, tests, scripts, anything.

```python
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Self


# --- HTTP schemas ---

class ProductCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    price: float = Field(gt=0)
    stock: int = Field(ge=0, default=0)

    @field_validator("name")
    @classmethod
    def name_no_spaces_only(cls, v: str) -> str:
        if v.strip() == "":
            raise ValueError("Name cannot be whitespace only")
        return v.strip()

    @field_validator("price")
    @classmethod
    def price_max_two_decimals(cls, v: float) -> float:
        if round(v, 2) != v:
            raise ValueError("Price cannot have more than 2 decimal places")
        return v


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    price: float | None = Field(default=None, gt=0)
    stock: int | None = Field(default=None, ge=0)
    active: bool | None = Field(default=None)

    @model_validator(mode="after")
    def at_least_one_field(self) -> Self:
        if all(v is None for v in self.model_dump().values()):
            raise ValueError("At least one field must be provided for update")
        return self


class ProductResponse(BaseModel):
    model_config = {"from_attributes": True}  # builds from ORM without manual mapping

    id: int
    name: str
    description: str | None
    price: float
    stock: int
    active: bool


class ProductListResponse(BaseModel):
    items: list[ProductResponse]
    total: int
    page: int
    page_size: int


# --- Domain schema (for pico-pydantic) ---

class ProductData(BaseModel):
    """
    Internal service contract. pico-pydantic enforces this on every
    call to the service, regardless of where the call comes from.
    """
    name: str = Field(min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    price: float = Field(gt=0)
    stock: int = Field(ge=0, default=0)

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        return v.strip()
```

`ProductData` is independent of FastAPI. The fact that the HTTP schema and the
domain schema look similar here is coincidental — in real systems they often
diverge.

---

## 3. Repository — `myapp/repositories.py`

```python
from pico_sqlalchemy import repository, query, SessionManager, get_session
from .models import Product


@repository(entity=Product)
class ProductRepository:
    def __init__(self, manager: SessionManager):
        self.manager = manager

    # Write methods — implicitly Read-Write by @repository

    async def save(self, product: Product) -> Product:
        session = get_session(self.manager)
        session.add(product)
        await session.flush()     # INSERT/UPDATE without commit
        await session.refresh(product)
        return product

    async def delete(self, product: Product) -> None:
        session = get_session(self.manager)
        await session.delete(product)

    # Declarative queries — implicitly Read-Only by @query.
    # The "..." body is ignored; pico-sqlalchemy generates and
    # executes the SQL from the expr.

    @query(expr="id = :id", unique=True)
    async def find_by_id(self, id: int) -> Product | None: ...

    @query(expr="active = true")
    async def find_all_active(self) -> list[Product]: ...

    @query(expr="active = true", paged=True)
    async def find_active_paged(self, page) -> ...: ...

    @query(expr="name like :pattern")
    async def search_by_name(self, pattern: str) -> list[Product]: ...
```

`flush()` sends the operation to the engine without committing. The commit
happens automatically when the `@transactional` method in the service returns.

`@query` generates SQL equivalent to:

```sql
SELECT * FROM products WHERE id = :id
SELECT * FROM products WHERE active = true
SELECT * FROM products WHERE name like :pattern
```

With `paged=True` it accepts a `PageRequest` and returns `Page[Product]` with
`items` (the list) and `total` (the unpaginated count).

---

## 4. Service — `myapp/services.py`

```python
from pico_ioc import component
from pico_sqlalchemy import transactional, PageRequest, Page
from pico_pydantic import validate
from pico_client_auth import SecurityContext
from fastapi import HTTPException, status

from .models import Product
from .repositories import ProductRepository
from .schemas import ProductData


@component
class ProductService:
    def __init__(self, repo: ProductRepository):
        self.repo = repo

    @validate          # pico-pydantic: validates ProductData before executing
    @transactional     # pico-sqlalchemy: opens the async session
    async def create(self, data: ProductData) -> Product:
        # If we get here, data is a valid ProductData.
        # pico-pydantic accepts both a dict and a ProductData — converts automatically.
        product = Product(
            name=data.name,
            description=data.description,
            price=data.price,
            stock=data.stock,
        )
        return await self.repo.save(product)

    async def get_by_id(self, product_id: int) -> Product:
        product = await self.repo.find_by_id(id=product_id)
        if product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {product_id} not found",
            )
        return product

    async def list_active(self) -> list[Product]:
        return await self.repo.find_all_active()

    async def list_paged(self, page: int, page_size: int) -> Page:
        return await self.repo.find_active_paged(
            page=PageRequest(page=page, size=page_size)
        )

    async def search(self, name: str) -> list[Product]:
        return await self.repo.search_by_name(pattern=f"%{name}%")

    @validate
    @transactional
    async def update(self, product_id: int, data: ProductData) -> Product:
        product = await self.get_by_id(product_id)
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(product, field, value)
        return await self.repo.save(product)

    @transactional
    async def deactivate(self, product_id: int) -> Product:
        product = await self.get_by_id(product_id)
        product.active = False
        return await self.repo.save(product)

    @transactional
    async def delete(self, product_id: int) -> None:
        product = await self.get_by_id(product_id)
        await self.repo.delete(product)
```

`@validate` always goes before `@transactional`: if the data is invalid, no
transaction is opened unnecessarily.

`SecurityContext.get()` is available anywhere in the call stack during a
request — without passing it as a parameter. Useful for audit logs, per-user
filtering, etc.

---

## 5. Controller — `myapp/controllers.py`

With `pico-client-auth` installed, **all routes are protected by default**.
Only those decorated with `@allow_anonymous` are public.

```python
from pico_fastapi import controller, get, post, put, patch, delete
from pico_client_auth import allow_anonymous, requires_role, SecurityContext
from fastapi import Query, status

from .services import ProductService
from .schemas import (
    ProductCreate, ProductUpdate,
    ProductResponse, ProductListResponse,
)


@controller(prefix="/api/v1/products", tags=["Products"])
class ProductController:
    def __init__(self, service: ProductService):
        self.service = service

    # Authenticated — any user with a valid token
    @get("/", response_model=list[ProductResponse])
    async def list_products(self):
        products = await self.service.list_active()
        return [ProductResponse.model_validate(p) for p in products]

    @get("/paged", response_model=ProductListResponse)
    async def list_paged(
        self,
        page: int = Query(default=1, ge=1),
        page_size: int = Query(default=10, ge=1, le=100),
    ):
        result = await self.service.list_paged(page=page, page_size=page_size)
        return ProductListResponse(
            items=[ProductResponse.model_validate(p) for p in result.items],
            total=result.total,
            page=page,
            page_size=page_size,
        )

    @get("/search", response_model=list[ProductResponse])
    async def search(self, q: str = Query(min_length=1)):
        products = await self.service.search(name=q)
        return [ProductResponse.model_validate(p) for p in products]

    @get("/{product_id}", response_model=ProductResponse)
    async def get_product(self, product_id: int):
        product = await self.service.get_by_id(product_id)
        return ProductResponse.model_validate(product)

    # Role-based access control
    @post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
    @requires_role("product-manager")
    async def create_product(self, body: ProductCreate):
        # model_dump()  dict; pico-pydantic converts it to ProductData in the service
        product = await self.service.create(body.model_dump())
        return ProductResponse.model_validate(product)

    @put("/{product_id}", response_model=ProductResponse)
    @requires_role("product-manager")
    async def update_product(self, product_id: int, body: ProductUpdate):
        product = await self.service.update(
            product_id, body.model_dump(exclude_none=True)
        )
        return ProductResponse.model_validate(product)

    @patch("/{product_id}/deactivate", response_model=ProductResponse)
    @requires_role("product-manager")
    async def deactivate_product(self, product_id: int):
        product = await self.service.deactivate(product_id)
        return ProductResponse.model_validate(product)

    @delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
    @requires_role("admin")
    async def delete_product(self, product_id: int):
        await self.service.delete(product_id)
```

The health endpoint lives in its own controller at `/api/v1/health` — keeping
it separate avoids route collisions with path parameters like `/{product_id}`:

```python
@controller(prefix="/api/v1", tags=["Health"])
class HealthController:
    @get("/health")
    @allow_anonymous
    async def health(self):
        return {"status": "ok"}
```

The role check happens before the method executes. If the token is valid but
the user lacks the required role, a 403 is returned without reaching the
controller body.

---

## 6. Custom RoleResolver — `myapp/auth.py`

Optional. Only needed if your IdP puts roles in a non-standard claim.
Example for Keycloak:

```python
from pico_ioc import component
from pico_client_auth import RoleResolver, TokenClaims


@component
class KeycloakRoleResolver:
    async def resolve(self, claims: TokenClaims, raw_claims: dict) -> list[str]:
        realm_roles = raw_claims.get("realm_access", {}).get("roles", [])
        client_roles = (
            raw_claims
            .get("resource_access", {})
            .get("my-api", {})
            .get("roles", [])
        )
        return list(set(realm_roles + client_roles))
```

Declaring `@component` is all it takes — the framework detects it and uses it
instead of the default `RoleResolver`. No additional registration needed.

---

## Validation summary

| Layer | What is validated | Tool | Error |
|-------|------------------|------|-------|
| Auth | JWT signature, `iss`, `aud`, `exp` | pico-client-auth | 401 |
| Auth | Required role / group | pico-client-auth | 403 |
| HTTP | Body and query params | Pydantic + FastAPI | 422 |
| Domain | Service contract | pico-pydantic `@validate` | `ValidationFailedError` |

## Endpoints

| Method | Path | Access |
|--------|------|--------|
| GET | `/api/v1/health` | public |
| GET | `/api/v1/products/` | authenticated |
| GET | `/api/v1/products/paged` | authenticated |
| GET | `/api/v1/products/search?q=` | authenticated |
| GET | `/api/v1/products/{id}` | authenticated |
| POST | `/api/v1/products/` | `product-manager` |
| PUT | `/api/v1/products/{id}` | `product-manager` |
| PATCH | `/api/v1/products/{id}/deactivate` | `product-manager` |
| DELETE | `/api/v1/products/{id}` | `admin` |
