import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../../types/axios";
import { useAuth } from "./AuthProvider";

export function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const { login } = useAuth();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    try {
      const res = await api.post("/auth/login", {
        username: email,
        password,
      });

      login(res.data.access_token);

      const payload = JSON.parse(
        atob(res.data.access_token.split(".")[1])
      );

      navigate(payload.role === "admin" ? "/admin" : "/intern");
    } catch {
      setError("Invalid credentials");
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <form
        onSubmit={handleSubmit}
        className="w-80 rounded bg-white p-6 shadow"
      >
        <h1 className="mb-4 text-xl font-semibold">Login</h1>

        {error && <p className="mb-2 text-sm text-red-600">{error}</p>}

        <input
          className="mb-3 w-full rounded border p-2"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />

        <input
          type="password"
          className="mb-4 w-full rounded border p-2"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />

        <button className="w-full rounded bg-blue-600 p-2 text-white">
          Sign in
        </button>
      </form>
    </div>
  );
}
