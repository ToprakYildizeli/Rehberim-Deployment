/* Öğrencinin denemeleri — gerçek backend (GET /api/exams/?student=<id>).
   Rehber salt-okur; öğrenci detay sayfasının "Denemeler" sekmesini besler. */
import api from './client';

const EXAM_TYPE_LABEL = { tyt: 'TYT', ayt: 'AYT' };

/** Backend deneme kaydını ekranın beklediği şekle çevirir. */
function adaptExam(e) {
  return {
    id: e.id,
    type: e.exam_type || '',
    typeLabel: EXAM_TYPE_LABEL[e.exam_type] || '',
    name: e.name || '',
    date: e.exam_date,
    totalNet: e.total_net,
    subjectNets: (e.subject_nets || []).map((n) => ({
      id: n.id,
      subject: n.subject,              // ders id (katalogla eşleştirmek için)
      subjectLabel: n.subject_label,
      correct: n.correct ?? 0,         // doğru
      wrong: n.wrong ?? 0,             // yanlış
      blank: n.blank,                  // boş = soru - doğru - yanlış (yoksa null)
      net: n.net,                      // net = doğru - yanlış/4
      max: n.question_count || null,   // dersin soru sayısı; yoksa null
    })),
  };
}

/** GET /api/exams/?student=<id> → öğrencinin denemeleri, en yeni başta. */
export async function listStudentExams(studentId) {
  const { data } = await api.get('/exams/', { params: { student: studentId } });
  return data
    .map(adaptExam)
    .sort((a, b) => (a.date < b.date ? 1 : -1));
}
