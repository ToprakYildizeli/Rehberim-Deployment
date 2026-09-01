import { Link } from 'react-router-dom';
import { ThemeToggle } from '../components/ui';
import styles from './Welcome.module.css';

function ArrowIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M5 12h14M12 5l7 7-7 7" />
    </svg>
  );
}

function FeatureCard({ icon, color, title, desc }) {
  return (
    <div className={styles.featureCard}>
      <div className={styles.featureIcon} style={{ background: `${color}18`, color }}>
        {icon}
      </div>
      <h3 className={styles.featureTitle}>{title}</h3>
      <p className={styles.featureDesc}>{desc}</p>
    </div>
  );
}

function Step({ n, title, desc }) {
  return (
    <div className={styles.step}>
      <div className={styles.stepNum}>{n}</div>
      <h3 className={styles.stepTitle}>{title}</h3>
      <p className={styles.stepDesc}>{desc}</p>
    </div>
  );
}

function DashboardPreview() {
  const students = [
    { init: 'A', name: 'Ali Korkmaz', grade: '12. Sınıf · Say', pct: 87, color: '#3b82f6' },
    { init: 'S', name: 'Selin Yıldız', grade: '12. Sınıf · EA', pct: 62, color: '#8b5cf6' },
    { init: 'M', name: 'Arda Mert', grade: '11. Sınıf', pct: 78, color: '#10b981' },
  ];
  const exams = [
    { subject: 'Matematik', net: 28.5, pct: 71, color: '#3b82f6' },
    { subject: 'Türkçe', net: 31.0, pct: 78, color: '#8b5cf6' },
    { subject: 'Fen', net: 14.5, pct: 48, color: '#10b981' },
  ];

  return (
    <div className={styles.preview}>
      <div className={styles.previewBar}>
        <div className={styles.previewDots}>
          <span style={{ background: '#ff5f57' }} />
          <span style={{ background: '#ffbd2e' }} />
          <span style={{ background: '#28c840' }} />
        </div>
        <span className={styles.previewBarTitle}>Rehberim · Dashboard</span>
      </div>

      <div className={styles.previewBody}>
        <div className={styles.previewGreet}>
          <div>
            <p className={styles.previewGreetName}>Merhaba, Hoca! 👋</p>
            <p className={styles.previewGreetSub}>3 aktif öğrenci · Bu hafta 2 toplantı</p>
          </div>
          <div className={styles.previewMonth}>Tem 2026</div>
        </div>

        <p className={styles.previewSectionLabel}>Öğrencilerim</p>

        {students.map(s => (
          <div key={s.name} className={styles.previewStudent}>
            <div className={styles.previewAvatar} style={{ background: s.color }}>
              {s.init}
            </div>
            <div className={styles.previewStudentInfo}>
              <div className={styles.previewStudentHeader}>
                <span className={styles.previewStudentName}>{s.name}</span>
                <span className={styles.previewStudentPct} style={{ color: s.color }}>{s.pct}%</span>
              </div>
              <div className={styles.previewProgressBg}>
                <div className={styles.previewProgressFill} style={{ width: `${s.pct}%`, background: s.color }} />
              </div>
              <span className={styles.previewStudentGrade}>{s.grade}</span>
            </div>
          </div>
        ))}

        <div className={styles.previewDivider} />

        <p className={styles.previewSectionLabel}>Son TYT Sonucu</p>

        {exams.map(e => (
          <div key={e.subject} className={styles.previewExam}>
            <span className={styles.previewExamSubject}>{e.subject}</span>
            <div className={styles.previewExamBarBg}>
              <div className={styles.previewExamBarFill} style={{ width: `${e.pct}%`, background: e.color }} />
            </div>
            <span className={styles.previewExamNet}>{e.net}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function Welcome() {
  return (
    <div className={styles.page}>

      {/* ── Navbar ── */}
      <nav className={styles.nav}>
        <div className={styles.navInner}>
          <span className={styles.brand}>
            <span className={styles.brandDot} />
            Rehberim
          </span>
          <div className={styles.navRight}>
            <ThemeToggle />
            <Link to="/giris" className={styles.navLink}>Giriş Yap</Link>
            <Link to="/kayit" className={styles.navCta}>Ücretsiz Başlayın</Link>
          </div>
        </div>
      </nav>

      {/* ── Hero ── */}
      <section className={styles.hero}>
        <div className={styles.heroInner}>
          <div className={styles.heroText}>
            <div className={styles.badge}>
              <span className={styles.badgePulse} />
              Rehber Koç Platformu
            </div>
            <h1 className={styles.heroTitle}>
              Öğrencilerinizi<br />
              <span className={styles.heroHighlight}>tam kontrolünüzde</span><br />
              tutun.
            </h1>
            <p className={styles.heroSubtitle}>
              Program hazırlayın, kazanımları girin, deneme sonuçlarını izleyin —
              tüm öğrencileriniz tek ekranda, her an ulaşılabilir.
            </p>
            <div className={styles.heroCta}>
              <Link to="/kayit" className={styles.btnPrimary}>
                Ücretsiz Başlayın <ArrowIcon />
              </Link>
              <Link to="/giris" className={styles.btnGhost}>Giriş Yap</Link>
            </div>
            <p className={styles.heroNote}>Kredi kartı gerekmez · Dakikalar içinde kurulum</p>
          </div>
          <div className={styles.heroVisual}>
            <div className={styles.previewGlow} />
            <DashboardPreview />
          </div>
        </div>
      </section>

      {/* ── Stats ── */}
      <section className={styles.stats}>
        <div className={styles.statsInner}>
          {[
            { n: '500+', l: 'Aktif Öğrenci' },
            { n: '50+', l: 'Rehber Koç' },
            { n: '10K+', l: 'Haftalık Program' },
            { n: '%94', l: 'Program Uyumu' },
          ].map(s => (
            <div key={s.l} className={styles.stat}>
              <strong>{s.n}</strong>
              <span>{s.l}</span>
            </div>
          ))}
        </div>
      </section>

      {/* ── Features ── */}
      <section className={styles.features}>
        <div className={styles.sectionInner}>
          <div className={styles.sectionTag}>Özellikler</div>
          <h2 className={styles.sectionTitle}>İhtiyacınız olan her şey, bir arada</h2>
          <p className={styles.sectionSub}>
            Bir rehber koç olarak yapmanız gereken her şeyi tek platformda yönetin.
          </p>
          <div className={styles.featureGrid}>
            <FeatureCard
              color="#2563eb"
              title="Haftalık Program"
              desc="Öğrencilere özel ders programı oluşturun. Öğrenci modifiye edebilir, siz onaylarsınız."
              icon={
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="3" y="4" width="18" height="18" rx="2" /><line x1="16" y1="2" x2="16" y2="6" /><line x1="8" y1="2" x2="8" y2="6" /><line x1="3" y1="10" x2="21" y2="10" />
                </svg>
              }
            />
            <FeatureCard
              color="#7c3aed"
              title="Deneme Takibi"
              desc="TYT/AYT net bazlı sonuçları girin, trend grafiklerini ve geçmiş gelişimi izleyin."
              icon={
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="18" y1="20" x2="18" y2="10" /><line x1="12" y1="20" x2="12" y2="4" /><line x1="6" y1="20" x2="6" y2="14" />
                </svg>
              }
            />
            <FeatureCard
              color="#059669"
              title="Kazanım Girişi"
              desc="Konu bazlı ilerlemeyi kaydedin. Öğrenci hangi konuyu hangi seviyede bitirdiğini anlık görsün."
              icon={
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M22 11.08V12a10 10 0 11-5.93-9.14" /><polyline points="22 4 12 14.01 9 11.01" />
                </svg>
              }
            />
            <FeatureCard
              color="#dc2626"
              title="Kitaplık"
              desc="Öğrencilerin okuma listelerini yönetin, kategori ve tamamlanma yüzdelerini takip edin."
              icon={
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M4 19.5A2.5 2.5 0 016.5 17H20" /><path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z" />
                </svg>
              }
            />
          </div>
        </div>
      </section>

      {/* ── How It Works ── */}
      <section className={styles.howItWorks}>
        <div className={styles.sectionInner}>
          <div className={styles.sectionTag}>Nasıl Çalışır</div>
          <h2 className={styles.sectionTitle}>3 adımda başlayın</h2>
          <div className={styles.steps}>
            <Step
              n="01"
              title="Hesap Oluşturun"
              desc="Dakikalar içinde rehber hesabınızı oluşturun. Kredi kartı veya kurulum gerekmez."
            />
            <div className={styles.stepConnector} />
            <Step
              n="02"
              title="Öğrenci Ekleyin"
              desc="Davet kodunuzu paylaşın. Öğrenci mobil uygulamadan kodu girerek anında bağlanır."
            />
            <div className={styles.stepConnector} />
            <Step
              n="03"
              title="Takibe Başlayın"
              desc="Program, deneme sonucu ve kazanımları yönetin. Veli de ilerlemeyi gerçek zamanlı takip eder."
            />
          </div>
        </div>
      </section>

      {/* ── Roles ── */}
      <section className={styles.roles}>
        <div className={styles.sectionInner}>
          <div className={styles.rolesGrid}>
            <div className={styles.roleCard}>
              <div className={styles.roleIcon} style={{ background: '#2563eb18', color: '#2563eb' }}>
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2" /><circle cx="12" cy="7" r="4" />
                </svg>
              </div>
              <h3>Rehber Koç</h3>
              <ul className={styles.roleList}>
                <li>Öğrenci bazlı haftalık program oluştur</li>
                <li>Deneme sonuçlarını ve netleri gir</li>
                <li>Konu kazanımlarını kaydet</li>
                <li>Tüm öğrencileri tek dashboard'dan izle</li>
                <li>Toplantıları ve takvimi yönet</li>
              </ul>
            </div>
            <div className={styles.roleCard}>
              <div className={styles.roleIcon} style={{ background: '#7c3aed18', color: '#7c3aed' }}>
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                </svg>
              </div>
              <h3>Öğrenci (Mobil)</h3>
              <ul className={styles.roleList}>
                <li>Günlük yapılacaklar listesini gör</li>
                <li>Programı modifiye et, hocaya ilet</li>
                <li>Konu ilerlemeni anlık izle</li>
                <li>Deneme sonuçlarını ve trendini gör</li>
                <li>Kitaplık ve hedef takibi</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* ── CTA ── */}
      <section className={styles.ctaSection}>
        <div className={styles.ctaInner}>
          <h2 className={styles.ctaTitle}>Hemen başlayın</h2>
          <p className={styles.ctaSub}>
            Ücretsiz hesap oluşturun, dakikalar içinde öğrencilerinizi ekleyin.
          </p>
          <div className={styles.ctaActions}>
            <Link to="/kayit" className={styles.btnWhite}>Hesap Oluştur</Link>
            <Link to="/giris" className={styles.btnWhiteOutline}>Giriş Yap</Link>
          </div>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className={styles.footer}>
        <div className={styles.footerInner}>
          <span className={styles.footerBrand}>Rehberim</span>
          <span className={styles.footerCopy}>© 2026 Rehberim. Tüm hakları saklıdır.</span>
        </div>
      </footer>

    </div>
  );
}
