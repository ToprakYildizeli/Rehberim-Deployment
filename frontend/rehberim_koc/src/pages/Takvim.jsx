import { useEffect, useMemo, useState } from 'react';
import { ChevronLeft, ChevronRight, Plus, Trash2 } from 'lucide-react';
import {
  Card, Button, Avatar, Field, Input, Select, EmptyState, Spinner,
} from '../components/ui';
import WheelPicker from '../components/ui/WheelPicker';
import { listAppointments, createAppointment, deleteAppointment } from '../api/appointments';
import { listStudents } from '../api/students';
import s from './Takvim.module.css';

const WEEKDAYS = ['Pzt', 'Sal', 'Çar', 'Per', 'Cum', 'Cmt', 'Paz'];
const MONTHS = [
  'Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
  'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık',
];

/** Local YYYY-MM-DD — avoids the UTC shift that toISOString() introduces. */
const toKey = (y, m, d) =>
  `${y}-${String(m + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;

/** Monday-first offset for the 1st of the month. */
const leadingBlanks = (y, m) => (new Date(y, m, 1).getDay() + 6) % 7;

/** Bir gün hücresine sığan etkinlik kutusu sayısı; fazlası "+N daha" olur.
 *  Hücre yüksekliği buna göre sabitlendiği için ikisi birlikte değişmeli
 *  (bkz. `.cell` min-height, Takvim.module.css). */
const CHIPS_PER_CELL = 2;
const catColor = (c) =>
  (c === 'Görüşme' ? 'var(--violet)' : c === 'Deneme' ? 'var(--warning)' : 'var(--accent)');

const TODAY = new Date();
const pad2 = (n) => String(n).padStart(2, '0');
const isoDate = (d) => `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`;

// 24-saat formatında saat (08–23) / dakika seçenekleri (AM/PM yok)
const HOUR_OPTS = Array.from({ length: 16 }, (_, i) => pad2(i + 8));
const MIN_OPTS = ['00', '05', '10', '15', '20', '25', '30', '35', '40', '45', '50', '55'];

export default function Takvim() {
  // Etkinlikler backend'den geliyor; takvimi içinde bulunduğumuz ay/günde aç.
  const [cursor, setCursor] = useState({ year: TODAY.getFullYear(), month: TODAY.getMonth() });
  const [selected, setSelected] = useState(isoDate(TODAY));
  const [items, setItems] = useState(null);
  const [students, setStudents] = useState([]);
  const [form, setForm] = useState({ time: '09:00', studentId: '', category: 'Toplantı', note: '' });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    let alive = true;
    Promise.all([listAppointments(), listStudents()]).then(([ap, st]) => {
      if (!alive) return;
      setItems(ap);
      setStudents(st);
      setForm((f) => ({ ...f, studentId: String(st[0]?.id ?? '') }));
    });
    return () => { alive = false; };
  }, []);

  const byDate = useMemo(() => {
    const map = new Map();
    (items ?? []).forEach((a) => {
      if (!map.has(a.date)) map.set(a.date, []);
      map.get(a.date).push(a);
    });
    map.forEach((list) => list.sort((a, b) => a.time.localeCompare(b.time)));
    return map;
  }, [items]);

  const dayCount = new Date(cursor.year, cursor.month + 1, 0).getDate();
  const blanks = leadingBlanks(cursor.year, cursor.month);
  const todayKey = toKey(new Date().getFullYear(), new Date().getMonth(), new Date().getDate());
  const selectedItems = byDate.get(selected) ?? [];

  function shiftMonth(delta) {
    setCursor(({ year, month }) => {
      const next = month + delta;
      if (next < 0) return { year: year - 1, month: 11 };
      if (next > 11) return { year: year + 1, month: 0 };
      return { year, month: next };
    });
  }

  async function handleSave(e) {
    e.preventDefault();
    if (!form.time) return;  // öğrenci opsiyonel → kişisel etkinlik olabilir
    setSaving(true);
    try {
      const created = await createAppointment({ ...form, date: selected });
      setItems((prev) => [...prev, created]);
      setForm((f) => ({ ...f, time: '09:00', note: '' }));
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id) {
    await deleteAppointment(id);
    setItems((prev) => prev.filter((x) => x.id !== id));
  }

  if (!items) {
    return <div style={{ display: 'grid', placeItems: 'center', padding: 60 }}><Spinner size={24} /></div>;
  }

  const selectedLabel = (() => {
    const [y, m, d] = selected.split('-').map(Number);
    return `${d} ${MONTHS[m - 1]} ${y}`;
  })();

  return (
    <div className={s.page}>
      <Card>
        <div className={s.calHead}>
          <h2 className={s.month}>{MONTHS[cursor.month]} {cursor.year}</h2>
          <div className={s.navGroup}>
            <button type="button" className={s.navBtn} onClick={() => shiftMonth(-1)} aria-label="Önceki ay">
              <ChevronLeft size={16} />
            </button>
            <button type="button" className={s.navBtn} onClick={() => shiftMonth(1)} aria-label="Sonraki ay">
              <ChevronRight size={16} />
            </button>
          </div>
        </div>

        <div className={s.grid}>
          {WEEKDAYS.map((d) => (
            <span className={s.weekday} key={d}>{d}</span>
          ))}

          {Array.from({ length: blanks }, (_, i) => (
            <span className={`${s.cell} ${s.cellEmpty}`} key={`blank-${i}`} />
          ))}

          {Array.from({ length: dayCount }, (_, i) => {
            const day = i + 1;
            const key = toKey(cursor.year, cursor.month, day);
            const dayItems = byDate.get(key) ?? [];
            // Hücreye kaç kutu sığdığı sabit; kalanı sessizce düşmesin diye sayılır.
            const shown = dayItems.slice(0, CHIPS_PER_CELL);
            const hidden = dayItems.length - shown.length;
            return (
              <button
                type="button"
                key={key}
                className={[
                  s.cell,
                  key === selected ? s.cellSelected : '',
                  key === todayKey ? s.cellToday : '',
                ].join(' ')}
                onClick={() => setSelected(key)}
                aria-pressed={key === selected}
                aria-label={`${day} ${MONTHS[cursor.month]}, ${dayItems.length} etkinlik`}
              >
                <span className={s.cellDay}>{day}</span>
                <span className={s.cellEvents}>
                  {shown.map((a) => (
                    <span
                      className={s.chip}
                      key={a.id}
                      style={{ borderLeftColor: catColor(a.category) }}
                      title={`${a.time} ${a.student?.name ?? ''} ${a.category}`.trim()}
                    >
                      {a.time && <span className={s.chipTime}>{a.time}</span>}
                      <span className={s.chipText}>{a.student?.name ?? a.category}</span>
                    </span>
                  ))}
                  {hidden > 0 && <span className={s.chipMore}>+{hidden} daha</span>}
                </span>
              </button>
            );
          })}
        </div>
      </Card>

      <Card>
        <h2 className={s.agendaDate}>{selectedLabel}</h2>
        <p className={s.agendaCount}>
          {selectedItems.length > 0 ? `${selectedItems.length} etkinlik` : 'Etkinlik yok'}
        </p>

        {selectedItems.length === 0 ? (
          <EmptyState text="Bu gün için planlanmış bir etkinlik yok." />
        ) : (
          <div className={s.agendaList}>
            {selectedItems.map((a) => (
              <div
                className={s.event}
                key={a.id}
                style={{ borderLeftColor: catColor(a.category) }}
              >
                <span className={s.eventTime}>{a.time}</span>
                {a.student && (
                  <Avatar name={a.student.name} color={a.student.color} size="sm" />
                )}
                {/* Başlık ana satır, kim/not ikinci satır. `category` backend'in
                    serbest metin `title`'ı olduğu için rozete sığmıyordu. */}
                <span className={s.eventBody}>
                  <span className={s.eventName} title={a.category}>{a.category}</span>
                  <p className={s.eventNote}>
                    {[a.student?.name ?? 'Kişisel', a.note].filter(Boolean).join(' · ')}
                  </p>
                </span>
                <button
                  type="button"
                  className={s.eventDelete}
                  onClick={() => handleDelete(a.id)}
                  aria-label={`${a.time} etkinliğini sil`}
                >
                  <Trash2 size={14} />
                </button>
              </div>
            ))}
          </div>
        )}

        <form className={s.form} onSubmit={handleSave}>
          <h3 className={s.formTitle}>Etkinlik Ekle</h3>

          <Field label="Saat">
            <div className={s.timePicker}>
              <WheelPicker
                ariaLabel="Saat"
                options={HOUR_OPTS}
                value={form.time.split(':')[0]}
                onChange={(hh) => setForm((f) => ({ ...f, time: `${hh}:${f.time.split(':')[1]}` }))}
              />
              <span className={s.timeSep}>:</span>
              <WheelPicker
                ariaLabel="Dakika"
                options={MIN_OPTS}
                value={form.time.split(':')[1]}
                onChange={(mm) => setForm((f) => ({ ...f, time: `${f.time.split(':')[0]}:${mm}` }))}
              />
            </div>
          </Field>

          <Field label="Tür">
            <Select
              value={form.category}
              onChange={(e) => setForm((f) => ({ ...f, category: e.target.value }))}
            >
              <option>Toplantı</option>
              <option>Görüşme</option>
              <option>Deneme</option>
              <option>Diğer</option>
            </Select>
          </Field>

          <Field label="Öğrenci">
            <Select
              value={form.studentId}
              onChange={(e) => setForm((f) => ({ ...f, studentId: e.target.value }))}
            >
              <option value="">Kişisel (öğrencisiz)</option>
              {students.map((st) => (
                <option value={st.id} key={st.id}>
                  {st.name} · {st.grade}
                </option>
              ))}
            </Select>
          </Field>

          <Field label="Not">
            <Input
              placeholder="Örn. Haftalık değerlendirme"
              value={form.note}
              onChange={(e) => setForm((f) => ({ ...f, note: e.target.value }))}
            />
          </Field>

          <div className={s.formActions}>
            <Button
              variant="ghost"
              onClick={() => setForm((f) => ({ ...f, time: '09:00', note: '' }))}
            >
              İptal
            </Button>
            <Button type="submit" disabled={saving || !form.time}>
              <Plus size={14} /> {saving ? 'Kaydediliyor…' : 'Kaydet'}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}
