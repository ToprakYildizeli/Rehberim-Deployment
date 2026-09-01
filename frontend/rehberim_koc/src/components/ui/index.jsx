import { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { Moon, Sun, X, Search, Inbox } from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';
import { initialsOf, colorFor } from './avatarUtils';
import { nextNumberState } from './numberInput';
import s from './ui.module.css';

const cx = (...parts) => parts.filter(Boolean).join(' ');

/* ---------- Button ---------- */
const VARIANTS = {
  primary: s.primary,
  ghost: s.ghost,
  soft: s.soft,
  danger: s.danger,
  subtle: s.subtle,
};
const SIZES = { sm: s.sizeSm, md: s.sizeMd, lg: s.sizeLg };

export function Button({
  variant = 'primary',
  size = 'md',
  iconOnly = false,
  block = false,
  className,
  children,
  ...rest
}) {
  return (
    <button
      type="button"
      className={cx(
        s.btn,
        VARIANTS[variant],
        SIZES[size],
        iconOnly && s.iconOnly,
        block && s.block,
        className
      )}
      {...rest}
    >
      {children}
    </button>
  );
}

/* ---------- Card ---------- */
export function Card({ pad = true, className, children, ...rest }) {
  return (
    <div className={cx(s.card, pad && s.cardPad, className)} {...rest}>
      {children}
    </div>
  );
}

export function CardHeader({ title, subtitle, actions, className }) {
  return (
    <div className={cx(s.cardHeader, className)}>
      <div>
        <h3 className={s.cardTitle}>{title}</h3>
        {subtitle && <p className={s.cardSub}>{subtitle}</p>}
      </div>
      {actions}
    </div>
  );
}

/* ---------- Field / Input / Select ---------- */
export function Field({ label, error, children, className }) {
  return (
    <label className={cx(s.field, className)}>
      {label}
      {children}
      {error && <span className={s.fieldError}>{error}</span>}
    </label>
  );
}

export function Input({ className, ...rest }) {
  return <input className={cx(s.control, className)} {...rest} />;
}

/**
 * Sayı girdisi — alanı boşaltmaya izin verir.
 *
 * Doğrudan `value={sayı}` + `onChange={Number(...)}` yazmak sinir bozucu bir hata
 * üretiyor: alan silinince `Number('')` 0 olduğu için kutuda "0" kalıyor ve
 * üstüne yazınca "0120" gibi değerler çıkıyor. Burada görünen metin bileşenin
 * kendi durumu; boş bırakılabiliyor, yalnız geçerli bir sayıya dönüştüğünde
 * `onCommit` çağrılıyor ve odak çıkınca metin son geçerli değere dönüyor.
 */
export function NumberInput({ value, onCommit, min, max, className, ...rest }) {
  const [text, setText] = useState(String(value ?? ''));

  // Dışarıdan değer değişirse (ör. sunucudan gelen program) metni eşitle.
  useEffect(() => { setText(String(value ?? '')); }, [value]);

  return (
    <input
      type="text"
      inputMode="numeric"
      className={cx(s.control, className)}
      value={text}
      onChange={(e) => {
        const { text: next, commit } = nextNumberState(e.target.value, min, max);
        setText(next);
        if (commit !== null) onCommit(commit);
      }}
      onBlur={() => setText(String(value ?? ''))}  // yarım kalan giriş geri alınır
      {...rest}
    />
  );
}

export function Select({ className, children, ...rest }) {
  return (
    <select className={cx(s.control, className)} {...rest}>
      {children}
    </select>
  );
}

export function SearchInput({ className, ...rest }) {
  return (
    <div className={cx(s.search, className)}>
      <span className={s.searchIcon}>
        <Search size={15} />
      </span>
      <input type="search" className={s.searchInput} {...rest} />
    </div>
  );
}

/* ---------- Avatar ---------- */
const AVATAR_SIZES = { xs: s.avatarXs, sm: s.avatarSm, md: s.avatarMd, lg: s.avatarLg };

export function Avatar({ name = '', color, size = 'md', className, ...rest }) {
  return (
    <span
      className={cx(s.avatar, AVATAR_SIZES[size], className)}
      style={{ background: color || colorFor(name) }}
      title={name}
      aria-hidden="true"
      {...rest}
    >
      {initialsOf(name)}
    </span>
  );
}

/* ---------- Badge ---------- */
const TONES = {
  neutral: s.badgeNeutral,
  accent: s.badgeAccent,
  success: s.badgeSuccess,
  warning: s.badgeWarning,
  danger: s.badgeDanger,
  violet: s.badgeViolet,
  cyan: s.badgeCyan,
};

export function Badge({ tone = 'neutral', className, children, ...rest }) {
  return (
    <span className={cx(s.badge, TONES[tone], className)} {...rest}>
      {children}
    </span>
  );
}

/* ---------- ProgressBar ---------- */
export function ProgressBar({ value, color, className }) {
  const pct = Math.max(0, Math.min(100, value ?? 0));
  return (
    <div
      className={cx(s.progressTrack, className)}
      role="progressbar"
      aria-valuenow={pct}
      aria-valuemin={0}
      aria-valuemax={100}
    >
      <div
        className={s.progressFill}
        style={{ width: `${pct}%`, background: color || 'var(--accent)' }}
      />
    </div>
  );
}

/* ---------- ProgressRing ---------- */
export function ProgressRing({ value, label, size = 88, stroke = 9, color = 'var(--accent)' }) {
  const pct = Math.max(0, Math.min(100, value ?? 0));
  const r = (size - stroke) / 2;
  const circumference = 2 * Math.PI * r;
  return (
    <div className={s.ring}>
      <div className={s.ringWrap} style={{ width: size, height: size }}>
        <svg className={s.ringSvg} width={size} height={size} aria-hidden="true">
          <circle
            className={s.ringTrack}
            cx={size / 2}
            cy={size / 2}
            r={r}
            fill="none"
            strokeWidth={stroke}
          />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            fill="none"
            stroke={color}
            strokeWidth={stroke}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={circumference * (1 - pct / 100)}
            style={{ transition: 'stroke-dashoffset 0.5s ease' }}
          />
        </svg>
        <span className={s.ringValue} style={{ fontSize: size * 0.22 }}>
          %{pct}
        </span>
      </div>
      {label && <span className={s.ringLabel}>{label}</span>}
    </div>
  );
}

/* ---------- Modal ---------- */
export function Modal({ open, onClose, children, width, labelledBy }) {
  const overlayRef = useRef(null);

  useEffect(() => {
    if (!open) return undefined;
    const onKey = (e) => {
      if (e.key === 'Escape') onClose?.();
    };
    document.addEventListener('keydown', onKey);
    const prev = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', onKey);
      document.body.style.overflow = prev;
    };
  }, [open, onClose]);

  if (!open) return null;

  return createPortal(
    <div
      ref={overlayRef}
      className={s.overlay}
      onMouseDown={(e) => {
        if (e.target === overlayRef.current) onClose?.();
      }}
    >
      <div
        className={s.modal}
        style={width ? { maxWidth: width } : undefined}
        role="dialog"
        aria-modal="true"
        aria-labelledby={labelledBy}
      >
        <button className={s.modalClose} onClick={onClose} aria-label="Kapat" type="button">
          <X size={18} />
        </button>
        {children}
      </div>
    </div>,
    document.body
  );
}

/* ---------- ThemeToggle ---------- */
export function ThemeToggle({ floating = false, className }) {
  const { theme, toggle } = useTheme();
  return (
    <button
      type="button"
      onClick={toggle}
      className={cx(s.themeBtn, floating && s.themeBtnFloating, className)}
      aria-label={theme === 'light' ? 'Koyu temaya geç' : 'Açık temaya geç'}
      title={theme === 'light' ? 'Koyu tema' : 'Açık tema'}
    >
      {theme === 'light' ? <Moon size={16} /> : <Sun size={16} />}
    </button>
  );
}

/* ---------- EmptyState ---------- */
export function EmptyState({ icon, title, text, action }) {
  return (
    <div className={s.empty}>
      <div className={s.emptyIcon}>{icon || <Inbox size={22} />}</div>
      {title && <p className={s.emptyTitle}>{title}</p>}
      {text && <p className={s.emptyText}>{text}</p>}
      {action}
    </div>
  );
}

/* ---------- Spinner ---------- */
export function Spinner({ size = 18 }) {
  return (
    <span
      className={s.spinner}
      style={{ width: size, height: size, display: 'inline-block' }}
      role="status"
      aria-label="Yükleniyor"
    />
  );
}

/* ---------- PillGroup (filter tabs) ---------- */
export function PillGroup({ options, value, onChange, className }) {
  return (
    <div className={cx(s.pillGroup, className)} role="tablist">
      {options.map((opt) => {
        const val = opt.value ?? opt;
        const lbl = opt.label ?? opt;
        return (
          <button
            key={val}
            type="button"
            role="tab"
            aria-selected={val === value}
            className={cx(s.pill, val === value && s.pillActive)}
            onClick={() => onChange(val)}
          >
            {lbl}
          </button>
        );
      })}
    </div>
  );
}
