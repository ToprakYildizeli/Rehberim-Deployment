import { useEffect, useRef, useState } from 'react';
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard, Users, Calendar, CalendarDays, Settings,
  GraduationCap, PanelLeftClose, PanelLeftOpen, Menu, Moon, Sun, LogOut,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useTheme } from '../../context/ThemeContext';
import { Avatar, SearchInput } from '../ui';
import s from './layout.module.css';

const NAV = [
  { to: '/panel', label: 'Panel', icon: LayoutDashboard },
  { to: '/ogrenciler', label: 'Öğrenciler', icon: Users },
  { to: '/takvim', label: 'Takvim', icon: Calendar },
  { to: '/ders-programi', label: 'Ders Programı', icon: CalendarDays },
  { to: '/ayarlar', label: 'Ayarlar', icon: Settings },
];

const TITLES = {
  '/panel': 'Panel',
  '/ogrenciler': 'Öğrenciler',
  '/takvim': 'Takvim',
  '/ders-programi': 'Ders Programı Planlayıcı',
  '/ayarlar': 'Ayarlar',
};

/** Avatar → tema geçişi + çıkış tek bir menüde toplanır (üst bar dağınık durmasın). */
function ProfileMenu({ displayName }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);
  const { clearSession } = useAuth();
  const { theme, toggle } = useTheme();
  const navigate = useNavigate();

  useEffect(() => {
    if (!open) return undefined;
    const onDoc = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    document.addEventListener('mousedown', onDoc);
    return () => document.removeEventListener('mousedown', onDoc);
  }, [open]);

  async function handleLogout() {
    setOpen(false);
    await clearSession();
    navigate('/giris', { replace: true });
  }

  return (
    <div className={s.profileWrap} ref={ref}>
      <button
        type="button"
        className={s.profileBtn}
        onClick={() => setOpen((o) => !o)}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label={displayName}
      >
        <Avatar name={displayName} size="sm" color="var(--violet)" />
      </button>
      {open && (
        <div className={s.menu} role="menu">
          <div className={s.menuHeader}>
            <span className={s.menuName}>{displayName}</span>
            <span className={s.menuRole}>Rehber</span>
          </div>
          <button type="button" className={s.menuItem} role="menuitem" onClick={toggle}>
            {theme === 'light' ? <Moon size={15} /> : <Sun size={15} />}
            {theme === 'light' ? 'Koyu tema' : 'Açık tema'}
          </button>
          <button
            type="button"
            className={`${s.menuItem} ${s.menuDanger}`}
            role="menuitem"
            onClick={handleLogout}
          >
            <LogOut size={15} /> Çıkış Yap
          </button>
        </div>
      )}
    </div>
  );
}

export default function DashboardLayout() {
  const location = useLocation();
  const { user } = useAuth();
  const [collapsed, setCollapsed] = useState(
    () => localStorage.getItem('sidebarCollapsed') === '1'
  );
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    localStorage.setItem('sidebarCollapsed', collapsed ? '1' : '0');
  }, [collapsed]);

  // Close the mobile drawer on navigation.
  useEffect(() => setMobileOpen(false), [location.pathname]);

  const title =
    TITLES[location.pathname] ??
    (location.pathname.startsWith('/ogrenciler/') ? 'Öğrenci Detayı' : 'Panel');
  const displayName =
    [user?.first_name, user?.last_name].filter(Boolean).join(' ') || user?.username || 'Rehber';

  return (
    <div className={s.shell}>
      <div
        className={`${s.scrim} ${mobileOpen ? s.scrimOpen : ''}`}
        onClick={() => setMobileOpen(false)}
        aria-hidden="true"
      />

      <div className={s.body}>
      <aside
        className={[
          s.sidebar,
          collapsed ? s.sidebarCollapsed : '',
          mobileOpen ? s.sidebarOpen : '',
        ].join(' ')}
      >
        <NavLink to="/panel" className={s.brand}>
          <span className={s.brandMark}>
            <GraduationCap size={17} color="#fff" />
          </span>
          {!collapsed && 'Rehberlik'}
        </NavLink>

        <nav className={s.nav}>
          {NAV.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              title={collapsed ? label : undefined}
              className={({ isActive }) =>
                `${s.navItem} ${isActive ? s.navItemActive : ''}`
              }
            >
              <span className={s.navIcon}>
                <Icon size={17} />
              </span>
              {!collapsed && label}
            </NavLink>
          ))}
        </nav>

        <button
          type="button"
          className={s.collapseBtn}
          onClick={() => setCollapsed((c) => !c)}
          aria-label={collapsed ? 'Menüyü genişlet' : 'Menüyü daralt'}
        >
          {collapsed ? <PanelLeftOpen size={16} /> : <PanelLeftClose size={16} />}
          {!collapsed && 'Daralt'}
        </button>
      </aside>

      <div className={s.main}>
        <header className={s.topbar}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, minWidth: 0 }}>
            <button
              type="button"
              className={`${s.iconBtn} ${s.mobileToggle}`}
              onClick={() => setMobileOpen(true)}
              aria-label="Menüyü aç"
            >
              <Menu size={18} />
            </button>
            <h1 className={s.pageTitle}>{title}</h1>
          </div>

          <div className={s.topbarRight}>
            <SearchInput className={s.topSearch} placeholder="Öğrenci ara..." aria-label="Öğrenci ara" />
            <ProfileMenu displayName={displayName} />
          </div>
        </header>

        <main className={s.canvas}>
          <Outlet />
        </main>
      </div>
      </div>
    </div>
  );
}
