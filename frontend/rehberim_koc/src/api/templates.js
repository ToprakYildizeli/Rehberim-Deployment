/* Program şablonları + atama — gerçek backend (/api/program-templates/, /api/programs/assign/).
   Şablon: rehberin isimli, tekrar kullanılabilir genel programı (öğrenci/tarih bağımsız,
   görevler haftanın gününe göre). Atama: bir planı öğrencinin programına yazar.

   Tahta pencere gün indeksiyle çalışır, şablon ise hafta günüyle (weekday 0-6);
   çeviri iki yönde de pencerenin başlangıç tarihine göre yapılır. Pencereye
   düşmeyen şablon günleri backend'de olduğu gibi burada da atlanır. */
import api from './client';
import { blockColor } from './catalog';
import { weekdayOf, addDays, fmtMin, minutesOf, DEFAULT_DAY_COUNT } from './programs';

/** Board bloğu → şablon/atama görevi (gün indeksi → weekday). */
function blockToTask(b, startDate) {
  const isExternal = b.kind === 'external';
  return {
    kind: b.kind || 'study',
    exam_scope: b.examScope || '',
    subject: !isExternal && b.subject ? Number(b.subject) : null,
    task_type: !isExternal && b.type ? Number(b.type) : null,
    book: !isExternal && b.book ? Number(b.book) : null,
    title: b.topic || '',
    weekday: weekdayOf(addDays(startDate, b.dayIndex)),
    start_time: fmtMin(b.startMin),
    duration_minutes: b.durationMin,
    order: 0,
  };
}

const toTasks = (blocks, startDate) => blocks.map((b) => blockToTask(b, startDate));

/** Şablon görevleri → board blokları. Görevin haftagünü pencerede hangi indekse
 *  düşüyorsa oraya konur; pencereye sığmayanlar atlanır (backend ile aynı kural).
 *  `{ blocks, skipped }` döner ki arayüz düşen görevleri kullanıcıya söyleyebilsin. */
export function templateToBlocks(tpl, startDate, dayCount = DEFAULT_DAY_COUNT) {
  const startWeekday = weekdayOf(startDate);
  const blocks = [];
  let skipped = 0;
  (tpl.tasks || []).forEach((t, i) => {
    const dayIndex = (t.weekday - startWeekday + 7) % 7;
    if (dayIndex >= dayCount) { skipped += 1; return; }
    const b = {
      id: `tpl${t.id}-${i}`,
      dayIndex,
      startMin: t.start_time ? minutesOf(t.start_time) : 8 * 60,
      durationMin: t.duration_minutes || 60,
      kind: t.kind || 'study',
      examScope: t.exam_scope || '',
      subject: t.subject != null ? String(t.subject) : '',
      subjectLabel: t.subject_label,
      type: t.task_type != null ? String(t.task_type) : '',
      typeName: t.task_type_name,
      topic: t.title || '',
      book: t.book != null ? t.book : null,
      bookLabel: t.book_label || null,
    };
    blocks.push({ ...b, subjectColor: blockColor(b) });
  });
  return { blocks, skipped };
}

export async function listTemplates() {
  const { data } = await api.get('/program-templates/');
  return data; // [{ id, name, schedule_type, tasks }]
}

export async function createTemplate(name, blocks, startDate, scheduleType = 'timed') {
  const { data } = await api.post('/program-templates/', {
    name,
    schedule_type: scheduleType,
    tasks: toTasks(blocks, startDate),
  });
  return data;
}

/** Mevcut şablonu (aynı obje) günceller — adı korunur, görevler değişir. */
export async function updateTemplate(id, name, blocks, startDate, scheduleType = 'timed') {
  const { data } = await api.patch(`/program-templates/${id}/`, {
    name,
    schedule_type: scheduleType,
    tasks: toTasks(blocks, startDate),
  });
  return data;
}

export async function deleteTemplate(id) {
  await api.delete(`/program-templates/${id}/`);
}

/** Şablonu bir öğrencinin rutini yapar: yeni hafta açıldığında görevleri
 *  kendiliğinden o haftaya düşer. Öğrenci başına tek rutin olabilir. */
export async function setRoutine(id, studentId) {
  const { data } = await api.patch(`/program-templates/${id}/`, {
    student: Number(studentId),
    auto_apply: true,
  });
  return data;
}

/** Rutini kapatır; şablon genel şablon olarak kalır. */
export async function clearRoutine(id) {
  const { data } = await api.patch(`/program-templates/${id}/`, {
    student: null,
    auto_apply: false,
  });
  return data;
}

/** Board'daki planı öğrenciye atar. Bloklar tahtanın penceresine (`boardStart`)
 *  göre weekday'e çevrilir; hedef pencere `startDate` + `dayCount` ile verilir.
 *  Hedef aralık mevcut bir programla örtüşürse backend 400 döner. */
export async function assignBoard(studentId, blocks, boardStart, { startDate, dayCount } = {}) {
  const body = { student: Number(studentId), tasks: toTasks(blocks, boardStart) };
  if (startDate) body.start_date = startDate;
  if (dayCount) body.day_count = dayCount;
  const { data } = await api.post('/programs/assign/', body);
  return data;
}

/** Kayıtlı şablonu doğrudan öğrenciye atar. */
export async function assignTemplate(templateId, studentId, { startDate, dayCount } = {}) {
  const body = { student: Number(studentId), template: templateId };
  if (startDate) body.start_date = startDate;
  if (dayCount) body.day_count = dayCount;
  const { data } = await api.post('/programs/assign/', body);
  return data;
}
