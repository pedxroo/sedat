const crypto = require('crypto');

function safeEqual(a, b) {
  const bufA = Buffer.from(String(a));
  const bufB = Buffer.from(String(b));
  if (bufA.length !== bufB.length) return false;
  return crypto.timingSafeEqual(bufA, bufB);
}

module.exports = async function handler(req, res) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST');
    return res.status(405).json({ ok: false, error: 'method_not_allowed' });
  }

  const adminPassword = process.env.ADMIN_PASSWORD;
  if (!adminPassword) {
    return res.status(500).json({ ok: false, error: 'admin_password_not_configured' });
  }

  let password = '';
  try {
    const body = typeof req.body === 'string' ? JSON.parse(req.body) : req.body;
    password = (body && body.password) || '';
  } catch (e) {
    return res.status(400).json({ ok: false, error: 'invalid_body' });
  }

  if (safeEqual(password, adminPassword)) {
    return res.status(200).json({ ok: true });
  }
  return res.status(401).json({ ok: false, error: 'wrong_password' });
};
