/* Konu Takibi — gerçek backend (/api/topic-progress/).
   Rehber, öğrencisinin her konusuna 1-5 hâkimiyet seviyesi girer/düzenler.
   Kayıt yoksa seviye kavramsal olarak 1'dir (backend satırları önceden üretmez). */
import api from './client';

/** GET /api/topic-progress/?student=<id>[&subject=<id>] → { topicId: level }.
 *  subjectId verilmezse öğrencinin TÜM derslerindeki seviyeler döner. */
export async function getTopicLevels(studentId, subjectId) {
  const params = { student: studentId };
  if (subjectId) params.subject = subjectId;
  const { data } = await api.get('/topic-progress/', { params });
  const byTopic = {};
  data.forEach((p) => { byTopic[p.topic] = p.level; });
  return byTopic;
}

/** POST /api/topic-progress/ (upsert) → rehber, öğrencisi için seviye yazar/günceller. */
export async function setTopicLevel(studentId, topicId, level) {
  const { data } = await api.post('/topic-progress/', {
    student: Number(studentId),
    topic: topicId,
    level,
  });
  return data;
}
