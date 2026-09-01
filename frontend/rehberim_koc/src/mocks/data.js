/* Ders Programı tahtasının sabitleri — gün ve saat ekseni, ders renkleri.
   Burası eskiden mock fixture'lardı; ekranların hepsi backend'e bağlandıktan
   sonra geriye yalnızca bu sabitler kaldı. Ders/metod/konu katalogları artık
   backend'den gelir (api/catalog.js → /subjects/, /task-types/, /topics/). */

export const SUBJECTS = [
  { id: 'matematik', name: 'Matematik', color: 'var(--subj-matematik)' },
  { id: 'turkce', name: 'Türkçe', color: 'var(--subj-turkce)' },
  { id: 'fizik', name: 'Fizik', color: 'var(--subj-fizik)' },
  { id: 'geometri', name: 'Geometri', color: 'var(--subj-geometri)' },
  { id: 'kimya', name: 'Kimya', color: 'var(--subj-kimya)' },
  { id: 'biyoloji', name: 'Biyoloji', color: 'var(--subj-biyoloji)' },
  { id: 'genel', name: 'Genel Çalışma', color: 'var(--subj-genel)' },
];

export const SUBJECT_MAP = Object.fromEntries(SUBJECTS.map((x) => [x.id, x]));

export const DAYS = [
  { id: 'pzt', short: 'Pzt', name: 'Pazartesi' },
  { id: 'sal', short: 'Sal', name: 'Salı' },
  { id: 'car', short: 'Çar', name: 'Çarşamba' },
  { id: 'per', short: 'Per', name: 'Perşembe' },
  { id: 'cum', short: 'Cum', name: 'Cuma' },
  { id: 'cmt', short: 'Cmt', name: 'Cumartesi' },
  { id: 'paz', short: 'Paz', name: 'Pazar' },
];

/** Tahtanın saat ekseni: 07:00 → 22:00. */
export const HOURS = Array.from({ length: 16 }, (_, i) => i + 7);
