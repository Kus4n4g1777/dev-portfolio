import './globals.css';
import Link from 'next/link';
import { logoutAction } from '../actions/auth';
import { cookies } from 'next/headers';

// FIXED: We make the layout an async function to await cookies
export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const cookieStore = await cookies();
  const isLoggedIn = cookieStore.has('auth_token');

  return (
    <html lang="en">
      <body className="min-h-screen text-gray-100 font-sans relative overflow-x-hidden bg-[#0a0a14]">
        {/* We use a deep space / Landscape Background effect */}
        <div className="fixed inset-0 z-[-2] bg-cover bg-center bg-no-repeat opacity-30 bg-[url('/bg-landscape.jpg')]" />
        <div className="fixed inset-0 z-[-1] bg-gradient-to-b from-transparent to-[#0a0a14] opacity-90" />

        {isLoggedIn && (
          <nav className="w-full flex justify-center gap-8 py-4 bg-white/5 backdrop-blur-md border-b border-white/10 sticky top-0 z-50">
            <Link href="/dashboard" className="hover:text-orange-400 transition-colors">Dashboard</Link>
            <Link href="/audit" className="hover:text-orange-400 transition-colors">Audit Logs</Link>
            <form action={logoutAction}>
              <button type="submit" className="text-gray-400 hover:text-red-400 transition-colors">Logout</button>
            </form>
          </nav>
        )}
        
        <main className="relative z-10 w-full max-w-5xl mx-auto p-4 flex flex-col items-center justify-center min-h-[90vh]">
          {children}
        </main>
      </body>
    </html>
  );
}
