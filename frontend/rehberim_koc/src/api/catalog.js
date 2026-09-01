/* Referans katalogları — gerçek backend'den (serbest metin/hardcoded yerine).
   Ders Programı bloklarının ders/metod/konu seçimlerini besler. */
import api from './client';

/** Blok türleri (backend `Task.kind`). Dış bloklar çalışma saatine sayılmaz. */
export const BLOCK_KINDS = [
  { value: 'study', label: 'Çalışma' },
  { value: 'external', label: 'Dış' },
  { value: 'exam', label: 'Deneme' },
];

/** Genel deneme kapsamı (backend `Task.exam_scope`) — ders seçilmeden. */
export const EXAM_SCOPES = [
  { value: 'tyt', label: 'Genel TYT' },
  { value: 'ayt', label: 'Genel AYT' },
];

const EXAM_SCOPE_LABEL = Object.fromEntries(EXAM_SCOPES.map((x) => [x.value, x.label]));

/** Blokta gösterilecek ad: dış blokta başlık, genel denemede kapsam, yoksa ders. */
export function blockLabel(b) {
  if (b.kind === 'external') return b.topic || 'Dış meşguliyet';
  if (b.examScope) return EXAM_SCOPE_LABEL[b.examScope] || 'Genel Deneme';
  return b.subjectLabel || '—';
}

/** Blok rengi: dış bloklar nötr, genel denemeler mor, çalışma blokları dersin rengi. */
export function blockColor(b) {
  if (b.kind === 'external') return 'var(--text-muted)';
  if (b.examScope) return 'var(--violet)';
  return subjectColor(b.subjectLabel || '');
}

/** Ders adından programdaki blok rengini üretir (mevcut --subj-* CSS değişkenleri). */
export function subjectColor(name = '') {
  const n = name.toLocaleLowerCase('tr-TR');
  if (n.includes('matemat')) return 'var(--subj-matematik)';
  if (n.includes('türkçe') || n.includes('edebiyat') || n.includes('türk dili')) return 'var(--subj-turkce)';
  if (n.includes('fizik')) return 'var(--subj-fizik)';
  if (n.includes('kimya')) return 'var(--subj-kimya)';
  if (n.includes('biyoloji')) return 'var(--subj-biyoloji)';
  if (n.includes('geometri')) return 'var(--subj-geometri)';
  return 'var(--subj-genel)';
}

/** GET /api/subjects/ → [{ id, name, label, category, color }] (33 gerçek ders). */
export async function listSubjects(params) {
  const { data } = await api.get('/subjects/', params ? { params } : undefined);
  return data.map((x) => ({
    id: x.id,
    name: x.name,
    label: x.label,        // "TYT Matematik" gibi gösterim etiketi
    category: x.category,
    questionCount: x.question_count ?? 0,   // sınavdaki soru sayısı (maks. net)
    color: subjectColor(x.label || x.name),
  }));
}

/** Öğrencinin **alanına düşen** dersler: tüm TYT + alanının AYT dersleri.
 *  Ders satırlı tahtanın varsayılan satırlarını açmak için — kısıt değil, başlangıç
 *  kümesi; kullanıcı satır ekleyip çıkarabilir. Alan→AYT eşlemesi backend'de. */
export async function listFieldSubjects(studentId) {
  return listSubjects(studentId ? { student: studentId, scope: 'field' } : { scope: 'field' });
}

/** GET /api/task-types/ → [{ id, name }] (çalışma metodları). */
export async function listTaskTypes() {
  const { data } = await api.get('/task-types/');
  return data.map((x) => ({ id: x.id, name: x.name }));
}

/** GET /api/topics/?subject=<id>[&grade=&curriculum=] → dersin konu kataloğu.
 *  Ders Programı yalnızca `subjectId` verir ({ id, name } yeterli). Konu Takibi
 *  ayrıca grade/curriculum geçip sıralı tam objeyi kullanır. */
export async function listTopics(subjectId, { grade, curriculum } = {}) {
  if (!subjectId) return [];
  const params = { subject: subjectId };
  if (grade) params.grade = grade;
  if (curriculum) params.curriculum = curriculum;
  const { data } = await api.get('/topics/', { params });
  return data.map((x) => ({ id: x.id, name: x.name, grade: x.grade, order: x.order }));
}

/** GET /api/block-durations/ → rehberin süre hafızası.
 *
 *  Hafıza **rehber özelinde**dir: bir kombinasyona bir öğrencide 20 dk denildiyse
 *  başka öğrencide de 20 dk varsayılan gelir. Anahtar (ders, metod, konu) üçlüsü —
 *  "Matematik denemesi 1 saat" demek "Matematik soru çözümü 1 saat" demek değildir.
 *  Yazma ucu yoktur; hafıza blok kaydedilirken backend'de kendiliğinden güncellenir.
 *
 *  Dönen değer, doğrudan aranabilen bir Map: `durationKey(...)` → dakika. */
export async function loadDurationMemory() {
  const { data } = await api.get('/block-durations/');
  return new Map(
    (data || []).map((x) => [durationKey(x.subject, x.task_type, x.topic), x.duration_minutes]),
  );
}

/** Süre hafızası anahtarı. Boş konu geçerli bir anahtardır (konusuz blok da bir
 *  kombinasyondur); id'ler string'e çevrilir çünkü form alanları string tutar. */
export function durationKey(subject, taskType, topic) {
  return `${subject ?? ''}|${taskType ?? ''}|${(topic || '').trim()}`;
}

/** GET /api/books/?student=<id> → öğrencinin kütüphanesi. Ders Programı'nda
 *  doğrudan sürüklenip blok yapılabilir kitaplar (kaynak = kitap). */
export async function listBooks(studentId) {
  if (!studentId) return [];
  const { data } = await api.get('/books/', { params: { student: studentId } });
  return data.map((b) => ({
    id: b.id,
    kind: b.kind,                       // 'ders' | 'okuma'
    label: b.label,                     // "TYT Matematik 345 Yay. Soru Bankası" / okuma başlığı
    subject: b.subject != null ? String(b.subject) : '',
    subjectLabel: b.subject_label,      // "TYT Matematik" (okuma kitabında null)
    bookFormat: b.book_format,          // 'soru_bankasi' | 'konu_anlatimi' | 'paragraf' | 'deneme'
    color: subjectColor(b.subject_label || b.label),
  }));
}
