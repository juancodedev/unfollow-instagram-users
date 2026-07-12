export async function onRequest(context) {
  const { request, env, next } = context;
  const url = new URL(request.url);

  if (url.pathname === '/api/auth') {
    return await next();
  }

  const cookieHeader = request.headers.get('Cookie') || '';
  const igAuth = extractCookie(cookieHeader, 'ig_auth');
  if (igAuth === env.SESSION_PASSWORD) {
    return await next();
  }

  return new Response(LOGIN_PAGE, {
    status: 401,
    headers: { 'Content-Type': 'text/html; charset=utf-8' },
  });
}

function extractCookie(header, name) {
  const match = header.match(new RegExp('(?:^|;)\\s*' + name + '=([^;]+)'));
  return match ? match[1] : null;
}

const LOGIN_PAGE = `<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>IG Cleaner — Acceso</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
html,body{height:100%}
body{
  font-family:system-ui,-apple-system,sans-serif;
  background:#080808;
  display:flex;align-items:center;justify-content:center;
  min-height:100dvh;padding:1rem
}
.card{
  background:#111;border:1px solid #1f1f1f;border-radius:16px;
  padding:2rem;width:100%;max-width:360px;
  box-shadow:0 8px 32px rgba(0,0,0,.5)
}
.brand{text-align:center;margin-bottom:1.5rem}
.brand h1{color:#a78bfa;font-size:1.25rem;font-weight:600;letter-spacing:-.02em}
.brand p{color:#555;font-size:.75rem;margin-top:4px}
.input-group{display:flex;flex-direction:column;gap:8px}
.input-group input{
  background:#1a1a1a;border:1px solid #2a2a2a;border-radius:10px;
  color:#e5e5e5;padding:12px 14px;font-size:.9375rem;outline:none;
  transition:border-color .15s
}
.input-group input:focus{border-color:#a78bfa}
.input-group input::placeholder{color:#555}
.input-group button{
  background:#a78bfa;color:#fff;border:none;border-radius:10px;
  padding:12px;font-size:.9375rem;font-weight:500;cursor:pointer;
  transition:opacity .15s
}
.input-group button:hover{opacity:.85}
.input-group button:active{opacity:.7}
.error{
  color:#ef4444;font-size:.8125rem;text-align:center;
  min-height:1.25rem;margin-top:12px
}
</style>
</head>
<body>
<div class="card">
  <div class="brand">
    <h1>IG Cleaner v2</h1>
    <p>Unfollow Manager</p>
  </div>
  <form id="loginForm">
    <div class="input-group">
      <input type="password" id="password" placeholder="Contraseña" autocomplete="current-password" required>
      <button type="submit">Ingresar</button>
    </div>
    <div class="error" id="error"></div>
  </form>
</div>
<script>
const form=document.getElementById('loginForm');
const pw=document.getElementById('password');
const err=document.getElementById('error');
form.addEventListener('submit',async e=>{
  e.preventDefault();
  err.textContent='';
  try{
    const r=await fetch('/api/auth',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({password:pw.value})
    });
    if(r.ok) location.href='/';
    else err.textContent='Contrase\u00f1a incorrecta';
  }catch(e){err.textContent='Error de conexi\u00f3n'}
});
</script>
</body>
</html>`;
