import { delay } from './mockDelay';
import {
  getStudentProgram, persistStudentSchedule, mondayOf, today, DEFAULT_DAY_COUNT,
} from './programs';

// Öğrenci seçilmeden hazırlanan "genel" tahta bir taslaktır: oturum içinde tutulur,
// kalıcılığı şablon olarak kaydedilerek sağlanır (api/templates.js). Öğrenciye özel
// mod gerçek /api/programs/'a bağlanır (programs.js).
//
// Genel tahtanın penceresi bu haftanın Pazartesi'sinden başlar: şablonlar hafta
// gününe göre saklandığından, Pazartesi başlangıçlı bir pencerede gün indeksi ile
// hafta günü birebir örtüşür ve kaydedilen şablon beklenen günlere oturur.
const store = new Map();
const generalWindow = { startDate: mondayOf(today()), dayCount: DEFAULT_DAY_COUNT };

export async function getSchedule(scope) {
  // scope bir öğrenci id ise gerçek program; değilse (genel) oturum-içi taslak.
  if (scope) return getStudentProgram(scope);
  await delay();
  if (!store.has('genel')) store.set('genel', []);
  return { programId: null, ...generalWindow, blocks: store.get('genel') };
}

export async function saveSchedule(scope, blocks, win) {
  if (scope) return persistStudentSchedule(scope, blocks, win);
  await delay(60);
  store.set('genel', blocks);
  return blocks;
}

/** Genel taslağın penceresini değiştirir (öğrenci modunda program PATCH'lenir). */
export function setGeneralWindow({ startDate, dayCount }) {
  if (startDate) generalWindow.startDate = startDate;
  if (dayCount) generalWindow.dayCount = dayCount;
  return { ...generalWindow };
}
