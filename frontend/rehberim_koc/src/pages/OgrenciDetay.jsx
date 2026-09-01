import { useEffect, useMemo, useRef, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ChevronLeft, ChevronRight, ChevronDown, BookOpen, ClipboardList, CalendarDays, Target, Check,
  ArrowUpDown, ShieldCheck, Lock, Trophy,
} from 'lucide-react';
import {
  Card, Avatar, Badge, Button, Select, PillGroup, EmptyState, Spinner, ProgressBar, SearchInput,
} from '../components/ui';
import { getStudent } from '../api/students';
import { listStudentBooks, getBook } from '../api/books';
import { listStudentExams } from '../api/exams';
import {
  getComplianceHistory, getProgramCompliance, getStudentPrograms, setProgramApproval,
  setTaskCompleted, windowDays, fmtMin,
} from '../api/programs';
import { listSubjects, listTopics, blockLabel } from '../api/catalog';
import { getTopicLevels, setTopicLevel } from '../api/topicProgress';
import { getStudentAchievements } from '../api/achievements';
import s from './OgrenciDetay.module.css';

const cx = (...parts) => parts.filter(Boolean).join(' ');

/** Dakika → "6,5 sa" / "45 dk". Uyum ve çalışma süreleri hep bu biçimde yazılır. */
const fmtHours = (min) => {
  if (!min) return '0 sa';
  if (min < 60) return `${min} dk`;
  return `${(min / 60).toFixed(1).replace('.', ',').replace(',0', '')} sa`;
};

const MONTH_NAMES = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
  'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık'];
const fmtMonth = (ym) => {
  const [y, m] = ym.split('-').map(Number);
  return `${MONTH_NAMES[m - 1]} ${y}`;
};

const FIELD_LABEL = { say: 'Sayısal', ea: 'Eşit Ağırlık', soz: 'Sözel' };
const MONTHS_SHORT = ['Oca', 'Şub', 'Mar', 'Nis', 'May', 'Haz', 'Tem', 'Ağu', 'Eyl', 'Eki', 'Kas', 'Ara'];
const fmtDate = (iso) => {
  if (!iso) return '';
  const [y, m, d] = iso.split('-').map(Number);
  return `${d} ${MONTHS_SHORT[m - 1]} ${y}`;
};

const TABS = [
  { value: 'kitaplar', label: 'Kitaplar' },
  { value: 'denemeler', label: 'Denemeler' },
  { value: 'program', label: 'Ders Programı' },
  { value: 'konular', label: 'Konu Takibi' },
  { value: 'basarimlar', label: 'Başarımlar' },
];

export default function OgrenciDetay() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [student, setStudent] = useState(null);
  const [notFound, setNotFound] = useState(false);
  const [tab, setTab] = useState('kitaplar');

  useEffect(() => {
    let alive = true;
    getStudent(id).then((st) => {
      if (!alive) return;
      if (st) setStudent(st);
      else setNotFound(true);
    });
    return () => { alive = false; };
  }, [id]);

  if (notFound) {
    return (
      <div className={s.page}>
        <BackLink onClick={() => navigate('/ogrenciler')} />
        <Card>
          <EmptyState title="Öğrenci bulunamadı" text="Bu öğrenci mevcut değil veya erişiminiz yok." />
        </Card>
      </div>
    );
  }

  if (!student) {
    return <div className={s.center}><Spinner size={24} /></div>;
  }

  return (
    <div className={s.page}>
      <BackLink onClick={() => navigate('/ogrenciler')} />

      <Card className={s.header}>
        <Avatar name={student.name} color={student.color} size="lg" />
        <div className={s.headerText}>
          <h2 className={s.name}>{student.name}</h2>
          <div className={s.meta}>
            <span className={s.grade}>{student.grade}</span>
            {student.study_field && (
              <Badge tone="accent">{FIELD_LABEL[student.study_field] || student.study_field}</Badge>
            )}
          </div>
        </div>
      </Card>

      <PillGroup options={TABS} value={tab} onChange={setTab} className={s.tabs} />

      {tab === 'kitaplar' && <KitaplarTab studentId={student.id} />}
      {tab === 'denemeler' && <DenemelerTab studentId={student.id} />}
      {tab === 'program' && <ProgramTab studentId={student.id} />}
      {tab === 'basarimlar' && <BasarimlarTab studentId={student.id} />}
      {tab === 'konular' && <KonuTakibiTab student={student} />}
    </div>
  );
}

function BackLink({ onClick }) {
  return (
    <button type="button" className={s.back} onClick={onClick}>
      <ChevronLeft size={16} /> Öğrenciler
    </button>
  );
}

/** Sekme yükleme/boş durumları için ortak sarmalayıcı. */
function TabState({ loading, empty, emptyProps, children }) {
  if (loading) return <div className={s.center}><Spinner size={22} /></div>;
  if (empty) return <Card><EmptyState {...emptyProps} /></Card>;
  return children;
}

/* ---------------- Kitaplar ---------------- */
const BOOK_CAT_FILTERS = [
  { value: 'all', label: 'Tümü' },
  { value: 'tyt', label: 'TYT' },
  { value: 'ayt', label: 'AYT' },
  { value: 'genel', label: 'Genel' },
];
const BOOK_FORMAT_FILTERS = [
  { value: 'all', label: 'Tüm' },
  { value: 'konu_anlatimi', label: 'Konu' },
  { value: 'soru_bankasi', label: 'Soru' },
  { value: 'deneme', label: 'Deneme' },
];
const BOOK_SORTS = [
  { value: 'status', label: 'Duruma göre' },
  { value: 'name', label: 'Ada göre' },
  { value: 'topics', label: 'Konu sayısı' },
];
const BOOK_STATUS_RANK = { tamamlandi: 0, devam: 1, baslanmadi: 2 };
// Kitabın sınav kategorisi (ders etiketinin ön ekinden) ve baz ders adı
const bookCat = (b) => (b.subjectLabel?.startsWith('TYT ') ? 'tyt' : b.subjectLabel?.startsWith('AYT ') ? 'ayt' : 'genel');
const bookSubject = (b) => ((b.kind === 'okuma' || !b.subjectLabel) ? null : stripExamPrefix(b.subjectLabel));

function KitaplarTab({ studentId }) {
  const [books, setBooks] = useState(null);
  const [cat, setCat] = useState('all');       // TYT/AYT/Genel
  const [subj, setSubj] = useState('all');     // ders
  const [fmt, setFmt] = useState('all');       // Konu/Soru/Deneme
  const [query, setQuery] = useState('');
  const [sortBy, setSortBy] = useState('status');

  useEffect(() => {
    let alive = true;
    listStudentBooks(studentId).then((d) => { if (alive) setBooks(d); });
    return () => { alive = false; };
  }, [studentId]);

  // Seçili kategorideki mevcut dersler (ders dropdown'ı için)
  const subjectOptions = useMemo(() => {
    const src = (books || []).filter((b) => cat === 'all' || bookCat(b) === cat);
    return [...new Set(src.map(bookSubject).filter(Boolean))].sort((a, b) => a.localeCompare(b, 'tr'));
  }, [books, cat]);

  const visible = useMemo(() => {
    let list = books || [];
    if (cat !== 'all') list = list.filter((b) => bookCat(b) === cat);
    if (subj !== 'all') list = list.filter((b) => bookSubject(b) === subj);
    if (fmt !== 'all') list = list.filter((b) => b.format === fmt);
    const q = query.trim().toLocaleLowerCase('tr-TR');
    if (q) {
      list = list.filter((b) => [b.label, b.title, b.author, b.subjectLabel, b.publisher]
        .filter(Boolean).some((x) => x.toLocaleLowerCase('tr-TR').includes(q)));
    }
    const arr = [...list];
    if (sortBy === 'name') arr.sort((a, b) => (a.title || a.label).localeCompare(b.title || b.label, 'tr'));
    else if (sortBy === 'topics') arr.sort((a, b) => (b.topicCount || 0) - (a.topicCount || 0));
    else arr.sort((a, b) => (BOOK_STATUS_RANK[a.status] ?? 9) - (BOOK_STATUS_RANK[b.status] ?? 9));
    return arr;
  }, [books, cat, subj, fmt, query, sortBy]);

  const ders = visible.filter((b) => b.kind === 'ders');
  const okuma = visible.filter((b) => b.kind === 'okuma');

  return (
    <TabState
      loading={!books}
      empty={books && books.length === 0}
      emptyProps={{ icon: <BookOpen size={22} />, title: 'Kitap yok', text: 'Öğrenci henüz kitaplığına kitap eklememiş.' }}
    >
      <div className={s.stack}>
        <div className={s.bookFilters}>
          <PillGroup options={BOOK_CAT_FILTERS} value={cat} onChange={(v) => { setCat(v); setSubj('all'); }} />
          <Select className={s.bookSubjSelect} value={subj} onChange={(e) => setSubj(e.target.value)} aria-label="Ders">
            <option value="all">Tüm dersler</option>
            {subjectOptions.map((n) => <option key={n} value={n}>{n}</option>)}
          </Select>
          <PillGroup options={BOOK_FORMAT_FILTERS} value={fmt} onChange={setFmt} />
        </div>
        <div className={s.examToolbar}>
          <SearchInput
            className={s.examSearch}
            placeholder="Kitap ara (ör. 345, yayınevi)..."
            aria-label="Kitap ara"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <SortMenu value={sortBy} options={BOOK_SORTS} onChange={setSortBy} />
        </div>

        {visible.length === 0 ? (
          <Card><EmptyState icon={<BookOpen size={22} />} title="Sonuç yok" text="Bu filtreyle eşleşen kitap yok." /></Card>
        ) : (
          <>
            {ders.length > 0 && (
              <section className={s.konuSection}>
                <h3 className={s.sectionTitle}>Ders Kitapları</h3>
                <div className={s.bookList}>{ders.map((b) => <BookRow key={b.id} book={b} />)}</div>
              </section>
            )}
            {okuma.length > 0 && (
              <section className={s.konuSection}>
                <h3 className={s.sectionTitle}>Okuma Kitapları</h3>
                <div className={s.bookList}>{okuma.map((b) => <BookRow key={b.id} book={b} />)}</div>
              </section>
            )}
          </>
        )}
      </div>
    </TabState>
  );
}

const bookStatusTone = (st) => (st === 'tamamlandi' ? 'success' : st === 'devam' ? 'warning' : 'neutral');

/** Tek kitap satırı — tıklayınca içindeki konuları (kitap özelindeki ilerleme) açar. */
function BookRow({ book }) {
  const [open, setOpen] = useState(false);
  const [detail, setDetail] = useState(null);

  useEffect(() => {
    if (!open || detail) return undefined;
    let alive = true;
    getBook(book.id).then((d) => { if (alive) setDetail(d); });
    return () => { alive = false; };
  }, [open, detail, book.id]);

  const doneCount = detail ? detail.topics.filter((t) => t.done).length : null;

  return (
    <Card className={s.bookCard} pad={false}>
      <button type="button" className={s.bookHead} onClick={() => setOpen((o) => !o)} aria-expanded={open}>
        <span className={`${s.chevron} ${open ? s.chevronOpen : ''}`}><ChevronRight size={16} /></span>
        <div className={s.bookMain}>
          <span className={s.bookLabel}>{book.title || book.label}</span>
          <div className={s.bookTags}>
            {book.subjectLabel && <Badge tone="cyan">{book.subjectLabel}</Badge>}
            {book.formatLabel && <Badge tone="neutral">{book.formatLabel}</Badge>}
            {book.author && <span className={s.bookMuted}>{book.author}</span>}
            {book.kind === 'ders' && book.topicCount != null && (
              <span className={s.bookMuted}>{book.topicCount} konu</span>
            )}
          </div>
        </div>
        <Badge tone={bookStatusTone(book.status)}>{book.statusLabel}</Badge>
      </button>

      {open && (
        <div className={s.bookBody}>
          {!detail ? (
            <div className={s.center}><Spinner size={18} /></div>
          ) : detail.topics.length > 0 ? (
            <>
              <p className={s.bookSummary}>
                {doneCount} / {detail.topics.length} konu tamamlandı
              </p>
              <ul className={s.topicList}>
                {detail.topics.map((t) => (
                  <li key={t.id} className={`${s.topicItem} ${t.done ? s.topicDone : ''}`}>
                    <span className={s.topicCheck}>{t.done && <Check size={13} />}</span>
                    <span className={s.topicName}>{t.name}</span>
                    <span className={s.topicStatus}>{t.statusLabel}</span>
                  </li>
                ))}
              </ul>
            </>
          ) : (
            <p className={s.bookMuted}>
              {detail.description || 'Bu kitap için konu takibi yok.'}
            </p>
          )}
        </div>
      )}
    </Card>
  );
}

/* ---------------- Denemeler ---------------- */
// "TYT "/"AYT " ön ekini at (deneme kartında zaten tür rozeti var → kısa etiket).
const stripExamPrefix = (label = '') => label.replace(/^(TYT|AYT)\s+/, '');
const round2 = (n) => Math.round(n * 100) / 100;   // net için 2 ondalık (0.25 → 0.25)

// Deneme içindeki dersleri sınav bölümlerine göre grupla (ÖSYM YKS yapısı).
const EXAM_GROUPS = {
  tyt: [
    { key: 'tur', title: 'Türkçe', names: ['Türkçe'] },
    { key: 'sos', title: 'Sosyal Bilimler', names: ['Tarih', 'Coğrafya', 'Felsefe', 'Din Kültürü ve Ahlak Bilgisi'] },
    { key: 'mat', title: 'Matematik', names: ['Matematik', 'Geometri'] },
    { key: 'fen', title: 'Fen Bilimleri', names: ['Fizik', 'Kimya', 'Biyoloji'] },
  ],
  ayt: [
    { key: 'mat', title: 'Matematik', names: ['Matematik', 'Geometri'] },
    { key: 'fen', title: 'Fen Bilimleri', names: ['Fizik', 'Kimya', 'Biyoloji'] },
    { key: 'sos1', title: 'Türk Dili ve Edebiyatı · Sosyal-1', names: ['Türk Dili ve Edebiyatı', 'Tarih-1', 'Coğrafya-1'] },
    { key: 'sos2', title: 'Sosyal Bilimler-2', names: ['Tarih-2', 'Coğrafya-2', 'Felsefe', 'Din Kültürü ve Ahlak Bilgisi'] },
  ],
};

// AYT puan türleri: hangi bölümlerin netleri toplanır (ÖSYM YKS).
const AYT_FIELDS = [
  { label: 'Sayısal', short: 'SAY', keys: ['mat', 'fen'] },
  { label: 'Eşit Ağırlık', short: 'EA', keys: ['mat', 'sos1'] },
  { label: 'Sözel', short: 'SÖZ', keys: ['sos1', 'sos2'] },
];

const EXAM_TYPE_FILTERS = [
  { value: 'all', label: 'Tümü' },
  { value: 'tyt', label: 'TYT' },
  { value: 'ayt', label: 'AYT' },
];

const SORT_OPTIONS = [
  { value: 'new', label: 'En yeni' },
  { value: 'old', label: 'En eski' },
  { value: 'high', label: 'Yüksek net' },
  { value: 'low', label: 'Düşük net' },
];

/** Uygulama tarzına uyan özel sıralama dropdown'ı (native select yerine). */
function SortMenu({ value, options, onChange }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);
  useEffect(() => {
    if (!open) return undefined;
    const onDoc = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    document.addEventListener('mousedown', onDoc);
    return () => document.removeEventListener('mousedown', onDoc);
  }, [open]);
  const current = options.find((o) => o.value === value);
  return (
    <div className={s.sortMenu} ref={ref}>
      <button type="button" className={s.sortBtn} onClick={() => setOpen((o) => !o)} aria-haspopup="listbox" aria-expanded={open}>
        <ArrowUpDown size={14} />
        <span className={s.sortBtnLabel}>{current?.label}</span>
        <ChevronDown size={14} className={s.sortChevron} />
      </button>
      {open && (
        <div className={s.sortList} role="listbox">
          {options.map((o) => (
            <button
              key={o.value}
              type="button"
              role="option"
              aria-selected={o.value === value}
              className={`${s.sortOption} ${o.value === value ? s.sortOptionActive : ''}`}
              onClick={() => { onChange(o.value); setOpen(false); }}
            >
              {o.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function DenemelerTab({ studentId }) {
  const [exams, setExams] = useState(null);
  const [byType, setByType] = useState({});   // { tyt: [subjects], ayt: [...] } katalog
  const [typeFilter, setTypeFilter] = useState('all');
  const [sortBy, setSortBy] = useState('new');
  const [query, setQuery] = useState('');

  useEffect(() => {
    let alive = true;
    Promise.all([listStudentExams(studentId), listSubjects()]).then(([ex, subs]) => {
      if (!alive) return;
      const grouped = { tyt: [], ayt: [] };
      subs
        .filter((x) => x.category === 'tyt' || x.category === 'ayt')
        .forEach((x) => grouped[x.category].push(x));
      setByType(grouped);
      setExams(ex);
    });
    return () => { alive = false; };
  }, [studentId]);

  /** Denemeyi sınav bölümlerine göre gruplar; girilmeyen ders 0 net gösterilir. */
  function examGroups(exam) {
    const defs = EXAM_GROUPS[exam.type];
    const catalog = byType[exam.type];
    if (!defs || !catalog || catalog.length === 0) {
      // Tür yoksa: tek grup, yalnızca girilen dersler.
      return [{ title: null, subjects: exam.subjectNets, totalNet: exam.totalNet, totalMax: null }];
    }
    const recorded = new Map(exam.subjectNets.map((n) => [n.subject, n]));
    const byName = new Map(catalog.map((sub) => [sub.name, sub]));
    return defs
      .map((g) => {
        const subjects = g.names
          .map((name) => byName.get(name))
          .filter(Boolean)
          .map((sub) => {
            const rec = recorded.get(sub.id);
            return {
              id: sub.id,
              subjectLabel: sub.label,
              correct: rec ? rec.correct : 0,   // doğru
              net: rec ? rec.net : 0,           // net = doğru - yanlış/4
              max: sub.questionCount || null,   // soru sayısı
            };
          });
        return {
          key: g.key,
          title: g.title,
          subjects,
          totalNet: round2(subjects.reduce((a, x) => a + x.net, 0)),
          totalMax: subjects.reduce((a, x) => a + (x.max || 0), 0),
        };
      })
      .filter((g) => g.subjects.length > 0);
  }

  // Tür filtresi + ad araması + sıralama uygula.
  const visible = useMemo(() => {
    let list = exams || [];
    if (typeFilter !== 'all') list = list.filter((e) => e.type === typeFilter);
    const q = query.trim().toLocaleLowerCase('tr-TR');
    if (q) list = list.filter((e) => (e.name || '').toLocaleLowerCase('tr-TR').includes(q));
    const arr = [...list];
    if (sortBy === 'old') arr.sort((a, b) => (a.date < b.date ? -1 : 1));
    else if (sortBy === 'high') arr.sort((a, b) => b.totalNet - a.totalNet);
    else if (sortBy === 'low') arr.sort((a, b) => a.totalNet - b.totalNet);
    else arr.sort((a, b) => (a.date < b.date ? 1 : -1));   // en yeni
    return arr;
  }, [exams, typeFilter, sortBy, query]);

  // Hangi türler mevcut → boş filtre butonu göstermemek için (opsiyonel bilgi).
  const availableTypes = useMemo(
    () => new Set((exams || []).map((e) => e.type)),
    [exams]
  );

  return (
    <TabState
      loading={!exams}
      empty={exams && exams.length === 0}
      emptyProps={{ icon: <ClipboardList size={22} />, title: 'Deneme yok', text: 'Öğrenci henüz deneme sonucu girmemiş.' }}
    >
      <div className={s.stack}>
        <div className={s.examToolbar}>
          <PillGroup
            className={s.examFilter}
            options={EXAM_TYPE_FILTERS.filter((o) => o.value === 'all' || availableTypes.has(o.value))}
            value={typeFilter}
            onChange={setTypeFilter}
          />
          <SearchInput
            className={s.examSearch}
            placeholder="Deneme ara (ör. Özdebir)..."
            aria-label="Deneme ara"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <SortMenu value={sortBy} options={SORT_OPTIONS} onChange={setSortBy} />
        </div>
        <div className={s.examCountRow}>{visible.length} deneme</div>

        {visible.length === 0 ? (
          <Card><EmptyState icon={<ClipboardList size={22} />} title="Sonuç yok" text="Bu filtreyle eşleşen deneme yok." /></Card>
        ) : (
          visible.map((e) => {
            const groups = examGroups(e);
            // AYT'de puan türü netleri: ilgili bölümlerin netleri toplanır.
            const aytFields = e.type === 'ayt'
              ? AYT_FIELDS.map((f) => {
                const gs = groups.filter((g) => f.keys.includes(g.key));
                return {
                  label: f.label,
                  short: f.short,
                  net: round2(gs.reduce((a, g) => a + g.totalNet, 0)),
                  max: gs.reduce((a, g) => a + g.totalMax, 0),
                };
              })
              : null;
            return <ExamRow key={e.id} exam={e} groups={groups} aytFields={aytFields} />;
          })
        )}
      </div>
    </TabState>
  );
}

/** Deneme satırı — kapalı: ince satır + özet net(ler); açık: tam detay. */
function ExamRow({ exam, groups, aytFields }) {
  const [open, setOpen] = useState(false);
  return (
    <Card className={s.examCard} pad={false}>
      <button type="button" className={s.examHeadBtn} onClick={() => setOpen((o) => !o)} aria-expanded={open}>
        <span className={`${s.chevron} ${open ? s.chevronOpen : ''}`}><ChevronRight size={16} /></span>
        <span className={s.examHeadMain}>
          <span className={s.examName}>{exam.name || 'Deneme'}</span>
          <span className={s.bookMuted}>{fmtDate(exam.date)}</span>
        </span>
        {!open && (
          <span className={s.examSummary}>
            {aytFields
              ? aytFields.map((f) => (
                <span className={s.examSummaryItem} key={f.short}>
                  <span className={s.examSummaryLbl}>{f.short}</span> {f.net}
                </span>
              ))
              : <span className={s.examNet}>{exam.totalNet} net</span>}
          </span>
        )}
        {exam.typeLabel && <Badge tone="accent">{exam.typeLabel}</Badge>}
      </button>

      {open && (
        <div className={s.examBody}>
          {aytFields && (
            <div className={s.netFields}>
              {aytFields.map((f) => (
                <div key={f.label} className={s.netField}>
                  <span className={s.netFieldLabel}>{f.label}</span>
                  <span className={s.netFieldValue}>
                    {f.net}
                    {f.max ? <span className={s.netMax}> / {f.max}</span> : null}
                  </span>
                </div>
              ))}
            </div>
          )}

          <div className={s.netGroups}>
            {groups.map((g, i) => (
              <div className={s.netGroup} key={g.title || i}>
                {g.title && <div className={s.netGroupTitle}>{g.title}</div>}
                <div className={s.netColList}>
                  {g.subjects.map((n) => (
                    <div key={n.id} className={s.netCell}>
                      <span className={s.netLabel}>{stripExamPrefix(n.subjectLabel)}</span>
                      <span className={s.netValue} title={`${n.net} net`}>
                        {n.correct}
                        {n.max != null && <span className={s.netMax}> / {n.max}</span>}
                      </span>
                    </div>
                  ))}
                </div>
                {g.totalMax ? (
                  <div className={s.netGroupFoot}>
                    <span>Net</span>
                    <span className={s.netGroupTotal}>{g.totalNet}</span>
                  </div>
                ) : null}
              </div>
            ))}
          </div>
        </div>
      )}
    </Card>
  );
}

/* ---------------- Ders Programı (geçmiş dahil) ---------------- */
function ProgramTab({ studentId }) {
  const [programs, setPrograms] = useState(null);
  const [activeId, setActiveId] = useState(null);
  // Onay ya da görev işareti değişince geçmiş kartı yeniden çekilsin.
  const [version, setVersion] = useState(0);

  useEffect(() => {
    let alive = true;
    getStudentPrograms(studentId).then((d) => {
      if (!alive) return;
      setPrograms(d);
      setActiveId(d.length ? d[0].id : null);
    });
    return () => { alive = false; };
  }, [studentId]);

  const active = useMemo(
    () => (programs || []).find((p) => p.id === activeId) || null,
    [programs, activeId]
  );

  /** Tek bir programı yerinde günceller (onay ya da görev işareti sonrası). */
  const patchProgram = (programId, patch) => {
    setPrograms((prev) => (prev || []).map(
      (p) => (p.id === programId ? { ...p, ...patch } : p)
    ));
    setVersion((v) => v + 1);
  };

  const options = useMemo(
    () => (programs || []).map((p) => ({
      value: p.id,
      label: `${fmtDate(p.startDate)} – ${fmtDate(p.endDate)}`
        + `${p.isCurrent ? ' • Güncel' : ''}${p.isApproved ? ' • Onaylı' : ''}`,
    })),
    [programs]
  );

  return (
    <TabState
      loading={!programs}
      empty={programs && programs.length === 0}
      emptyProps={{ icon: <CalendarDays size={22} />, title: 'Program yok', text: 'Bu öğrenci için henüz ders programı oluşturulmamış.' }}
    >
      <div className={s.stack}>
        {options.length > 1 && (
          <Select
            className={s.programSelect}
            value={activeId ?? ''}
            onChange={(e) => setActiveId(Number(e.target.value))}
            aria-label="Program haftası seç"
          >
            {options.map((o) => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </Select>
        )}
        {active && (
          <>
            <ApprovalBar program={active} onChange={(patch) => patchProgram(active.id, patch)} />
            <WeekBoard
              program={active}
              onToggleTask={async (taskId, next) => {
                patchProgram(active.id, {
                  blocks: active.blocks.map(
                    (b) => (b.taskId === taskId ? { ...b, isCompleted: next } : b)
                  ),
                });
                // Yüzdeyi tarayıcıda tekrar hesaplamak yerine sunucudan al.
                const fresh = await getProgramCompliance(active.id).catch(() => null);
                if (fresh) patchProgram(active.id, { compliance: fresh });
              }}
            />
            <ComplianceHistory studentId={studentId} version={version} />
          </>
        )}
      </div>
    </TabState>
  );
}

/** Haftalık onay çubuğu (B1): uyum özeti + onay/geri alma.
 *
 *  Onay, "öğrencinin yaptım dedikleri gerçekten yapılmış" beyanıdır; bu yüzden
 *  yalnızca **pencere kapandıktan sonra** verilebilir (backend de zorlar) ve
 *  onaydan sonra öğrenci görevlere dokunamaz. */
function ApprovalBar({ program, onChange }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  // Uyum sunucuda **süre** üzerinden hesaplanır; burada tekrar hesaplanmaz ki
  // panel, öğrenci sayfası ve veli aynı sayıyı görsün.
  const c = program.compliance;

  async function toggle(approved) {
    setBusy(true);
    setError('');
    try {
      onChange(await setProgramApproval(program.id, approved));
    } catch (err) {
      const data = err?.response?.data;
      const first = data && typeof data === 'object' ? Object.values(data)[0] : data;
      setError(String(Array.isArray(first) ? first[0] : first || 'İşlem tamamlanamadı.'));
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card className={s.approvalBar}>
      <div className={s.approvalInfo}>
        {program.isApproved
          ? <Badge tone="success"><ShieldCheck size={12} /> Onaylandı</Badge>
          : <Badge tone={program.isFinished ? 'warning' : 'neutral'}>
              {program.isFinished ? 'Onay bekliyor' : 'Devam ediyor'}
            </Badge>}
        {c && c.percent != null ? (
          <span className={s.approvalStat}>
            %{c.percent} uyum
            <span className={s.approvalSub}>
              {c.basis === 'duration'
                ? ` · ${fmtHours(c.completedMinutes)} / ${fmtHours(c.totalMinutes)} çalışma`
                : ` · ${c.completedTasks}/${c.totalTasks} görev`}
            </span>
          </span>
        ) : (
          <span className={s.approvalNote}>Bu programda çalışma bloğu yok</span>
        )}
        {program.isApproved && program.approvedByName && (
          <span className={s.approvalNote}>
            {program.approvedByName} onayladı{program.approvedAt ? ` · ${fmtDate(program.approvedAt.slice(0, 10))}` : ''}
          </span>
        )}
        {!program.isApproved && !program.isFinished && (
          <span className={s.approvalNote}>Onay, program {fmtDate(program.endDate)} tarihinde bittikten sonra verilebilir.</span>
        )}
      </div>
      <div className={s.approvalActions}>
        {error && <span className={s.approvalError}>{error}</span>}
        {program.isApproved ? (
          <Button variant="subtle" size="sm" disabled={busy} onClick={() => toggle(false)}>
            Onayı geri al
          </Button>
        ) : (
          <Button
            size="sm"
            disabled={busy || !program.isFinished}
            title={program.isFinished ? undefined : 'Program henüz bitmedi'}
            onClick={() => toggle(true)}
          >
            <Check size={14} /> Haftayı onayla
          </Button>
        )}
      </div>
    </Card>
  );
}

/** Programın günleri — uzunluk esnek olduğundan sabit 7 gün değil, pencerenin
 *  kendi günleri (windowDays) çizilir. Onaydan **önce** rehber her bloğu
 *  tamamlandı/tamamlanmadı olarak düzeltebilir; onaydan sonra tahta salt-okunur
 *  görünür (rehber yine yetkilidir ama mühürü kazara bozmasın diye kilitli). */
function WeekBoard({ program, onToggleTask }) {
  const days = windowDays(program.startDate, program.dayCount);
  const [busyTask, setBusyTask] = useState(null);
  const locked = program.isApproved;

  async function toggle(block) {
    if (locked || busyTask) return;
    setBusyTask(block.taskId);
    try {
      onToggleTask(block.taskId, await setTaskCompleted(block.taskId, !block.isCompleted));
    } catch {
      /* sunucu reddettiyse tahta olduğu gibi kalır */
    } finally {
      setBusyTask(null);
    }
  }

  return (
    <div className={s.week} style={{ '--cols': days.length }}>
      {days.map((day) => {
        const items = program.blocks
          .filter((b) => b.dayIndex === day.index)
          .sort((a, b) => a.startMin - b.startMin);
        return (
          <div className={s.day} key={day.index}>
            <span className={s.dayName}>{day.short} {day.dayNum}</span>
            {items.length === 0 ? (
              <span className={s.dayEmpty}>—</span>
            ) : (
              items.map((b) => (
                <button
                  type="button"
                  className={cx(s.block, b.isCompleted && s.blockDone, locked && s.blockLocked)}
                  key={b.id}
                  style={{ borderLeftColor: b.subjectColor }}
                  disabled={locked || busyTask === b.taskId}
                  onClick={() => toggle(b)}
                  aria-pressed={b.isCompleted}
                  title={locked
                    ? 'Onaylanmış program kilitlidir'
                    : (b.isCompleted ? 'Yapılmadı olarak işaretle' : 'Yapıldı olarak işaretle')}
                >
                  <span className={s.blockTime}>
                    {b.isCompleted ? <Check size={10} /> : (locked ? <Lock size={10} /> : null)}
                    {fmtMin(b.startMin)}
                  </span>
                  <span className={s.blockSubject}>{blockLabel(b)}</span>
                  {b.kind !== 'external' && b.topic && <span className={s.blockTopic}>{b.topic}</span>}
                  {b.bookLabel && <span className={s.blockBook}>{b.bookLabel}</span>}
                </button>
              ))
            )}
          </div>
        );
      })}
    </div>
  );
}

/* ---------------- Başarımlar (C3) ---------------- */

/** Başarım eşikleri **rehbere** aittir; hoca ileride Ayarlar'dan ekleyip
 *  çıkarabilecek (uçlar hazır: `src/api/achievements.js`). Burası yalnızca
 *  öğrencinin durumunu gösterir — kazanım sunucuda anlık hesaplanır. */
function BasarimlarTab({ studentId }) {
  const [data, setData] = useState(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let alive = true;
    getStudentAchievements(studentId)
      .then((d) => alive && setData(d))
      .catch(() => alive && setFailed(true));
    return () => { alive = false; };
  }, [studentId]);

  if (failed) {
    return <EmptyState icon={<Trophy size={22} />} title="Başarımlar yüklenemedi" />;
  }
  return (
    <TabState
      loading={!data}
      empty={data && data.totalCount === 0}
      emptyProps={{
        icon: <Trophy size={22} />,
        title: 'Başarım tanımlı değil',
        text: 'Bu öğrenci için geçerli bir başarım listesi yok.',
      }}
    >
      {data && <BasarimIcerik data={data} />}
    </TabState>
  );
}

function BasarimIcerik({ data }) {
  const { facts } = data;
  const earned = data.achievements.filter((a) => a.earned);
  const pending = data.achievements.filter((a) => !a.earned);
  return (
    <div className={s.stack}>
      <div className={s.statRow}>
        <Stat
          label="Kazanılan başarım"
          value={`${data.earnedCount}/${data.totalCount}`}
          hint={data.totalCount ? `%${Math.round(data.earnedCount / data.totalCount * 100)}` : null}
        />
        <Stat label="En iyi TYT net" value={fmtNet(facts.examNetTyt)} hint="tüm denemeler içinde" />
        <Stat label="En iyi AYT net" value={fmtNet(facts.examNetAyt)} hint="tüm denemeler içinde" />
        <Stat
          label="Konu tamamlama"
          value={facts.topicCompletion == null ? '—' : `%${facts.topicCompletion}`}
          hint={`${facts.topicsDone}/${facts.topicsTotal} konu`}
        />
      </div>

      {earned.length > 0 && (
        <div>
          <h4 className={s.chartTitle}>Kazanılanlar</h4>
          <div className={s.badgeGrid}>
            {earned.map((a) => <BasarimKarti key={a.id} a={a} />)}
          </div>
        </div>
      )}

      {pending.length > 0 && (
        <div>
          <h4 className={s.chartTitle}>
            Sıradakiler <span className={s.chartNote}>(eşiğe en yakından uzağa)</span>
          </h4>
          <div className={s.badgeGrid}>
            {pending.map((a) => <BasarimKarti key={a.id} a={a} />)}
          </div>
        </div>
      )}
    </div>
  );
}

const fmtNet = (n) => (n == null ? '—' : String(n).replace('.', ','));

/** Ölçüte göre ham değerin nasıl yazılacağı — net sayı, yüzde ise yüzde. */
const fmtDeger = (a) => {
  if (a.value == null) return 'veri yok';
  return a.metric === 'exam_net' ? `${fmtNet(a.value)} net` : `%${a.value}`;
};

function BasarimKarti({ a }) {
  return (
    <div className={cx(s.badgeCard, a.earned && s.badgeCardEarned)}>
      <span className={s.badgeIcon} aria-hidden="true">
        <Trophy size={16} />
      </span>
      <span className={s.badgeBody}>
        <span className={s.badgeName}>{a.name}</span>
        {a.description && <span className={s.badgeDesc}>{a.description}</span>}
        {a.earned ? (
          <span className={s.badgeEarned}><Check size={11} /> Kazanıldı · {fmtDeger(a)}</span>
        ) : (
          <>
            <ProgressBar className={s.badgeBar} value={a.progress} />
            <span className={s.badgeDesc}>{fmtDeger(a)} · hedef {fmtNet(a.threshold)}</span>
          </>
        )}
      </span>
    </div>
  );
}

/* ---------------- Uyum geçmişi (B2) ---------------- */

/** Öğrencinin uyum geçmişi: genel özet + haftalık zaman serisi + ay ay dağılım.
 *
 *  Yüzdeler sunucudan gelir ve **süre** üzerinden hesaplanır. Aylık ve genel
 *  ortalamalar yalnız **onaylanmış** haftalardan çıkar (B1): onaysız haftanın
 *  beyanı doğrulanmamıştır, uzun vadeli istatistiği kirletmemeli. Haftalık seride
 *  onaysızlar da görünür ama içi boş nokta ile ayrışır. */
function ComplianceHistory({ studentId, version }) {
  const [data, setData] = useState(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let alive = true;
    getComplianceHistory(studentId)
      .then((d) => alive && setData(d))
      .catch(() => alive && setFailed(true));
    return () => { alive = false; };
  }, [studentId, version]);

  if (failed) return null;
  if (!data) {
    return <Card><div className={s.center}><Spinner /></div></Card>;
  }
  const points = data.programs.filter((p) => p.percent != null);
  if (!points.length) {
    return (
      <Card>
        <h3 className={s.sectionTitle}>Uyum Geçmişi</h3>
        <p className={s.approvalNote}>
          Henüz tamamlanmış bir program yok — hafta bittikçe burada uyum geçmişi birikir.
        </p>
      </Card>
    );
  }

  const { overall, months, pendingApproval } = data;
  return (
    <Card>
      <h3 className={s.sectionTitle}>Uyum Geçmişi</h3>

      <div className={s.statRow}>
        <Stat
          label="Genel uyum"
          value={overall.percent != null ? `%${overall.percent}` : '—'}
          hint={`${overall.programCount} onaylı hafta`}
        />
        <Stat label="Planlanan çalışma" value={`${overall.studyHours} sa`} hint="onaylı haftalarda" />
        <Stat label="Tamamlanan" value={fmtHours(overall.completedMinutes)} hint="onaylı haftalarda" />
        {pendingApproval > 0 && (
          <Stat label="Onay bekleyen" value={pendingApproval} hint="istatistiğe girmiyor" warn />
        )}
      </div>

      <h4 className={s.chartTitle}>Haftalık uyum</h4>
      <ComplianceLine points={points} />

      {months.length > 0 && (
        <>
          <h4 className={s.chartTitle}>Ay ay uyum <span className={s.chartNote}>(yalnız onaylı haftalar)</span></h4>
          <MonthBars months={months} />
        </>
      )}
    </Card>
  );
}

function Stat({ label, value, hint, warn }) {
  return (
    <div className={cx(s.stat, warn && s.statWarn)}>
      <span className={s.statLabel}>{label}</span>
      <span className={s.statValue}>{value}</span>
      {hint && <span className={s.statHint}>{hint}</span>}
    </div>
  );
}

/** Haftalık uyum çizgisi. Tek seri olduğu için lejant yok — başlık seriyi adlandırıyor.
 *  Onaysız haftalar içi boş nokta (ikincil kodlama), renk tek başına anlam taşımıyor. */
function ComplianceLine({ points }) {
  const W = 720;
  const H = 190;
  const PAD = { top: 12, right: 16, bottom: 26, left: 34 };
  const plotW = W - PAD.left - PAD.right;
  const plotH = H - PAD.top - PAD.bottom;
  const x = (i) => PAD.left + (points.length === 1 ? plotW / 2 : (i / (points.length - 1)) * plotW);
  const y = (v) => PAD.top + plotH - (v / 100) * plotH;
  const path = points.map((p, i) => `${i ? 'L' : 'M'}${x(i)} ${y(p.percent)}`).join(' ');
  const last = points[points.length - 1];

  return (
    <div className={s.chartWrap}>
      <svg className={s.chart} viewBox={`0 0 ${W} ${H}`} role="img"
        aria-label={`Haftalık uyum yüzdesi grafiği, ${points.length} hafta, son hafta yüzde ${last.percent}`}>
        {[0, 50, 100].map((v) => (
          <g key={v}>
            <line className={s.grid} x1={PAD.left} x2={W - PAD.right} y1={y(v)} y2={y(v)} />
            <text className={s.axisLabel} x={PAD.left - 7} y={y(v) + 3.5} textAnchor="end">{v}</text>
          </g>
        ))}
        <path className={s.line} d={path} />
        {points.map((p, i) => (
          <g key={p.id}>
            <circle
              className={p.isApproved ? s.dot : s.dotOpen}
              cx={x(i)} cy={y(p.percent)} r={4.5}
            >
              <title>
                {`${fmtDate(p.startDate)} – ${fmtDate(p.endDate)}\n`}
                {`%${p.percent} uyum · ${fmtHours(p.completedMinutes)} / ${fmtHours(p.totalMinutes)}\n`}
                {p.isApproved ? 'Onaylandı' : 'Onay bekliyor (ortalamaya girmiyor)'}
              </title>
            </circle>
          </g>
        ))}
        {/* Yalnız ilk ve son etiketlenir; her noktaya sayı yazmak grafiği okunmaz yapar. */}
        <text className={s.axisLabel} x={PAD.left} y={H - 8} textAnchor="start">
          {fmtDate(points[0].startDate)}
        </text>
        {points.length > 1 && (
          <text className={s.axisLabel} x={W - PAD.right} y={H - 8} textAnchor="end">
            {fmtDate(last.startDate)}
          </text>
        )}
        <text className={s.pointLabel} x={x(points.length - 1)} y={y(last.percent) - 10} textAnchor="end">
          %{last.percent}
        </text>
      </svg>
      <p className={s.chartNote}>
        İçi dolu nokta onaylanmış haftayı, içi boş nokta onay bekleyeni gösterir.
      </p>
    </div>
  );
}

/** Ay ay uyum — büyüklük karşılaştırması olduğu için çubuk. */
function MonthBars({ months }) {
  return (
    <ul className={s.monthList}>
      {months.map((m) => (
        <li className={s.monthRow} key={m.month}>
          <span className={s.monthName}>{fmtMonth(m.month)}</span>
          <span className={s.monthTrack}>
            <span className={s.monthFill} style={{ width: `${m.percent ?? 0}%` }} />
          </span>
          <span className={s.monthValue}>%{m.percent ?? 0}</span>
          <span className={s.monthHint}>
            {m.programCount} hafta · {m.studyHours} sa
          </span>
        </li>
      ))}
    </ul>
  );
}

/* ---------------- Konu Takibi ---------------- */
const LEVELS = [1, 2, 3, 4, 5];
const LEVEL_COLORS = { 1: '#ef4444', 2: '#f97316', 3: '#eab308', 4: '#4ade80', 5: '#16a34a' };
const LEVEL_LABELS = { 1: 'Çok zayıf', 2: 'Zayıf', 3: 'Orta', 4: 'İyi', 5: 'Çok iyi' };
const colorForAvg = (avg) => LEVEL_COLORS[Math.min(5, Math.max(1, Math.round(avg)))];

/** Bir dersin konuları + seviyelerinden özet metrikler üretir. */
function subjectStats(topics, levels) {
  const n = topics.length;
  if (!n) return { n: 0, avg: 0, done: 0, weak: 0, dist: {}, lowest: null };
  const dist = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 };
  let sum = 0;
  let lowest = null;
  topics.forEach((t) => {
    const lvl = levels[t.id] ?? 1;   // kayıt yoksa 1
    dist[lvl] += 1;
    sum += lvl;
    if (!lowest || lvl < lowest.lvl) lowest = { name: t.name, lvl };
  });
  return {
    n,
    avg: sum / n,
    done: dist[5],
    weak: dist[1] + dist[2],
    dist,
    lowest,
  };
}

const KONU_CAT_LABELS = { tyt: 'TYT Dersleri', ayt: 'AYT Dersleri', okul: 'Dersler' };
const KONU_CAT_ORDER = ['tyt', 'ayt', 'okul'];

// Ders sırası = sınav sırası (alfabetik değil).
const SUBJECT_ORDER = {
  tyt: ['Türkçe', 'Tarih', 'Coğrafya', 'Felsefe', 'Din Kültürü ve Ahlak Bilgisi',
    'Matematik', 'Geometri', 'Fizik', 'Kimya', 'Biyoloji'],
  ayt: ['Türk Dili ve Edebiyatı', 'Tarih-1', 'Coğrafya-1', 'Tarih-2', 'Coğrafya-2',
    'Felsefe', 'Din Kültürü ve Ahlak Bilgisi', 'Matematik', 'Geometri', 'Fizik', 'Kimya', 'Biyoloji'],
  okul: ['Türk Dili ve Edebiyatı', 'Tarih', 'Coğrafya', 'Felsefe', 'Din Kültürü ve Ahlak Bilgisi',
    'Matematik', 'Geometri', 'Fizik', 'Kimya', 'Biyoloji', 'İngilizce'],
};
const subjectOrderIndex = (sub) => {
  const arr = SUBJECT_ORDER[sub.category] || [];
  const i = arr.indexOf(sub.name);
  return i === -1 ? 999 : i;
};

function KonuTakibiTab({ student }) {
  const [subjects, setSubjects] = useState(null);           // görebileceği dersler
  const [topicsBySubject, setTopicsBySubject] = useState({});// { sid: [topics] }
  const [levels, setLevels] = useState({});                 // { topicId: level } (tüm dersler)
  const [selected, setSelected] = useState(null);           // seçili ders id (null = önizleme)
  const [query, setQuery] = useState('');
  const [catFilter, setCatFilter] = useState('all');        // Tümü | tyt | ayt
  const [saving, setSaving] = useState(null);
  const [loading, setLoading] = useState(true);

  // Tüm dersler + konuları + öğrencinin seviyeleri (önizleme metrikleri için tek seferde).
  useEffect(() => {
    let alive = true;
    setLoading(true);
    const params = student.isExam
      ? { curriculum: 'eski' }
      : { grade: student.gradeCode, curriculum: student.curriculum };
    listSubjects().then((all) => {
      const cats = student.isExam ? ['tyt', 'ayt'] : ['okul'];
      const avail = all.filter((x) => cats.includes(x.category));
      return Promise.all([
        Promise.all(avail.map((sub) => listTopics(sub.id, params).then((tp) => [sub.id, tp]))),
        getTopicLevels(student.id),
        Promise.resolve(avail),
      ]);
    }).then(([pairs, lv, avail]) => {
      if (!alive) return;
      setSubjects(avail);
      setTopicsBySubject(Object.fromEntries(pairs));
      setLevels(lv);
      setLoading(false);
    });
    return () => { alive = false; };
  }, [student.id, student.isExam, student.gradeCode, student.curriculum]);

  async function changeLevel(topicId, level) {
    const prev = levels[topicId];
    setLevels((m) => ({ ...m, [topicId]: level }));   // iyimser güncelleme
    setSaving(topicId);
    try {
      await setTopicLevel(student.id, topicId, level);
    } catch {
      setLevels((m) => ({ ...m, [topicId]: prev }));   // hata → geri al
    } finally {
      setSaving(null);
    }
  }

  // Ders başına özet + en geride kalan ders.
  const overview = useMemo(() => {
    if (!subjects) return [];
    return subjects
      .map((sub) => ({ sub, stats: subjectStats(topicsBySubject[sub.id] || [], levels) }))
      .filter((x) => x.stats.n > 0)
      .sort((a, b) => a.stats.avg - b.stats.avg);   // en geride olan başta
  }, [subjects, topicsBySubject, levels]);

  const filtered = useMemo(() => {
    const q = query.trim().toLocaleLowerCase('tr-TR');
    if (!q) return overview;
    return overview.filter((x) => x.sub.label.toLocaleLowerCase('tr-TR').includes(q));
  }, [overview, query]);

  if (loading) return <div className={s.center}><Spinner size={22} /></div>;
  if (!subjects || overview.length === 0) {
    return <Card><EmptyState icon={<Target size={22} />} title="Konu yok" text="Bu öğrenci için konu kataloğu bulunamadı." /></Card>;
  }

  // Detay görünümü (bir ders seçili)
  if (selected != null) {
    const entry = overview.find((x) => String(x.sub.id) === String(selected));
    if (entry) {
      return (
        <KonuDetay
          entry={entry}
          topics={topicsBySubject[selected] || []}
          levels={levels}
          saving={saving}
          onChange={changeLevel}
          onBack={() => setSelected(null)}
        />
      );
    }
  }

  // Önizleme: filtre + arama + kategoriye göre gruplu ders kartları
  const showFilter = student.isExam;   // sınav öğrencisi → TYT + AYT filtresi
  const byFilter = catFilter === 'all' ? filtered : filtered.filter((e) => e.sub.category === catFilter);
  const grouped = KONU_CAT_ORDER
    .map((c) => ({
      cat: c,
      label: KONU_CAT_LABELS[c],
      items: byFilter.filter((e) => e.sub.category === c)
        .sort((a, b) => subjectOrderIndex(a.sub) - subjectOrderIndex(b.sub)),
    }))
    .filter((g) => g.items.length);
  const weakest = byFilter.length
    ? byFilter.reduce((a, b) => (b.stats.avg < a.stats.avg ? b : a))
    : null;

  return (
    <div className={s.stack}>
      <div className={s.konuBar}>
        {showFilter && (
          <PillGroup
            className={s.examFilter}
            options={EXAM_TYPE_FILTERS}
            value={catFilter}
            onChange={setCatFilter}
          />
        )}
        <SearchInput
          className={s.konuSearch}
          placeholder="Ders ara..."
          aria-label="Ders ara"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <LevelLegend />
      </div>

      {!query && weakest && (
        <Card className={s.weakCallout} onClick={() => setSelected(String(weakest.sub.id))}>
          <span className={s.weakIcon}><Target size={18} /></span>
          <div>
            <p className={s.weakLabel}>En geride kalan ders</p>
            <p className={s.weakName}>
              {stripExamPrefix(weakest.sub.label)} · ort. {weakest.stats.avg.toFixed(1)} / 5
            </p>
          </div>
          <ChevronRight size={18} className={s.weakChevron} />
        </Card>
      )}

      {grouped.length === 0 ? (
        <Card><EmptyState icon={<Target size={22} />} title="Sonuç yok" text="Bu aramayla eşleşen ders yok." /></Card>
      ) : (
        grouped.map((g) => (
          <section key={g.cat} className={s.konuSection}>
            {showFilter && <h3 className={s.sectionTitle}>{g.label}</h3>}
            <div className={s.subjectGrid}>
              {g.items.map(({ sub, stats }) => (
                <button
                  key={sub.id}
                  type="button"
                  className={s.subjectCard}
                  onClick={() => setSelected(String(sub.id))}
                >
                  <div className={s.subjectTop}>
                    <span className={s.subjectName}>{stripExamPrefix(sub.label)}</span>
                    <span className={s.subjectAvg} style={{ color: colorForAvg(stats.avg) }}>
                      {stats.avg.toFixed(1)}
                    </span>
                  </div>
                  <ProgressBar value={(stats.avg / 5) * 100} color={colorForAvg(stats.avg)} />
                  <div className={s.subjectMeta}>
                    <span>{stats.n} konu</span>
                    <span>{stats.done} tamam · {stats.weak} zayıf</span>
                  </div>
                </button>
              ))}
            </div>
          </section>
        ))
      )}
    </div>
  );
}

/** Tek dersin konu-seviye editörü + yan istatistik paneli. */
function KonuDetay({ entry, topics, levels, saving, onChange, onBack }) {
  const { sub, stats } = entry;
  return (
    <div className={s.stack}>
      <div className={s.konuBar}>
        <button type="button" className={s.back} onClick={onBack}>
          <ChevronLeft size={16} /> Dersler
        </button>
        <LevelLegend />
      </div>

      <div className={s.konuLayout}>
        <Card className={s.konuCard}>
          <ul className={s.konuList}>
            {topics.map((t) => {
              const lvl = levels[t.id] ?? 1;
              return (
                <li key={t.id} className={s.konuRow}>
                  <span className={s.konuName}>{t.name}</span>
                  <div
                    className={s.dots}
                    role="radiogroup"
                    aria-label={`${t.name} seviyesi`}
                    data-saving={saving === t.id ? '' : undefined}
                  >
                    {LEVELS.map((n) => (
                      <button
                        key={n}
                        type="button"
                        role="radio"
                        aria-checked={lvl === n}
                        title={`${n} — ${LEVEL_LABELS[n]}`}
                        className={s.dot}
                        onClick={() => onChange(t.id, n)}
                        style={n <= lvl ? { background: LEVEL_COLORS[lvl], borderColor: LEVEL_COLORS[lvl] } : undefined}
                      />
                    ))}
                  </div>
                </li>
              );
            })}
          </ul>
        </Card>

        <aside className={s.konuInfo}>
          <h3 className={s.infoSubject}>{sub.label}</h3>

          <div className={s.infoStat}>
            <span className={s.infoBig} style={{ color: colorForAvg(stats.avg) }}>
              {stats.avg.toFixed(1)}
            </span>
            <span className={s.infoBigUnit}>/ 5 ort. seviye</span>
          </div>

          <div className={s.infoRow}>
            <span className={s.infoRowLabel}>Konu sayısı</span>
            <span className={s.infoRowValue}>{stats.n}</span>
          </div>
          <div className={s.infoRow}>
            <span className={s.infoRowLabel}>Tam hâkim (sv. 5)</span>
            <span className={s.infoRowValue}>{stats.done}</span>
          </div>
          <div className={s.infoRow}>
            <span className={s.infoRowLabel}>Zayıf (sv. ≤2)</span>
            <span className={s.infoRowValue}>{stats.weak}</span>
          </div>
          {stats.lowest && (
            <div className={s.infoRow}>
              <span className={s.infoRowLabel}>En geri konu</span>
              <span className={s.infoRowValue} title={stats.lowest.name}>{stats.lowest.name}</span>
            </div>
          )}

          <div className={s.infoDist}>
            <span className={s.infoDistLabel}>Seviye dağılımı</span>
            {LEVELS.map((n) => (
              <div className={s.infoDistRow} key={n}>
                <span className={s.infoDistNum} style={{ color: LEVEL_COLORS[n] }}>{n}</span>
                <div className={s.infoDistTrack}>
                  <div
                    className={s.infoDistFill}
                    style={{ width: `${stats.n ? (stats.dist[n] / stats.n) * 100 : 0}%`, background: LEVEL_COLORS[n] }}
                  />
                </div>
                <span className={s.infoDistCount}>{stats.dist[n]}</span>
              </div>
            ))}
          </div>
        </aside>
      </div>
    </div>
  );
}

function LevelLegend() {
  return (
    <div className={s.legend}>
      {LEVELS.map((n) => (
        <span key={n} className={s.legendItem} title={LEVEL_LABELS[n]}>
          <span className={s.legendDot} style={{ background: LEVEL_COLORS[n] }} />
          {n}
        </span>
      ))}
    </div>
  );
}
