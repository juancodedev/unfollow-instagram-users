import { neon } from '@neondatabase/serverless';
import { drizzle } from 'drizzle-orm/neon-http';
import { states } from '../../db/schema';
import { eq, sql } from 'drizzle-orm';

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, DELETE, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};

export async function onRequest(context) {
  const { request, env } = context;

  if (request.method === 'OPTIONS') {
    return new Response(null, { status: 204, headers: CORS });
  }

  const sqlClient = neon(env.DATABASE_URL);
  const db = drizzle(sqlClient);

  try {
    const url = new URL(request.url);
    const pathParts = url.pathname.replace(/\/api\/?/, '').split('/').filter(Boolean);
    const username = pathParts[0] || null;

    switch (request.method) {
      case 'GET': {
        const rows = await db
          .select()
          .from(states)
          .orderBy(states.updatedAt, 'desc');

        return new Response(JSON.stringify(rows), {
          headers: { ...CORS, 'Content-Type': 'application/json' },
        });
      }

      case 'POST': {
        const body = await request.json();
        const { username: uname, state, updated_at } = body;

        if (!uname || !state) {
          return new Response(
            JSON.stringify({ error: 'username and state required' }),
            { status: 400, headers: { ...CORS, 'Content-Type': 'application/json' } },
          );
        }

        await db
          .insert(states)
          .values({
            username: uname,
            state,
            updatedAt: updated_at || new Date().toISOString(),
          })
          .onConflictDoUpdate({
            target: states.username,
            set: {
              state: sql`EXCLUDED.state`,
              updatedAt: sql`EXCLUDED.updated_at`,
            },
          });

        return new Response(JSON.stringify({ ok: true }), {
          headers: { ...CORS, 'Content-Type': 'application/json' },
        });
      }

      case 'DELETE': {
        if (!username) {
          return new Response(
            JSON.stringify({ error: 'username required — mass delete not allowed' }),
            { status: 400, headers: { ...CORS, 'Content-Type': 'application/json' } },
          );
        }

        await db.delete(states).where(eq(states.username, username));

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
    console.error('Pages function error:', e);
    return new Response(JSON.stringify({ error: e.message }), {
      status: 500,
      headers: { ...CORS, 'Content-Type': 'application/json' },
    });
  }
}
