import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Users, CalendarClock, CalendarPlus, TrendingDown, TrendingUp, Minus, Target, ChevronRight,
  ClipboardList, Gauge, BarChart3, LineChart,
} from 'lucide-react';
import {
  Card, CardHeader, Button, Avatar, Badge, ProgressBar, PillGroup, Select, EmptyState, Spinner,
} from '../components/ui';
import { getDashboard, AYT_FIELDS } from '../api/dashboard';
import s from './Panel.module.css';

const MONTHS = ['Oca', 'Şub', 'Mar', 'Nis', 'May', 'Haz', 'Tem', 'Ağu', 'Eyl', 'Eki', 'Kas', 'Ara'];
const fmtDay = (iso) => { const [, m, d] = iso.split('-').map(Number); return `${d} ${MONTHS[m - 1]}`; };
const todayIso = () => { const d = new Date(); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`; };

const METRICS = [
  { value: 'avgNet', label: 'Deneme Ort.', unit: 'net', max: 120 },   // TYT üzerinden
  { value: 'avgLevel', label: 'Konu Puanı', unit: '', max: 5 },
  { value: 'weeklyHours', label: 'Haftalık Saat', unit: 'sa', max: 80 },
];
const NET_TYPES = [{ value: 'tyt', label: 'TYT' }, { value: 'ayt', label: 'AYT' }];

const complianceColor = (c) => (c >= 80 ? 'var(--success)' : c >= 60 ? 'var(--warning)' : 'var(--danger)');
const levelTone = (l) => (l >= 4 ? 'success' : l >= 3 ? 'accent' : l >= 2 ? 'warning' : 'danger');

export default function Panel() {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [metric, setMetric] = useState('avgNet');
  const [netExam, setNetExam] = useState('tyt');   // "Deneme Ort." kıyası: TYT/AYT
  const [netField, setNetField] = useState('say'); // AYT'de kıyaslanan alan
  const [netGroup, setNetGroup] = useState('total'); // ve ders grubu (sınava/alana göre)
  const [netType, setNetType] = useState('tyt');
  const [hidden, setHidden] = useState(() => new Set());

  useEffect(() => {
    let alive = true;
    getDashboard().then((d) => { if (alive) setData(d); }).catch(() => { if (alive) setData({ error: true }); });
    return () => { alive = false; };
  }, []);

  const openStudent = (id) => navigate(`/ogrenciler/${id}`);
  const toggle = (id) => setHidden((prev) => {
    const next = new Set(prev);
    if (next.has(id)) next.delete(id); else next.add(id);
    return next;
  });

  // Kıyas değeri: "Deneme Ort."ta seçili tür+grup neti; diğer metriklerde alanın kendisi.
  // AYT'de seçilen alan bir SÜZGEÇ değil, ÖLÇEKtir: herkes o alanın ders kümesiyle
  // hesaplanıp listelenir. Sayısalcı, EA ölçeğinde de kendi matematik netiyle görünür.
  const dimKey = netExam === 'ayt' ? `ayt_${netField}_${netGroup}` : `tyt_${netGroup}`;
  const metricVal = (st) => (metric === 'avgNet' ? (st.netDims?.[dimKey] ?? null) : st[metric]);
  const ranked = useMemo(() => {
    if (!data?.students) return [];
    const val = (st) => (metric === 'avgNet' ? (st.netDims?.[dimKey] ?? null) : st[metric]);
    return data.students.filter((st) => val(st) != null).sort((a, b) => val(b) - val(a));
  }, [data, metric, dimKey]);

  if (!data) return <div className={s.center}><Spinner size={24} /></div>;

  const { kpis, upcoming, needProgram, complianceRanked, netChanges, konuRanked, netSeries, netDimGroups } = data;
  const metricDef = METRICS.find((x) => x.value === metric);
  // AYT'de grup listesi (ve maksimumları) seçili alana bağlı; TYT'de tek liste.
  const groupOpts = (netExam === 'ayt'
    ? netDimGroups?.ayt?.[netField]
    : netDimGroups?.tyt) || [];
  const dimDef = groupOpts.find((d) => d.key === netGroup) || groupOpts[0] || { max: 120 };
  const rankMax = metric === 'avgNet' ? dimDef.max : metricDef.max;
  const rankUnit = metric === 'avgNet' ? 'net' : metricDef.unit;
  const available = netSeries[netType] || [];
  const visible = available.filter((se) => !hidden.has(se.id));

  return (
    <div className={s.page}>
      {/* ── KPI şeridi ── */}
      <div className={s.kpiRow}>
        <KpiCard icon={<Users size={18} />} value={kpis.count} label="Öğrenci" tone="accent" />
        <KpiCard icon={<CalendarPlus size={18} />} value={kpis.withoutProgram}
          label="Bu hafta programsız" tone={kpis.withoutProgram ? 'danger' : 'success'} />
        <KpiCard icon={<CalendarClock size={18} />} value={kpis.upcoming} label="Yaklaşan görüşme" tone="violet" />
        <KpiCard icon={<Gauge size={18} />} value={kpis.avgNet ?? '—'} label="Ort. net" tone="cyan" />
      </div>

      {/* ── Öğrenci net grafiği (çok çizgili, seçilebilir) ── */}
      <Card>
        <div className={s.cmpHead}>
          <div>
            <h2 className={s.cmpTitle}><LineChart size={16} /> Öğrenci Net Grafiği</h2>
            <p className={s.cmpSub}>Deneme başına net; öğrenci ve sınav türünü seç</p>
          </div>
          <PillGroup options={NET_TYPES} value={netType} onChange={setNetType} />
        </div>
        <div className={s.netChips}>
          {available.map((se) => (
            <button key={se.id} type="button"
              className={`${s.chip} ${hidden.has(se.id) ? s.chipOff : ''}`} onClick={() => toggle(se.id)}>
              <span className={s.chipDot} style={{ background: se.color }} />
              {se.name.split(' ')[0]}
            </button>
          ))}
        </div>
        <MultiLineChart series={visible} />
      </Card>

      {/* ── Aksiyon satırı ── */}
      <div className={s.widgetRow}>
        <Card className={s.wCard}>
          <CardHeader title="Yaklaşan Görüşmeler" actions={<span className={s.countBadge}>{upcoming.length}</span>} />
          {upcoming.length === 0 ? (
            <EmptyState icon={<CalendarClock size={20} />} text="Yaklaşan görüşme yok." />
          ) : (
            <div className={s.list}>
              {upcoming.map((a) => (
                <button key={a.id} type="button" className={s.row}
                  onClick={() => (a.studentId ? openStudent(a.studentId) : navigate('/takvim'))}>
                  <span className={s.dateChip}>
                    <span className={s.dateChipDay}>{a.date === todayIso() ? 'Bugün' : fmtDay(a.date)}</span>
                    <span className={s.dateChipTime}>{a.time || '—'}</span>
                  </span>
                  <span className={s.rowMain}>
                    <span className={s.rowName}>{a.student?.name || 'Kişisel'}</span>
                    <span className={s.rowSub}>{a.category}</span>
                  </span>
                  <ChevronRight size={16} className={s.rowChevron} />
                </button>
              ))}
            </div>
          )}
        </Card>

        <Card className={s.wCard}>
          <CardHeader title="Program Gerekenler" actions={<span className={`${s.countBadge} ${needProgram.length ? s.countDanger : ''}`}>{needProgram.length}</span>} />
          {needProgram.length === 0 ? (
            <EmptyState icon={<ClipboardList size={20} />} text="Herkesin bu hafta programı var." />
          ) : (
            <div className={s.list}>
              {needProgram.map((st) => (
                <div key={st.id} className={s.row}>
                  <Avatar name={st.name} color={st.color} size="sm" />
                  <span className={s.rowMain}>
                    <span className={s.rowName}>{st.name}</span>
                    <span className={s.rowSub}>{st.grade}</span>
                  </span>
                  <Button variant="soft" size="sm" onClick={() => navigate(`/ders-programi?ogrenci=${st.id}`)}>
                    Program yap
                  </Button>
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card className={s.wCard}>
          <CardHeader title="Net Değişimi (son denemeye göre)" actions={<span className={s.countBadge}>{netChanges.length}</span>} />
          {netChanges.length === 0 ? (
            <EmptyState icon={<TrendingDown size={20} />} text="Karşılaştırılacak deneme yok." />
          ) : (
            <div className={s.list}>
              {netChanges.map((st) => {
                const up = st.netDelta > 0; const flat = st.netDelta === 0;
                const tone = flat ? 'neutral' : up ? 'success' : 'danger';
                const Icon = flat ? Minus : up ? TrendingUp : TrendingDown;
                return (
                  <button key={st.id} type="button" className={s.row} onClick={() => openStudent(st.id)}>
                    <Avatar name={st.name} color={st.color} size="sm" />
                    <span className={s.rowMain}>
                      <span className={s.rowName}>{st.name}</span>
                      <span className={s.rowSub}>{st.lastNet} net (son deneme)</span>
                    </span>
                    <Badge tone={tone}><Icon size={12} /> {up ? '+' : ''}{st.netDelta}</Badge>
                  </button>
                );
              })}
            </div>
          )}
        </Card>
      </div>

      {/* ── Uyum (sıralı %) + Konu takibi (ort. seviye) ── */}
      <div className={s.pairRow}>
        <Card className={s.wCard}>
          <CardHeader title="Program Uyumu" actions={<span className={s.countBadge}>{complianceRanked.length}</span>} />
          {complianceRanked.length === 0 ? (
            <EmptyState icon={<Gauge size={20} />} text="Bu hafta programlı öğrenci yok." />
          ) : (
            <div className={s.list}>
              {complianceRanked.map((st) => (
                <button key={st.id} type="button" className={s.row} onClick={() => openStudent(st.id)}>
                  <Avatar name={st.name} color={st.color} size="sm" />
                  <span className={s.rowMain}>
                    <span className={s.rowName}>{st.name}</span>
                    <ProgressBar value={st.compliance} color={complianceColor(st.compliance)} />
                  </span>
                  <span className={s.rowStat}>%{st.compliance}</span>
                </button>
              ))}
            </div>
          )}
        </Card>

        <Card className={s.wCard}>
          <CardHeader title="Konu Takibi — Ortalama Seviye" actions={<span className={s.countBadge}>{konuRanked.length}</span>} />
          {konuRanked.length === 0 ? (
            <EmptyState icon={<Target size={20} />} text="Konu ilerlemesi işaretlenmemiş." />
          ) : (
            <div className={s.list}>
              {konuRanked.map((st) => (
                <button key={st.id} type="button" className={s.row} onClick={() => openStudent(st.id)}>
                  <Avatar name={st.name} color={st.color} size="sm" />
                  <span className={s.rowMain}>
                    <span className={s.rowName}>{st.name}</span>
                    <span className={s.rowSub}>{st.weakCount} zayıf konu</span>
                  </span>
                  <Badge tone={levelTone(st.avgLevel)}>{st.avgLevel} / 5</Badge>
                </button>
              ))}
            </div>
          )}
        </Card>
      </div>

      {/* ── Ortalama üzerinden kıyaslama ── */}
      <Card>
        <div className={s.cmpHead}>
          <div>
            <h2 className={s.cmpTitle}><BarChart3 size={16} /> Öğrenci Kıyaslama</h2>
          </div>
          <div className={s.cmpControls}>
            <PillGroup options={METRICS} value={metric} onChange={setMetric} />
            {metric === 'avgNet' && (
              <span className={s.netDimCtl}>
                <PillGroup
                  options={NET_TYPES}
                  value={netExam}
                  onChange={(v) => { setNetExam(v); setNetGroup('total'); }}
                />
                {netExam === 'ayt' && (
                  <Select
                    className={s.dimSelect}
                    value={netField}
                    onChange={(e) => { setNetField(e.target.value); setNetGroup('total'); }}
                    aria-label="Alan"
                  >
                    {AYT_FIELDS.map((f) => <option key={f.value} value={f.value}>{f.label}</option>)}
                  </Select>
                )}
                <Select className={s.dimSelect} value={netGroup} onChange={(e) => setNetGroup(e.target.value)} aria-label="Ders grubu">
                  {groupOpts.map((d) => <option key={d.key} value={d.key}>{d.label}</option>)}
                </Select>
              </span>
            )}
          </div>
        </div>
        {ranked.length === 0 ? (
          <EmptyState text="Bu metrik için veri yok." />
        ) : (
          <div className={s.rankList}>
            {ranked.map((st) => (
              <button key={st.id} type="button" className={s.rankRow} onClick={() => openStudent(st.id)}>
                <Avatar name={st.name} color={st.color} size="xs" />
                <span className={s.rankName}>{st.name}</span>
                <span className={s.rankTrack}>
                  <span className={s.rankFill} style={{ width: `${Math.min(100, (metricVal(st) / rankMax) * 100)}%`, background: st.color || 'var(--accent)' }} />
                </span>
                <span className={s.rankValue}>{metricVal(st)} / {rankMax}{rankUnit ? ` ${rankUnit}` : ''}</span>
              </button>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}

function KpiCard({ icon, value, label, tone }) {
  return (
    <Card className={s.kpiCard}>
      <span className={`${s.kpiIcon} ${s[`kpi_${tone}`]}`}>{icon}</span>
      <span className={s.kpiValue}>{value}</span>
      <span className={s.kpiLabel}>{label}</span>
    </Card>
  );
}

/** Çok çizgili net grafiği — her öğrenci kendi renginde (SVG, tek eksen).
 *  Büyük viewBox + non-scaling-stroke → çizgi/nokta ekranda ince ve net kalır. */
function MultiLineChart({ series }) {
  if (!series.length) return <EmptyState icon={<LineChart size={20} />} text="Görüntülenecek öğrenci seç." />;
  const W = 760; const H = 300; const padL = 42; const padR = 20; const padT = 18; const padB = 38;
  const maxX = Math.max(...series.map((se) => se.points.length));
  const allNet = series.flatMap((se) => se.points.map((p) => p.net));
  const lo = Math.min(...allNet); const hi = Math.max(...allNet);
  const min = Math.floor(lo - (hi - lo || 4) * 0.15);
  const max = Math.ceil(hi + (hi - lo || 4) * 0.15);
  const xs = (x) => padL + (maxX <= 1 ? (W - padL - padR) / 2 : (x * (W - padL - padR)) / (maxX - 1));
  const ys = (v) => padT + (1 - (v - min) / ((max - min) || 1)) * (H - padT - padB);
  const grids = [min, Math.round((min + max) / 2), max];
  return (
    <svg className={s.trendSvg} viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="xMinYMid meet"
      role="img" aria-label="Öğrenci net grafiği">
      {grids.map((g) => (
        <g key={g}>
          <line x1={padL} y1={ys(g)} x2={W - padR} y2={ys(g)} className={s.grid} vectorEffect="non-scaling-stroke" />
          <text x={padL - 8} y={ys(g) + 4} className={s.axisTxt} textAnchor="end">{g}</text>
        </g>
      ))}
      {Array.from({ length: maxX }).map((_, i) => (
        <text key={i} x={xs(i)} y={H - 12} className={s.axisTxt} textAnchor="middle">D{i + 1}</text>
      ))}
      {series.map((se) => {
        const line = se.points.map((p, i) => `${i ? 'L' : 'M'}${xs(p.x).toFixed(1)},${ys(p.net).toFixed(1)}`).join(' ');
        return (
          <g key={se.id}>
            <path d={line} fill="none" stroke={se.color} strokeWidth="2" strokeLinejoin="round"
              strokeLinecap="round" vectorEffect="non-scaling-stroke" />
            {se.points.map((p) => (
              <circle key={p.x} cx={xs(p.x)} cy={ys(p.net)} r="3" fill="var(--bg-card)"
                stroke={se.color} strokeWidth="2" vectorEffect="non-scaling-stroke">
                <title>{se.name} — {p.label}: {p.net} net</title>
              </circle>
            ))}
          </g>
        );
      })}
    </svg>
  );
}
