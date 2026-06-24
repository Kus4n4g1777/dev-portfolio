import { cookies } from 'next/headers';

/**
 * We use this utility to handle all server-side GraphQL requests.
 * It automatically extracts the JWT from our secure cookies and attaches it.
 */
export async function fetchGraphQL(query: string, variables = {}) {
  // FIXED: We await the cookies() promise
  const cookieStore = await cookies();
  const token = cookieStore.get('auth_token')?.value;
  const endpoint = process.env.NEXT_PUBLIC_GRAPHQL_URL || 'http://graphql-gateway:4000/graphql';

  const res = await fetch(endpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      // We attach the authorization header if the user is authenticated
      ...(token && { Authorization: `Bearer ${token}` }),
    },
    body: JSON.stringify({ query, variables }),
    // We disable caching for live analytics, ensuring real-time data
    cache: 'no-store', 
  });

  if (!res.ok) {
    throw new Error(`GraphQL Error: ${res.statusText}`);
  }

  return res.json();
}
