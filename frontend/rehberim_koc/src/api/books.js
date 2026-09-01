/* Öğrencinin kitaplığı — gerçek backend (GET /api/books/?student=<id>).
   Rehber salt-okur; öğrenci detay sayfasının "Kitaplar" sekmesini besler.
   (catalog.js#listBooks Ders Programı'nda kaynak seçimi için daha dar alanlar
   döndürür; burada durum/format/yayınevi gibi tam gösterim alanları gerekir.) */
import api from './client';

const STATUS_LABEL = {
  baslanmadi: 'Başlanmadı',
  devam: 'Devam ediyor',
  tamamlandi: 'Tamamlandı',
};

const FORMAT_LABEL = {
  paragraf: 'Paragraf',
  konu_anlatimi: 'Konu Anlatımı',
  soru_bankasi: 'Soru Bankası',
  deneme: 'Deneme',
};

function adaptBook(b) {
  return {
    id: b.id,
    kind: b.kind,                                 // 'ders' | 'okuma'
    label: b.label,
    title: b.title || '',
    author: b.author || '',
    subjectLabel: b.subject_label || '',
    publisher: b.publisher || '',
    format: b.book_format || '',
    formatLabel: FORMAT_LABEL[b.book_format] || '',
    status: b.status,
    statusLabel: STATUS_LABEL[b.status] || b.status,
    topicCount: b.topic_count ?? null,
  };
}

/** GET /api/books/?student=<id> → öğrencinin tüm kitapları. */
export async function listStudentBooks(studentId) {
  const { data } = await api.get('/books/', { params: { student: studentId } });
  return data.map(adaptBook);
}

/** GET /api/books/<id>/ → kitap + içindeki konular (kitap özelindeki ilerleme). */
export async function getBook(bookId) {
  const { data } = await api.get(`/books/${bookId}/`);
  return {
    ...adaptBook(data),
    description: data.description || '',
    topics: (data.topics || []).map((t) => ({
      id: t.id,
      name: t.topic_name,
      grade: t.grade,
      status: t.status,
      statusLabel: STATUS_LABEL[t.status] || t.status,
      done: t.status === 'tamamlandi',
      testsSolved: t.tests_solved,
    })),
  };
}
