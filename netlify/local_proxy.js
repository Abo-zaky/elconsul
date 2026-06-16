const express = require('express');
const fetch = require('node-fetch');
const app = express();
const PORT = 8004;
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Simple CORS for local testing
app.use((req, res, next) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,POST,OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') return res.sendStatus(200);
  next();
});

function isSessionsScript(url) {
  return url && url.includes('AKfycbw11d7xiBS_xfu22yVd17DcvqkU4_DmJyXblIPBsolCDMtIR65k6LwwanKo-rCWxAHp/exec');
}

app.all('/proxy', async (req, res) => {
  const q = req.query.url || '';
  const decoded = decodeURIComponent(q);
  // If this matches the sessions API used by the app, return mocked responses
  if (isSessionsScript(decoded)) {
    let targetAction = '';
    try {
      targetAction = new URL(decoded).searchParams.get('action') || '';
    } catch (e) {}
    const action = (req.body && req.body.action) || req.query.action || targetAction || '';
    if (action === 'getSessions') {
      const now = new Date();
      const old = new Date(now.getTime() - 18 * 60 * 1000);
      return res.json([
        { centerName: 'admin', centerCode: 'ADMIN', lastActive: now.toISOString(), date: now.toLocaleDateString('ar-EG') },
        { centerName: 'office', centerCode: 'office', lastActive: old.toISOString(), date: old.toLocaleDateString('ar-EG') },
        { centerName: 'center1', centerCode: 'center1', lastActive: now.toISOString(), date: now.toLocaleDateString('ar-EG') }
      ]);
    }
    if (action === 'getUsers') {
      return res.json({ success: true, users: [
        { username: 'admin', role: 'admin', center: '', status: 'نشط' },
        { username: 'office', role: 'office', center: '', status: 'نشط' },
        { username: 'center1', role: 'center', center: 'العدوة', status: 'نشط' }
      ]});
    }
    if (action === 'login') {
      const { username, password } = req.body || {};
      // simple mock logic
      if (username === 'admin' && password === 'admin') return res.json({ success: true, user: { username: 'admin', role: 'admin', name: 'مدير النظام' } });
      if (username === 'office' && password === 'office') return res.json({ success: true, user: { username: 'office', role: 'office', name: 'موظف المكتب' } });
      if (username === 'center' && password === 'center') return res.json({ success: true, user: { username: 'center', role: 'center', center: 'المنيا', name: 'مستخدم المركز' } });
      return res.json({ success: false, message: 'اسم المستخدم أو كلمة المرور غير صحيحة (mock)' });
    }
    if (action === 'getLogs') {
      return res.json({ success: true, logs: [
        { date: new Date().toISOString(), action: 'login', user: 'admin', details: 'تسجيل دخول تجريبي', result: 'نجاح' }
      ]});
    }

    // default mock ack
    return res.json({ success: true, message: 'mock proxy - no specific action' });
  }

  // Otherwise try to proxy the real request (GET/POST)
  try {
    const method = req.method.toUpperCase();
    const headers = {};
    if (req.headers['content-type']) headers['content-type'] = req.headers['content-type'];
    const opts = { method, headers };
    if (method === 'POST') opts.body = JSON.stringify(req.body);
    const r = await fetch(decoded, opts);
    const txt = await r.text();
    res.status(r.status).send(txt);
  } catch (e) {
    res.status(500).send('proxy error: ' + e.message);
  }
});

app.listen(PORT, () => {
  console.log(`Mock proxy listening on http://127.0.0.1:${PORT}/proxy`);
});
