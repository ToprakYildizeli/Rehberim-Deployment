/* Rehber panosu — TAMAMEN gerçek veriden türetilir (mock yok). Rehberin kendi
   öğrencilerinin verilerini (öğrenci, program+görev, deneme+net, konu ilerlemesi,
   takvim) tek seferde çekip client-side toplar. Backend'e aggregate uç gerekmez. */
import api from './client';
import { listStudents } from './students';
import { listAppointments } from './appointments';
import { listSubjects } from './catalog';

const pad2 = (n) => String(n).padStart(2, '0');
const isoOf = (d) => `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`;
const todayIso = () => isoOf(new Date());
const round1 = (n) => Math.round(n * 10) / 10;

// "Deneme Ort." kıyası — TYT'de tek ölçek; AYT'de ölçek **alana** bağlıdır.
const TYT_DIM_GROUPS = [
  { key: 'total', label: 'Toplam', subs: null, max: 120 },
  { key: 'tr', label: 'Türkçe', subs: ['TYT Türkçe'], max: 40 },
  { key: 'sos', label: 'Sosyal', subs: ['TYT Tarih', 'TYT Coğrafya', 'TYT Felsefe', 'TYT Din Kültürü ve Ahlak Bilgisi'], max: 20 },
  { key: 'mat', label: 'Matematik', subs: ['TYT Matematik', 'TYT Geometri'], max: 40 },
  { key: 'fen', label: 'Fen', subs: ['TYT Fizik', 'TYT Kimya', 'TYT Biyoloji'], max: 20 },
];

/** AYT ders grupları — hangi derslerin hangi başlık altında toplandığı.
 *  Maksimum netler burada YAZILI DEĞİL; alana göre `/api/subjects/`ten gelen
 *  `question_count` toplanarak hesaplanır (bkz. aytGroupsFor). */
const AYT_DIM_GROUPS = [
  { key: 'edb', label: 'Edebiyat', subs: ['AYT Türk Dili ve Edebiyatı'] },
  { key: 'tar', label: 'Tarih', subs: ['AYT Tarih-1', 'AYT Tarih-2'] },
  { key: 'cog', label: 'Coğrafya', subs: ['AYT Coğrafya-1', 'AYT Coğrafya-2'] },
  { key: 'fel', label: 'Felsefe', subs: ['AYT Felsefe'] },
  { key: 'din', label: 'Din Kültürü', subs: ['AYT Din Kültürü ve Ahlak Bilgisi'] },
  { key: 'mat', label: 'Matematik', subs: ['AYT Matematik', 'AYT Geometri'] },
  { key: 'fiz', label: 'Fizik', subs: ['AYT Fizik'] },
  { key: 'kim', label: 'Kimya', subs: ['AYT Kimya'] },
  { key: 'biy', label: 'Biyoloji', subs: ['AYT Biyoloji'] },
];

/** Alanların gösterim sırası ve adları (backend `Student.StudyField`). */
export const AYT_FIELDS = [
  { value: 'say', label: 'Sayısal' },
  { value: 'ea', label: 'Eşit Ağırlık' },
  { value: 'soz', label: 'Sözel' },
];

/** Alan → o alanın AYT dersleri. Backend'deki `Student.AYT_FIELD_SUBJECTS`in
 *  birebir aynısı; o eşleme genel bir uçtan yayınlanmadığı (yalnızca öğrenci
 *  bazlı `/api/subjects/?student=&scope=field` var) için burada yansıtılıyor.
 *  Ders adları katalogla aynı yazılmalı. */
const AYT_FIELD_SUBJECTS = {
  say: ['AYT Matematik', 'AYT Geometri', 'AYT Fizik', 'AYT Kimya', 'AYT Biyoloji'],
  ea: ['AYT Matematik', 'AYT Geometri', 'AYT Türk Dili ve Edebiyatı', 'AYT Tarih-1', 'AYT Coğrafya-1'],
  soz: ['AYT Türk Dili ve Edebiyatı', 'AYT Tarih-1', 'AYT Coğrafya-1', 'AYT Tarih-2',
    'AYT Coğrafya-2', 'AYT Felsefe', 'AYT Din Kültürü ve Ahlak Bilgisi'],
};

/** Bir alanın AYT grupları: gruplar o alanın derslerine kırpılır, maksimum net
 *  katalogdaki soru sayılarından toplanır. Böylece EA'da "Tarih" yalnız Tarih-1
 *  (10 net) olur, Sözel'de Tarih-1+2 (21 net) olur — ve "Toplam" her alanda 80'i
 *  aşamaz. Eskiden tek bir 80'lik ölçek kullanıldığı için AYT'de 90/80 gibi
 *  imkânsız değerler çıkabiliyordu. */
function aytGroupsFor(field, maxByLabel) {
  const own = AYT_FIELD_SUBJECTS[field];
  if (!own) return null;
  const sum = (labels) => labels.reduce((a, l) => a + (maxByLabel[l] || 0), 0);
  const groups = AYT_DIM_GROUPS
    .map((g) => ({ ...g, subs: g.subs.filter((l) => own.includes(l)) }))
    .filter((g) => g.subs.length)
    .map((g) => ({ ...g, max: sum(g.subs) }));
  return [{ key: 'total', label: 'Toplam', subs: own, max: sum(own) }, ...groups];
}

/** Bir öğrencinin bir net boyutundaki (tür + ders grubu) denemeler-arası ortalaması. */
function dimAvg(exams, type, subs) {
  const exs = exams.filter((e) => e.exam_type === type);
  if (!exs.length) return null;
  const vals = exs.map((e) => (subs
    ? round1((e.subject_nets || []).filter((n) => subs.includes(n.subject_label)).reduce((a, n) => a + n.net, 0))
    : e.total_net));
  return round1(vals.reduce((a, x) => a + x, 0) / vals.length);
}

/** Panoyu besleyen tüm türetilmiş veriyi döndürür. */
export async function getDashboard() {
  const [students, appts, programsRes, examsRes, tpRes, subjects] = await Promise.all([
    listStudents(),
    listAppointments(),
    api.get('/programs/'),
    api.get('/exams/'),
    api.get('/topic-progress/'),
    listSubjects(),          // maksimum netler katalogtaki soru sayılarından gelir
  ]);
  // Ders etiketi → sınavdaki soru sayısı (= o dersten çıkarılabilecek en yüksek net).
  const maxByLabel = Object.fromEntries(subjects.map((x) => [x.label, x.questionCount]));
  const aytGroupsByField = Object.fromEntries(
    AYT_FIELDS.map((f) => [f.value, aytGroupsFor(f.value, maxByLabel)])
  );
  const programs = programsRes.data || [];
  const exams = examsRes.data || [];
  const tps = tpRes.data || [];
  const today = todayIso();

  // Öğrenci başına verileri grupla
  const bucket = {};
  students.forEach((s) => { bucket[s.id] = { exams: [], programs: [], tps: [] }; });
  exams.forEach((e) => { bucket[e.student]?.exams.push(e); });
  programs.forEach((p) => { bucket[p.student]?.programs.push(p); });
  tps.forEach((t) => { bucket[t.student]?.tps.push(t); });

  const enriched = students.map((s) => {
    const b = bucket[s.id];
    const exSorted = b.exams.slice().sort((a, c) => (a.exam_date < c.exam_date ? 1 : -1));
    // Trend AYNI sınav türü içinde (TYT↔AYT kıyaslamak anlamsız).
    const lastEx = exSorted[0] || null;
    const prevSame = exSorted.slice(1).find((e) => e.exam_type === lastEx?.exam_type) || null;
    const lastNet = lastEx?.total_net ?? null;
    const prevNet = prevSame?.total_net ?? null;
    // Deneme ort. yalnız TYT (herkes girer, ortak 120'lik ölçek → kıyaslanabilir)
    const tytEx = b.exams.filter((e) => e.exam_type === 'tyt');
    const avgNet = tytEx.length ? round1(tytEx.reduce((a, e) => a + e.total_net, 0) / tytEx.length) : null;
    const netDelta = (lastNet != null && prevNet != null) ? round1(lastNet - prevNet) : null;
    const trend = netDelta == null ? null : netDelta > 0 ? 'up' : netDelta < 0 ? 'down' : 'flat';

    const avgLevel = b.tps.length ? round1(b.tps.reduce((a, t) => a + t.level, 0) / b.tps.length) : null;
    const weakCount = b.tps.filter((t) => t.level <= 2).length;

    // Haftalık saat YALNIZ çalışma + deneme bloklarını sayar. Dış meşguliyet
    // (okul, dershane, antrenman, doktor) programda yer kaplar ama çalışma değildir
    // — backend bunu `counts_as_study` ile söyler.
    // Pencere 7 günden farklı olabildiği için ("Salıdan Cumaya 4 gün") her programın
    // toplamı haftalık hıza çevriliyor, yoksa kısa programlı öğrenci az çalışıyor görünür.
    const weekHours = b.programs.map((p) => {
      const mins = (p.tasks || [])
        .filter((t) => t.counts_as_study !== false)
        .reduce((a, t) => a + (t.duration_minutes || 0), 0);
      return (mins / 60) * (7 / (p.day_count || 7));
    });
    const weeklyHours = weekHours.length ? round1(weekHours.reduce((a, x) => a + x, 0) / weekHours.length) : 0;

    // Pencere artık 7 gün olmak zorunda değil — bitişi sunucudan gelen `end_date` söyler.
    const current = b.programs.find((p) => p.start_date <= today && today <= p.end_date);
    const hasCurrentProgram = !!current;
    // Uyum yüzdesi sunucuda **süre** üzerinden hesaplanır (B2) — burada görev
    // sayısıyla tekrar hesaplanmaz ki panel ile öğrenci sayfası aynı sayıyı göstersin.
    const compliance = current ? (current.compliance?.percent ?? 0) : null;

    // TYT herkes için aynı ölçek. AYT'de ölçek alana göre değişir ve her öğrencinin
    // **üç alanda da** neti hesaplanır — seçilen alan "kimin listeleneceğini" değil,
    // "hangi ölçekle bakılacağını" belirler. Sayısalcının 40 mat + 30 fen neti
    // Sayısal ölçeğinde 70, EA ölçeğinde 40'tır; ikisi de anlamlı ve kıyaslanabilir.
    const netDims = {};
    TYT_DIM_GROUPS.forEach((g) => { netDims[`tyt_${g.key}`] = dimAvg(b.exams, 'tyt', g.subs); });
    Object.entries(aytGroupsByField).forEach(([field, groups]) => {
      (groups || []).forEach((g) => {
        netDims[`ayt_${field}_${g.key}`] = dimAvg(b.exams, 'ayt', g.subs);
      });
    });

    return {
      ...s,
      examCount: b.exams.length,
      lastNet, avgNet, netDelta, trend,
      avgLevel, weakCount,
      weeklyHours,
      hasCurrentProgram, compliance,
      netDims,
      lastExamDate: exSorted[0]?.exam_date ?? null,
    };
  });

  const enrById = Object.fromEntries(enriched.map((e) => [e.id, e]));

  // Öğrenci-bazlı net serisi (çok çizgili grafik) — tür başına, tarihe göre sıralı
  const seriesFor = (type) => students
    .map((s) => {
      const exs = bucket[s.id].exams
        .filter((e) => e.exam_type === type)
        .sort((a, c) => (a.exam_date < c.exam_date ? -1 : 1));
      return exs.length ? {
        id: s.id, name: enrById[s.id].name, color: enrById[s.id].color,
        points: exs.map((e, i) => ({ x: i, label: e.name.replace(/^(TYT|AYT)\s+/, ''), net: e.total_net })),
      } : null;
    })
    .filter(Boolean);
  const netSeries = { tyt: seriesFor('tyt'), ayt: seriesFor('ayt') };

  // Yaklaşan görüşmeler (bugünden itibaren)
  const upcoming = appts
    .filter((a) => a.date >= today)
    .sort((a, b) => `${a.date}${a.time}`.localeCompare(`${b.date}${b.time}`));

  // KPI'lar
  const withProgram = enriched.filter((e) => e.hasCurrentProgram).length;
  const netted = enriched.filter((e) => e.avgNet != null);
  const kpis = {
    count: enriched.length,
    withProgram,
    withoutProgram: enriched.length - withProgram,
    upcoming: upcoming.length,
    avgNet: netted.length ? round1(netted.reduce((a, e) => a + e.avgNet, 0) / netted.length) : null,
  };

  // Aksiyon listeleri
  const needProgram = enriched.filter((e) => !e.hasCurrentProgram);
  // Program uyumu — bu hafta programlı herkes, düşükten yükseğe sıralı (%)
  const complianceRanked = enriched
    .filter((e) => e.hasCurrentProgram && e.compliance != null)
    .sort((a, b) => a.compliance - b.compliance);

  // Net değişimi: herkes — son denemenin (aynı tür) öncekine göre farkı; en çok düşen başta
  const netChanges = enriched
    .filter((e) => e.netDelta != null)
    .sort((a, b) => a.netDelta - b.netDelta);

  // Konu takibi — konu ilerlemesi olan herkes, ortalama seviye yüksekten düşüğe
  const konuRanked = enriched
    .filter((e) => e.avgLevel != null)
    .sort((a, b) => b.avgLevel - a.avgLevel);

  return {
    students: enriched, enrById, upcoming, kpis, needProgram,
    complianceRanked, netChanges, konuRanked, netSeries,
    netDimGroups: {
      tyt: TYT_DIM_GROUPS.map(({ key, label, max }) => ({ key, label, max })),
      // AYT'de grup listesi ve maksimumlar alana göre değişir.
      ayt: Object.fromEntries(
        AYT_FIELDS.map((f) => [
          f.value,
          (aytGroupsByField[f.value] || []).map(({ key, label, max }) => ({ key, label, max })),
        ])
      ),
    },
  };
}
