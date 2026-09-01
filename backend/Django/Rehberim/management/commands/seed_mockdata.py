"""Test/geliştirme için sahte (mock) veri üretir.

İki mod:
  python manage.py seed_mockdata          # İSİMLİ demo seti (öngörülebilir, derin geçmiş)
  python manage.py seed_mockdata --bulk    # ÖLÇEKLİ, rastgele, yüksek hacim
  python manage.py seed_mockdata --clear   # yalnızca mock veriyi sil

Bulk parametreleri (varsayılanlar ~2 koç / 200 öğrenci / 1000 task):
  --counselors N          (varsayılan 2)
  --students N            (varsayılan 200)
  --tasks-per-student N   (varsayılan 5)   → students * bu ≈ toplam task
  --exams-per-student N   (varsayılan 2)   (yalnızca sınav öğrencileri)
  --goals-per-student N   (varsayılan 3)
  --random-seed N         (tekrar üretilebilir rastgelelik için)

Demo modunda geçmiş derinliği:
  --weeks N               (varsayılan 20)  → N haftalık program geçmişi. Grafiklerin
                          eğilim gösterebilmesi için haftalar birbirinin kopyası
                          değildir: hacim ve tamamlanma oranı zamanla artar,
                          deneme netleri yükselen bir eğilim izler.

Tüm mock kullanıcılar 'mock_' ön ekiyle oluşturulur; komut her çalıştığında önce
eskiyi silip yeniden kurar (idempotent). Gerçek verilere ve migration'la gelen
Ders/Görev-Tipi kayıtlarına dokunmaz. Şifre hepsinde aynı: bkz. MOCK_PASSWORD.

DB lokal olduğundan (SQLite, git'te değil) herkes bunu kendi makinesinde çalıştırır.
"""
import random
from collections import defaultdict
from datetime import time, timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import Counselor, Parent, Student
from Rehberim.models import (
    BlockKind, Book, BookTopic, CalendarEvent, ExamResult, ExamScope, Goal,
    Publisher, Subject, SubjectNet, Task, TaskType, Topic, TopicProgress,
    WeeklyProgram,
)

User = get_user_model()


def _as_time(total_minutes: int) -> time:
    """Gece yarısından beri geçen dakikayı saate çevirir (blok yerleşimi için)."""
    return time(total_minutes // 60, total_minutes % 60)


def _free_slot(busy, earliest, duration, latest=22 * 60):
    """`busy` aralıklarıyla çakışmayan ilk başlangıcı bulur (yoksa None).

    Adaylar 15 dakikalık ızgara ve mevcut blokların bitişleri; böylece bloklar
    hem çakışmaz hem de aralarında gereksiz boşluk kalmaz."""
    candidates = {t for t in range(earliest, latest - duration + 1, 15)}
    candidates.update(end for _, end in busy if earliest <= end <= latest - duration)
    for start in sorted(candidates):
        end = start + duration
        if all(end <= b_start or b_end <= start for b_start, b_end in busy):
            return start
    return None

MOCK_PREFIX = "mock_"
MOCK_PASSWORD = "Mock1234!"

FIRST_NAMES = [
    "Ali", "Zeynep", "Mehmet", "Elif", "Ahmet", "Ayşe", "Mustafa", "Fatma",
    "Can", "Ece", "Emre", "Deniz", "Burak", "Selin", "Kerem", "İrem", "Yusuf",
    "Zehra", "Ömer", "Merve", "Efe", "Nisa", "Berk", "Defne", "Arda", "Sıla",
]
LAST_NAMES = [
    "Yılmaz", "Demir", "Şahin", "Çelik", "Kaya", "Yıldız", "Yıldırım", "Öztürk",
    "Aydın", "Arslan", "Doğan", "Kılıç", "Aslan", "Çetin", "Kara", "Koç",
    "Kurt", "Özdemir", "Şen", "Polat",
]


class Command(BaseCommand):
    help = "Test için sahte (mock) veri üretir. --bulk ile ölçekli, --clear ile siler."

    def add_arguments(self, parser):
        parser.add_argument("--clear", action="store_true",
                            help="Mock veriyi sil, yenisini oluşturma.")
        parser.add_argument("--bulk", action="store_true",
                            help="Küçük demo yerine ölçekli rastgele veri üret.")
        parser.add_argument("--counselors", type=int, default=2)
        parser.add_argument("--students", type=int, default=200)
        parser.add_argument("--tasks-per-student", type=int, default=5)
        parser.add_argument("--exams-per-student", type=int, default=2)
        parser.add_argument("--goals-per-student", type=int, default=3)
        parser.add_argument("--random-seed", type=int, default=None)
        parser.add_argument("--weeks", type=int, default=20,
                            help="Kaç haftalık geçmiş program üretilsin (varsayılan 20).")

    def handle(self, *args, **options):
        self._clear()
        if options["clear"]:
            self.stdout.write(self.style.SUCCESS("Mock veri silindi."))
            return
        with transaction.atomic():
            if options["bulk"]:
                self._seed_bulk(options)
            else:
                self._seed_demo(weeks=max(1, options["weeks"]),
                                seed=options["random_seed"])

    # --- ortak yardımcılar --------------------------------------------------

    def _clear(self):
        qs = User.objects.filter(username__startswith=MOCK_PREFIX)
        count = qs.count()
        qs.delete()  # profiller, programlar, görevler vb. CASCADE ile gider
        if count:
            self.stdout.write(f"Silinen mock kullanıcı: {count}")

    def _subject(self, name, category):
        return Subject.objects.filter(name=name, category=category).first()

    def _new_user(self, uname, first, last, pwd_hash=None, **flags):
        """create_user'ın hash maliyetini atlar: hazır hash verilirse onu kullanır."""
        u = User(username=MOCK_PREFIX + uname, first_name=first, last_name=last,
                 email=f"{MOCK_PREFIX}{uname}@example.com", **flags)
        u.password = pwd_hash or make_password(MOCK_PASSWORD)
        u.save()
        return u

    # === KÜÇÜK DEMO SETİ ====================================================

    def _seed_demo(self, weeks=20, seed=None):
        today = timezone.localdate()
        monday = today - timedelta(days=today.weekday())
        pwd = make_password(MOCK_PASSWORD)
        rnd = random.Random(seed if seed is not None else 20260823)

        counselors = [
            Counselor.objects.create(
                user=self._new_user("rehber1", "Ayşe", "Kaya", pwd, is_counselor=True)),
            Counselor.objects.create(
                user=self._new_user("rehber2", "Mehmet", "Demir", pwd, is_counselor=True)),
        ]

        student_specs = [
            ("ogr1", "Ali", "Yılmaz", "12", "say", counselors[0]),
            ("ogr2", "Zeynep", "Demir", "11", "ea", counselors[0]),
            ("ogr3", "Mehmet", "Şahin", "10", None, counselors[0]),
            ("ogr4", "Elif", "Çelik", "mezun", "say", counselors[1]),
            ("ogr5", "Deniz", "Arslan", "9", None, counselors[1]),
        ]

        students = []
        for uname, first, last, grade, field, counselor in student_specs:
            student = Student.objects.create(
                user=self._new_user(uname, first, last, pwd, is_student=True),
                counselor=counselor, grade=grade, study_field=field)
            students.append(student)

        parents = [
            ("veli1", "Hasan", "Yılmaz", [students[0]]),
            ("veli2", "Fatma", "Demir", [students[1], students[2]]),
            ("veli3", "Can", "Kara", [students[4]]),
        ]
        for uname, first, last, linked_students in parents:
            parent = Parent.objects.create(
                user=self._new_user(uname, first, last, pwd, is_parent=True))
            parent.students.add(*linked_students)

        for student in students:
            self._demo_programs(student, student.counselor, monday, weeks, rnd)

        for student in students:
            self._demo_exams(student)
            self._demo_goals(student)

        Goal.objects.create(student=students[1], goal_type=Goal.GoalType.KITAP_OKUMA,
                            title="Sefiller")
        self._demo_calendar(counselors[0], students[0], monday)
        self._demo_books(students[0], students[3], students[1], students[2])
        self._demo_topic_progress(students)

        mock_tasks = Task.objects.filter(program__student__in=students).count()
        mock_exams = ExamResult.objects.filter(student__in=students).count()
        self.stdout.write(self.style.SUCCESS(
            f"\nDemo veri oluşturuldu — {weeks} haftalık program geçmişi, "
            f"{mock_tasks} blok, {mock_exams} deneme."))
        self.stdout.write(f"Şifre (hepsi): {MOCK_PASSWORD}\n")
        for rol, uname in [
            ("Rehber 1", "mock_rehber1"), ("Rehber 2", "mock_rehber2"),
            ("Öğrenci (12/say)", "mock_ogr1"), ("Öğrenci (11/ea)", "mock_ogr2"),
            ("Öğrenci (10)", "mock_ogr3"), ("Öğrenci (mezun/say)", "mock_ogr4"),
            ("Öğrenci (9)", "mock_ogr5"), ("Veli (→ogr1)", "mock_veli1"),
            ("Veli (→ogr2,ogr3)", "mock_veli2"), ("Veli (→ogr5)", "mock_veli3"),
        ]:
            self.stdout.write(f"  {rol:22} {uname}")

    def _demo_programs(self, student, counselor, monday, weeks, rnd):
        """Geriye doğru `weeks` haftalık program üretir (en eskisi ilk).

        Grafiklerin bir eğilim gösterebilmesi için haftalar birbirinin kopyası
        değil: hem hacim hem tamamlanma oranı zamanla artar."""
        for index in range(weeks):
            week_no = weeks - 1 - index            # 0 = en eski hafta
            start_date = monday - timedelta(days=7 * (weeks - 1 - week_no))
            is_current = start_date == monday
            program = WeeklyProgram.objects.create(
                student=student,
                counselor=counselor,
                start_date=start_date,
                # Saatsiz programda süre tutulmaz, dolayısıyla saat grafikleri
                # boş çıkar. Bu yüzden yalnız 9. sınıf saatsiz kalıyor (o yolun
                # da veride karşılığı olsun diye), gerisi saatli.
                schedule_type=(WeeklyProgram.ScheduleType.UNTIMED
                               if student.grade == Student.GradeLevel.GRADE_9
                               else WeeklyProgram.ScheduleType.TIMED),
                note="" if is_current else f"{week_no + 1}. hafta",
            )
            # Uyum oranı baştan sona ~%55'ten ~%92'ye tırmanır; içinde gürültü var.
            progress = week_no / max(1, weeks - 1)
            compliance = 0.55 + 0.37 * progress + rnd.uniform(-0.08, 0.08)
            self._demo_program_tasks(program, student, start_date, rnd,
                                     compliance=min(1.0, max(0.3, compliance)),
                                     is_current=is_current, intensity=progress)

    def _demo_program_tasks(self, program, student, start_date, rnd,
                            compliance, is_current, intensity):
        """Bir haftanın bloklarını üretir: çalışma + dış meşguliyet + deneme."""
        timed = program.schedule_type == WeeklyProgram.ScheduleType.TIMED
        if student.is_exam_student:
            subject_pool = list(student.field_subjects())
        else:
            subject_pool = list(Subject.objects.filter(category=Subject.Category.SCHOOL)[:8])
        if not subject_pool:
            return
        task_type_pool = list(TaskType.objects.all())
        topics_by_subject = {
            s.id: list(Topic.objects.filter(subject=s).values_list('name', flat=True)[:25])
            for s in subject_pool
        }

        tasks = []
        for day_offset in range(7):
            day = start_date + timedelta(days=day_offset)
            order = 0
            # Günün sabit blokları önce yerleşir; çalışma blokları bunların
            # arasındaki boşluklara konur. Böylece hiçbir blok çakışmaz —
            # tahta çakışan blokları zaten kabul etmiyor.
            fixed = []

            if timed and day_offset < 5:
                fixed.append((8 * 60 + rnd.choice([0, 30]), 300, "Okul"))
            if timed and day_offset in (1, 3):
                fixed.append((19 * 60, 90, rnd.choice(["Antrenman", "Kurs", "Etüt"])))

            for start, dur, title in sorted(fixed):
                tasks.append(Task(
                    program=program, kind=BlockKind.EXTERNAL, title=title,
                    date=day, start_time=_as_time(start), duration_minutes=dur,
                    order=order, created_by=student.user,
                    is_completed=not is_current,
                ))
                order += 1

            busy = [(start, start + dur) for start, dur, _ in fixed]

            # Cumartesi genel deneme (sınav öğrencilerinde)
            if timed and day_offset == 5 and student.is_exam_student:
                scope = ExamScope.TYT if rnd.random() < 0.6 else ExamScope.AYT
                dur = 135 if scope == ExamScope.TYT else 180
                start = _free_slot(busy, 9 * 60, dur)
                if start is not None:
                    tasks.append(Task(
                        program=program, kind=BlockKind.EXAM, exam_scope=scope,
                        title="", date=day, start_time=_as_time(start),
                        duration_minutes=dur, order=order, created_by=student.user,
                        is_completed=(not is_current) and rnd.random() < compliance,
                    ))
                    busy.append((start, start + dur))
                    order += 1

            # Çalışma blokları — hafta ilerledikçe biraz daha yoğun
            block_count = rnd.randint(2, 3) + (1 if intensity > 0.5 else 0)
            if day_offset == 6:
                block_count += 1                        # Pazar telafi günü
            for _ in range(block_count):
                subject = rnd.choice(subject_pool)
                topics = topics_by_subject.get(subject.id) or []
                duration = rnd.choice([20, 30, 40, 45, 60, 60, 90, 120])
                start = _free_slot(busy, 8 * 60, duration) if timed else None
                if timed and start is None:
                    break                               # gün doldu
                if timed:
                    busy.append((start, start + duration))
                tasks.append(Task(
                    program=program,
                    subject=subject,
                    task_type=rnd.choice(task_type_pool) if task_type_pool else None,
                    title=rnd.choice(topics) if topics else "",
                    date=day,
                    start_time=_as_time(start) if timed else None,
                    duration_minutes=duration if timed else None,
                    order=order,
                    created_by=student.user,
                    # Geçmiş haftalarda uyum oranına göre işaretlenir; bu hafta
                    # yalnız bugüne kadarki günler tamamlanmış olabilir.
                    is_completed=(rnd.random() < compliance
                                  and (not is_current or day < timezone.localdate())),
                ))
                order += 1

        Task.objects.bulk_create(tasks)

    def _demo_exams(self, student):
        """Dönem boyunca ~2 haftada bir deneme; netler yükselen bir eğilim izler.

        11. sınıf da TYT denemesi çözer (alan seçmiş sayılır); AYT yalnız sınava
        hazırlananlarda (12/mezun) çıkar. 9-10. sınıflar deneme çözmez."""
        if not student.selects_field:
            return
        today = timezone.localdate()
        rnd = random.Random(student.pk)                 # öğrenci başına tekrarlanabilir

        tyt_subjects = [s for s in Subject.objects.filter(category=Subject.Category.TYT)
                        if s.question_count]
        ayt_subjects = ([s for s in student.field_subjects()
                         if s.category == Subject.Category.AYT and s.question_count]
                        if student.is_exam_student else [])

        publishers = ["Özdebir", "3D", "Apotemi", "Bilfen", "Final", "Karekök"]
        exams = []
        # 12 deneme × 2 hafta ≈ 6 ay
        for i in range(12):
            weeks_ago = (11 - i) * 2
            progress = i / 11                           # 0 → 1 (zamanla iyileşme)
            is_ayt = bool(ayt_subjects) and i % 3 == 2  # her üç denemeden biri AYT
            subjects = ayt_subjects if is_ayt else tyt_subjects
            exam = ExamResult.objects.create(
                student=student,
                exam_type="ayt" if is_ayt else "tyt",
                name=f"{rnd.choice(publishers)} {'AYT' if is_ayt else 'TYT'}-{i + 1}",
                exam_date=today - timedelta(days=7 * weeks_ago + rnd.randint(0, 2)),
            )
            rows = []
            for subj in subjects:
                qc = subj.question_count
                # Başarı oranı %35'ten %80'e tırmanır, üstüne ders bazlı sapma
                base = 0.35 + 0.45 * progress + rnd.uniform(-0.12, 0.12)
                correct = max(0, min(qc, round(qc * max(0.05, min(0.95, base)))))
                wrong = max(0, min(qc - correct, round((qc - correct) * rnd.uniform(0.2, 0.6))))
                rows.append(SubjectNet(exam_result=exam, subject=subj, correct=correct,
                                       wrong=wrong, net=SubjectNet.compute_net(correct, wrong)))
            SubjectNet.objects.bulk_create(rows)
            exams.append(exam)
        return exams

    def _demo_goals(self, student):
        today = timezone.localdate()
        Goal.objects.create(student=student, goal_type=Goal.GoalType.DENEME_NETI,
                            exam_scope="tyt", target_net=110,
                            target_date=today + timedelta(days=60))
        Goal.objects.create(student=student, goal_type=Goal.GoalType.DENEME_NETI,
                            exam_scope="tyt", subject=self._subject("Matematik", "tyt"),
                            target_net=35)
        Goal.objects.create(student=student, goal_type=Goal.GoalType.KITAP_BITIRME,
                            title="TYT Türkçe 345 Yayınları")
        Goal.objects.create(student=student, goal_type=Goal.GoalType.KITAP_OKUMA,
                            title="Suç ve Ceza")
        Goal.objects.create(student=student, goal_type=Goal.GoalType.KONU_BITIRME,
                            title="Türev konusunu bitir", is_achieved=True)

    def _demo_calendar(self, rehber, student, monday):
        CalendarEvent.objects.create(
            counselor=rehber, student=student, title="Ali ile görüşme",
            date=monday + timedelta(days=5),
            start_time=time(14, 0), end_time=time(15, 0))
        CalendarEvent.objects.create(
            counselor=rehber, title="Özdebir TYT sınavı", date=monday + timedelta(days=6))

    def _mark_some_book_topics(self, book):
        """Kitabın ilk birkaç konusunu tamamlandı/devam olarak işaretle (örnek ilerleme)."""
        bts = list(book.book_topics.all()[:3])
        marks = [(BookTopic.Status.COMPLETED, 8), (BookTopic.Status.IN_PROGRESS, 3)]
        for bt, (status, tests) in zip(bts, marks):
            bt.status = status
            bt.tests_solved = tests
            bt.save()

    def _demo_books(self, ali, elif_, zeynep, mehmet):
        """Öğrencilere örnek kitaplar. Ders kitaplarında konular otomatik dolar."""
        pubs = list(Publisher.objects.values_list("name", flat=True)) or ["345 Yayınları"]

        def pub(i):
            return pubs[i % len(pubs)]

        # Ali (12/say, eski): TYT Biyoloji soru bankası (9-10 konuları) + okuma
        b1 = Book.objects.create(
            student=ali, kind=Book.BookKind.DERS, subject=self._subject("Biyoloji", "tyt"),
            book_format=Book.BookFormat.SORU_BANKASI, publisher=pub(0))
        b1.populate_topics()
        self._mark_some_book_topics(b1)
        Book.objects.create(
            student=ali, kind=Book.BookKind.OKUMA, title="Suç ve Ceza",
            author="Dostoyevski", status=Book.Status.IN_PROGRESS)

        # Elif (mezun/say, eski): AYT Matematik konu anlatımı (11-12 konuları)
        b2 = Book.objects.create(
            student=elif_, kind=Book.BookKind.DERS, subject=self._subject("Matematik", "ayt"),
            book_format=Book.BookFormat.KONU_ANLATIMI, publisher=pub(1))
        b2.populate_topics()

        # Zeynep (11/ea, maarif): okul Matematik soru bankası (11. sınıf konuları)
        b3 = Book.objects.create(
            student=zeynep, kind=Book.BookKind.DERS, subject=self._subject("Matematik", "okul"),
            book_format=Book.BookFormat.SORU_BANKASI, publisher=pub(2))
        b3.populate_topics()
        self._mark_some_book_topics(b3)

        # Mehmet (10, maarif): okul Fizik konu anlatımı (10. sınıf konuları)
        b4 = Book.objects.create(
            student=mehmet, kind=Book.BookKind.DERS, subject=self._subject("Fizik", "okul"),
            book_format=Book.BookFormat.KONU_ANLATIMI, publisher=pub(3))
        b4.populate_topics()

    def _demo_topic_progress(self, students):
        """Konu Takibi sayfası için ilerleme. Her öğrencinin kendi derslerinde,
        müfredat sırasına göre baştan sona azalan bir hâkimiyet: baştaki konular
        bitmiş, ortadakiler devam ediyor, sondakiler başlanmamış."""
        for student in students:
            rnd = random.Random(student.pk + 7)
            subjects = list(student.field_subjects())[:6]
            rows = []
            for subject in subjects:
                topics = list(Topic.objects.filter(
                    subject=subject, curriculum=student.curriculum).order_by('grade', 'order')[:20])
                if not topics:
                    continue
                # Öğrencinin bu derste ne kadar ilerlediği (%40-%90 arası)
                reach = rnd.uniform(0.4, 0.9)
                for i, topic in enumerate(topics):
                    ratio = i / max(1, len(topics) - 1)
                    if ratio < reach - 0.15:
                        status, level = TopicProgress.Status.COMPLETED, rnd.randint(4, 5)
                    elif ratio < reach:
                        status, level = TopicProgress.Status.IN_PROGRESS, rnd.randint(2, 4)
                    else:
                        status, level = TopicProgress.Status.NOT_STARTED, 1
                    rows.append(TopicProgress(
                        student=student, topic=topic, status=status, level=level,
                        tests_solved=(rnd.randint(3, 12)
                                      if status == TopicProgress.Status.COMPLETED
                                      else rnd.randint(0, 4)),
                    ))
            TopicProgress.objects.bulk_create(rows, ignore_conflicts=True)

    # === ÖLÇEKLİ (BULK) ÜRETİM ==============================================

    def _seed_bulk(self, opts):
        rnd = random.Random(opts["random_seed"])
        today = timezone.localdate()
        monday = today - timedelta(days=today.weekday())
        pwd = make_password(MOCK_PASSWORD)

        n_c = opts["counselors"]
        n_s = opts["students"]
        tps = opts["tasks_per_student"]
        eps = opts["exams_per_student"]
        gps = opts["goals_per_student"]

        # Referans veriyi bir kez çek
        exam_subjects = list(Subject.objects.filter(category__in=["tyt", "ayt"]))
        school_subjects = list(Subject.objects.filter(category="okul"))
        tyt_subjects = list(Subject.objects.filter(category="tyt"))
        task_types = list(TaskType.objects.all())
        if not (exam_subjects and school_subjects and task_types):
            self.stderr.write("Ders/Görev-Tipi seed'i yok — önce migrate çalıştır.")
            return

        def name():
            return rnd.choice(FIRST_NAMES), rnd.choice(LAST_NAMES)

        # 1) Rehberler
        counselors = []
        for i in range(1, n_c + 1):
            f, l = name()
            counselors.append(Counselor.objects.create(
                user=self._new_user(f"c{i}", f, l, pwd, is_counselor=True)))

        # 2) Öğrenciler (rastgele sınıf/alan, rastgele rehber)
        students = []
        for i in range(1, n_s + 1):
            f, l = name()
            grade = rnd.choice(["9", "10", "11", "12", "mezun"])
            field = None if grade in ("9", "10") else rnd.choice(["say", "ea", "soz"])
            students.append(Student.objects.create(
                user=self._new_user(f"s{i}", f, l, pwd, is_student=True),
                counselor=rnd.choice(counselors), grade=grade, study_field=field))

        # 3) Veliler (öğrenci sayısının ~1/4'ü, her biri 1 çocuğa bağlı)
        n_p = max(1, n_s // 4)
        for i in range(1, n_p + 1):
            f, l = name()
            p = Parent.objects.create(
                user=self._new_user(f"p{i}", f, l, pwd, is_parent=True))
            p.students.add(rnd.choice(students))

        # 4) Programlar (öğrenci başına 1, rastgele saatli/saatsiz)
        programs = []
        for st in students:
            stype = rnd.choice([WeeklyProgram.ScheduleType.TIMED,
                                WeeklyProgram.ScheduleType.UNTIMED])
            prog = WeeklyProgram.objects.create(
                student=st, counselor=st.counselor, start_date=monday,
                schedule_type=stype, note="bulk")
            programs.append(prog)

        # 5) Görevler (bulk_create) — gün içi order/saat tutarlı
        tasks = []
        per_day = defaultdict(int)  # (program_id, date) -> sayaç
        for prog in programs:
            st = prog.student
            avail = exam_subjects if st.is_exam_student else school_subjects
            for _ in range(tps):
                day = monday + timedelta(days=rnd.randint(0, 6))
                idx = per_day[(prog.id, day)]
                per_day[(prog.id, day)] += 1
                t = Task(program=prog, subject=rnd.choice(avail),
                         task_type=rnd.choice(task_types), title="",
                         date=day, order=idx, created_by=st.user)
                if prog.schedule_type == WeeklyProgram.ScheduleType.TIMED:
                    t.start_time = time(min(8 + idx, 22), 0)
                    t.duration_minutes = 60
                tasks.append(t)
        Task.objects.bulk_create(tasks, batch_size=500)

        # 6) Denemeler + netler (yalnızca sınav öğrencileri)
        nets = []
        exam_count = 0
        for st in students:
            if not st.is_exam_student:
                continue
            for j in range(eps):
                exam = ExamResult.objects.create(
                    student=st, exam_type="tyt", name=f"Deneme {j + 1}",
                    exam_date=today - timedelta(days=7 * (j + 1)))
                exam_count += 1
                for subj in rnd.sample(tyt_subjects, min(4, len(tyt_subjects))):
                    qc = subj.question_count or 40
                    c = rnd.randint(qc // 3, qc)          # doğru
                    w = rnd.randint(0, qc - c)            # yanlış (kalan = boş)
                    nets.append(SubjectNet(exam_result=exam, subject=subj, correct=c,
                                           wrong=w, net=SubjectNet.compute_net(c, w)))
        SubjectNet.objects.bulk_create(nets, batch_size=500)

        # 7) Hedefler (bulk_create) — karışık türler
        goals = []
        books = ["Suç ve Ceza", "Sefiller", "1984", "Tutunamayanlar", "Kürk Mantolu Madonna"]
        testbooks = ["TYT Türkçe 345 Yay.", "AYT Matematik 3D", "TYT Fizik Palme"]
        topics = ["Türev", "İntegral", "Paragraf", "Kuvvet", "Hücre"]
        for st in students:
            for _ in range(gps):
                gt = rnd.choice(list(Goal.GoalType))
                if gt == Goal.GoalType.DENEME_NETI:
                    subj = rnd.choice([None] + tyt_subjects)
                    goals.append(Goal(student=st, goal_type=gt, exam_scope="tyt",
                                      subject=subj, target_net=rnd.choice([90, 100, 110, 30, 35])))
                elif gt == Goal.GoalType.KITAP_OKUMA:
                    goals.append(Goal(student=st, goal_type=gt, title=rnd.choice(books)))
                elif gt == Goal.GoalType.KITAP_BITIRME:
                    goals.append(Goal(student=st, goal_type=gt, title=rnd.choice(testbooks)))
                else:
                    goals.append(Goal(student=st, goal_type=gt,
                                      title=f"{rnd.choice(topics)} konusunu bitir"))
        Goal.objects.bulk_create(goals, batch_size=500)

        # 8) Takvim (her rehbere birkaç etkinlik)
        events = []
        for c in counselors:
            own = [s for s in students if s.counselor_id == c.id]
            for _ in range(min(5, len(own))):
                st = rnd.choice(own)
                events.append(CalendarEvent(
                    counselor=c, student=st, title=f"{st.user.first_name} ile görüşme",
                    date=monday + timedelta(days=rnd.randint(0, 6)),
                    start_time=time(rnd.randint(9, 17), 0), end_time=None))
        CalendarEvent.objects.bulk_create(events)

        # 9) Kitaplar (öğrenci başına 1 ders kitabı → konular otomatik dolar; ~%40 okuma)
        reading = ["Suç ve Ceza", "Sefiller", "1984", "Tutunamayanlar", "Kürk Mantolu Madonna"]
        pubs = list(Publisher.objects.values_list("name", flat=True)) or ["345 Yayınları"]
        formats = list(Book.BookFormat.values)
        book_count = 0
        booktopic_count = 0
        for st in students:
            avail = exam_subjects if st.is_exam_student else school_subjects
            b = Book.objects.create(
                student=st, kind=Book.BookKind.DERS, subject=rnd.choice(avail),
                book_format=rnd.choice(formats), publisher=rnd.choice(pubs))
            booktopic_count += b.populate_topics()
            book_count += 1
            if rnd.random() < 0.4:
                Book.objects.create(student=st, kind=Book.BookKind.OKUMA,
                                    title=rnd.choice(reading))
                book_count += 1

        # 10) Konu ilerlemesi (öğrenci başına ~5 konu, müfredatına uygun)
        topics_by_curr = {
            "eski": list(Topic.objects.filter(curriculum="eski")),
            "maarif": list(Topic.objects.filter(curriculum="maarif")),
        }
        statuses = list(TopicProgress.Status.values)
        progress = []
        for st in students:
            pool = topics_by_curr.get(st.curriculum, [])
            if not pool:
                continue
            for t in rnd.sample(pool, min(5, len(pool))):
                progress.append(TopicProgress(
                    student=st, topic=t, status=rnd.choice(statuses),
                    tests_solved=rnd.randint(0, 20)))
        TopicProgress.objects.bulk_create(progress, batch_size=500, ignore_conflicts=True)

        self.stdout.write(self.style.SUCCESS("\nÖlçekli (bulk) mock veri oluşturuldu."))
        self.stdout.write(f"Şifre (hepsi): {MOCK_PASSWORD}")
        self.stdout.write(
            f"  Rehber: {len(counselors)} (mock_c1..)  |  Öğrenci: {len(students)} (mock_s1..)  |  "
            f"Veli: {n_p} (mock_p1..)")
        self.stdout.write(
            f"  Program: {len(programs)}  |  Görev: {len(tasks)}  |  "
            f"Deneme: {exam_count}  |  Hedef: {len(goals)}  |  Takvim: {len(events)}")
        self.stdout.write(
            f"  Kitap: {book_count}  |  Kitap-konusu: {booktopic_count}  |  "
            f"Konu ilerlemesi: {len(progress)}")
