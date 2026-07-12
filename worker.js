/**
 * Cloudflare Worker — API bridge entre el HTML y Neon Postgres.
 *
 * Deploy:
 *   1. Andá a https://dash.cloudflare.com → Workers & Pages → Create → Worker
 *   2. Pegá este código
 *   3. Settings → Variables → agregá DATABASE_URL con la connection string de Neon
 *      (ej: postgres://user:pass@ep-xxxx.us-east-2.aws.neon.tech/neondb?sslmode=require)
 *   4. Deployá → copiás la URL (ej: https://ig-states.xxxx.workers.dev)
 *   5. Ponés esa URL en el HTML como API_ENDPOINT
 *
 * Endpoints:
 *   GET  /         → devuelve todos los estados como JSON [{username, state, updated_at}]
 *   POST /         → upsert: { username, state, updated_at }
 *   DELETE /       → sin body: borra ALL. Con { username }: borra ese username
 */

// Usa la conexión Neon via HTTP (no necesita driver, usa fetch internamente)
// @neondatabase/serverless se puede importar directo en Workers
import { neon } from '@neondatabase/serverless';

// CORS headers para que el HTML pueda llamar desde cualquier lado
const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, DELETE, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};

export default {
  async fetch(request, env) {
    // Handle CORS preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: CORS });
    }

    const sql = neon(env.DATABASE_URL);

    try {
      switch (request.method) {
        case 'GET': {
          const rows = await sql`
            SELECT username, state, updated_at
            FROM states
            ORDER BY updated_at DESC
          `;
          return new Response(JSON.stringify(rows), {
            headers: { ...CORS, 'Content-Type': 'application/json' },
          });
        }

        case 'POST': {
          const body = await request.json();
          const { username, state, updated_at } = body;

          if (!username || !state) {
            return new Response(JSON.stringify({ error: 'username and state required' }), {
              status: 400,
              headers: { ...CORS, 'Content-Type': 'application/json' },
            });
          }

          await sql`
            INSERT INTO states (username, state, updated_at)
            VALUES (${username}, ${state}, ${updated_at || new Date().toISOString()})
            ON CONFLICT (username)
            DO UPDATE SET state = EXCLUDED.state, updated_at = EXCLUDED.updated_at
          `;

          return new Response(JSON.stringify({ ok: true }), {
            headers: { ...CORS, 'Content-Type': 'application/json' },
          });
        }

        case 'DELETE': {
          const body = await request.json().catch(() => ({}));

          if (body.username) {
            await sql`DELETE FROM states WHERE username = ${body.username}`;
          } else {
            await sql`DELETE FROM states`;
          }

          return new Response(JSON.stringify({ ok: true }), {
            headers: { ...CORS, 'Content-Type': 'application/json' },
          });
        }

        default:
          return new Response(JSON.stringify({ error: 'Method not allowed' }), {
            status: 405,
            headers: { ...CORS, 'Content-Type': 'application/json' },
          });
      }
    } catch (e) {
      console.error('Worker error:', e);
      return new Response(JSON.stringify({ error: e.message }), {
        status: 500,
        headers: { ...CORS, 'Content-Type': 'application/json' },
      });
    }
  },
};
