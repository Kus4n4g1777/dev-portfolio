'use server';

import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';

export async function loginAction(formData: FormData) {
  const username = formData.get('username') as string;
  const password = formData.get('password') as string;
  const baseUrl = process.env.FASTAPI_INTERNAL_URL || 'http://dashboard_backend:8000';

  try {
    const apiFormData = new URLSearchParams();
    apiFormData.append('username', username);
    apiFormData.append('password', password);

    // We securely hit the FastAPI backend inside the Docker network
    const response = await fetch(`${baseUrl}/token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: apiFormData.toString(),
    });

    if (!response.ok) {
      return { error: 'Invalid username or password' };
    }

    const data = await response.json();

    // FIXED: We await the cookies() promise in modern Next.js
    const cookieStore = await cookies();
    cookieStore.set('auth_token', data.access_token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      maxAge: 60 * 60 * 24, // 1 day
      path: '/',
    });

    return { success: true };
  } catch (error) {
    return { error: 'Internal server communication failed.' };
  }
}

export async function logoutAction() {
  // FIXED: We await the cookies() promise before deleting
  const cookieStore = await cookies();
  cookieStore.delete('auth_token');
  redirect('/login');
}
