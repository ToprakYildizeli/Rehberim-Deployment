import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { LogOut, Moon, Sun } from 'lucide-react';
import { Card, CardHeader, Button, Field, Input } from '../components/ui';
import { updateMe } from '../api/auth';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import s from './Ayarlar.module.css';

/** Düzenlenebilir alanlar (auth-contract §5.4b). Kullanıcı adı salt-okunur. */
const EDITABLE = ['first_name', 'last_name', 'email'];

export default function Ayarlar() {
  const navigate = useNavigate();
  const { user, updateUser, clearSession } = useAuth();
  const { theme, toggle } = useTheme();

  const saved = useMemo(
    () => ({
      first_name: user?.first_name ?? '',
      last_name: user?.last_name ?? '',
      email: user?.email ?? '',
    }),
    [user]
  );

  const [profile, setProfile] = useState(saved);
  const [errors, setErrors] = useState({});
  const [status, setStatus] = useState(null);   // 'saving' | 'saved' | null
  const [formError, setFormError] = useState(null);

  const isDirty = EDITABLE.some((k) => profile[k] !== saved[k]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setProfile((p) => ({ ...p, [name]: value }));
    setErrors((p) => ({ ...p, [name]: undefined }));
    setStatus(null);
    setFormError(null);
  };

  async function handleSave() {
    setStatus('saving');
    setErrors({});
    setFormError(null);
    // Yalnızca değişen alanları gönder — uç kısmi güncellemeyi destekliyor.
    const changed = Object.fromEntries(
      EDITABLE.filter((k) => profile[k] !== saved[k]).map((k) => [k, profile[k]])
    );
    try {
      const updated = await updateMe(changed);
      updateUser(updated);
      setProfile({
        first_name: updated.first_name ?? '',
        last_name: updated.last_name ?? '',
        email: updated.email ?? '',
      });
      setStatus('saved');
    } catch (err) {
      setStatus(null);
      const data = err?.response?.data;
      if (data && typeof data === 'object' && !data.detail) {
        // { "email": ["Bu e-posta ile zaten bir hesap var."] }
        setErrors(
          Object.fromEntries(
            Object.entries(data).map(([k, v]) => [k, Array.isArray(v) ? v[0] : String(v)])
          )
        );
      } else {
        setFormError(data?.detail ?? 'Profil kaydedilemedi. Lütfen tekrar dene.');
      }
    }
  }

  async function handleLogout() {
    await clearSession();
    navigate('/giris', { replace: true });
  }

  return (
    <div className={s.page}>
      <Card>
        <CardHeader title="Profil" subtitle="Hesap bilgileriniz" />
        <div className={s.form}>
          <div className={s.row}>
            <Field label="Ad" error={errors.first_name}>
              <Input name="first_name" value={profile.first_name} onChange={handleChange} />
            </Field>
            <Field label="Soyad" error={errors.last_name}>
              <Input name="last_name" value={profile.last_name} onChange={handleChange} />
            </Field>
          </div>
          <Field label="Kullanıcı adı">
            <Input name="username" value={user?.username ?? ''} readOnly disabled />
          </Field>
          <Field label="E-posta" error={errors.email}>
            <Input name="email" type="email" value={profile.email} onChange={handleChange} />
          </Field>

          <p className={s.note}>
            Kullanıcı adı giriş kimliğin olduğu için değiştirilemez.
          </p>

          {formError && <p className={s.formError}>{formError}</p>}

          <div className={s.actions}>
            <Button onClick={handleSave} disabled={!isDirty || status === 'saving'}>
              {status === 'saving' ? 'Kaydediliyor…' : 'Kaydet'}
            </Button>
            {status === 'saved' && <span className={s.savedHint}>Kaydedildi</span>}
          </div>
        </div>
      </Card>

      <Card>
        <CardHeader title="Görünüm" subtitle="Arayüz tercihleri" />
        <div className={s.option}>
          <div>
            <p className={s.optionLabel}>Tema</p>
            <p className={s.optionHint}>
              {theme === 'light' ? 'Açık tema kullanılıyor' : 'Koyu tema kullanılıyor'}
            </p>
          </div>
          <Button variant="ghost" size="sm" onClick={toggle}>
            {theme === 'light' ? <Moon size={14} /> : <Sun size={14} />}
            {theme === 'light' ? 'Koyu temaya geç' : 'Açık temaya geç'}
          </Button>
        </div>
      </Card>

      <Card>
        <CardHeader title="Hesap" />
        <div className={s.option}>
          <div>
            <p className={s.optionLabel}>Oturumu kapat</p>
            <p className={s.optionHint}>Bu cihazdaki oturumunuz sonlandırılır.</p>
          </div>
          <Button variant="danger" size="sm" onClick={handleLogout}>
            <LogOut size={14} /> Çıkış Yap
          </Button>
        </div>
      </Card>
    </div>
  );
}
