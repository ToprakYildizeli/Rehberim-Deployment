/* Takvim gerçek backend'e bağlı (/api/calendar/). Rehber kendi etkinliklerini
   listeler/ekler/siler. Backend alanları (title/description/start_time/student)
   ekranın beklediği mock şekline (category/note/time/studentId) çevrilir.
   Not: backend'de ayrı 'category' alanı yok → kategori `title`'da taşınır. */
import api from './client';
import { colorFor } from '../components/ui/avatarUtils';

/** Backend CalendarEvent → ekranın beklediği randevu şekli. */
function adaptEvent(e) {
  return {
    id: e.id,
    date: e.date,
    time: e.start_time ? e.start_time.slice(0, 5) : '',
    studentId: e.student,
    category: e.title,
    note: e.description ?? '',
    student: e.student
      ? { id: e.student, name: e.student_name, color: colorFor(e.student_name ?? '') }
      : null,
  };
}

export async function listAppointments() {
  const { data } = await api.get('/calendar/');
  return data.map(adaptEvent);
}

export async function createAppointment({ date, time, studentId, category = 'Toplantı', note = '' }) {
  const { data } = await api.post('/calendar/', {
    student: studentId ? Number(studentId) : null,
    title: category,
    description: note,
    date,
    start_time: time ? `${time}:00` : null,
  });
  return adaptEvent(data);
}

export async function deleteAppointment(id) {
  await api.delete(`/calendar/${id}/`);
  return { ok: true };
}
