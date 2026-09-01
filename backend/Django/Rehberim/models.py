from datetime import date, datetime, time, timedelta

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class Subject(models.Model):
    """Ders. Kategorisi (TYT/AYT/Okul) öğrencinin sınıf düzeyine göre gösterilir."""
    class Category(models.TextChoices):
        TYT = 'tyt', 'TYT'
        AYT = 'ayt', 'AYT'
        SCHOOL = 'okul', 'Okul Dersi'

    name = models.CharField(max_length=100, verbose_name="Ders Adı")
    category = models.CharField(max_length=4, choices=Category.choices, verbose_name="Kategori")
    # Sınavdaki soru sayısı = o dersten alınabilecek maksimum net. Sınav dersleri
    # (TYT/AYT) için doludur; okul dersleri sınav dersi olmadığından 0'dır.
    question_count = models.PositiveSmallIntegerField(
        default=0, verbose_name="Soru Sayısı (maks. net)",
    )

    class Meta:
        verbose_name = "Ders"
        verbose_name_plural = "Dersler"
        ordering = ['category', 'name']
        # Aynı kategoride aynı isimde iki ders olmasın (TYT Matematik / AYT Matematik ayrı geçerli)
        unique_together = ('name', 'category')

    def __str__(self):
        if self.category == self.Category.SCHOOL:
            return self.name
        return f"{self.get_category_display()} {self.name}"


class ExamSource(models.TextChoices):
    """Denemenin nerede çözüldüğü (E1).

    Öğrenci bazen evde tek başına deneme çözer, bazen kurum geneli bir sınav olur.
    İkisi aynı kefeye konulamaz: kurumsal sınav gözetimli ve aynı anda herkesle
    aynı koşulda, kişisel deneme değil. İstatistikte ayrıştırılabilsin diye ayrı
    tutulur.
    """
    PERSONAL = 'personal', 'Kişisel'
    INSTITUTIONAL = 'institutional', 'Kurumsal'


class ExamResult(models.Model):
    student = models.ForeignKey('accounts.Student', on_delete=models.CASCADE, related_name='exam_results')
    exam_type = models.CharField(
        max_length=3, choices=[('tyt', 'TYT'), ('ayt', 'AYT')],
        blank=True, verbose_name="Sınav Türü",
    )
    # Varsayılan kişisel: öğrencinin kendi başına çözdüğü deneme daha sık ve mevcut
    # kayıtların tamamı bu türden (migration da onları böyle işaretler).
    source = models.CharField(
        max_length=13, choices=ExamSource.choices, default=ExamSource.PERSONAL,
        verbose_name="Deneme Türü",
    )
    name = models.CharField(max_length=120, blank=True, verbose_name="Sınav Adı")
    exam_date = models.DateField(verbose_name="Tarih")

    class Meta:
        verbose_name = "Sınav Sonucu"
        verbose_name_plural = "Sınav Sonuçları"
        ordering = ['-exam_date']

    @property
    def total_net(self):
        """Ders bazlı netlerin otomatik toplamı."""
        return round(sum(n.net for n in self.subject_nets.all()), 2)

    @property
    def is_institutional(self) -> bool:
        return self.source == ExamSource.INSTITUTIONAL

    def __str__(self):
        etiket = self.name or self.get_exam_type_display() or "Sınav"
        return f"{etiket} - {self.student.user.get_full_name()} ({self.exam_date})"


class SubjectNet(models.Model):
    """Bir sınavda tek bir dersin sonucu.

    Öğrenci **doğru** ve **yanlış** sayısını girer; **boş** = soru sayısı - doğru - yanlış
    (türetilir). **Net** = doğru - yanlış/4 (sunucuda hesaplanır, `net` alanında tutulur
    ki `ExamResult.total_net` toplaması tek alandan çalışsın)."""
    exam_result = models.ForeignKey(ExamResult, on_delete=models.CASCADE, related_name='subject_nets')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='nets')
    correct = models.PositiveSmallIntegerField(default=0, verbose_name="Doğru")
    wrong = models.PositiveSmallIntegerField(default=0, verbose_name="Yanlış")
    net = models.FloatField(default=0, verbose_name="Net")

    class Meta:
        verbose_name = "Ders Neti"
        verbose_name_plural = "Ders Netleri"
        unique_together = ('exam_result', 'subject')

    @staticmethod
    def compute_net(correct: int, wrong: int) -> float:
        """Net = doğru - yanlış/4 (2 ondalığa yuvarlı)."""
        return round(correct - wrong / 4, 2)

    @property
    def blank(self) -> int | None:
        """Boş = soru sayısı - doğru - yanlış (ders soru sayısı biliniyorsa)."""
        qc = self.subject.question_count
        if not qc:
            return None
        return max(0, qc - self.correct - self.wrong)

    def save(self, *args, **kwargs):
        self.net = self.compute_net(self.correct, self.wrong)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.subject}: {self.correct}D {self.wrong}Y ({self.net} net)"


class TaskType(models.Model):
    """Görev tipi (Test, Deneme, Konu Çalışması, Video İzleme...). Admin'den genişletilebilir."""
    name = models.CharField(max_length=50, unique=True, verbose_name="Görev Tipi")

    class Meta:
        verbose_name = "Görev Tipi"
        verbose_name_plural = "Görev Tipleri"
        ordering = ['name']

    def __str__(self):
        return self.name


class Publisher(models.Model):
    """Yayınevi (referans veri). Kitap eklerken dropdown'ı doldurur. Katalog admin/
    seed ile yönetilir; öğrenci listede olmayan bir yayınevini serbest metin olarak
    da girebilir (bkz. `Book.publisher`)."""
    name = models.CharField(max_length=100, unique=True, verbose_name="Yayınevi")
    order = models.PositiveSmallIntegerField(default=0, verbose_name="Sıra")

    class Meta:
        verbose_name = "Yayınevi"
        verbose_name_plural = "Yayınevleri"
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


class WeeklyProgram(models.Model):
    """Bir öğrenciye ait, görüşme gününden başlayan çalışma programı.

    Uzunluk esnektir (`day_count`, varsayılan 7): rehber Salı günü, geçmiş
    Pazartesiden başlayan 5 günlük bir program da açabilir. Aynı öğrencinin iki
    programının tarih aralığı **örtüşemez** (bkz. `find_overlap`).

    İki mod: 'timed' (saatlik dilimli) veya 'untimed' (sadece o güne yapılacaklar).
    """
    class ScheduleType(models.TextChoices):
        TIMED = 'timed', 'Saatli'
        UNTIMED = 'untimed', 'Saatsiz'

    student = models.ForeignKey(
        'accounts.Student', on_delete=models.CASCADE, related_name='programs',
        verbose_name="Öğrenci",
    )
    counselor = models.ForeignKey(
        'accounts.Counselor', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='programs', verbose_name="Oluşturan Rehber",
    )
    start_date = models.DateField(verbose_name="Başlangıç (Görüşme Günü)")
    # Programın kaç gün sürdüğü. 7 = klasik hafta; rehber atamadan önce değiştirebilir.
    day_count = models.PositiveSmallIntegerField(
        default=7, validators=[MinValueValidator(1), MaxValueValidator(31)],
        verbose_name="Gün Sayısı",
    )
    schedule_type = models.CharField(
        max_length=8, choices=ScheduleType.choices, default=ScheduleType.TIMED,
        verbose_name="Program Tipi",
    )
    note = models.CharField(max_length=255, blank=True, verbose_name="Not")
    # Haftalık onay: hafta bitince rehber, öğrencinin "yaptım" dediklerini toplantıda
    # kontrol edip programı mühürler. Onaylanmamış program veliye hiç gösterilmez ve
    # onaydan sonra öğrenci görevlerine dokunamaz (bkz. `is_locked_for_student`).
    approved_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Onay Zamanı",
    )
    approved_by = models.ForeignKey(
        'accounts.Counselor', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='approved_programs', verbose_name="Onaylayan Rehber",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Haftalık Program"
        verbose_name_plural = "Haftalık Programlar"
        ordering = ['-start_date']
        # Not: "aynı öğrenciye aynı başlangıç günü için tek program" kısıtı kalktı;
        # yerini tarih aralığı örtüşme kontrolü aldı (find_overlap). Uzunluk artık
        # değişken olduğundan tek bir başlangıç gününü kilitlemek yetmiyor.

    @property
    def end_date(self) -> date:
        """Programın son günü (dahil): başlangıç + gün sayısı - 1."""
        return self.start_date + timedelta(days=self.day_count - 1)

    @property
    def is_timed(self) -> bool:
        return self.schedule_type == self.ScheduleType.TIMED

    def covers(self, day: date) -> bool:
        return self.start_date <= day <= self.end_date

    @property
    def is_approved(self) -> bool:
        return self.approved_at is not None

    @property
    def is_finished(self) -> bool:
        """Pencere kapandı mı? Onay ancak son gün geçtikten sonra verilebilir."""
        return self.end_date < timezone.localdate()

    def compliance(self) -> dict:
        """Bu programa **süre** üzerinden ne kadar uyulduğu.

        Karar (kullanıcı, 25 Ağu 2026): yüzde görev sayısı değil **süre**
        üzerinden hesaplanır — 20 dk'lık bir tekrar ile 3 saatlik bir deneme
        aynı ağırlıkta sayılmamalı.

        Paydaya yalnızca `counts_as_study` bloklar girer: dış meşguliyet (okul,
        antrenman, doktor) çalışma değildir, denemeler ise çalışmadır — B3'ün
        haftalık saat hesabıyla **aynı küme**, iki sayı birbirini tutsun diye.

        Saatsiz programda (ya da süresi girilmemiş bloklarda) süre yoktur; o
        zaman görev sayısına düşülür ve `basis` bunu söyler.
        """
        tasks = [t for t in self.tasks.all() if t.counts_as_study]
        total_min = sum(t.duration_minutes or 0 for t in tasks)
        done_min = sum(t.duration_minutes or 0 for t in tasks if t.is_completed)
        done_count = sum(1 for t in tasks if t.is_completed)

        if total_min:
            percent = round(done_min / total_min * 100)
            basis = 'duration'
        elif tasks:
            percent = round(done_count / len(tasks) * 100)
            basis = 'count'
        else:
            percent = None
            basis = 'empty'
        return {
            'percent': percent,
            'basis': basis,
            'total_minutes': total_min,
            'completed_minutes': done_min,
            'total_tasks': len(tasks),
            'completed_tasks': done_count,
            # Pencere 7 gün olmak zorunda değil; panel gibi burada da haftalık hıza
            # çevrilmiş saat veriliyor ki kısa programlı öğrenci az çalışıyor görünmesin.
            'study_hours': round(total_min / 60, 1),
            # `study_hours` planlanan, `completed_hours` gerçekten çalışılan saat —
            # veli ekranı "bu hafta kaç saat çalıştı" için ikincisini kullanır (E3).
            'completed_hours': round(done_min / 60, 1),
            'weekly_hours': round((total_min / 60) * (7 / self.day_count), 1),
        }

    def approve(self, counselor) -> None:
        self.approved_at = timezone.now()
        self.approved_by = counselor
        self.save(update_fields=['approved_at', 'approved_by', 'updated_at'])

    def revoke_approval(self) -> None:
        self.approved_at = None
        self.approved_by = None
        self.save(update_fields=['approved_at', 'approved_by', 'updated_at'])

    @classmethod
    def find_overlap(cls, student, start_date: date, day_count: int,
                     exclude_pk: int | None = None) -> "WeeklyProgram | None":
        """Verilen pencereyle çakışan ilk programı döndürür (yoksa None).

        Pencereler kapalı aralıktır; iki aralık kesişir ⇔ `a.start <= b.end` ve
        `b.start <= a.end`. `end_date` DB alanı değil türetilen bir property
        olduğundan üst sınır SQL'de, alt sınır Python'da elenir — bir öğrencinin
        program sayısı küçük olduğu için bu yeterli."""
        end_date = start_date + timedelta(days=day_count - 1)
        qs = cls.objects.filter(student=student, start_date__lte=end_date).order_by('start_date')
        if exclude_pk is not None:
            qs = qs.exclude(pk=exclude_pk)
        return next((p for p in qs if p.end_date >= start_date), None)

    @classmethod
    def first_free_day(cls, student) -> date:
        """Öğrenciye program atanmamış ilk gün — yeni programın varsayılan başlangıcı.

        Son programın bitişinden sonraki gün; hiç program yoksa bugün."""
        latest = cls.objects.filter(student=student).order_by('-start_date').first()
        if latest is None:
            return timezone.localdate()
        return max(latest.end_date + timedelta(days=1), timezone.localdate())

    def __str__(self) -> str:
        return (f"{self.student.user.get_full_name()} — "
                f"{self.start_date} ({self.day_count} gün)")


class BlockKind(models.TextChoices):
    """Programdaki bir bloğun ne olduğu.

    - `study`   : normal çalışma bloğu (ders + metod). Varsayılan.
    - `external`: okul dersi, dershane, antrenman, doktor randevusu gibi çalışma
                  **dışı** meşguliyet. Programda yer kaplar ama haftalık çalışma
                  saatine sayılmaz (bkz. `counts_as_study`).
    - `exam`    : deneme bloğu. Ders bazlı olabilir (`subject`) ya da genel
                  (`exam_scope` = TYT/AYT, ders seçilmeden).
    """
    STUDY = 'study', 'Çalışma'
    EXTERNAL = 'external', 'Dış Meşguliyet'
    EXAM = 'exam', 'Deneme'


class ExamScope(models.TextChoices):
    """Genel deneme bloğunun kapsamı — ders seçilmeden 'Genel TYT/AYT denemesi'."""
    TYT = 'tyt', 'Genel TYT'
    AYT = 'ayt', 'Genel AYT'


class Task(models.Model):
    """Bir program bloğu: DERS + METOD + başlık. Haftalık programa bir güne eklenir;
    saatli programda saat+süreyle (çalışma bloğu), saatsiz programda sadece güne.

    Blok türü (`kind`) bloğun çalışma mı, dış meşguliyet mi, deneme mi olduğunu
    belirler; yalnızca çalışma ve deneme blokları haftalık çalışma saatine sayılır."""
    program = models.ForeignKey(
        WeeklyProgram, on_delete=models.CASCADE, related_name='tasks',
        verbose_name="Program",
    )
    subject = models.ForeignKey(
        Subject, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='tasks', verbose_name="Ders",
    )
    task_type = models.ForeignKey(
        TaskType, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='tasks', verbose_name="Metod",
    )
    # Opsiyonel kaynak: öğrencinin kütüphanesindeki bir kitap. Görev doğrudan bir
    # kitaptan eklendiğinde (ders akışı yerine) dersi bu kitaptan türetilir.
    book = models.ForeignKey(
        'Book', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='tasks', verbose_name="Kaynak Kitap",
    )
    kind = models.CharField(
        max_length=8, choices=BlockKind.choices, default=BlockKind.STUDY,
        verbose_name="Blok Türü",
    )
    # Yalnızca kind='exam' ve ders seçilmemiş "genel deneme" bloklarında dolu.
    exam_scope = models.CharField(
        max_length=3, choices=ExamScope.choices, blank=True, default='',
        verbose_name="Deneme Kapsamı",
    )
    title = models.CharField(max_length=100, blank=True, verbose_name="Başlık")
    description = models.TextField(blank=True)
    date = models.DateField(verbose_name="Gün")
    # Saatli programda dolu; saatsizde boş kalır
    start_time = models.TimeField(null=True, blank=True, verbose_name="Başlangıç Saati")
    duration_minutes = models.PositiveIntegerField(null=True, blank=True, verbose_name="Süre (dk)")
    is_completed = models.BooleanField(default=False, verbose_name="Tamamlandı")
    created_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_tasks', verbose_name="Ekleyen",
    )
    order = models.PositiveSmallIntegerField(default=0, verbose_name="Sıra")

    class Meta:
        verbose_name = "Görev"
        verbose_name_plural = "Görevler"
        ordering = ['date', 'start_time', 'order']

    @property
    def end_time(self) -> time | None:
        """Saatli görevlerde bitiş saati (başlangıç + süre); saatsizde None."""
        if self.start_time is None or self.duration_minutes is None:
            return None
        return (datetime.combine(self.date, self.start_time)
                + timedelta(minutes=self.duration_minutes)).time()

    @property
    def counts_as_study(self) -> bool:
        """Bu blok haftalık çalışma saatine sayılır mı? Dış meşguliyetler sayılmaz."""
        return self.kind != BlockKind.EXTERNAL

    @property
    def label(self) -> str:
        """Blokta gösterilecek ad: başlık > genel deneme kapsamı > ders."""
        if self.title:
            return self.title
        if self.exam_scope:
            return ExamScope(self.exam_scope).label
        return str(self.subject) if self.subject_id else "Görev"

    def __str__(self) -> str:
        return f"{self.date} — {self.label}"


class BlockDurationDefault(models.Model):
    """Rehberin bir blok kombinasyonu için en son kullandığı süre.

    Hoca bir öğrenciye "TYT Türkçe → Soru → Paragraf = 20 dk" dediyse, aynı bloğu
    başka bir öğrenciye kurarken de 20 dk varsayılan gelir: hafıza **rehber
    özelinde**, öğrenci özelinde değildir.

    Kombinasyon (ders, metod, konu) üçlüsüdür — "Matematik denemesi 1 saat" demek,
    "Matematik soru çözümü de 1 saat" demek değildir. Konu, `Task.title` metnidir
    (web'de `/api/topics/` kataloğundan seçilir); konusuz blok da kendi başına bir
    kombinasyondur, o yüzden `topic` boş metin olabilir ama NULL olamaz.

    Yalnızca **ders ve metodu belli** bloklar hatırlanır; dış meşguliyet blokları
    ve ders seçilmemiş genel deneme blokları kapsam dışıdır.
    """
    counselor = models.ForeignKey(
        'accounts.Counselor', on_delete=models.CASCADE,
        related_name='block_duration_defaults', verbose_name="Rehber",
    )
    subject = models.ForeignKey(
        Subject, on_delete=models.CASCADE,
        related_name='block_duration_defaults', verbose_name="Ders",
    )
    task_type = models.ForeignKey(
        TaskType, on_delete=models.CASCADE,
        related_name='block_duration_defaults', verbose_name="Metod",
    )
    topic = models.CharField(max_length=100, blank=True, default='', verbose_name="Konu")
    duration_minutes = models.PositiveIntegerField(verbose_name="Süre (dk)")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Blok Süre Hafızası"
        verbose_name_plural = "Blok Süre Hafızası"
        # topic NULL olamadığı için bu kısıt SQLite'ta da gerçekten uygulanır.
        unique_together = ('counselor', 'subject', 'task_type', 'topic')
        ordering = ['subject', 'task_type', 'topic']

    @classmethod
    def remember(cls, counselor, task: Task) -> None:
        """Kaydedilen bir görevden hafızayı sessizce günceller (son kullanılan kazanır).

        Hatırlanamayacak blokları (rehber yok, ders/metod/süre eksik, dış
        meşguliyet) sessizce atlar — görev kaydını hiçbir koşulda bozmaz.
        """
        if counselor is None or task.duration_minutes is None:
            return
        if task.subject_id is None or task.task_type_id is None:
            return
        if task.kind == BlockKind.EXTERNAL:
            return
        cls.objects.update_or_create(
            counselor=counselor,
            subject_id=task.subject_id,
            task_type_id=task.task_type_id,
            topic=(task.title or '').strip()[:100],
            defaults={'duration_minutes': task.duration_minutes},
        )

    def __str__(self) -> str:
        parts = [str(self.subject), self.task_type.name]
        if self.topic:
            parts.append(self.topic)
        return f"{' · '.join(parts)} = {self.duration_minutes} dk"


class Goal(models.Model):
    """Öğrencinin kendine koyduğu hedef. Türüne göre farklı girdi ister.

    Öğrenci oluşturur/düzenler/siler; rehberi ve velisi yalnızca görür (salt-okur).

    Türler:
    - deneme_net  : bir sınav neti hedefi (TYT/AYT; ders boşsa TOPLAM net) → sayı ister.
    - konu        : bir konuyu bitirme → ileride eklenecek Konu listesinden seçilir.
    - kitap_bitirme: bir soru/test kitabını bitirme (ör. 'TYT Türkçe 345 Yay.').
    - kitap_okuma : bir edebiyat kitabını okuma (ör. 'Suç ve Ceza').
      → kitap türleri ileride eklenecek Kitap listesinden seçilir.
    """
    class GoalType(models.TextChoices):
        DENEME_NETI = 'deneme_net', 'Deneme Neti'
        KONU_BITIRME = 'konu', 'Konu Bitirme'
        KITAP_BITIRME = 'kitap_bitirme', 'Kitap Bitirme'   # soru/test kitabı
        KITAP_OKUMA = 'kitap_okuma', 'Kitap Okuma'         # edebiyat kitabı

    class ExamScope(models.TextChoices):
        TYT = 'tyt', 'TYT'
        AYT = 'ayt', 'AYT'

    student = models.ForeignKey(
        'accounts.Student', on_delete=models.CASCADE, related_name='goals',
        verbose_name="Öğrenci",
    )
    goal_type = models.CharField(
        max_length=13, choices=GoalType.choices, verbose_name="Hedef Türü",
    )
    title = models.CharField(max_length=150, blank=True, verbose_name="Hedef")
    description = models.TextField(blank=True, verbose_name="Açıklama")
    target_date = models.DateField(null=True, blank=True, verbose_name="Hedef Tarihi")
    is_achieved = models.BooleanField(default=False, verbose_name="Ulaşıldı")

    # --- Deneme neti hedefi (goal_type=deneme_net) ---------------------------
    exam_scope = models.CharField(
        max_length=3, choices=ExamScope.choices, blank=True, verbose_name="Sınav Türü",
    )
    subject = models.ForeignKey(
        Subject, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='goals', verbose_name="Ders",  # boş = toplam net
    )
    target_net = models.FloatField(null=True, blank=True, verbose_name="Hedef Net")

    # --- Konu / Kitap hedefleri (referanslar ileride bağlanacak) -------------
    # TODO: Konu ve Kitap modelleri eklenince FK olarak bağla:
    #   topic = FK('Rehberim.Topic')  → goal_type=konu
    #   book  = FK('Rehberim.Book')   → goal_type=kitap_bitirme / kitap_okuma
    # (kitap türü Book modelinde ayrılır: soru kitabı vs. okuma kitabı)
    # O zamana kadar bu türlerde hedef, serbest metin `title` ile tutulur.

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Hedef"
        verbose_name_plural = "Hedefler"
        ordering = ['is_achieved', 'target_date', '-created_at']

    def clean(self):
        super().clean()
        from django.core.exceptions import ValidationError
        errors = {}
        if self.goal_type == self.GoalType.DENEME_NETI:
            if self.target_net is None:
                errors['target_net'] = "Deneme neti hedefi için net değeri gereklidir."
            elif self.target_net < 0:
                errors['target_net'] = "Net negatif olamaz."
            if not self.exam_scope:
                errors['exam_scope'] = "Deneme neti hedefi için sınav türü (TYT/AYT) gereklidir."
        else:
            # Deneme'ye özgü alanlar yalnızca deneme neti hedefinde kullanılır.
            if self.exam_scope or self.target_net is not None or self.subject_id:
                errors['goal_type'] = "Deneme alanları yalnızca 'Deneme Neti' hedefinde kullanılır."
        if errors:
            raise ValidationError(errors)

    def display_label(self) -> str:
        """Kullanıcıya gösterilecek etiket. Deneme netinde alanlardan üretilir."""
        if self.goal_type == self.GoalType.DENEME_NETI and self.target_net is not None:
            net = int(self.target_net) if float(self.target_net).is_integer() else self.target_net
            if self.subject_id:
                # Subject etiketi zaten TYT/AYT içerir (ör. 'AYT Matematik')
                return f"{self.subject} {net} net"
            scope = self.get_exam_scope_display() or ""
            return f"{scope} Toplam {net} net".strip()
        return self.title or self.get_goal_type_display()

    def __str__(self) -> str:
        return f"{self.student.user.get_full_name()} — {self.display_label()}"


class Book(models.Model):
    """Öğrencinin kitaplığındaki bir kitap.

    Öğrenci oluşturur/düzenler/siler; rehberi ve velisi yalnızca görür (salt-okur).

    İki tür:
    - ders_kitabi  : bir derse ait çalışma kitabı. `subject` FK ile tür+ders birlikte
      tutulur (ör. 'TYT Türkçe', 'AYT Matematik', '11. Sınıf Fizik' — Subject zaten
      kategoriyi içerir). Ayrıca yayınevi ve kitap formatı (Paragraf / Konu Anlatımı /
      Soru Bankası / Deneme) girilir.
    - okuma_kitabi : ders dışı okuma kitabı (ör. 'Suç ve Ceza'). Sadece başlık +
      opsiyonel yazar; subject/yayınevi/format kullanılmaz.

    NOT (ileride): Bir kitabın üniteleri ayrı bir `BookUnit` modeliyle tutulup öğrenci
    her üniteyi tamamlandı/devam/başlanmadı olarak işaretleyebilecek; tamamlanma
    yüzdesi oradan hesaplanacak. Şimdilik kitap seviyesinde `status` yeterli.
    """
    class BookKind(models.TextChoices):
        DERS = 'ders', 'Ders Kitabı'
        OKUMA = 'okuma', 'Okuma Kitabı'

    class BookFormat(models.TextChoices):
        PARAGRAF = 'paragraf', 'Paragraf'
        KONU_ANLATIMI = 'konu_anlatimi', 'Konu Anlatımı'
        SORU_BANKASI = 'soru_bankasi', 'Soru Bankası'
        DENEME = 'deneme', 'Deneme'

    class Status(models.TextChoices):
        NOT_STARTED = 'baslanmadi', 'Başlanmadı'
        IN_PROGRESS = 'devam', 'Devam Ediliyor'
        COMPLETED = 'tamamlandi', 'Tamamlandı'

    student = models.ForeignKey(
        'accounts.Student', on_delete=models.CASCADE, related_name='books',
        verbose_name="Öğrenci",
    )
    kind = models.CharField(
        max_length=5, choices=BookKind.choices, default=BookKind.DERS,
        verbose_name="Kitap Türü",
    )
    title = models.CharField(max_length=200, blank=True, verbose_name="Kitap Adı")
    description = models.TextField(blank=True, verbose_name="Açıklama")
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.NOT_STARTED,
        verbose_name="Durum",
    )

    # --- Ders kitabı alanları (kind=ders) ------------------------------------
    subject = models.ForeignKey(
        Subject, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='books', verbose_name="Ders",  # 'TYT Türkçe' tür+dersi kapsar
    )
    publisher = models.CharField(max_length=100, blank=True, verbose_name="Yayınevi")
    book_format = models.CharField(
        max_length=13, choices=BookFormat.choices, blank=True, verbose_name="Format",
    )

    # --- Okuma kitabı alanları (kind=okuma) ----------------------------------
    author = models.CharField(max_length=150, blank=True, verbose_name="Yazar")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Kitap"
        verbose_name_plural = "Kitaplar"
        ordering = ['status', 'kind', '-created_at']

    def clean(self):
        super().clean()
        from django.core.exceptions import ValidationError
        errors = {}
        if self.kind == self.BookKind.DERS:
            if self.subject_id is None:
                errors['subject'] = "Ders kitabı için ders seçilmelidir."
            if not self.book_format:
                errors['book_format'] = "Ders kitabı için format seçilmelidir."
            if self.author:
                errors['author'] = "Yazar yalnızca okuma kitabında kullanılır."
        else:  # OKUMA
            if not self.title:
                errors['title'] = "Okuma kitabı için kitap adı gereklidir."
            if self.subject_id or self.publisher or self.book_format:
                errors['kind'] = "Ders/yayınevi/format alanları yalnızca ders kitabında kullanılır."
        if errors:
            raise ValidationError(errors)

    def display_label(self) -> str:
        """Kullanıcıya gösterilecek etiket."""
        if self.title:
            return self.title
        if self.kind == self.BookKind.DERS and self.subject_id:
            parcalar = [str(self.subject), self.publisher, self.get_book_format_display()]
            return " ".join(p for p in parcalar if p)
        return self.get_kind_display()

    def populate_topics(self) -> int:
        """Ders kitabının içeriğini KONU kataloğundan otomatik doldurur.

        Kitabın dersi (subject) sınav dersiyse ilgili okul dersinin belirli
        sınıflarındaki konuları, okul dersiyse öğrencinin kendi sınıfını alır:
        - TYT [ders] → 9. ve 10. sınıf,  AYT [ders] → 11. ve 12. sınıf.
        - Okul dersi → öğrencinin sınıfı.
        Müfredat öğrencinin sınıfına göre (eski/maarif) seçilir.

        Yeni `BookTopic` satırları oluşturur (var olanlara dokunmaz). Eklenen
        satır sayısını döner. Okuma kitabında / dersi olmayan kitapta hiçbir şey yapmaz.
        """
        if self.kind != self.BookKind.DERS or self.subject_id is None:
            return 0
        # Sınav dersi adını okul dersi adına çevir (topics okul derslerinde tutulur)
        school_name = EXAM_TO_SCHOOL_SUBJECT.get(self.subject.name, self.subject.name)
        school_subject = Subject.objects.filter(
            name=school_name, category=Subject.Category.SCHOOL
        ).first()
        if school_subject is None:
            return 0
        if self.subject.category == Subject.Category.TYT:
            grades = [Grade.GRADE_9, Grade.GRADE_10]
        elif self.subject.category == Subject.Category.AYT:
            grades = [Grade.GRADE_11, Grade.GRADE_12]
        else:  # okul dersi → öğrencinin sınıfı
            grades = [self.student.grade]
        # grade metin alanı ('9','10'...); sayısal sırala ki 9. sınıf 10'dan önce gelsin.
        topics = sorted(
            Topic.objects.filter(
                subject=school_subject, grade__in=grades, curriculum=self.student.curriculum,
            ),
            key=lambda t: (int(t.grade), t.order),
        )
        added = 0
        # Var olan en yüksek sıradan devam et (idempotent yeniden çağrımlar için)
        start = self.book_topics.aggregate(m=models.Max('order'))['m']
        order = 0 if start is None else start + 1
        for t in topics:
            _, created = BookTopic.objects.get_or_create(
                book=self, topic=t, defaults={'order': order},
            )
            if created:
                order += 1
                added += 1
        return added

    def __str__(self) -> str:
        return f"{self.student.user.get_full_name()} — {self.display_label()}"


# Sınav dersi adı → okul dersi adı (konu kataloğu okul derslerine bağlıdır).
# Aynı isimliler otomatik eşleşir; farklı isimliler burada verilir.
EXAM_TO_SCHOOL_SUBJECT = {
    "Türkçe": "Türk Dili ve Edebiyatı",
    "Tarih-1": "Tarih",
    "Tarih-2": "Tarih",
    "Coğrafya-1": "Coğrafya",
    "Coğrafya-2": "Coğrafya",
}


class BookTopic(models.Model):
    """Bir kitabın içindeki tek bir KONU + öğrencinin o kitaptaki ilerlemesi.

    Ders kitabı oluşturulunca `Book.populate_topics()` ile katalogdan otomatik dolar.
    `TopicProgress`'ten ayrıdır: o, öğrencinin genel konu hâkimiyetidir; bu ise
    *o kitap özelinde* ilerlemedir (öğrencide aynı dersten birden çok kitap olabilir).
    """
    class Status(models.TextChoices):
        NOT_STARTED = 'baslanmadi', 'Başlanmadı'
        IN_PROGRESS = 'devam', 'Devam Ediyor'
        COMPLETED = 'tamamlandi', 'Tamamlandı'

    book = models.ForeignKey(
        'Book', on_delete=models.CASCADE, related_name='book_topics', verbose_name="Kitap",
    )
    topic = models.ForeignKey(
        'Topic', on_delete=models.CASCADE, related_name='book_links', verbose_name="Konu",
    )
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.NOT_STARTED,
        verbose_name="Durum",
    )
    tests_solved = models.PositiveIntegerField(default=0, verbose_name="Çözülen Test Sayısı")
    order = models.PositiveSmallIntegerField(default=0, verbose_name="Sıra")

    class Meta:
        verbose_name = "Kitap Konusu"
        verbose_name_plural = "Kitap Konuları"
        ordering = ['book', 'order']
        unique_together = ('book', 'topic')

    def save(self, *args, **kwargs):
        # "Tamamlandı"ya geçişte öğrencinin o konudaki hâkimiyet seviyesini +1 yükselt
        # (tavan 5). Yalnızca geçişte tetiklenir; tekrar kaydetmek üst üste artırmaz.
        newly_completed = self.status == self.Status.COMPLETED and (
            self.pk is None
            or BookTopic.objects.filter(pk=self.pk)
            .exclude(status=self.Status.COMPLETED).exists()
        )
        super().save(*args, **kwargs)
        if newly_completed:
            self._bump_topic_progress()

    def _bump_topic_progress(self) -> None:
        """İlgili (öğrenci, konu) TopicProgress seviyesini bir kademe yükseltir."""
        tp, _ = TopicProgress.objects.get_or_create(
            student=self.book.student, topic=self.topic)
        if tp.level < 5:
            tp.level += 1
            tp.save(update_fields=['level', 'updated_at'])

    def __str__(self) -> str:
        return f"{self.book.display_label()} — {self.topic.name} ({self.get_status_display()})"


class CalendarEvent(models.Model):
    """Rehberin kendi takvimindeki etkinlik.

    `student` boşsa yalnızca rehberin kişisel notudur (ör. 'Özdebir TYT — 16 Tem).
    `student` doluysa o öğrenciyle ilgili bir etkinliktir (ör. 'Cumartesi 14-15
    görüşme'); ilgili öğrenci ve velisi bunu salt-okur görür. Uygulama içi
    randevulaşma yoktur — rehber tek taraflı ekler, öğrenci haberdar olur.
    """
    counselor = models.ForeignKey(
        'accounts.Counselor', on_delete=models.CASCADE, related_name='calendar_events',
        verbose_name="Rehber",
    )
    student = models.ForeignKey(
        'accounts.Student', on_delete=models.CASCADE, null=True, blank=True,
        related_name='calendar_events', verbose_name="İlgili Öğrenci",
    )
    title = models.CharField(max_length=150, verbose_name="Başlık")
    description = models.TextField(blank=True, verbose_name="Açıklama")
    date = models.DateField(verbose_name="Tarih")
    start_time = models.TimeField(null=True, blank=True, verbose_name="Başlangıç Saati")
    end_time = models.TimeField(null=True, blank=True, verbose_name="Bitiş Saati")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Takvim Etkinliği"
        verbose_name_plural = "Takvim Etkinlikleri"
        ordering = ['date', 'start_time']

    @property
    def is_all_day(self) -> bool:
        """Saat girilmemişse tüm-gün etkinliği (ör. 'Özdebir TYT 16 Temmuz')."""
        return self.start_time is None

    def __str__(self) -> str:
        kim = f" ({self.student.user.get_full_name()})" if self.student_id else ""
        return f"{self.date} — {self.title}{kim}"


class AchievementMetric(models.TextChoices):
    """Bir başarımın neyi ölçtüğü (C3)."""
    EXAM_NET = 'exam_net', 'Deneme Neti'
    TOPIC_COMPLETION = 'topic_completion', 'Konu Tamamlama (%)'
    COMPLIANCE = 'compliance', 'Program Uyumu (%)'


class Achievement(models.Model):
    """Rehberin öğrencilerine koyduğu başarım eşiği (C3).

    Başarımlar **rehber başına** tutulur: her rehber kendi listesini Ayarlar'dan
    düzenleyebilsin diye global bir katalog değil, rehbere ait satırlar. Yeni bir
    rehber kaydolduğunda varsayılan set kendisine kopyalanır (`seed_defaults`),
    sonrasında istediğini siler, ekler ya da eşiğini değiştirir — kimseyi
    etkilemez.

    Kazanım **saklanmaz, anlık hesaplanır** (`evaluate_for`): eşik değişince ya da
    bir deneme silinince kayıtla gerçek arasında tutarsızlık kalmasın diye.
    """
    counselor = models.ForeignKey(
        'accounts.Counselor', on_delete=models.CASCADE, related_name='achievements',
        verbose_name="Rehber",
    )
    name = models.CharField(max_length=80, verbose_name="Ad")
    description = models.CharField(max_length=200, blank=True, verbose_name="Açıklama")
    metric = models.CharField(
        max_length=16, choices=AchievementMetric.choices, verbose_name="Ölçüt",
    )
    # Yalnızca `exam_net` için anlamlı: hangi sınavın neti (tyt/ayt).
    scope = models.CharField(
        max_length=3, choices=[('tyt', 'TYT'), ('ayt', 'AYT')],
        blank=True, default='', verbose_name="Kapsam",
    )
    threshold = models.FloatField(verbose_name="Eşik")
    # Silmeden gizlemek için: rehber bir başarımı geçici olarak kapatabilir.
    is_active = models.BooleanField(default=True, verbose_name="Etkin")
    order = models.PositiveSmallIntegerField(default=0, verbose_name="Sıra")

    class Meta:
        verbose_name = "Başarım"
        verbose_name_plural = "Başarımlar"
        ordering = ['order', 'metric', 'threshold']
        unique_together = ('counselor', 'name')

    # Hocanın saydığı eşikler (yol haritası C3). Rehber bunları sonradan
    # değiştirebildiği için burası yalnızca **başlangıç** listesidir.
    DEFAULTS = [
        ('exam_net', 'tyt', 60, "TYT 60 Net", "TYT denemesinde 60 net"),
        ('exam_net', 'tyt', 80, "TYT 80 Net", "TYT denemesinde 80 net"),
        ('exam_net', 'tyt', 90, "TYT 90 Net", "TYT denemesinde 90 net"),
        ('exam_net', 'tyt', 100, "TYT 100 Net", "TYT denemesinde 100 net"),
        ('exam_net', 'tyt', 110, "TYT 110 Net", "TYT denemesinde 110 net"),
        ('topic_completion', '', 25, "Konuların %25'i", "Konuların dörtte biri tamamlandı"),
        ('topic_completion', '', 50, "Konuların %50'si", "Konuların yarısı tamamlandı"),
        ('topic_completion', '', 75, "Konuların %75'i", "Konuların dörtte üçü tamamlandı"),
        ('topic_completion', '', 100, "Tüm Konular", "Bütün konular tamamlandı"),
        ('compliance', '', 60, "Program Uyumu %60", "Onaylı haftalarda %60 uyum"),
        ('compliance', '', 80, "Program Uyumu %80", "Onaylı haftalarda %80 uyum"),
        ('compliance', '', 100, "Tam Uyum", "Onaylı haftalarda %100 uyum"),
    ]

    @classmethod
    def seed_defaults(cls, counselor) -> int:
        """Rehbere varsayılan başarımları kopyalar; zaten varsa dokunmaz.

        Adı çakışanı atladığı için tekrar çağrılması güvenlidir — ama silinmiş bir
        varsayılanı geri getirir, o yüzden yalnızca rehber ilk oluşturulurken ve
        veri migration'ında çağrılır, her okumada değil.
        """
        existing = set(cls.objects.filter(counselor=counselor).values_list('name', flat=True))
        rows = [
            cls(counselor=counselor, metric=metric, scope=scope, threshold=threshold,
                name=name, description=description, order=i)
            for i, (metric, scope, threshold, name, description) in enumerate(cls.DEFAULTS)
            if name not in existing
        ]
        cls.objects.bulk_create(rows)
        return len(rows)

    def evaluate_for(self, student, *, facts: dict) -> dict:
        """Bu başarımın öğrencideki durumu. `facts` bir kez hesaplanıp paylaşılır."""
        value = facts.get(self.metric if self.metric != AchievementMetric.EXAM_NET
                          else f'exam_net_{self.scope or "tyt"}')
        earned = value is not None and value >= self.threshold
        # İlerleme çubuğu için: eşiğin yüzde kaçında.
        progress = 0 if not value or self.threshold <= 0 else min(
            100, round(value / self.threshold * 100))
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'metric': self.metric,
            'scope': self.scope,
            'threshold': self.threshold,
            'value': value,
            'earned': earned,
            'progress': 100 if earned else progress,
        }

    def __str__(self) -> str:
        return f"{self.name} ({self.counselor.user.get_full_name()})"


def student_achievement_facts(student) -> dict:
    """Başarım eşikleriyle karşılaştırılacak ham değerler (C3).

    Bir kez hesaplanıp bütün başarımlara paylaştırılır — her başarım için ayrı
    sorgu atılsa aynı öğrenci için düzinelerce sorgu olurdu.

    - `exam_net_tyt` / `exam_net_ayt`: o türdeki denemelerin **en yüksek** toplam
      neti. Başarım "bir kez ulaştı" demektir, ortalamaya bakılmaz — sonraki kötü
      bir deneme kazanılmış başarımı geri almamalı.
    - `topic_completion`: **seviye 5** konuların, öğrencinin kapsamındaki toplam
      konuya oranı. Payda öğrencinin dersleri (`available_subjects`) ve
      müfredatıyla sınırlı; kayıt tutulmayan konu tamamlanmamış sayılır.
    - `compliance`: onaylı haftaların dakika ağırlıklı uyum yüzdesi (B2 ile aynı
      hesap). Onaysız hafta girmez.
    """
    nets: dict[str, float | None] = {'exam_net_tyt': None, 'exam_net_ayt': None}
    for exam in student.exam_results.prefetch_related('subject_nets'):
        key = f'exam_net_{exam.exam_type}'
        if key in nets:
            total = exam.total_net
            if nets[key] is None or total > nets[key]:
                nets[key] = total

    subject_ids = list(student.available_subjects().values_list('id', flat=True))
    total_topics = Topic.objects.filter(
        subject_id__in=subject_ids, curriculum=student.curriculum,
    ).count()
    done_topics = TopicProgress.objects.filter(
        student=student, level=5, topic__subject_id__in=subject_ids,
        topic__curriculum=student.curriculum,
    ).count()
    topic_pct = round(done_topics / total_topics * 100, 1) if total_topics else None

    total_min = done_min = 0
    for program in student.programs.filter(approved_at__isnull=False).prefetch_related('tasks'):
        c = program.compliance()
        total_min += c['total_minutes']
        done_min += c['completed_minutes']
    compliance_pct = round(done_min / total_min * 100, 1) if total_min else None

    return {
        **nets,
        'topic_completion': topic_pct,
        'compliance': compliance_pct,
        # Arayüzün "12/340 konu" gibi bağlam gösterebilmesi için ham sayılar.
        'topics_total': total_topics,
        'topics_done': done_topics,
    }


class Grade(models.TextChoices):
    """Sınıf düzeyi (9-12). Konular sınıfa göre ayrılır."""
    GRADE_9 = '9', '9. Sınıf'
    GRADE_10 = '10', '10. Sınıf'
    GRADE_11 = '11', '11. Sınıf'
    GRADE_12 = '12', '12. Sınıf'


class Curriculum(models.TextChoices):
    """Müfredat. Türkiye YKS geçiş döneminde iki set konu yürürlükte:

    - `eski`   : mevcut müfredat (bu yılki sınav) → 12. sınıf ve mezunlar.
    - `maarif` : Türkiye Yüzyılı Maarif Modeli (sonraki sınavlar) → 9/10/11. sınıf.
    """
    ESKI = 'eski', 'Mevcut Müfredat'
    MAARIF = 'maarif', 'Maarif Modeli'


class Topic(models.Model):
    """Bir dersin belirli bir sınıf + müfredattaki KONUSU (referans/katalog verisi).

    Ör. (Matematik, 10. sınıf, maarif) → 'Kombinatorik Sayma ve Olasılık'. Her
    (ders, sınıf, müfredat) kombinasyonunun kendine has konu listesi vardır. Katalog
    admin/seed ile yönetilir; öğrencinin bu konudaki ilerlemesi ayrı `TopicProgress`.
    """
    subject = models.ForeignKey(
        Subject, on_delete=models.CASCADE, related_name='topics', verbose_name="Ders",
    )
    grade = models.CharField(max_length=2, choices=Grade.choices, verbose_name="Sınıf")
    curriculum = models.CharField(
        max_length=6, choices=Curriculum.choices, default=Curriculum.MAARIF,
        verbose_name="Müfredat",
    )
    name = models.CharField(max_length=250, verbose_name="Konu")
    order = models.PositiveSmallIntegerField(default=0, verbose_name="Sıra")

    class Meta:
        verbose_name = "Konu"
        verbose_name_plural = "Konular"
        ordering = ['subject', 'grade', 'order', 'name']
        # Aynı ders + sınıf + müfredatta aynı isimde iki konu olmasın
        unique_together = ('subject', 'grade', 'curriculum', 'name')

    def __str__(self) -> str:
        return f"{self.get_grade_display()} {self.subject.name} — {self.name}"


class TopicProgress(models.Model):
    """Bir öğrencinin tek bir KONUDAKI ilerlemesi.

    - `status`: konuyu bitirdi mi? (başlanmadı / biraz = devam / bitti = tamamlandı)
    - `tests_solved`: o konuda çözülen test sayısı (efor göstergesi; ör. 'Kombinasyondan 5 test').

    Öğrenci oluşturur/günceller; rehberi ve velisi yalnızca görür (salt-okur).
    Her (öğrenci, konu) için tek kayıt.
    """
    class Status(models.TextChoices):
        NOT_STARTED = 'baslanmadi', 'Başlanmadı'
        IN_PROGRESS = 'devam', 'Devam Ediyor'   # "biraz bitti"
        COMPLETED = 'tamamlandi', 'Tamamlandı'   # "bitti"

    student = models.ForeignKey(
        'accounts.Student', on_delete=models.CASCADE, related_name='topic_progress',
        verbose_name="Öğrenci",
    )
    topic = models.ForeignKey(
        Topic, on_delete=models.CASCADE, related_name='progress', verbose_name="Konu",
    )
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.NOT_STARTED,
        verbose_name="Durum",
    )
    # Konu hâkimiyet seviyesi: 1 en düşük … 5 en yüksek. Rehber girer; öğrenci bir
    # kitap konusunu tamamlayınca otomatik +1 (bkz. BookTopic.save). Kayıt yoksa
    # kavramsal olarak 1 (en düşük) kabul edilir. Renkler frontend'de eşlenir.
    level = models.PositiveSmallIntegerField(
        default=1, validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Seviye",
    )
    tests_solved = models.PositiveIntegerField(default=0, verbose_name="Çözülen Test Sayısı")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Konu İlerlemesi"
        verbose_name_plural = "Konu İlerlemeleri"
        ordering = ['topic', '-updated_at']
        unique_together = ('student', 'topic')

    def __str__(self) -> str:
        return f"{self.student.user.get_full_name()} — {self.topic.name} ({self.get_status_display()})"


class ProgramTemplate(models.Model):
    """Rehberin tekrar kullanmak için sakladığı isimli 'şablon program' (ör. 'Sayısal 1').

    Haftalık programın (WeeklyProgram) öğrenciden/tarihten bağımsız hâli: görevler
    haftanın gününe (weekday 0-6) göre tutulur. Rehber bir öğrenciye atadığında bu
    şablon somut bir haftaya (WeeklyProgram + Task) materyalize edilir.

    **Rutin:** `student` doldurulup `auto_apply` açılırsa şablon o öğrencinin
    *rutini* olur — öğrenciye yeni bir hafta açıldığında görevler kendiliğinden
    materyalize edilir. `student` boşken şablon geneldir ve yalnızca elle atanır.
    Öğrenci başına en fazla bir otomatik rutin olabilir.

    Rutini **rehber de öğrenci de** kurabilir. Öğrenci kendi rutinini kurduğunda
    `counselor` öğrencinin rehberidir; öğrenci henüz bir rehbere bağlı değilse boş
    kalır. Bu yüzden `counselor` opsiyoneldir — ama bir şablonun en az bir sahibi
    (rehber ya da öğrenci) olmak zorundadır."""
    counselor = models.ForeignKey(
        'accounts.Counselor', on_delete=models.CASCADE, null=True, blank=True,
        related_name='program_templates', verbose_name="Rehber",
    )
    student = models.ForeignKey(
        'accounts.Student', on_delete=models.CASCADE, null=True, blank=True,
        related_name='routines', verbose_name="Öğrenci (rutin ise)",
    )
    auto_apply = models.BooleanField(
        default=False, verbose_name="Yeni haftaya otomatik uygula",
    )
    name = models.CharField(max_length=100, verbose_name="Şablon Adı")
    schedule_type = models.CharField(
        max_length=8, choices=WeeklyProgram.ScheduleType.choices,
        default=WeeklyProgram.ScheduleType.TIMED, verbose_name="Program Tipi",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Program Şablonu"
        verbose_name_plural = "Program Şablonları"
        ordering = ['name']
        constraints = [
            # Sahipsiz şablon olamaz.
            models.CheckConstraint(
                condition=models.Q(counselor__isnull=False) | models.Q(student__isnull=False),
                name='sablonun_sahibi_olmali',
            ),
            # Otomatik uygulanacaksa hangi öğrenciye uygulanacağı belli olmalı.
            models.CheckConstraint(
                condition=models.Q(auto_apply=False) | models.Q(student__isnull=False),
                name='otomatik_rutin_ogrenci_ister',
            ),
            # Bir öğrencinin aynı anda birden fazla otomatik rutini olamaz.
            models.UniqueConstraint(
                fields=['student'], condition=models.Q(auto_apply=True),
                name='ogrenci_basina_tek_otomatik_rutin',
            ),
            # Genel şablonlarda ad rehber içinde benzersiz. (Rutinler hariç tutulur;
            # aynı rehberin iki öğrencisi rutinine aynı adı verebilmeli.)
            models.UniqueConstraint(
                fields=['counselor', 'name'], condition=models.Q(student__isnull=True),
                name='genel_sablon_adi_rehberde_benzersiz',
            ),
            # Rutinlerde ad öğrenci içinde benzersiz.
            models.UniqueConstraint(
                fields=['student', 'name'],
                name='rutin_adi_ogrencide_benzersiz',
            ),
        ]

    def __str__(self) -> str:
        if self.student_id:
            return f"{self.name} — {self.student.user.get_full_name()} rutini"
        if self.counselor_id:
            return f"{self.name} ({self.counselor.user.get_full_name()})"
        return self.name


class TemplateTask(models.Model):
    """Şablondaki tek çalışma bloğu. WeeklyProgram'ın Task'ıyla aynı ama tarih yerine
    haftanın günü (weekday) tutulur; atama sırasında güne çevrilir."""
    template = models.ForeignKey(
        ProgramTemplate, on_delete=models.CASCADE, related_name='tasks', verbose_name="Şablon",
    )
    subject = models.ForeignKey(
        Subject, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='template_tasks', verbose_name="Ders",
    )
    task_type = models.ForeignKey(
        TaskType, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='template_tasks', verbose_name="Metod",
    )
    book = models.ForeignKey(
        'Book', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='template_tasks', verbose_name="Kaynak Kitap",
    )
    kind = models.CharField(
        max_length=8, choices=BlockKind.choices, default=BlockKind.STUDY,
        verbose_name="Blok Türü",
    )
    exam_scope = models.CharField(
        max_length=3, choices=ExamScope.choices, blank=True, default='',
        verbose_name="Deneme Kapsamı",
    )
    title = models.CharField(max_length=100, blank=True, verbose_name="Başlık")
    # Haftanın günü: 0=Pazartesi … 6=Pazar (WeeklyProgram tarih penceresine eşlenir)
    weekday = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(6)], verbose_name="Gün (0-6)",
    )
    start_time = models.TimeField(null=True, blank=True, verbose_name="Başlangıç Saati")
    duration_minutes = models.PositiveIntegerField(null=True, blank=True, verbose_name="Süre (dk)")
    order = models.PositiveSmallIntegerField(default=0, verbose_name="Sıra")

    class Meta:
        verbose_name = "Şablon Görevi"
        verbose_name_plural = "Şablon Görevleri"
        ordering = ['weekday', 'start_time', 'order']

    @property
    def label(self) -> str:
        if self.title:
            return self.title
        if self.exam_scope:
            return ExamScope(self.exam_scope).label
        return str(self.subject) if self.subject_id else "Görev"

    def __str__(self) -> str:
        return f"gün {self.weekday} — {self.label}"
