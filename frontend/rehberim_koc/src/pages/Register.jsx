import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { registerCounselor } from '../api/auth';
import { useAuth } from '../context/AuthContext';
import { ThemeToggle } from '../components/ui';
import styles from './Auth.module.css';

const INITIAL = {
  first_name: '',
  last_name: '',
  username: '',
  email: '',
  password: '',
  password2: '',
};

export default function Register() {
  const navigate = useNavigate();
  const { saveSession } = useAuth();

  const [form, setForm] = useState(INITIAL);
  const [fieldErrors, setFieldErrors] = useState({});
  const [globalError, setGlobalError] = useState('');
  const [loading, setLoading] = useState(false);

  function handleChange(e) {
    setForm(f => ({ ...f, [e.target.name]: e.target.value }));
    setFieldErrors(fe => ({ ...fe, [e.target.name]: undefined }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setGlobalError('');
    setFieldErrors({});

    if (form.password !== form.password2) {
      setFieldErrors({ password2: ['Şifreler eşleşmiyor.'] });
      return;
    }

    setLoading(true);
    try {
      const payload = {
        username: form.username,
        email: form.email,
        password: form.password,
        first_name: form.first_name,
        last_name: form.last_name,
      };
      const { data } = await registerCounselor(payload);
      saveSession(data.access, data.refresh, data.user);
      navigate('/dashboard');
    } catch (err) {
      if (err.response?.status === 400) {
        setFieldErrors(err.response.data);
      } else {
        setGlobalError('Kayıt başarısız. Lütfen tekrar deneyin.');
      }
    } finally {
      setLoading(false);
    }
  }

  function fieldError(name) {
    const msgs = fieldErrors[name];
    return msgs ? <span className={styles.fieldError}>{msgs[0]}</span> : null;
  }

  return (
    <div className={styles.page}>
      <ThemeToggle floating />

      <div className={styles.card}>
        <Link to="/" className={styles.logo}>Rehberim</Link>
        <h1 className={styles.heading}>Hesap Oluşturun</h1>
        <p className={styles.sub}>Rehber hesabı açmak birkaç saniye sürer.</p>

        <form onSubmit={handleSubmit} className={styles.form} noValidate>
          <div className={styles.row}>
            <label className={styles.label}>
              Ad
              <input
                className={styles.input}
                type="text"
                name="first_name"
                value={form.first_name}
                onChange={handleChange}
                required
              />
              {fieldError('first_name')}
            </label>
            <label className={styles.label}>
              Soyad
              <input
                className={styles.input}
                type="text"
                name="last_name"
                value={form.last_name}
                onChange={handleChange}
                required
              />
              {fieldError('last_name')}
            </label>
          </div>

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
            {fieldError('username')}
          </label>

          <label className={styles.label}>
            E-posta
            <input
              className={styles.input}
              type="email"
              name="email"
              value={form.email}
              onChange={handleChange}
              autoComplete="email"
              required
            />
            {fieldError('email')}
          </label>

          <label className={styles.label}>
            Şifre
            <input
              className={styles.input}
              type="password"
              name="password"
              value={form.password}
              onChange={handleChange}
              autoComplete="new-password"
              required
            />
            {fieldError('password')}
          </label>

          <label className={styles.label}>
            Şifre tekrar
            <input
              className={styles.input}
              type="password"
              name="password2"
              value={form.password2}
              onChange={handleChange}
              autoComplete="new-password"
              required
            />
            {fieldError('password2')}
          </label>

          {globalError && <p className={styles.error}>{globalError}</p>}

          <button className={styles.btnPrimary} type="submit" disabled={loading}>
            {loading ? 'Hesap oluşturuluyor…' : 'Hesap Oluştur'}
          </button>
        </form>

        <p className={styles.footer}>
          Zaten hesabınız var mı?{' '}
          <Link to="/giris" className={styles.link}>Giriş yapın</Link>
        </p>
      </div>
    </div>
  );
}
