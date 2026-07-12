export async function onRequest(context) {
  const { request, env } = context;

  if (request.method !== 'POST') {
    return new Response(JSON.stringify({ error: 'Method not allowed' }), {
      status: 405,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  let body;
  try {
    body = await request.json();
  } catch {
    return new Response(JSON.stringify({ error: 'Invalid JSON' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  if (body.password === env.SESSION_PASSWORD) {
    const cookie = `ig_auth=${env.SESSION_PASSWORD}; Path=/; HttpOnly; SameSite=Strict; Max-Age=86400`;
    return new Response(JSON.stringify({ ok: true }), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        'Set-Cookie': cookie,
      },
    });
  }

  return new Response(JSON.stringify({ error: 'Contraseña incorrecta' }), {
    status: 401,
    headers: { 'Content-Type': 'application/json' },
  });
}
