import React, { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { Lock, User } from "lucide-react"; 
import "../index.css";

const LoginPage = () => {
  const [username, setUsername] = useState("testuser");
  const [password, setPassword] = useState("testpassword");
  const [error, setError] = useState(null);

  const { login, loading } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    try {
      await login(username, password);
      console.log("Login successful!");
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-purple-50">
      {/* Caja del login */}
      <div className="w-full max-w-md bg-purple-300/70 p-10 rounded-2xl shadow-2xl">
        {/* Título */}
        <h2 className="text-3xl font-bold text-center text-purple-900 drop-shadow-md">
          Welcome Back
        </h2>
        <p className="text-center text-purple-800 mt-2 mb-6">
          Please sign in to your account
        </p>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Username */}
          <div>
            <label className="block text-sm font-medium text-purple-900">
              Username
            </label>
            <div className="mt-1 relative">
              <User className="absolute left-3 top-2.5 text-purple-500" size={18} />
              <input
                type="text"
                autoComplete="username"
                className="w-full pl-10 pr-4 py-2 border border-purple-300 rounded-lg bg-white/80 shadow-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
              />
            </div>
          </div>

          {/* Password */}
          <div>
            <label className="block text-sm font-medium text-purple-900">
              Password
            </label>
            <div className="mt-1 relative">
              <Lock className="absolute left-3 top-2.5 text-purple-500" size={18} />
              <input
                type="password"
                autoComplete="current-password"
                className="w-full pl-10 pr-4 py-2 border border-purple-300 rounded-lg bg-white/80 shadow-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
          </div>

          {/* Botón */}
          <button
            type="submit"
            disabled={loading}
            className="w-full py-2 px-4 rounded-lg text-sm font-semibold text-white bg-purple-600 hover:bg-purple-700 shadow-lg focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 transition"
          >
            {loading ? "Logging in..." : "Log In"}
          </button>
        </form>

        {/* Error */}
        {error && (
          <p className="mt-4 text-center text-red-500 text-sm font-medium">
            {error}
          </p>
        )}

        {/* Footer */}
        <p className="mt-6 text-center text-sm text-purple-800">
          Don’t have an account?{" "}
          <a
            href="/register"
            className="text-purple-700 font-medium hover:underline"
          >
            Sign up
          </a>
        </p>
      </div>
    </div>
  );
};

export default LoginPage;
