import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { login } from '../api/auth';
import { useAuth } from '../context/AuthContext';
import { ThemeToggle } from '../components/ui';
import styles from './Auth.module.css';

export default function Login() {
  const navigate = useNavigate();
  const { saveSession } = useAuth();

  const [form, setForm] = useState({ username: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  function handleChange(e) {
    setForm(f => ({ ...f, [e.target.name]: e.target.value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const { data } = await login(form.username, form.password);
      saveSession(data.access, data.refresh, data.user);
      navigate('/dashboard');
    } catch (err) {
      const msg = err.response?.data?.detail || 'Giriş başarısız. Bilgilerinizi kontrol edin.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className={styles.page}>
      <ThemeToggle floating />

      <div className={styles.card}>
        <Link to="/" className={styles.logo}>Rehberim</Link>
        <h1 className={styles.heading}>Hoş geldiniz</h1>
        <p className={styles.sub}>Rehber hesabınızla giriş yapın.</p>

        <form onSubmit={handleSubmit} className={styles.form} noValidate>
          <label className={styles.label}>
            Kullanıcı adı
            <input
              className={styles.input}
              type="text"
              name="username"
              value={form.username}
              onChange={handleChange}
              autoComplete="username"
              required
            />
          </label>

          <label className={styles.label}>
            Şifre
            <input
              className={styles.input}
              type="password"
              name="password"
              value={form.password}
              onChange={handleChange}
              autoComplete="current-password"
              required
            />
          </label>

          {error && <p className={styles.error}>{error}</p>}

          <button className={styles.btnPrimary} type="submit" disabled={loading}>
            {loading ? 'Giriş yapılıyor…' : 'Giriş Yap'}
          </button>
        </form>

        <p className={styles.footer}>
          Hesabınız yok mu?{' '}
          <Link to="/kayit" className={styles.link}>Hesap oluşturun</Link>
        </p>
      </div>
    </div>
  );
}
