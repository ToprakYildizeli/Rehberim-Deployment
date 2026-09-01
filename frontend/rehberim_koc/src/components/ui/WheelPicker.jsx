import { useEffect, useRef } from 'react';
import s from './WheelPicker.module.css';

const ITEM_H = 36;   // .item yüksekliği (css ile aynı)
const PAD = ITEM_H;  // VISIBLE=3 → üstte/altta birer boş satır

/**
 * iPhone alarm gibi dönen (drum) seçici. Kaydırınca ortadaki değere snap'lenir;
 * listeyi 3 kez tekrarlayıp uçlarda ortaya geri sararak döngüsel his verir.
 */
export default function WheelPicker({ options, value, onChange, ariaLabel }) {
  const ref = useRef(null);
  const settle = useRef(null);
  const n = options.length;
  const baseIndex = Math.max(0, options.indexOf(value));

  // Değer/dış durum değişince ortadaki kopyada seçili değere konumlan.
  useEffect(() => {
    const el = ref.current;
    if (el) el.scrollTop = (n + baseIndex) * ITEM_H;
  }, [value, baseIndex, n]);

  function handleScroll() {
    const el = ref.current;
    if (!el) return;
    clearTimeout(settle.current);
    settle.current = setTimeout(() => {
      let idx = Math.round(el.scrollTop / ITEM_H);
      // Uçlara gelince sessizce ortadaki kopyaya geri sar (döngüsel his).
      if (idx < n) { idx += n; el.scrollTop = idx * ITEM_H; }
      else if (idx >= 2 * n) { idx -= n; el.scrollTop = idx * ITEM_H; }
      const val = options[((idx % n) + n) % n];
      if (val !== value) onChange(val);
    }, 100);
  }

  const items = [...options, ...options, ...options];

  return (
    <div className={s.wheel} role="listbox" aria-label={ariaLabel}>
      <div className={s.highlight} />
      <div className={s.scroller} ref={ref} onScroll={handleScroll}>
        <div style={{ height: PAD }} />
        {items.map((opt, i) => (
          <div className={s.item} key={i} aria-hidden>{opt}</div>
        ))}
        <div style={{ height: PAD }} />
      </div>
    </div>
  );
}
