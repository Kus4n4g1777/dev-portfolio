'use client';

import { useState } from 'react';
import { loginAction } from '../../../actions/auth';
import { useRouter } from 'next/navigation';

export default function LoginPage() {
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  async function handleSubmit(formData: FormData) {
    setLoading(true);
    setError(null);
    const result = await loginAction(formData);
    
    if (result?.error) {
      setError(result.error);
      setLoading(false);
    } else {
      router.push('/dashboard');
    }
  }

  return (
    <div className="w-full max-w-sm my-auto p-8 rounded-3xl bg-gradient-to-br from-[#4b276b]/60 to-[#1a1025]/80 backdrop-blur-xl border border-white/10 shadow-2xl">
      <h1 className="text-3xl font-bold text-center text-white mb-8 drop-shadow-lg">
        Hearts & Stars Detector
      </h1>
      
      <form action={handleSubmit} className="space-y-5">
        <div>
          <input
            name="username"
            type="text"
            placeholder="Username"
            required
            className="w-full px-4 py-3 bg-white/10 border border-white/5 rounded-xl text-white placeholder-gray-300 focus:outline-none focus:ring-2 focus:ring-orange-500 transition-all"
          />
        </div>
        <div>
          <input
            name="password"
            type="password"
            placeholder="Password"
            required
            className="w-full px-4 py-3 bg-white/10 border border-white/5 rounded-xl text-white placeholder-gray-300 focus:outline-none focus:ring-2 focus:ring-orange-500 transition-all"
          />
        </div>

        {error && <p className="text-red-400 text-sm text-center font-medium">{error}</p>}

        <button
          type="submit"
          disabled={loading}
          className="w-full py-3 mt-4 rounded-xl font-bold text-white bg-[#fb7140] hover:bg-[#ff8a5c] shadow-[0_0_15px_rgba(251,113,64,0.4)] transition-all disabled:opacity-50"
        >
          {loading ? 'Authenticating...' : 'Login'}
        </button>
      </form>
      
      <p className="mt-6 text-center text-xs text-gray-400">
        Portoflio. Just click here create new user
      </p>
    </div>
  );
}
