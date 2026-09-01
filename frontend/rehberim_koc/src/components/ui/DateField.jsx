/* Tarih seçici — native <input type="date"> yerine.

   Gerekçe: native girdide yalnız `min`/`max` verilebilir, aradaki tek tek günler
   kapatılamaz. Program penceresi seçerken "dolu" günler dağınık aralıklar hâlinde
   olduğundan (öğrencinin mevcut programları) her günün ayrı ayrı kapatılabilmesi
   gerekiyor; bu yüzden ay ızgarasını kendimiz çiziyoruz. */
import { useEffect, useMemo, useRef, useState } from 'react';
import { ChevronLeft, ChevronRight, Calendar } from 'lucide-react';
import s from './DateField.module.css';

const WEEKDAYS = ['Pzt', 'Sal', 'Çar', 'Per', 'Cum', 'Cmt', 'Paz'];
const MONTHS = [
  'Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
  'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık',
];
const MONTHS_SHORT = ['Oca', 'Şub', 'Mar', 'Nis', 'May', 'Haz', 'Tem', 'Ağu', 'Eyl', 'Eki', 'Kas', 'Ara'];

const pad2 = (n) => String(n).padStart(2, '0');
const toKey = (y, m, d) => `${y}-${pad2(m + 1)}-${pad2(d)}`;
/** Ayın 1'i için Pazartesi-başlangıçlı boşluk sayısı. */
const leadingBlanks = (y, m) => (new Date(y, m, 1).getDay() + 6) % 7;
const daysInMonth = (y, m) => new Date(y, m + 1, 0).getDate();

function parse(iso) {
  if (!iso) return null;
  const [y, m, d] = iso.split('-').map(Number);
  return { year: y, month: m - 1, day: d };
}

/** "24 Ağu 2026 Pzt" */
function label(iso) {
  const p = parse(iso);
  if (!p) return 'Tarih seç';
  const wd = WEEKDAYS[(new Date(p.year, p.month, p.day).getDay() + 6) % 7];
  return `${p.day} ${MONTHS_SHORT[p.month]} ${p.year} ${wd}`;
}

/**
 * @param value       seçili tarih (YYYY-MM-DD)
 * @param onChange    (iso) => void
 * @param isDisabled  (iso) => boolean — true ise o gün tıklanamaz
 * @param disabledHint kapalı günlerin altında gösterilecek açıklama
 */
export default function DateField({ value, onChange, isDisabled, disabledHint, ariaLabel, className }) {
  const [open, setOpen] = useState(false);
  const initial = parse(value) || parse(new Date().toISOString().slice(0, 10));
  const [cursor, setCursor] = useState({ year: initial.year, month: initial.month });
  const ref = useRef(null);

  // Dışarı tıklanınca / Esc ile kapan
  useEffect(() => {
    if (!open) return undefined;
    const onDoc = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    const onKey = (e) => { if (e.key === 'Escape') setOpen(false); };
    document.addEventListener('mousedown', onDoc);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onDoc);
      document.removeEventListener('keydown', onKey);
    };
  }, [open]);

  // Açılışta seçili ayı göster
  useEffect(() => {
    if (!open) return;
    const p = parse(value);
    if (p) setCursor({ year: p.year, month: p.month });
  }, [open, value]);

  const cells = useMemo(() => {
    const { year, month } = cursor;
    const blanks = leadingBlanks(year, month);
    const total = daysInMonth(year, month);
    const out = Array.from({ length: blanks }, () => null);
    for (let d = 1; d <= total; d += 1) {
      const iso = toKey(year, month, d);
      out.push({ day: d, iso, disabled: isDisabled ? isDisabled(iso) : false });
    }
    return out;
  }, [cursor, isDisabled]);

  const shift = (delta) => setCursor((c) => {
    const m = c.month + delta;
    return { year: c.year + Math.floor(m / 12), month: ((m % 12) + 12) % 12 };
  });

  return (
    <div className={`${s.wrap} ${className || ''}`} ref={ref}>
      <button
        type="button"
        className={s.trigger}
        onClick={() => setOpen((o) => !o)}
        aria-label={ariaLabel}
        aria-expanded={open}
      >
        <Calendar size={13} />
        <span className={s.triggerText}>{label(value)}</span>
      </button>

      {open && (
        <div className={s.pop} role="dialog" aria-label={ariaLabel}>
          <div className={s.head}>
            <button type="button" className={s.navBtn} onClick={() => shift(-1)} aria-label="Önceki ay">
              <ChevronLeft size={14} />
            </button>
            <span className={s.monthName}>{MONTHS[cursor.month]} {cursor.year}</span>
            <button type="button" className={s.navBtn} onClick={() => shift(1)} aria-label="Sonraki ay">
              <ChevronRight size={14} />
            </button>
          </div>

          <div className={s.grid}>
            {WEEKDAYS.map((w) => <span className={s.wd} key={w}>{w}</span>)}
            {cells.map((c, i) => (c === null ? (
              // eslint-disable-next-line react/no-array-index-key
              <span key={`b${i}`} />
            ) : (
              <button
                key={c.iso}
                type="button"
                className={`${s.day} ${c.iso === value ? s.daySelected : ''}`}
                disabled={c.disabled}
                title={c.disabled ? disabledHint : undefined}
                onClick={() => { onChange(c.iso); setOpen(false); }}
              >
                {c.day}
              </button>
            )))}
          </div>

          {disabledHint && <p className={s.hint}>{disabledHint}</p>}
        </div>
      )}
    </div>
  );
}
