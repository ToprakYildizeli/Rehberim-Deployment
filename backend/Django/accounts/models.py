import secrets
import string

from django.contrib.auth.models import AbstractUser
from django.db import IntegrityError, models, transaction


def generate_code(length=6):
    """Kısa, benzersiz davet/bağlanma kodu (ör. 'A3K9Q2')."""
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def save_with_unique_code(instance, field, save, tries=10):
    """`field` boşsa benzersiz bir kod üretip kaydeder; çakışırsa yeniden dener.

    "Önce var mı diye bak, sonra kaydet" tek başına yetmez: iki eşzamanlı kayıt
    aynı kodu üretip ikisi de boş bulabilir. Asıl güvence veritabanındaki
    `unique=True`; burada `IntegrityError` yakalanıp yeni kodla tekrar denenerek
    o güvence kullanıcıya 500 olarak yansımadan çözülür.
    """
    if getattr(instance, field):
        save()
        return
    for _ in range(tries):
        setattr(instance, field, generate_code())
        try:
            with transaction.atomic():
                save()
        except IntegrityError:
            setattr(instance, field, "")
            continue
        return
    raise IntegrityError(f"{instance.__class__.__name__}.{field} icin benzersiz kod uretilemedi.")


class User(AbstractUser):
    is_student = models.BooleanField(default=False, verbose_name="Öğrenci mi?")
    is_counselor = models.BooleanField(default=False, verbose_name="Rehber Hoca mı?")
    is_parent = models.BooleanField(default=False, verbose_name="Veli mi?")

    def __str__(self):
        return self.username


class Counselor(models.Model):
    # Öğrencinin rehbere bağlanmak, velinin çocuğuna bağlanmak için girdiği kod.
    # **Benzersiz ve değişmez**: bir kez üretilir, ömrü boyunca aynı kalır (E3).
    # Değişmezliği `save()` zorlar; veritabanı tarafında da `unique=True` var.
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='counselor_profile')
    invite_code = models.CharField(
        max_length=6, unique=True, blank=True, editable=False, verbose_name="Davet Kodu")

    class Meta:
        verbose_name = "Rehber Hoca"
        verbose_name_plural = "Rehber Hocalar"

    @classmethod
    def from_db(cls, db, field_names, values):
        obj = super().from_db(db, field_names, values)
        # Değişmezlik denetimi için diskteki hâli saklanır.
        obj._db_invite_code = obj.invite_code
        return obj

    def save(self, *args, **kwargs):
        original = getattr(self, '_db_invite_code', None)
        if original and self.invite_code != original:
            raise ValueError(
                "Rehberin davet kodu değiştirilemez; kod bir kez üretilir ve sabittir."
            )
        # `update_fields` verilmişse kod alanı zaten yazılmıyor demektir.
        save_with_unique_code(self, 'invite_code', lambda: super(Counselor, self).save(*args, **kwargs))
        self._db_invite_code = self.invite_code

    def __str__(self):
        return f"Hoca: {self.user.get_full_name()}"


class Student(models.Model):
    class GradeLevel(models.TextChoices):
        GRADE_9 = '9', '9. Sınıf'
        GRADE_10 = '10', '10. Sınıf'
        GRADE_11 = '11', '11. Sınıf'
        GRADE_12 = '12', '12. Sınıf'
        GRADUATED = 'mezun', 'Mezun'

    class StudyField(models.TextChoices):
        SAYISAL = 'say', 'Sayısal'
        ESIT_AGIRLIK = 'ea', 'Eşit Ağırlık'
        SOZEL = 'soz', 'Sözel'

    # 12. sınıf ve mezunlar sınava hazırlandığı için TYT/AYT derslerini görür.
    EXAM_GRADES = {GradeLevel.GRADE_12, GradeLevel.GRADUATED}
    # Alan seçimi 11. sınıftan itibaren yapılır; 9 ve 10. sınıflar alan seçmez.
    NON_FIELD_GRADES = {GradeLevel.GRADE_9, GradeLevel.GRADE_10}

    # Hangi alan hangi AYT derslerinden sorumlu. TYT herkes için ortaktır, bu
    # yüzden yalnız AYT tarafı alana göre ayrışır. Anahtarlar `Subject.name` ile
    # birebir eşleşir (`Subject` içinde ad+kategori benzersizdir), bu yüzden ders
    # adı değiştirilirse burası da güncellenmeli.
    AYT_FIELD_SUBJECTS = {
        StudyField.SAYISAL: {
            'Matematik', 'Geometri', 'Fizik', 'Kimya', 'Biyoloji',
        },
        StudyField.ESIT_AGIRLIK: {
            'Matematik', 'Geometri', 'Türk Dili ve Edebiyatı', 'Tarih-1', 'Coğrafya-1',
        },
        StudyField.SOZEL: {
            'Türk Dili ve Edebiyatı', 'Tarih-1', 'Coğrafya-1', 'Tarih-2', 'Coğrafya-2',
            'Felsefe', 'Din Kültürü ve Ahlak Bilgisi',
        },
    }

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    counselor = models.ForeignKey(Counselor, on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
    grade = models.CharField(max_length=5, choices=GradeLevel.choices, default=GradeLevel.GRADE_12)
    study_field = models.CharField(
        max_length=3, choices=StudyField.choices,
        blank=True, null=True, verbose_name="Alan",
    )
    # Velinin öğrenciye bağlanmak için girdiği kod
    connect_code = models.CharField(max_length=6, unique=True, blank=True, verbose_name="Bağlanma Kodu")

    class Meta:
        verbose_name = "Öğrenci"
        verbose_name_plural = "Öğrenciler"

    def save(self, *args, **kwargs):
        save_with_unique_code(self, 'connect_code', lambda: super(Student, self).save(*args, **kwargs))

    def __str__(self):
        return f"Öğrenci: {self.user.get_full_name()}"

    @property
    def is_exam_student(self):
        """12. sınıf veya mezun mu? (TYT/AYT dersleri görecek mi?)"""
        return self.grade in self.EXAM_GRADES

    @property
    def selects_field(self):
        """Bu öğrenci alan seçer mi? (9-10. sınıflar seçmez.)"""
        return self.grade not in self.NON_FIELD_GRADES

    @property
    def curriculum(self):
        """Öğrencinin tabi olduğu müfredat (konu seti seçimi için).

        12. sınıf ve mezunlar bu yılki sınava girer → mevcut/'eski' müfredat.
        9/10/11. sınıflar sonraki sınavlara girer → 'maarif' modeli.

        NOT: Kural sınıfa dayalı; yıl geçtikçe kohortlar kayacağı için ileride
        öğrenciye giriş yılı/kohort alanı eklenip buradan türetilmesi gerekebilir.
        """
        # Rehberim.models içe aktarımı döngü yaratmasın diye string döndürüyoruz.
        return 'eski' if self.grade in self.EXAM_GRADES else 'maarif'

    def clean(self):
        super().clean()
        from django.core.exceptions import ValidationError
        if self.selects_field and not self.study_field:
            raise ValidationError({
                'study_field': "11. sınıf ve üzeri öğrenciler alan seçmelidir.",
            })
        if not self.selects_field and self.study_field:
            raise ValidationError({
                'study_field': "9 ve 10. sınıf öğrencileri alan seçemez.",
            })

    def available_subjects(self):
        """Öğrencinin sınıf düzeyine göre görmesi gereken dersler.

        AYT tarafı **alana göre süzülmez** — öğrenci alanı dışından da ders
        çalışabilir/deneme girebilir. Alanına düşen dersler için `field_subjects()`.
        """
        from Rehberim.models import Subject
        if self.is_exam_student:
            return Subject.objects.filter(
                category__in=[Subject.Category.TYT, Subject.Category.AYT]
            )
        return Subject.objects.filter(category=Subject.Category.SCHOOL)

    def field_subjects(self):
        """Öğrencinin **alanına düşen** dersler: tüm TYT + alanının AYT dersleri.

        `available_subjects()`'in aksine bu bir kısıt değil, makul bir başlangıç
        kümesidir — ders programı tahtasında hangi ders satırlarının varsayılan
        olarak açılacağını belirler. Alan seçmeyen (9-10.) ve sınava hazırlanmayan
        öğrencilerde `available_subjects()`'e düşer.
        """
        from Rehberim.models import Subject
        if not self.is_exam_student:
            return self.available_subjects()
        names = self.AYT_FIELD_SUBJECTS.get(self.study_field)
        if not names:                     # alan seçilmemişse tüm sınav dersleri
            return self.available_subjects()
        return Subject.objects.filter(
            models.Q(category=Subject.Category.TYT)
            | models.Q(category=Subject.Category.AYT, name__in=names)
        )

    def subject_label(self, subject):
        """Okul dersini sınıf ön ekiyle etiketler: '11. Sınıf Fizik'."""
        from Rehberim.models import Subject
        if subject.category == Subject.Category.SCHOOL and not self.is_exam_student:
            return f"{self.get_grade_display()} {subject.name}"
        return str(subject)


class Parent(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='parent_profile')
    students = models.ManyToManyField(Student, related_name='parents', blank=True, verbose_name="Öğrenciler")

    class Meta:
        verbose_name = "Veli"
        verbose_name_plural = "Veliler"

    def __str__(self):
        return f"Veli: {self.user.get_full_name()}"
