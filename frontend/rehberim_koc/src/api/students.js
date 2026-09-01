/* Öğrenci listesi gerçek backend'e bağlı (GET /api/students/, yalnızca rehber).
   Backend yalnızca kimlik alanlarını döndürür; net/uyum/tamamlanma gibi metrikler
   henüz backend'de üretilmiyor, bu yüzden yer tutucu (null/boş) veriliyor. */
import api from './client';
import { colorFor } from '../components/ui/avatarUtils';

/** Backend öğrenci kaydını ekranların beklediği şekle çevirir.
    Metrik alanları backend'de yok → null/boş (UI "—" gösterir). */
function adaptStudent(s) {
  // 12. sınıf ve mezun → sınav öğrencisi (TYT/AYT dersleri, 'eski' müfredat);
  // 9/10/11 → okul dersleri, 'maarif' müfredat. (Backend Student modeliyle aynı kural.)
  const isExam = s.grade === '12' || s.grade === 'mezun';
  return {
    id: s.id,
    name: s.full_name,
    grade: s.grade_display,
    gradeCode: s.grade,                 // '9'..'12' | 'mezun' (ham değer)
    isExam,
    curriculum: isExam ? 'eski' : 'maarif',
    study_field: s.study_field,
    color: colorFor(s.full_name),
    lastNet: null,
    compliance: null,
    completion: null,
    trend: null,
    lastMeeting: null,
    nextMeeting: null,
    examHistory: [],
    subjects: {},
  };
}

export async function listStudents() {
  const { data } = await api.get('/students/');
  return data.map(adaptStudent);
}

export async function getStudent(id) {
  const list = await listStudents();
  return list.find((x) => x.id === Number(id)) ?? null;
}
