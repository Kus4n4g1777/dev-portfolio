import fetch from 'node-fetch';

const FASTAPI_URL = process.env.FASTAPI_URL || 'http://dashboard_backend:8000';

export class FastAPIDataSource {
  constructor(token) {
    this.token = token;
    this.headers = {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
    };
  }

  async getHealth() {
    const res = await fetch(`${FASTAPI_URL}/health`, { headers: this.headers });
    return res.json();
  }

  async getDashboardStats() {
    const res = await fetch(`${FASTAPI_URL}/api/stats`, { headers: this.headers });
    if (!res.ok) throw new Error(`FastAPI error: ${res.status}`);
    return res.json();
  }

  async login(username, password) {
    const res = await fetch(`${FASTAPI_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    if (!res.ok) throw new Error('Invalid credentials');
    return res.json();
  }
}
