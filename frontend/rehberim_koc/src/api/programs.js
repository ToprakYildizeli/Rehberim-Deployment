/* Öğrenciye özel Ders Programı — gerçek backend (/api/programs/ + /api/tasks/).

   Program penceresi esnektir: `start_date` + `day_count` (varsayılan 7). Tahtanın
   sütunları pencerenin günleridir, bu yüzden bloklar hafta günüyle değil **gün
   indeksiyle** (0 = pencerenin ilk günü) tutulur — 7 günden uzun pencerelerde
   hafta günü tekrar edeceği için tek başına ayırt edici olmaz. */
import api from './client';
import { blockColor } from './catalog';

const pad2 = (n) => String(n).padStart(2, '0');

export const isoDate = (d) => `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`;
export const parseDate = (str) => {
  const [y, m, d] = str.split('-').map(Number);
  return new Date(y, m - 1, d);
};
export const today = () => isoDate(new Date());
export const addDays = (str, n) => {
  const d = parseDate(str);
  d.setDate(d.getDate() + n);
  return isoDate(d);
};
export const daysBetween = (from, to) =>
  Math.round((parseDate(to) - parseDate(from)) / 86400000);
/** JS getDay() (Paz=0..Cmt=6) → backend weekday (Pzt=0..Paz=6). */
export const weekdayOf = (str) => (parseDate(str).getDay() + 6) % 7;
/** Verilen tarihi içeren haftanın Pazartesi'si. */
export const mondayOf = (str) => addDays(str, -weekdayOf(str));

const DAY_SHORT = ['Pzt', 'Sal', 'Çar', 'Per', 'Cum', 'Cmt', 'Paz'];
const MONTH_SHORT = ['Oca', 'Şub', 'Mar', 'Nis', 'May', 'Haz', 'Tem', 'Ağu', 'Eyl', 'Eki', 'Kas', 'Ara'];

export const DEFAULT_DAY_COUNT = 7;

/** Pencerenin sütunları: [{ index, date, weekday, short, dayNum, monthShort }] */
export function windowDays(startDate, dayCount) {
  return Array.from({ length: Math.max(1, dayCount) }, (_, index) => {
    const date = addDays(startDate, index);
    const d = parseDate(date);
    return {
      index,
      date,
      weekday: weekdayOf(date),
      short: DAY_SHORT[weekdayOf(date)],
      dayNum: d.getDate(),
      monthShort: MONTH_SHORT[d.getMonth()],
    };
  });
}

/** "25 Ağu – 29 Ağu" biçiminde pencere aralığı (özet metinleri için). */
export function windowRangeText(startDate, dayCount) {
  const days = windowDays(startDate, dayCount);
  const first = days[0];
  const last = days[days.length - 1];
  return `${first.dayNum} ${first.monthShort} – ${last.dayNum} ${last.monthShort}`;
}

/** Süreler ve başlangıçlar tahtada **dakika** cinsinden tutulur: rehber 20 dk gibi
 *  serbest süreler girebildiği için saat cinsinden kesirli sayı tutmak yuvarlama
 *  hatası üretirdi. `startMin` = gece yarısından beri geçen dakika. */
export const SLOT_MIN = 15;                       // tahtanın çözünürlüğü
export const minutesOf = (t) =>
  (t ? parseInt(t.slice(0, 2), 10) * 60 + parseInt(t.slice(3, 5), 10) : 0);
export const fmtMin = (m) => `${pad2(Math.floor(m / 60))}:${pad2(m % 60)}`;

/** Haftalık toplamı saate çevirir: 255 → "4,25 saat".
 *  Tek blokların süresi dakika olarak gösterilir; yalnız toplamlarda saat kullanılır. */
export function fmtHours(min) {
  const h = min / 60;
  return `${(Math.round(h * 100) / 100).toString().replace('.', ',')} saat`;
}

/** Backend Task → board bloğu (denormalize gösterim alanlarıyla). */
function mapTaskToBlock(task, startDate) {
  const b = {
    id: `t${task.id}`,
    taskId: task.id,
    dayIndex: daysBetween(startDate, task.date),
    startMin: minutesOf(task.start_time),
    durationMin: task.duration_minutes || 60,
    kind: task.kind || 'study',
    examScope: task.exam_scope || '',
    countsAsStudy: task.counts_as_study !== false,
    subject: task.subject != null ? String(task.subject) : '',
    subjectLabel: task.subject_label,
    type: task.task_type != null ? String(task.task_type) : '',
    typeName: task.task_type_name,
    topic: task.title || '',
    book: task.book != null ? task.book : null,
    bookLabel: task.book_label || null,
    isCompleted: !!task.is_completed,
  };
  return { ...b, subjectColor: blockColor(b) };
}

/** Board bloğu → backend Task gövdesi. Dış bloklarda ders/metod/kitap gitmez. */
export function blockToTaskPayload(b, startDate) {
  const isExternal = b.kind === 'external';
  return {
    kind: b.kind || 'study',
    exam_scope: b.examScope || '',
    subject: !isExternal && b.subject ? Number(b.subject) : null,
    task_type: !isExternal && b.type ? Number(b.type) : null,
    book: !isExternal && b.book ? Number(b.book) : null,
    title: b.topic || '',
    date: addDays(startDate, b.dayIndex),
    start_time: fmtMin(b.startMin),
    duration_minutes: b.durationMin,
  };
}

/** Board bloklarının çalışma süresi (dk) — dış meşguliyetler sayılmaz. */
export function studyMinutes(blocks) {
  return (blocks || []).reduce((sum, b) => (b.kind === 'external' ? sum : sum + b.durationMin), 0);
}

/** Dış meşguliyet bloklarının toplamı (dk; ayrı gösterilir). */
export function externalMinutes(blocks) {
  return (blocks || []).reduce((sum, b) => (b.kind === 'external' ? sum + b.durationMin : sum), 0);
}

// Diff için scope başına son yüklenen durum: { programId, startDate, dayCount, blocks }
const cache = new Map();

function programToEntry(program) {
  const startDate = program ? program.start_date : today();
  const dayCount = program ? program.day_count || DEFAULT_DAY_COUNT : DEFAULT_DAY_COUNT;
  return {
    programId: program ? program.id : null,
    startDate,
    dayCount,
    blocks: program ? program.tasks.map((t) => mapTaskToBlock(t, startDate)) : [],
  };
}

/** Öğrencinin güncel programını pencere + bloklar olarak döndürür. */
export async function getStudentProgram(studentId) {
  const { data } = await api.get('/programs/');
  const now = today();
  const mine = data
    .filter((p) => String(p.student) === String(studentId))
    .sort((a, b) => (a.start_date < b.start_date ? 1 : -1));
  const current = mine.find((p) => p.start_date <= now && now <= p.end_date) || mine[0] || null;

  const entry = programToEntry(current);
  cache.set(String(studentId), entry);
  // Referans kopyası döndür (board mutasyonu cache'i bozmasın)
  return { ...entry, blocks: entry.blocks.map((b) => ({ ...b })) };
}

/** Öğrencinin TÜM programlarını (geçmiş dahil) salt-okunur döndürür.
 *  Detay sayfasının "Ders Programı" sekmesi için; en yeni başta sıralı. */
export async function getStudentPrograms(studentId) {
  const { data } = await api.get('/programs/');
  const now = today();
  return data
    .filter((p) => String(p.student) === String(studentId))
    .sort((a, b) => (a.start_date < b.start_date ? 1 : -1))
    .map((p) => ({
      id: p.id,
      startDate: p.start_date,
      endDate: p.end_date,
      dayCount: p.day_count || DEFAULT_DAY_COUNT,
      isCurrent: p.start_date <= now && now <= p.end_date,
      // Haftalık onay (B1): onay ancak pencere kapandıktan sonra verilebilir.
      isApproved: !!p.is_approved,
      isFinished: !!p.is_finished,
      approvedAt: p.approved_at || null,
      approvedByName: p.approved_by_name || null,
      // Uyum özeti (B2) sunucudan gelir — süre üzerinden hesaplanır, tarayıcıda tekrar
      // hesaplanmaz ki panel, öğrenci sayfası ve veli aynı sayıyı görsün.
      compliance: mapCompliance(p.compliance),
      blocks: (p.tasks || []).map((t) => mapTaskToBlock(t, p.start_date)),
    }));
}

/** Backend uyum özeti → kamelCase. Boş programda `percent` null gelir. */
function mapCompliance(c) {
  if (!c) return null;
  return {
    percent: c.percent,
    basis: c.basis,                        // 'duration' | 'count' | 'empty'
    totalMinutes: c.total_minutes,
    completedMinutes: c.completed_minutes,
    totalTasks: c.total_tasks,
    completedTasks: c.completed_tasks,
    studyHours: c.study_hours,
    weeklyHours: c.weekly_hours,
  };
}

/** Öğrencinin uyum geçmişi (B2): bitmiş haftaların serisi + ay ay ve genel özet.
 *  Aylık/genel özet yalnız **onaylanmış** haftalardan çıkar (B1'in güven modeli). */
export async function getComplianceHistory(studentId) {
  const { data } = await api.get('/programs/compliance/', {
    params: studentId ? { student: studentId } : undefined,
  });
  const sum = (o) => ({
    percent: o.percent,
    studyHours: o.study_hours,
    programCount: o.program_count,
    totalMinutes: o.total_minutes,
    completedMinutes: o.completed_minutes,
  });
  return {
    pendingApproval: data.pending_approval,
    programs: (data.programs || []).map((p) => ({
      id: p.id,
      startDate: p.start_date,
      endDate: p.end_date,
      dayCount: p.day_count,
      isApproved: p.is_approved,
      ...mapCompliance(p),
    })),
    months: (data.months || []).map((m) => ({ month: m.month, ...sum(m) })),
    overall: sum(data.overall || {}),
  };
}

/** Bir görevi tamamlandı/tamamlanmadı işaretler (rehber, onay öncesi düzeltme). */
export async function setTaskCompleted(taskId, isCompleted) {
  const { data } = await api.patch(`/tasks/${taskId}/`, { is_completed: isCompleted });
  return !!data.is_completed;
}

/** Tek programın güncel uyum özetini çeker — görev işaretlendikten sonra yüzdeyi
 *  tarayıcıda yeniden hesaplamak yerine sunucudan almak için. */
export async function getProgramCompliance(programId) {
  const { data } = await api.get(`/programs/${programId}/`);
  return mapCompliance(data.compliance);
}

/** Haftalık onay (B1). `approved=false` onayı geri alır. Backend program objesi döner. */
export async function setProgramApproval(programId, approved) {
  const url = `/programs/${programId}/approve/`;
  const { data } = approved ? await api.post(url) : await api.delete(url);
  return {
    isApproved: !!data.is_approved,
    isFinished: !!data.is_finished,
    approvedAt: data.approved_at || null,
    approvedByName: data.approved_by_name || null,
    compliance: mapCompliance(data.compliance),
  };
}

/** Atama için önerilen başlangıç: öğrenciye program atanmamış ilk gün.
 *  Backend `first_free_day` ile aynı kural (son programın bitişinden sonraki gün,
 *  geçmişte kalıyorsa bugün). */
export async function suggestNextWeekStart(studentId) {
  const progs = await getStudentPrograms(studentId);   // en yeni başta
  const now = today();
  if (!progs.length) return now;
  const next = addDays(progs[0].endDate, 1);
  return next < now ? now : next;
}

/** Mevcut programın penceresini değiştirir (başlangıç ve/veya gün sayısı).
 *  Backend örtüşen aralığı reddeder; hata çağırana yükselir. */
export async function updateProgramWindow(programId, { startDate, dayCount }) {
  const body = {};
  if (startDate) body.start_date = startDate;
  if (dayCount) body.day_count = dayCount;
  const { data } = await api.patch(`/programs/${programId}/`, body);
  const key = [...cache.entries()].find(([, e]) => e.programId === programId)?.[0];
  if (key) cache.set(key, programToEntry(data));
  return data;
}

/** Board değişikliklerini backend'e yazar; reconcile edilmiş blokları döndürür.
 *  `win` = { startDate, dayCount } — program yoksa bu pencerede oluşturulur. */
export async function persistStudentSchedule(studentId, nextBlocks, win) {
  const key = String(studentId);
  const entry = cache.get(key)
    || { programId: null, startDate: win.startDate, dayCount: win.dayCount, blocks: [] };
  const prevById = new Map(entry.blocks.map((b) => [b.id, b]));

  // Program yoksa ve eklenen blok varsa önce oluştur.
  let { programId } = entry;
  if (programId == null && nextBlocks.length > 0) {
    const { data } = await api.post('/programs/', {
      student: Number(studentId),
      start_date: win.startDate,
      day_count: win.dayCount,
      schedule_type: 'timed',
    });
    programId = data.id;
    entry.programId = data.id;
    entry.startDate = data.start_date;
    entry.dayCount = data.day_count;
  }
  const startDate = entry.startDate;

  const changed = (a, b) =>
    a.dayIndex !== b.dayIndex || a.startMin !== b.startMin || a.durationMin !== b.durationMin ||
    a.subject !== b.subject || a.type !== b.type || a.topic !== b.topic ||
    a.book !== b.book || a.kind !== b.kind || a.examScope !== b.examScope;

  const nextIds = new Set(nextBlocks.map((b) => b.id));
  // Silinenler
  const deletes = entry.blocks
    .filter((b) => b.taskId && !nextIds.has(b.id))
    .map((b) => api.delete(`/tasks/${b.taskId}/`));

  // Ekle / güncelle
  const result = [];
  const ops = nextBlocks.map(async (b) => {
    if (!b.taskId) {
      const { data } = await api.post(`/programs/${programId}/tasks/`, blockToTaskPayload(b, startDate));
      result.push(mapTaskToBlock(data, startDate));
    } else {
      const prev = prevById.get(b.id);
      if (prev && changed(prev, b)) {
        const { data } = await api.patch(`/tasks/${b.taskId}/`, blockToTaskPayload(b, startDate));
        result.push(mapTaskToBlock(data, startDate));
      } else {
        result.push(b);
      }
    }
  });

  await Promise.all([...deletes, ...ops]);
  entry.blocks = result.map((b) => ({ ...b }));
  cache.set(key, entry);
  return result;
}
