import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { authApi } from "../api/auth";
import { useAuthStore } from "../store/auth";
import { formatAuthError } from "../utils/authErrors";
import s from "./AuthPage.module.css";

export default function AuthPage() {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const setToken = useAuthStore((s) => s.setToken);
  const navigate = useNavigate();

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data =
        mode === "login"
          ? await authApi.login(email.trim(), password)
          : await authApi.register(username.trim(), email.trim(), password);
      await setToken(data.access_token);
      navigate("/");
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
      setError(formatAuthError(detail));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={s.root}>
      <div className={s.card}>
        <h1 className={s.logo}>Quazar</h1>
        <div className={s.tabs}>
          <button className={mode === "login" ? s.activeTab : s.tab} onClick={() => setMode("login")}>
            Войти
          </button>
          <button className={mode === "register" ? s.activeTab : s.tab} onClick={() => setMode("register")}>
            Регистрация
          </button>
        </div>

        <form onSubmit={submit} className={s.form}>
          {mode === "register" && (
            <input
              className={s.input}
              placeholder="Имя пользователя"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          )}
          <input
            className={s.input}
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <input
            className={s.input}
            type="password"
            placeholder="Пароль"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          {error && <p className={s.error}>{error}</p>}
          <button className={s.submit} type="submit" disabled={loading}>
            {loading ? "..." : mode === "login" ? "Войти" : "Создать аккаунт"}
          </button>
        </form>
      </div>
    </div>
  );
}
