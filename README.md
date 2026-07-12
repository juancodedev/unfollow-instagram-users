# Instagram Unfollow Tool

Limpieza masiva de seguidos de Instagram con sincronización cross-device.

## Stack

| Componente | Tecnología |
|---|---|
| Frontend | HTML + Vanilla JS (standalone) |
| API | Cloudflare Pages Function |
| ORM | Drizzle |
| DB | Neon (PostgreSQL serverless) |
| Deploy | Cloudflare Pages (auto desde GitHub) |

## URL

**https://ig-unfollow.pages.dev**

## Funcionalidades

- **Carga 9.730 seguidos** desde los datos exportados de Instagram
- **Filtros** por estado (keep / unfollow / deleted / private / pending), año de follow, búsqueda por usuario
- **Modo sesión** con progreso diario y límite configurable
- **Sincronización cross-device** vía Neon — marcás en un equipo, lo ves en otro
- **Importar listas** desde otro equipo (pegar usuarios en lote)
- **Exportar** listas .txt por categoría
- **Modo offline** — localStorage como fallback, sync asíncrono

## Setup local

```bash
# Clonar
git clone https://github.com/juancodedev/unfollow-instagram-users.git

# Dependencias (solo para la Pages Function)
npm install

# Exportar datos de Instagram y generar tool con datos embebidos
python build.py
```

### Variables de entorno (Cloudflare Pages secret)

| Secret | Descripción |
|---|---|
| `DATABASE_URL` | Connection string de Neon (PostgreSQL) |

## Estructura

```
├── index.html                     # Tool principal
├── functions/api/[[route]].js     # Pages Function (API)
├── db/schema.ts                   # Drizzle schema
├── drizzle.config.ts              # Drizzle config
├── wrangler.toml                  # Cloudflare Pages config
├── build.py                       # Build script (genera index.html embebido)
├── worker.js                      # Worker de referencia (legacy)
└── docs/json/                     # Exports de Instagram
```

## DB Schema

```sql
CREATE TABLE states (
  username    TEXT PRIMARY KEY,
  state       TEXT NOT NULL CHECK (state IN ('keep','unfollow','deleted','private','pending')),
  updated_at  TIMESTAMPTZ DEFAULT NOW()
);
```

## Deploy

El repo está conectado a Cloudflare Pages. Cada push a `main` deploya automáticamente.

```bash
git push origin main
```
