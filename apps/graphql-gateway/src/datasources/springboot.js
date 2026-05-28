import fetch from 'node-fetch';
import DataLoader from 'dataloader';

const SPRING_URL = process.env.SPRINGBOOT_URL || 'http://springboot_backend:8081';

export class SpringBootDataSource {
  constructor(token) {
    this.token = token;
    this.headers = {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
    };

    // DataLoader — batch user fetches, solves N+1
    this.userLoader = new DataLoader(async (ids) => {
      const res = await fetch(`${SPRING_URL}/api/users/batch`, {
        method: 'POST',
        headers: this.headers,
        body: JSON.stringify({ ids }),
      });
      const users = await res.json();
      // Must return in same order as input ids
      return ids.map(id => users.find(u => String(u.id) === String(id)) || null);
    });
  }

  async getUsers() {
    const res = await fetch(`${SPRING_URL}/api/users`, { headers: this.headers });
    if (!res.ok) throw new Error(`Spring Boot error: ${res.status}`);
    return res.json();
  }

  async getUserById(id) {
    return this.userLoader.load(id);
  }

  async createUser(input) {
    const res = await fetch(`${SPRING_URL}/api/users`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify(input),
    });
    if (!res.ok) throw new Error(`Create user failed: ${res.status}`);
    return res.json();
  }

  async updateUser(id, input) {
    const res = await fetch(`${SPRING_URL}/api/users/${id}`, {
      method: 'PUT',
      headers: this.headers,
      body: JSON.stringify(input),
    });
    if (!res.ok) throw new Error(`Update user failed: ${res.status}`);
    return res.json();
  }

  async deleteUser(id) {
    const res = await fetch(`${SPRING_URL}/api/users/${id}`, {
      method: 'DELETE',
      headers: this.headers,
    });
    return res.ok;
  }
}
