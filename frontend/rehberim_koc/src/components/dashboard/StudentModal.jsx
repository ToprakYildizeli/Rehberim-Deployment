import { Sparkles, ArrowRight } from 'lucide-react';
import { Modal, Avatar, Badge, ProgressBar } from '../ui';
import { SUBJECT_MAP } from '../../mocks/data';
import { trendMeta } from './trend';
import s from './StudentModal.module.css';

/** Deep-dive overlay opened from an AI insight card or a student row. */
export default function StudentModal({ student, open, onClose, onModifySchedule }) {
  if (!student) return null;
  const trend = trendMeta(student.trend);

  return (
    <Modal open={open} onClose={onClose} width={560} labelledBy="student-modal-title">
      <header className={s.header}>
        <Avatar name={student.name} color={student.color} size="lg" />
        <div className={s.headText}>
          <h2 className={s.name} id="student-modal-title">{student.name}</h2>
          <p className={s.meta}>
            {student.grade}{student.compliance != null ? ` · Haftalık Uyum %${student.compliance}` : ''}
          </p>
        </div>
        <Badge tone={trend.tone}>
          <trend.Icon size={12} /> {trend.label}
        </Badge>
      </header>

      <div className={s.stats}>
        <div className={s.stat}>
          <span className={s.statLabel}>Son Deneme Neti</span>
          <span className={s.statValue}>{student.lastNet ?? '—'}</span>
        </div>
        <div className={s.stat}>
          <span className={s.statLabel}>Haftalık Uyum</span>
          <span className={s.statValue}>{student.compliance != null ? `%${student.compliance}` : '—'}</span>
        </div>
        <div className={s.stat}>
          <span className={s.statLabel}>Trend</span>
          <span className={s.statValue} style={{ color: `var(--${trend.tone})` }}>
            {trend.label}
          </span>
        </div>
      </div>

      {Object.keys(student.subjects ?? {}).length > 0 && (
        <section className={s.section}>
          <h3 className={s.sectionTitle}>Ders Performansı</h3>
          <div className={s.subjectList}>
            {Object.entries(student.subjects).map(([key, pct]) => (
              <div className={s.subjectRow} key={key}>
                <span className={s.subjectName}>{SUBJECT_MAP[key]?.name ?? key}</span>
                <ProgressBar value={pct} color={SUBJECT_MAP[key]?.color} />
                <span className={s.subjectPct}>%{pct}</span>
              </div>
            ))}
          </div>
        </section>
      )}

      <section className={s.section}>
        <h3 className={s.sectionTitle}>
          <Sparkles size={14} /> AI Analizi
        </h3>
        <div className={s.analysis}>
          <p className={s.analysisText}>{buildAnalysis(student)}</p>
          <button type="button" className={s.cta} onClick={() => onModifySchedule?.(student)}>
            Programında değişiklik yap <ArrowRight size={14} />
          </button>
        </div>
      </section>
    </Modal>
  );
}

function buildAnalysis(student) {
  const entries = Object.entries(student.subjects ?? {});
  if (entries.length === 0) {
    return 'Bu öğrenci için henüz yeterli veri yok. Deneme sonuçları ve program girildikçe analiz burada oluşacak.';
  }
  const weakest = entries.reduce((a, b) => (b[1] < a[1] ? b : a));
  const strongest = entries.reduce((a, b) => (b[1] > a[1] ? b : a));
  const weakName = SUBJECT_MAP[weakest[0]]?.name ?? weakest[0];
  const strongName = SUBJECT_MAP[strongest[0]]?.name ?? strongest[0];

  if (student.trend === 'down') {
    return `Haftalık görev tamamlanma oranı %${student.compliance} ile düşük seviyede. En zayıf alan ${weakName} (%${weakest[1]}). Ders programı yoğunluğu gözden geçirilmeli.`;
  }
  if (student.trend === 'up') {
    return `Net trendi yükselişte. ${strongName} alanında güçlü (%${strongest[1]}), ${weakName} alanında (%${weakest[1]}) ek çalışma planlanması öneriliyor.`;
  }
  return `Performans sabit seyrediyor. ${strongName} güçlü yanı (%${strongest[1]}); ${weakName} için (%${weakest[1]}) hedefli tekrar bloğu eklenebilir.`;
}
