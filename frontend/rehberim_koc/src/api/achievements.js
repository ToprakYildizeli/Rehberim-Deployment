/* Başarımlar (C3). Tanımlar **rehbere** aittir ve Ayarlar'dan düzenlenebilir;
   öğrencinin durumu sunucuda anlık hesaplanır (saklanmaz), böylece eşik değişince
   ya da bir deneme silinince kayıtla gerçek arasında tutarsızlık kalmaz. */
import api from './client';

const adapt = (a) => ({
  id: a.id,
  name: a.name,
  description: a.description,
  metric: a.metric,               // 'exam_net' | 'topic_completion' | 'compliance'
  metricLabel: a.metric_display,
  scope: a.scope,                 // exam_net'te 'tyt' | 'ayt', diğerlerinde ''
  threshold: a.threshold,
  value: a.value,                 // öğrencinin ham değeri (null = veri yok)
  earned: !!a.earned,
  progress: a.progress,           // eşiğin yüzde kaçı (kazanıldıysa 100)
});

/** Bir öğrencinin başarım durumu. Kazanılanlar önce, sonra eşiğe en yakınlar. */
export async function getStudentAchievements(studentId) {
  const { data } = await api.get('/achievements/progress/', {
    params: studentId ? { student: studentId } : undefined,
  });
  return {
    earnedCount: data.earned_count,
    totalCount: data.total_count,
    facts: {
      examNetTyt: data.facts?.exam_net_tyt ?? null,
      examNetAyt: data.facts?.exam_net_ayt ?? null,
      topicCompletion: data.facts?.topic_completion ?? null,
      topicsDone: data.facts?.topics_done ?? 0,
      topicsTotal: data.facts?.topics_total ?? 0,
      compliance: data.facts?.compliance ?? null,
    },
    achievements: (data.achievements || []).map(adapt),
  };
}

/* --- Tanım yönetimi: Ayarlar ekranı için hazır (C3 / Faz D) --------------- */

export async function listAchievements() {
  const { data } = await api.get('/achievements/');
  return data.map(adapt);
}

export async function createAchievement(body) {
  const { data } = await api.post('/achievements/', body);
  return adapt(data);
}

export async function updateAchievement(id, body) {
  const { data } = await api.patch(`/achievements/${id}/`, body);
  return adapt(data);
}

export async function deleteAchievement(id) {
  await api.delete(`/achievements/${id}/`);
}
