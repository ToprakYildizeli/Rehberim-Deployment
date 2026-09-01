from datetime import timedelta

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Student
from accounts.permissions import IsCounselor, IsStudent

from .models import (
    Achievement, BlockDurationDefault, BlockKind, Book, BookTopic, CalendarEvent,
    ExamResult, ExamSource, Goal, ProgramTemplate, Publisher, Subject,
    student_achievement_facts, Task, TaskType, TemplateTask, Topic, TopicProgress,
    WeeklyProgram,
)
from .permissions import (
    CanApproveProgram,
    CanModifyProgram,
    IsBookOwnerStudentOrReadOnly,
    IsBookTopicOwnerStudentOrReadOnly,
    IsCalendarOwnerOrTargetRead,
    IsExamOwnerStudentOrReadOnly,
    IsGoalOwnerStudentOrReadOnly,
    IsProgramParticipant,
    IsTopicProgressOwnerStudentOrReadOnly,
)
from .serializers import (
    AchievementSerializer,
    BlockDurationDefaultSerializer,
    BookDetailSerializer,
    BookSerializer,
    BookTopicSerializer,
    CalendarEventSerializer,
    ExamResultSerializer,
    GoalSerializer,
    ProgramAssignSerializer,
    ProgramTemplateSerializer,
    PublisherSerializer,
    SubjectSerializer,
    TaskSerializer,
    TaskTypeSerializer,
    TopicProgressSerializer,
    TopicSerializer,
    WeeklyProgramSerializer,
)


# --- Referans veri (frontend dropdown'ları) ---------------------------------

class SubjectListView(generics.ListAPIView):
    """GET /api/subjects/ — öğrenciyse sınıfına uygun dersler, değilse tümü.

    `?student=<id>&scope=field` ile rehber, **kendi öğrencisinin alanına düşen**
    dersleri ister (tüm TYT + alanının AYT dersleri). Ders programı tahtasında
    varsayılan ders satırlarını açmak için; bir kısıt değil, başlangıç kümesi.
    """
    serializer_class = SubjectSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if getattr(user, 'is_student', False) and hasattr(user, 'student_profile'):
            student = user.student_profile
            return (student.field_subjects() if self.request.query_params.get('scope') == 'field'
                    else student.available_subjects())

        student_id = self.request.query_params.get('student')
        if student_id and getattr(user, 'is_counselor', False) and hasattr(user, 'counselor_profile'):
            from accounts.models import Student
            student = Student.objects.filter(
                pk=student_id, counselor=user.counselor_profile,
            ).first()
            if student is None:
                raise NotFound("Öğrenci bulunamadı.")
            return (student.field_subjects() if self.request.query_params.get('scope') == 'field'
                    else student.available_subjects())
        return Subject.objects.all()


class TaskTypeListView(generics.ListAPIView):
    """GET /api/task-types/ — METOD listesi."""
    serializer_class = TaskTypeSerializer
    permission_classes = [IsAuthenticated]
    queryset = TaskType.objects.all()


class BlockDurationDefaultListView(generics.ListAPIView):
    """GET /api/block-durations/ — rehberin süre hafızası (A4).

    Blok formunda (ders, metod, konu) seçilince varsayılan süreyi doldurmak için
    kullanılır; web bunu sayfa açılışında bir kez çeker. Yazma ucu yoktur —
    hafıza blok kaydedilirken kendiliğinden güncellenir."""
    serializer_class = BlockDurationDefaultSerializer
    permission_classes = [IsAuthenticated, IsCounselor]

    def get_queryset(self):
        return BlockDurationDefault.objects.filter(
            counselor=self.request.user.counselor_profile
        )


class PublisherListView(generics.ListAPIView):
    """GET /api/publishers/ — YAYINEVİ listesi (kitap eklerken dropdown)."""
    serializer_class = PublisherSerializer
    permission_classes = [IsAuthenticated]
    queryset = Publisher.objects.all()


# --- Programlar --------------------------------------------------------------

class ProgramListCreateView(generics.ListCreateAPIView):
    """GET: rolüne göre programlar · POST: rehber öğrencisine program açar."""
    serializer_class = WeeklyProgramSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsCounselor()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        qs = (
            WeeklyProgram.objects
            .select_related('student__user', 'counselor__user')
            .prefetch_related('tasks__subject', 'tasks__task_type')
        )
        if getattr(user, 'is_counselor', False) and hasattr(user, 'counselor_profile'):
            return qs.filter(student__counselor=user.counselor_profile)
        if getattr(user, 'is_student', False) and hasattr(user, 'student_profile'):
            return qs.filter(student=user.student_profile)
        if getattr(user, 'is_parent', False) and hasattr(user, 'parent_profile'):
            # Veliye onaylanmamış program gösterilmez (B1).
            qs = qs.filter(student__in=user.parent_profile.students.all(),
                           approved_at__isnull=False)
            student_id = self.request.query_params.get('student')
            if student_id:      # birden çok çocuğu olan veli tek çocuğa daraltır
                qs = qs.filter(student_id=student_id)
            return qs
        return qs.none()

    def perform_create(self, serializer):
        counselor = self.request.user.counselor_profile
        student = serializer.validated_data['student']
        if student.counselor_id != counselor.id:
            raise PermissionDenied("Yalnızca kendi öğrencinize program oluşturabilirsiniz.")
        program = serializer.save(counselor=counselor)
        # Yeni hafta açıldı: öğrencinin otomatik rutini varsa görevleri buraya düşer.
        apply_routine_if_any(program, self.request.user)


class ProgramDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PATCH/DELETE /api/programs/{id}/ — program-seviyesi değişiklik rehbere."""
    serializer_class = WeeklyProgramSerializer
    permission_classes = [IsAuthenticated, CanModifyProgram]
    queryset = WeeklyProgram.objects.select_related('student__user', 'counselor__user')


class CurrentProgramView(generics.RetrieveAPIView):
    """GET /api/programs/current/ — öğrencinin bugünü kapsayan güncel programı."""
    serializer_class = WeeklyProgramSerializer
    permission_classes = [IsAuthenticated, IsStudent]

    def get_object(self) -> WeeklyProgram:
        student = self.request.user.student_profile
        today = timezone.localdate()
        # Programlar örtüşemediğinden bugünü kapsayan en fazla bir program vardır:
        # bugün ya da öncesinde başlayan en yeni program. `end_date` türetilen bir
        # property olduğu için kapsama kontrolü Python'da yapılır.
        latest_started = (
            student.programs.filter(start_date__lte=today).order_by('-start_date').first()
        )
        program = latest_started if latest_started and latest_started.covers(today) else None
        if program is None:
            program = student.programs.first()  # en yeni program
        if program is None:
            raise NotFound("Aktif program bulunamadı.")
        return program


class ProgramComplianceView(APIView):
    """GET /api/programs/compliance/?student=<id> — bir öğrencinin uyum geçmişi (B2).

    Üç parça döner:
    - `programs`: **bitmiş** programların zaman serisi (eskiden yeniye). Devam eden
      hafta kısmi kalacağı için seriye girmez — onun anlık yüzdesi zaten program
      objesindeki `compliance` alanında var.
    - `months`: ay ay özet ("6 aydır kullanıyorsa yüzde kaçı tutturmuş"). Ay,
      programın `start_date`'ine göre seçilir.
    - `overall`: tüm dönemin özeti.

    `months` ve `overall` yalnızca **onaylanmış** programlardan hesaplanır: onay,
    rehberin "gerçekten yapılmış" beyanıdır (B1); onaysız haftaların beyanı
    doğrulanmamıştır, uzun vadeli istatistiği kirletmemeli. Kaç haftanın onay
    beklediği `pending_approval` ile ayrıca söylenir.

    Yüzdeler **dakika ağırlıklıdır** — haftaların yüzdelerinin ortalaması değil,
    dönemin toplam tamamlanan dakikası / toplam dakikası. Yoksa 1 saatlik bir hafta
    ile 30 saatlik bir hafta aynı ağırlıkta sayılırdı.
    """
    permission_classes = [IsAuthenticated]

    def get_student(self):
        user = self.request.user
        student_id = self.request.query_params.get('student')
        if getattr(user, 'is_student', False) and hasattr(user, 'student_profile'):
            return user.student_profile
        if getattr(user, 'is_counselor', False) and hasattr(user, 'counselor_profile'):
            if not student_id:
                raise ValidationError({'student': "Öğrenci belirtilmelidir."})
            return get_object_or_404(
                Student, pk=student_id, counselor=user.counselor_profile)
        if getattr(user, 'is_parent', False) and hasattr(user, 'parent_profile'):
            qs = user.parent_profile.students
            return get_object_or_404(qs, pk=student_id) if student_id else get_object_or_404(qs)
        raise PermissionDenied("Bu veriye erişim yetkiniz yok.")

    def get(self, request) -> Response:
        student = self.get_student()
        programs = (
            WeeklyProgram.objects
            .filter(student=student)
            .prefetch_related('tasks')
            .order_by('start_date')
        )
        # Veli yalnız onaylı programları görebilir (B1) — istatistiği de onaylıdan çıkar.
        parent_view = getattr(request.user, 'is_parent', False)

        series, pending = [], 0
        for p in programs:
            if not p.is_finished:
                continue
            if parent_view and not p.is_approved:
                continue
            c = p.compliance()
            if not p.is_approved:
                pending += 1
            series.append({
                'id': p.id,
                'start_date': p.start_date,
                'end_date': p.end_date,
                'day_count': p.day_count,
                'is_approved': p.is_approved,
                **c,
            })

        approved = [row for row in series if row['is_approved']]

        def summarize(rows: list[dict]) -> dict:
            total = sum(r['total_minutes'] for r in rows)
            done = sum(r['completed_minutes'] for r in rows)
            return {
                'percent': round(done / total * 100) if total else None,
                'total_minutes': total,
                'completed_minutes': done,
                'study_hours': round(total / 60, 1),
                'program_count': len(rows),
            }

        by_month: dict[str, list[dict]] = {}
        for row in approved:
            by_month.setdefault(row['start_date'].strftime('%Y-%m'), []).append(row)

        return Response({
            'student': student.id,
            'student_name': student.user.get_full_name(),
            'pending_approval': pending,
            'programs': series,
            'months': [{'month': m, **summarize(rows)} for m, rows in sorted(by_month.items())],
            'overall': summarize(approved),
        })


class AchievementListCreateView(generics.ListCreateAPIView):
    """GET/POST /api/achievements/ — rehberin başarım tanımları (C3).

    Başarımlar rehbere aittir: her rehber kendi listesini düzenler (Ayarlar'dan).
    Yeni rehbere varsayılan set kaydolurken kopyalanır
    (`Rehberim.signals.seed_counselor_achievements`), sonrası tamamen kendisine
    kalmıştır — silebilir, ekleyebilir, eşiğini değiştirebilir.
    """
    serializer_class = AchievementSerializer
    permission_classes = [IsAuthenticated, IsCounselor]

    def get_queryset(self):
        return Achievement.objects.filter(counselor=self.request.user.counselor_profile)

    def get_serializer_context(self):
        # Ad tekilliği rehber içinde doğrulanır (bkz. AchievementSerializer.validate_name).
        return {**super().get_serializer_context(),
                'counselor': self.request.user.counselor_profile}

    def perform_create(self, serializer):
        serializer.save(counselor=self.request.user.counselor_profile)


class AchievementDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PATCH/DELETE /api/achievements/{id}/ — yalnızca sahibi rehber."""
    serializer_class = AchievementSerializer
    permission_classes = [IsAuthenticated, IsCounselor]

    def get_queryset(self):
        return Achievement.objects.filter(counselor=self.request.user.counselor_profile)

    def get_serializer_context(self):
        return {**super().get_serializer_context(),
                'counselor': self.request.user.counselor_profile}


class AchievementProgressView(APIView):
    """GET /api/achievements/progress/?student=<id> — öğrencinin başarım durumu (C3).

    Rehberin **kendi** başarım tanımları öğrenciye uygulanır; kazanım saklanmaz,
    her istekte hesaplanır (eşik değişince ya da bir deneme silinince kayıtla
    gerçek arasında tutarsızlık kalmasın diye).

    Rehberi olmayan öğrencide liste boştur — başarımları koyan rehberdir.
    """
    permission_classes = [IsAuthenticated]

    def get_student(self):
        user = self.request.user
        student_id = self.request.query_params.get('student')
        if getattr(user, 'is_student', False) and hasattr(user, 'student_profile'):
            return user.student_profile
        if getattr(user, 'is_counselor', False) and hasattr(user, 'counselor_profile'):
            if not student_id:
                raise ValidationError({'student': "Öğrenci belirtilmelidir."})
            return get_object_or_404(
                Student, pk=student_id, counselor=user.counselor_profile)
        if getattr(user, 'is_parent', False) and hasattr(user, 'parent_profile'):
            qs = user.parent_profile.students
            return get_object_or_404(qs, pk=student_id) if student_id else get_object_or_404(qs)
        raise PermissionDenied("Bu veriye erişim yetkiniz yok.")

    def get(self, request) -> Response:
        student = self.get_student()
        if student.counselor_id is None:
            return Response({'student': student.id, 'student_name': student.user.get_full_name(),
                             'earned_count': 0, 'total_count': 0, 'facts': {}, 'achievements': []})

        facts = student_achievement_facts(student)
        rows = [
            a.evaluate_for(student, facts=facts)
            for a in Achievement.objects.filter(counselor_id=student.counselor_id, is_active=True)
        ]
        # Kazanılanlar önce, sonra eşiğe en yakın olanlar — "sıradaki hedef" görünsün.
        rows.sort(key=lambda r: (not r['earned'], -r['progress'], r['threshold']))
        return Response({
            'student': student.id,
            'student_name': student.user.get_full_name(),
            'earned_count': sum(1 for r in rows if r['earned']),
            'total_count': len(rows),
            'facts': facts,
            'achievements': rows,
        })


class StudyStatsView(APIView):
    """GET /api/study-stats/?student=<id> — öğrencinin çalışma istatistikleri (E2).

    "Şu ana kadar kaç saat çalıştım, yüzde kaç TYT / kaç AYT, hangi derse ne kadar"
    sorularının cevabı. Hesap bizde, çizim (daire grafiği vb.) Yunus'ta.

    **Sayılan şey: gerçekten yapılan çalışma** — `is_completed` işaretli ve
    `counts_as_study` bloklar. Dış meşguliyet (okul, antrenman, doktor) çalışma
    değildir; denemeler çalışmadır (B2/B3 ile aynı küme).

    Rol farkı: öğrenci ve rehber tüm tamamlanan çalışmayı görür; **veli yalnız
    onaylanmış programlardakini** — onaysız programın hiçbir verisi veliye
    gösterilmez (B1).

    `?from=YYYY-MM-DD` / `?to=YYYY-MM-DD` ile dönem daraltılabilir.
    """
    permission_classes = [IsAuthenticated]

    def get_student(self):
        user = self.request.user
        student_id = self.request.query_params.get('student')
        if getattr(user, 'is_student', False) and hasattr(user, 'student_profile'):
            return user.student_profile
        if getattr(user, 'is_counselor', False) and hasattr(user, 'counselor_profile'):
            if not student_id:
                raise ValidationError({'student': "Öğrenci belirtilmelidir."})
            return get_object_or_404(
                Student, pk=student_id, counselor=user.counselor_profile)
        if getattr(user, 'is_parent', False) and hasattr(user, 'parent_profile'):
            qs = user.parent_profile.students
            return get_object_or_404(qs, pk=student_id) if student_id else get_object_or_404(qs)
        raise PermissionDenied("Bu veriye erişim yetkiniz yok.")

    def get(self, request) -> Response:
        student = self.get_student()
        tasks = (
            Task.objects
            .filter(program__student=student, is_completed=True)
            .exclude(kind=BlockKind.EXTERNAL)
            .select_related('subject', 'program')
        )
        if getattr(request.user, 'is_parent', False):
            tasks = tasks.filter(program__approved_at__isnull=False)

        for param, lookup in (('from', 'date__gte'), ('to', 'date__lte')):
            raw = request.query_params.get(param)
            if raw:
                tasks = tasks.filter(**{lookup: raw})

        by_category: dict[str, int] = {}
        by_subject: dict[int, dict] = {}
        total = 0
        for t in tasks:
            minutes = t.duration_minutes or 0
            if not minutes:
                continue          # saatsiz program: süre yok, dağılıma katılamaz
            total += minutes
            # Ders seçilmemiş genel deneme bloğu kendi kapsamına (tyt/ayt) sayılır.
            category = t.subject.category if t.subject_id else (t.exam_scope or 'diger')
            by_category[category] = by_category.get(category, 0) + minutes
            if t.subject_id:
                row = by_subject.setdefault(
                    t.subject_id,
                    {'subject': t.subject_id, 'subject_label': str(t.subject),
                     'category': t.subject.category, 'minutes': 0},
                )
                row['minutes'] += minutes

        def share(minutes: int) -> float:
            return round(minutes / total * 100, 1) if total else 0.0

        return Response({
            'student': student.id,
            'student_name': student.user.get_full_name(),
            'total_minutes': total,
            'total_hours': round(total / 60, 1),
            'by_category': [
                {'category': k, 'minutes': v, 'hours': round(v / 60, 1), 'percent': share(v)}
                for k, v in sorted(by_category.items(), key=lambda kv: -kv[1])
            ],
            'by_subject': [
                {**row, 'hours': round(row['minutes'] / 60, 1), 'percent': share(row['minutes'])}
                for row in sorted(by_subject.values(), key=lambda r: -r['minutes'])
            ],
        })


class ProgramApprovalView(APIView):
    """POST/DELETE /api/programs/{pk}/approve/ — haftalık onay (B1).

    Onay, rehberin "öğrencinin yaptım dedikleri gerçekten yapılmış" beyanıdır:
    hafta bitince toplantıda kontrol edilir. Bu yüzden **pencere kapanmadan**
    onaylanamaz. Onaydan sonra program veliye görünür olur ve öğrenci görevlerine
    dokunamaz; rehber düzeltmeye devam edebilir (bkz. `IsProgramParticipant`).

    Onay geri alınabilir (`DELETE`) — rehber yanlış onayladıysa veli görünümü
    de geri kapanır.
    """
    permission_classes = [IsAuthenticated, IsCounselor, CanApproveProgram]

    def get_program(self) -> WeeklyProgram:
        program = get_object_or_404(
            WeeklyProgram.objects.select_related('student__user', 'approved_by__user'),
            pk=self.kwargs['pk'],
        )
        self.check_object_permissions(self.request, program)
        return program

    def post(self, request, pk: int) -> Response:
        program = self.get_program()
        if not program.is_finished:
            return Response(
                {'detail': f"Program {program.end_date} tarihinde bitiyor; "
                           f"onay ancak bittikten sonra verilebilir."},
                status=400,
            )
        if not program.is_approved:
            program.approve(request.user.counselor_profile)
        return Response(WeeklyProgramSerializer(program).data)

    def delete(self, request, pk: int) -> Response:
        program = self.get_program()
        if program.is_approved:
            program.revoke_approval()
        return Response(WeeklyProgramSerializer(program).data)


# --- Program Şablonları (ProgramTemplate) + Atama ---------------------------

def templates_visible_to(user):
    """Rehber: kendi şablonları + öğrencilerinin rutinleri. Öğrenci: kendi rutinleri."""
    qs = ProgramTemplate.objects.prefetch_related('tasks__subject', 'tasks__task_type')
    if getattr(user, 'is_counselor', False) and hasattr(user, 'counselor_profile'):
        counselor = user.counselor_profile
        return qs.filter(Q(counselor=counselor) | Q(student__counselor=counselor)).distinct()
    if getattr(user, 'is_student', False) and hasattr(user, 'student_profile'):
        return qs.filter(student=user.student_profile)
    return qs.none()


class ProgramTemplateListCreateView(generics.ListCreateAPIView):
    """GET/POST /api/program-templates/

    Rehber kendi şablonlarını ve öğrencilerinin rutinlerini görür/yönetir; öğrenci
    yalnızca kendi rutinlerini."""
    serializer_class = ProgramTemplateSerializer
    permission_classes = [IsAuthenticated, IsCounselor | IsStudent]

    def get_queryset(self):
        return templates_visible_to(self.request.user)

    def get_serializer_context(self):
        # Rutin doğrulaması "öğrenci bu rehbere mi ait" kontrolü için kullanır.
        return {**super().get_serializer_context(),
                'counselor': getattr(self.request.user, 'counselor_profile', None)}

    def perform_create(self, serializer):
        user = self.request.user
        if getattr(user, 'is_student', False) and hasattr(user, 'student_profile'):
            # Öğrencinin rutini rehberine de bağlanır ki rehber görebilsin;
            # henüz bir rehbere bağlı değilse boş kalır.
            student = user.student_profile
            serializer.save(student=student, counselor=student.counselor)
        else:
            serializer.save(counselor=user.counselor_profile)


class ProgramTemplateDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PATCH/DELETE /api/program-templates/{id}/ — sahibi rehber ya da öğrenci."""
    serializer_class = ProgramTemplateSerializer
    permission_classes = [IsAuthenticated, IsCounselor | IsStudent]

    def get_queryset(self):
        return templates_visible_to(self.request.user)

    def get_serializer_context(self):
        return {**super().get_serializer_context(),
                'counselor': getattr(self.request.user, 'counselor_profile', None)}


def materialize_into_program(program, source, created_by, get=getattr):
    """Şablon görevlerini (weekday 0-6) programın tarih penceresine yazar.

    `source` ya `TemplateTask` nesneleri ya da doğrudan gelen sözlüklerdir; hangisi
    olduğunu `get` belirler (varsayılan `getattr`, sözlükler için `dict.get`).
    Şablon atama ve rutinin otomatik uygulanması aynı yoldan geçsin diye ortak.

    Pencere 7 günden kısaysa o günlere düşmeyen şablon görevleri **atlanır**
    (ör. 5 günlük Pzt–Cum programında şablonun Cumartesi bloğu yazılmaz)."""
    start_date = program.start_date
    tasks = []
    for t in source:
        weekday = get(t, 'weekday') or 0
        offset = (weekday - start_date.weekday()) % 7      # weekday'i pencereye eşle
        if offset >= program.day_count:
            continue                                       # gün pencerenin dışında
        tasks.append(Task(
            program=program,
            subject=get(t, 'subject'),
            task_type=get(t, 'task_type'),
            book=get(t, 'book'),
            kind=get(t, 'kind') or BlockKind.STUDY,
            exam_scope=get(t, 'exam_scope') or '',
            title=get(t, 'title') or '',
            date=start_date + timedelta(days=offset),
            start_time=get(t, 'start_time'),
            duration_minutes=get(t, 'duration_minutes'),
            order=get(t, 'order') or 0,
            created_by=created_by,
        ))
    Task.objects.bulk_create(tasks)
    return tasks


def apply_routine_if_any(program, created_by):
    """Öğrencinin otomatik rutini varsa yeni açılan haftaya materyalize eder.

    Rutin *o anki* hâliyle uygulanır; sonradan değiştirilmesi zaten açılmış
    haftaları etkilemez (geçmiş korunur)."""
    routine = (
        ProgramTemplate.objects
        .filter(student=program.student, auto_apply=True)
        .prefetch_related('tasks')
        .first()
    )
    if routine is None:
        return None
    materialize_into_program(program, list(routine.tasks.all()), created_by)
    return routine


class ProgramAssignView(APIView):
    """POST /api/programs/assign/ — bir planı (şablon ya da görev listesi) öğrencinin
    programına yazar.

    `start_date` verilmezse öğrenciye program atanmamış ilk gün, `day_count`
    verilmezse 7 gün kullanılır. Açıkça verilen bir aralık mevcut bir programla
    çakışıyorsa istek sessizce kaydırılmaz, `400` döner."""
    permission_classes = [IsAuthenticated, IsCounselor]

    def post(self, request):
        ser = ProgramAssignSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        counselor = request.user.counselor_profile
        student = data['student']
        if student.counselor_id != counselor.id:
            raise PermissionDenied("Yalnızca kendi öğrencinize atama yapabilirsiniz.")

        template = data.get('template')
        if template is not None and template.counselor_id != counselor.id:
            raise PermissionDenied("Yalnızca kendi şablonunuzu atayabilirsiniz.")

        # Kaynak görevler + program tipi
        if template is not None:
            source = list(template.tasks.all())
            schedule_type = data.get('schedule_type') or template.schedule_type
            get = getattr
        else:
            source = data['tasks']
            schedule_type = data.get('schedule_type') or WeeklyProgram.ScheduleType.TIMED
            get = lambda t, f: t.get(f)  # noqa: E731

        start_date = data.get('start_date') or WeeklyProgram.first_free_day(student)
        day_count = data.get('day_count') or 7

        clash = WeeklyProgram.find_overlap(student, start_date, day_count)
        if clash is not None:
            raise ValidationError(
                {'start_date': f"Bu tarih aralığı öğrencinin mevcut bir programıyla "
                               f"çakışıyor ({clash.start_date} – {clash.end_date})."}
            )

        program = WeeklyProgram.objects.create(
            student=student, counselor=counselor,
            start_date=start_date, day_count=day_count, schedule_type=schedule_type,
        )
        # Açıkça bir plan atanıyor; rutin ayrıca uygulanmaz (çift yazma olurdu).
        materialize_into_program(program, source, request.user, get)
        program.refresh_from_db()
        return Response(WeeklyProgramSerializer(program).data, status=201)


# --- Görevler (Task) ---------------------------------------------------------

class TaskListCreateView(generics.ListCreateAPIView):
    """GET/POST /api/programs/{program_pk}/tasks/ — hoca ve öğrenci görev ekler."""
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated, IsProgramParticipant]

    def get_program(self) -> WeeklyProgram:
        if not hasattr(self, '_program'):
            program = get_object_or_404(WeeklyProgram, pk=self.kwargs['program_pk'])
            self.check_object_permissions(self.request, program)
            self._program = program
        return self._program

    def get_queryset(self):
        return self.get_program().tasks.select_related('subject', 'task_type')

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        if self.request.method == 'POST':
            ctx['program'] = self.get_program()
        return ctx

    def perform_create(self, serializer):
        serializer.save(program=self.get_program(), created_by=self.request.user)


class TaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PATCH/DELETE /api/tasks/{id}/ — katılımcı (öğrenci de) düzenler/taşır/siler.

    Görevi başka güne taşımak = PATCH ile `date` alanını değiştirmek.
    """
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated, IsProgramParticipant]
    queryset = Task.objects.select_related('program__student', 'subject', 'task_type')


# --- Denemeler (ExamResult) --------------------------------------------------

class ExamResultListCreateView(generics.ListCreateAPIView):
    """GET: öğrenci kendi denemeleri · rehber ve **veli** ilgili öğrencininki
    (ikisi de `?student=<id>` ile daraltabilir) · POST: yalnızca öğrenci, kendi
    denemesini girer.

    Veli erişimi E3 ile açıldı: veli çocuğunun denemelerini ders kırılımıyla
    (`subject_nets`: doğru/yanlış/boş/net) salt-okunur görür. Program verisinin
    aksine **onay şartı yoktur** — deneme programa bağlı değil, öğrencinin
    doğrudan girdiği bir sonuçtur.

    `?source=personal|institutional` ile kişisel/kurumsal denemeler ayrıştırılır (E1)."""
    serializer_class = ExamResultSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsStudent()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        qs = (
            ExamResult.objects
            .select_related('student__user')
            .prefetch_related('subject_nets__subject')
        )
        # Kişisel/kurumsal süzgeci (E1) role bakmaksızın uygulanır.
        source = self.request.query_params.get('source')
        if source in ExamSource.values:
            qs = qs.filter(source=source)

        if getattr(user, 'is_student', False) and hasattr(user, 'student_profile'):
            return qs.filter(student=user.student_profile)
        student_id = self.request.query_params.get('student')
        if getattr(user, 'is_counselor', False) and hasattr(user, 'counselor_profile'):
            qs = qs.filter(student__counselor=user.counselor_profile)
            if student_id:
                qs = qs.filter(student_id=student_id)
            return qs
        if getattr(user, 'is_parent', False) and hasattr(user, 'parent_profile'):
            qs = qs.filter(student__in=user.parent_profile.students.all())
            if student_id:
                qs = qs.filter(student_id=student_id)
            return qs
        return qs.none()

    def perform_create(self, serializer):
        # Öğrenci her zaman KENDİ adına kaydeder — student dışarıdan gelmez
        serializer.save(student=self.request.user.student_profile)


class ExamResultDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PATCH/DELETE /api/exams/{id}/ — sahibi öğrenci tam; rehberi ve velisi salt-okur."""
    serializer_class = ExamResultSerializer
    permission_classes = [IsAuthenticated, IsExamOwnerStudentOrReadOnly]
    queryset = (
        ExamResult.objects
        .select_related('student__user')
        .prefetch_related('subject_nets__subject')
    )


# --- Hedefler (Goal) ---------------------------------------------------------

class GoalListCreateView(generics.ListCreateAPIView):
    """GET: rolüne göre hedefler (rehber ?student=<id> ile filtreler) ·
    POST: öğrenci kendine hedef koyar.

    **Veli hedefleri görmez** (E3 kapsam kararı) — liste boş döner."""
    serializer_class = GoalSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsStudent()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        qs = Goal.objects.select_related('student__user', 'subject')
        if getattr(user, 'is_student', False) and hasattr(user, 'student_profile'):
            return qs.filter(student=user.student_profile)
        if getattr(user, 'is_counselor', False) and hasattr(user, 'counselor_profile'):
            qs = qs.filter(student__counselor=user.counselor_profile)
            student_id = self.request.query_params.get('student')
            if student_id:
                qs = qs.filter(student_id=student_id)
            return qs
        return qs.none()          # veli dahil diğer roller: hedef görünmez (E3)

    def perform_create(self, serializer):
        # Öğrenci her zaman KENDİ adına kaydeder — student dışarıdan gelmez
        serializer.save(student=self.request.user.student_profile)


class GoalDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PATCH/DELETE /api/goals/{id}/ — sahibi öğrenci tam, rehberi salt-okur (veli göremez)."""
    serializer_class = GoalSerializer
    permission_classes = [IsAuthenticated, IsGoalOwnerStudentOrReadOnly]
    queryset = Goal.objects.select_related('student__user', 'subject')


# --- Kitaplık (Book) ---------------------------------------------------------

class BookListCreateView(generics.ListCreateAPIView):
    """GET: rolüne göre kitaplar (rehber ?student=<id> ile filtreler) ·
    POST: öğrenci kendi kitaplığına kitap ekler.

    **Veli kitaplığı görmez** (kullanıcı kararı, E3) — liste boş döner."""
    serializer_class = BookSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsStudent()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        qs = Book.objects.select_related('student__user', 'subject')
        if getattr(user, 'is_student', False) and hasattr(user, 'student_profile'):
            return qs.filter(student=user.student_profile)
        if getattr(user, 'is_counselor', False) and hasattr(user, 'counselor_profile'):
            qs = qs.filter(student__counselor=user.counselor_profile)
            student_id = self.request.query_params.get('student')
            if student_id:
                qs = qs.filter(student_id=student_id)
            return qs
        return qs.none()          # veli dahil diğer roller: kitaplık görünmez (E3)

    def perform_create(self, serializer):
        # Öğrenci her zaman KENDİ adına kaydeder — student dışarıdan gelmez
        book = serializer.save(student=self.request.user.student_profile)
        # Ders kitabıysa konularını katalogdan otomatik doldur
        book.populate_topics()


class BookDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PATCH/DELETE /api/books/{id}/ — sahibi öğrenci tam, rehberi salt-okur.
    Veli göremez (E3). Yanıt kitabın içindeki konuları (`topics`) da içerir."""
    serializer_class = BookDetailSerializer
    permission_classes = [IsAuthenticated, IsBookOwnerStudentOrReadOnly]
    queryset = Book.objects.select_related('student__user', 'subject').prefetch_related(
        'book_topics__topic'
    )


class BookTopicDetailView(generics.RetrieveUpdateAPIView):
    """GET/PATCH /api/book-topics/{id}/ — kitabın içindeki bir konuyu işaretle
    (durum/test). Sahibi öğrenci düzenler; rehberi/velisi salt-okur."""
    serializer_class = BookTopicSerializer
    permission_classes = [IsAuthenticated, IsBookTopicOwnerStudentOrReadOnly]
    queryset = BookTopic.objects.select_related('book__student__user', 'topic')


# --- Konular (Topic + TopicProgress) -----------------------------------------

class TopicListView(generics.ListAPIView):
    """GET /api/topics/?subject=<id>&grade=<9-12>&curriculum=<eski|maarif> — konu kataloğu.

    `curriculum` verilmezse ve istek bir öğrenciden geliyorsa, öğrencinin sınıfına
    uygun müfredat (12/mezun→eski, 9/10/11→maarif) otomatik uygulanır. Öğrenci
    isteğinde her konuya kendi ilerlemesi (`my_progress`) gömülür; 'Konular' sayfası
    tek çağrıda dolar."""
    serializer_class = TopicSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Topic.objects.select_related('subject')
        subject_id = self.request.query_params.get('subject')
        grade = self.request.query_params.get('grade')
        curriculum = self.request.query_params.get('curriculum')
        if subject_id:
            qs = qs.filter(subject_id=subject_id)
        if grade:
            qs = qs.filter(grade=grade)
        if not curriculum:
            user = self.request.user
            if getattr(user, 'is_student', False) and hasattr(user, 'student_profile'):
                curriculum = user.student_profile.curriculum
        if curriculum:
            qs = qs.filter(curriculum=curriculum)
        return qs

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        user = self.request.user
        if getattr(user, 'is_student', False) and hasattr(user, 'student_profile'):
            topic_ids = self.get_queryset().values_list('id', flat=True)
            ctx['progress_map'] = {
                p.topic_id: p for p in TopicProgress.objects.filter(
                    student=user.student_profile, topic_id__in=list(topic_ids)
                )
            }
        return ctx


class TopicProgressListCreateView(generics.ListCreateAPIView):
    """GET: rolüne göre konu ilerlemeleri (rehber ?student=<id>, ayrıca ?subject= &
    ?grade= ile filtreler) · POST: öğrenci kendi konusunu, rehber öğrencisinin
    konusunu kaydeder/günceller (aynı konu tekrar gelirse upsert)."""
    serializer_class = TopicProgressSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), (IsStudent | IsCounselor)()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        qs = TopicProgress.objects.select_related(
            'student__user', 'topic__subject'
        )
        if getattr(user, 'is_student', False) and hasattr(user, 'student_profile'):
            qs = qs.filter(student=user.student_profile)
        elif getattr(user, 'is_counselor', False) and hasattr(user, 'counselor_profile'):
            qs = qs.filter(student__counselor=user.counselor_profile)
            student_id = self.request.query_params.get('student')
            if student_id:
                qs = qs.filter(student_id=student_id)
        elif getattr(user, 'is_parent', False) and hasattr(user, 'parent_profile'):
            # Veli çocuğunun konu takip listesini salt-okunur görür (E3).
            qs = qs.filter(student__in=user.parent_profile.students.all())
            student_id = self.request.query_params.get('student')
            if student_id:
                qs = qs.filter(student_id=student_id)
        else:
            return qs.none()
        subject_id = self.request.query_params.get('subject')
        grade = self.request.query_params.get('grade')
        if subject_id:
            qs = qs.filter(topic__subject_id=subject_id)
        if grade:
            qs = qs.filter(topic__grade=grade)
        return qs

    def perform_create(self, serializer):
        user = self.request.user
        # Öğrenci kendi adına kaydeder; student dışarıdan gelmez.
        if getattr(user, 'is_student', False) and hasattr(user, 'student_profile'):
            serializer.save(student=user.student_profile)
            return
        # Rehber: hedef öğrenci payload'daki 'student' olmalı ve kendi öğrencisi olmalı.
        student = user.counselor_profile.students.filter(
            pk=self.request.data.get('student')).first()
        if student is None:
            raise PermissionDenied("Bu öğrenci sizin öğrenciniz değil.")
        serializer.save(student=student)


class TopicProgressDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PATCH/DELETE /api/topic-progress/{id}/ — sahibi öğrenci tam, rehberi/velisi salt-okur."""
    serializer_class = TopicProgressSerializer
    permission_classes = [IsAuthenticated, IsTopicProgressOwnerStudentOrReadOnly]
    queryset = TopicProgress.objects.select_related('student__user', 'topic__subject')


# --- Takvim (CalendarEvent) --------------------------------------------------

class CalendarEventListCreateView(generics.ListCreateAPIView):
    """GET: rehber kendi takvimi; öğrenci/veli kendine bağlı etkinlikler
    (?from=&to= tarih aralığı, rehber ayrıca ?student=<id>) · POST: yalnızca rehber."""
    serializer_class = CalendarEventSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsCounselor()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        qs = CalendarEvent.objects.select_related('counselor__user', 'student__user')
        if getattr(user, 'is_counselor', False) and hasattr(user, 'counselor_profile'):
            qs = qs.filter(counselor=user.counselor_profile)
            student_id = self.request.query_params.get('student')
            if student_id:
                qs = qs.filter(student_id=student_id)
        elif getattr(user, 'is_student', False) and hasattr(user, 'student_profile'):
            qs = qs.filter(student=user.student_profile)
        elif getattr(user, 'is_parent', False) and hasattr(user, 'parent_profile'):
            qs = qs.filter(student__in=user.parent_profile.students.all())
        else:
            return qs.none()
        date_from = self.request.query_params.get('from')
        date_to = self.request.query_params.get('to')
        if date_from:
            qs = qs.filter(date__gte=date_from)
        if date_to:
            qs = qs.filter(date__lte=date_to)
        return qs

    def perform_create(self, serializer):
        counselor = self.request.user.counselor_profile
        student = serializer.validated_data.get('student')
        if student is not None and student.counselor_id != counselor.id:
            raise PermissionDenied("Etkinliğe yalnızca kendi öğrencinizi bağlayabilirsiniz.")
        serializer.save(counselor=counselor)


class CalendarEventDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PATCH/DELETE /api/calendar/{id}/ — sahibi rehber tam, hedef öğrenci/veli
    salt-okur."""
    serializer_class = CalendarEventSerializer
    permission_classes = [IsAuthenticated, IsCalendarOwnerOrTargetRead]
    queryset = CalendarEvent.objects.select_related('counselor__user', 'student__user')

    def perform_update(self, serializer):
        counselor = self.request.user.counselor_profile
        student = serializer.validated_data.get('student', serializer.instance.student)
        if student is not None and student.counselor_id != counselor.id:
            raise PermissionDenied("Etkinliğe yalnızca kendi öğrencinizi bağlayabilirsiniz.")
        serializer.save()
