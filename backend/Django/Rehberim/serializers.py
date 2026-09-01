from datetime import date as date_cls, timedelta

from django.db import transaction
from django.db.models import F, Max
from rest_framework import serializers

from .models import (
    Achievement, AchievementMetric, BlockDurationDefault, BlockKind, Book,
    BookTopic, CalendarEvent, ExamResult, Goal, ProgramTemplate, Publisher,
    Subject, SubjectNet, Task, TaskType, TemplateTask, Topic, TopicProgress,
    WeeklyProgram,
)


def validate_block_kind(kind: str, exam_scope: str, subject, task_type, book,
                        title: str) -> None:
    """Blok türüne göre alan kurallarını uygular (Task ve TemplateTask ortak).

    - `external` (okul/antrenman/doktor): ders, metod ve kitap taşımaz; ne olduğu
      yalnızca başlıktan anlaşıldığı için başlık zorunludur.
    - `exam`: ya bir ders (ders bazlı deneme) ya da `exam_scope` (genel TYT/AYT
      denemesi) verilmelidir; ikisi birden verilemez.
    - `study`: `exam_scope` taşıyamaz.
    """
    if kind == BlockKind.EXTERNAL:
        if subject is not None or task_type is not None or book is not None:
            raise serializers.ValidationError(
                {'kind': "Dış meşguliyet bloğuna ders, metod veya kitap eklenemez."}
            )
        if not (title or '').strip():
            raise serializers.ValidationError(
                {'title': "Dış meşguliyet bloğu için başlık zorunludur."}
            )
        if exam_scope:
            raise serializers.ValidationError(
                {'exam_scope': "Deneme kapsamı yalnızca deneme bloğunda kullanılır."}
            )
    elif kind == BlockKind.EXAM:
        if subject is None and not exam_scope:
            raise serializers.ValidationError(
                {'exam_scope': "Deneme bloğunda ders ya da deneme kapsamı (TYT/AYT) "
                               "seçilmelidir."}
            )
        if subject is not None and exam_scope:
            raise serializers.ValidationError(
                {'exam_scope': "Genel deneme bloğunda ders seçilemez."}
            )
    elif exam_scope:
        raise serializers.ValidationError(
            {'exam_scope': "Deneme kapsamı yalnızca deneme bloğunda kullanılır."}
        )


class SubjectSerializer(serializers.ModelSerializer):
    """DERS dropdown'u için — id, isim, kategori, gösterim etiketi."""
    label = serializers.SerializerMethodField()

    class Meta:
        model = Subject
        fields = ['id', 'name', 'category', 'label', 'question_count']

    def get_label(self, obj: Subject) -> str:
        return str(obj)


class TaskTypeSerializer(serializers.ModelSerializer):
    """METOD dropdown'u için."""

    class Meta:
        model = TaskType
        fields = ['id', 'name']


class PublisherSerializer(serializers.ModelSerializer):
    """YAYINEVİ dropdown'u için (kitap eklenirken)."""

    class Meta:
        model = Publisher
        fields = ['id', 'name']


class BlockDurationDefaultSerializer(serializers.ModelSerializer):
    """Rehberin süre hafızası — salt-okunur.

    Yazma işlemi ayrı bir uçla değil, blok kaydedilirken sessizce yapılır
    (`TaskSerializer._remember_duration`). Web bu listeyi bir kez çekip
    (ders, metod, konu) → süre haritası kurar."""

    class Meta:
        model = BlockDurationDefault
        fields = ['subject', 'task_type', 'topic', 'duration_minutes', 'updated_at']


class TaskSerializer(serializers.ModelSerializer):
    """Programa eklenen tek görev: DERS + METOD + başlık, bir güne (opsiyonel saatle)."""
    subject_label = serializers.SerializerMethodField()
    task_type_name = serializers.SerializerMethodField()
    book_label = serializers.SerializerMethodField()
    end_time = serializers.TimeField(read_only=True)
    counts_as_study = serializers.BooleanField(read_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'program', 'subject', 'subject_label', 'task_type',
            'task_type_name', 'book', 'book_label', 'kind', 'exam_scope',
            'title', 'description',
            'date', 'start_time', 'duration_minutes', 'end_time',
            'is_completed', 'counts_as_study', 'created_by', 'order',
        ]
        read_only_fields = ['program', 'created_by', 'counts_as_study']

    def get_subject_label(self, obj: Task) -> str | None:
        return str(obj.subject) if obj.subject_id else None

    def get_task_type_name(self, obj: Task) -> str | None:
        return obj.task_type.name if obj.task_type_id else None

    def get_book_label(self, obj: Task) -> str | None:
        return obj.book.display_label() if obj.book_id else None

    def _eff(self, attrs: dict, field: str):
        """Create'de attrs'tan, update'te eksikse mevcut instance'tan değer al."""
        return attrs.get(field, getattr(self.instance, field, None))

    def validate(self, attrs: dict) -> dict:
        program = self.context.get('program') or getattr(self.instance, 'program', None)
        item_date: date_cls | None = self._eff(attrs, 'date')
        start = self._eff(attrs, 'start_time')
        duration = self._eff(attrs, 'duration_minutes')

        # 1) Gün programın tarih aralığında olmalı (uzunluk artık değişken)
        if program and item_date and not program.covers(item_date):
            raise serializers.ValidationError(
                {'date': f"Görev, programın {program.start_date} – {program.end_date} "
                         f"aralığında olmalıdır."}
            )
        # Kaynak kitap verildiyse programın öğrencisine ait olmalı
        book = self._eff(attrs, 'book')
        if book is not None and program is not None and book.student_id != program.student_id:
            raise serializers.ValidationError(
                {'book': "Kaynak kitap, programın öğrencisine ait olmalıdır."}
            )

        # 2) Blok türü kuralları (dış meşguliyet / genel deneme)
        validate_block_kind(
            kind=self._eff(attrs, 'kind') or BlockKind.STUDY,
            exam_scope=self._eff(attrs, 'exam_scope') or '',
            subject=self._eff(attrs, 'subject'),
            task_type=self._eff(attrs, 'task_type'),
            book=book,
            title=self._eff(attrs, 'title') or '',
        )

        if program is None:
            return attrs

        # 3) Program tipine göre saat kuralı
        if program.is_timed:
            if start is None or duration is None:
                raise serializers.ValidationError(
                    {'start_time': "Saatli programda başlangıç saati ve süre zorunludur."}
                )
            if duration <= 0:
                raise serializers.ValidationError(
                    {'duration_minutes': "Süre pozitif olmalıdır."}
                )
            # 4) Çakışma: aynı gün zaman aralığı çakışan görev olamaz. Dış
            #    meşguliyet blokları da sayılır — okuldayken ders çalışılamaz.
            new_start = start.hour * 60 + start.minute
            new_end = new_start + duration
            siblings = program.tasks.filter(date=item_date, start_time__isnull=False)
            if self.instance is not None:
                siblings = siblings.exclude(pk=self.instance.pk)
            for other in siblings:
                o_start = other.start_time.hour * 60 + other.start_time.minute
                o_end = o_start + other.duration_minutes
                if new_start < o_end and o_start < new_end:
                    raise serializers.ValidationError(
                        {'start_time': "Bu saatte çakışan bir görev var."}
                    )
        else:
            # Saatsiz programda saat/süre girilemez
            if start is not None or duration is not None:
                raise serializers.ValidationError(
                    {'start_time': "Saatsiz programda saat/süre girilemez."}
                )
        return attrs

    # --- Sıralama (drag & drop) ---------------------------------------------
    # `order` = görevin gün içindeki 0-based pozisyonu. Bir görev eklenince/
    # taşınınca aynı günün diğer görevleri kayar; sıra tutarlı (çakışmasız) kalır.

    @staticmethod
    def _siblings(program, date):
        return Task.objects.filter(program=program, date=date)

    # --- Süre hafızası -------------------------------------------------------

    @staticmethod
    def _memory_signature(task: Task) -> tuple:
        """Bloğun hafızayı ilgilendiren tanımı: (ders, metod, konu, süre).

        Bunun dışındaki alanlar (gün, saat, sıra, tamamlandı) bloğun *nerede*
        durduğudur, *ne olduğu* değil — değişmeleri hafızayı ilgilendirmez."""
        return (task.subject_id, task.task_type_id, task.title, task.duration_minutes)

    def _remember_duration(self, task: Task) -> None:
        """Bloğu kaydeden rehberin süre hafızasını günceller (A4).

        Yalnızca rehber yazar: öğrenci kendi görevini kaydettiğinde (ya da bir
        görevi 'tamamlandı' işaretlediğinde) hocanın varsayılanları değişmez.
        """
        user = getattr(self.context.get('request'), 'user', None)
        counselor = getattr(user, 'counselor_profile', None)
        BlockDurationDefault.remember(counselor, task)

    def create(self, validated_data: dict) -> Task:
        program = validated_data['program']
        date = validated_data['date']
        with transaction.atomic():
            if 'order' in validated_data:
                # Belirli pozisyona ekle → o pozisyondan itibaren herkesi bir kaydır
                target = validated_data['order']
                self._siblings(program, date).filter(order__gte=target).update(
                    order=F('order') + 1
                )
            else:
                # Pozisyon verilmediyse günün sonuna ekle
                current_max = self._siblings(program, date).aggregate(m=Max('order'))['m']
                validated_data['order'] = 0 if current_max is None else current_max + 1
            task = super().create(validated_data)
        self._remember_duration(task)
        return task

    def update(self, instance: Task, validated_data: dict) -> Task:
        program = instance.program
        old_date, old_order = instance.date, instance.order
        # Blok tanımı değişmediyse hafıza yazılmaz: tahtada eski bir bloğu
        # sürüklemek, o kombinasyon için daha yeni girilmiş süreyi geri almamalı.
        before = self._memory_signature(instance)
        new_date = validated_data.get('date', old_date)
        order_given = 'order' in validated_data
        new_order = validated_data.get('order', old_order)
        with transaction.atomic():
            if new_date != old_date:
                # Eski günde bıraktığı boşluğu kapat
                self._siblings(program, old_date).filter(
                    order__gt=old_order
                ).exclude(pk=instance.pk).update(order=F('order') - 1)
                if order_given:
                    # Yeni günde hedef pozisyona yer aç
                    self._siblings(program, new_date).filter(
                        order__gte=new_order
                    ).exclude(pk=instance.pk).update(order=F('order') + 1)
                else:
                    # Pozisyon yoksa yeni günün sonuna
                    current_max = self._siblings(program, new_date).exclude(
                        pk=instance.pk
                    ).aggregate(m=Max('order'))['m']
                    validated_data['order'] = 0 if current_max is None else current_max + 1
            elif order_given and new_order != old_order:
                # Aynı gün içinde yeniden sırala
                sibs = self._siblings(program, old_date).exclude(pk=instance.pk)
                if new_order > old_order:
                    sibs.filter(order__gt=old_order, order__lte=new_order).update(
                        order=F('order') - 1
                    )
                else:
                    sibs.filter(order__gte=new_order, order__lt=old_order).update(
                        order=F('order') + 1
                    )
            task = super().update(instance, validated_data)
        if self._memory_signature(task) != before:
            self._remember_duration(task)
        return task


class WeeklyProgramSerializer(serializers.ModelSerializer):
    """Program + içindeki görevler (nested, salt-okunur listelenir).

    Uzunluk `day_count` ile verilir (varsayılan 7); `end_date` ondan türetilir.
    Aynı öğrencinin programları tarih aralığı olarak örtüşemez."""
    tasks = TaskSerializer(many=True, read_only=True)
    end_date = serializers.DateField(read_only=True)
    student_name = serializers.SerializerMethodField()
    # Onay salt-okunur: yalnızca /programs/{id}/approve/ ucundan değişir.
    is_approved = serializers.BooleanField(read_only=True)
    is_finished = serializers.BooleanField(read_only=True)
    approved_by_name = serializers.SerializerMethodField()
    # Uyum özeti (B2) — süre üzerinden, salt-okunur. Bkz. WeeklyProgram.compliance().
    compliance = serializers.SerializerMethodField()

    class Meta:
        model = WeeklyProgram
        fields = [
            'id', 'student', 'student_name', 'counselor', 'start_date', 'day_count',
            'end_date', 'schedule_type', 'note', 'tasks',
            'is_approved', 'is_finished', 'approved_at', 'approved_by',
            'approved_by_name', 'compliance', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'counselor', 'approved_at', 'approved_by', 'created_at', 'updated_at',
        ]

    def get_student_name(self, obj: WeeklyProgram) -> str:
        return obj.student.user.get_full_name()

    def get_approved_by_name(self, obj: WeeklyProgram) -> str | None:
        return obj.approved_by.user.get_full_name() if obj.approved_by_id else None

    def get_compliance(self, obj: WeeklyProgram) -> dict:
        return obj.compliance()

    def validate(self, attrs: dict) -> dict:
        def eff(field, default=None):
            if field in attrs:
                return attrs[field]
            return getattr(self.instance, field, default)

        student = eff('student')
        start_date = eff('start_date')
        day_count = eff('day_count') or 7
        if student is None or start_date is None:
            return attrs

        clash = WeeklyProgram.find_overlap(
            student, start_date, day_count,
            exclude_pk=self.instance.pk if self.instance else None,
        )
        if clash is not None:
            raise serializers.ValidationError(
                {'start_date': f"Bu tarih aralığı öğrencinin mevcut bir programıyla "
                               f"çakışıyor ({clash.start_date} – {clash.end_date})."}
            )

        # Pencere daraltılırken dışarıda kalan görev olmamalı. Görev eklerken
        # `program.covers(date)` bakılıyor ama pencereyi kısaltmak aynı kuralı
        # tersten deler: görev öksüz kalır, hiçbir programa düşmez.
        if self.instance is not None:
            end_date = start_date + timedelta(days=day_count - 1)
            orphans = [
                t for t in self.instance.tasks.all()
                if not (start_date <= t.date <= end_date)
            ]
            if orphans:
                days = sorted({t.date for t in orphans})
                listed = ", ".join(d.isoformat() for d in days[:3])
                if len(days) > 3:
                    listed += f" ve {len(days) - 3} gün daha"
                raise serializers.ValidationError(
                    {'day_count': f"Bu pencereye sığmayan {len(orphans)} görev var "
                                  f"({listed}). Önce onları taşıyın veya silin."}
                )
        return attrs


# === PROGRAM ŞABLONLARI (ProgramTemplate + TemplateTask) ===================

class TemplateTaskSerializer(serializers.ModelSerializer):
    """Şablondaki tek görev — WeeklyProgram Task'ıyla aynı, tarih yerine weekday (0-6)."""
    subject_label = serializers.SerializerMethodField()
    task_type_name = serializers.SerializerMethodField()
    book_label = serializers.SerializerMethodField()

    class Meta:
        model = TemplateTask
        fields = [
            'id', 'subject', 'subject_label', 'task_type', 'task_type_name',
            'book', 'book_label', 'kind', 'exam_scope', 'title', 'weekday',
            'start_time', 'duration_minutes', 'order',
        ]

    def get_subject_label(self, obj: TemplateTask) -> str | None:
        return str(obj.subject) if obj.subject_id else None

    def get_task_type_name(self, obj: TemplateTask) -> str | None:
        return obj.task_type.name if obj.task_type_id else None

    def get_book_label(self, obj: TemplateTask) -> str | None:
        return obj.book.display_label() if obj.book_id else None

    def validate(self, attrs: dict) -> dict:
        validate_block_kind(
            kind=attrs.get('kind') or BlockKind.STUDY,
            exam_scope=attrs.get('exam_scope') or '',
            subject=attrs.get('subject'),
            task_type=attrs.get('task_type'),
            book=attrs.get('book'),
            title=attrs.get('title') or '',
        )
        return attrs


class ProgramTemplateSerializer(serializers.ModelSerializer):
    """İsimli şablon program + görevleri (nested). Rehber oluşturur/düzenler/siler.

    `student` doldurulup `auto_apply` açılırsa şablon o öğrencinin **rutini** olur:
    öğrenciye yeni hafta açıldığında görevler kendiliğinden materyalize edilir."""
    tasks = TemplateTaskSerializer(many=True)
    student_name = serializers.SerializerMethodField()

    class Meta:
        model = ProgramTemplate
        fields = [
            'id', 'name', 'schedule_type', 'student', 'student_name', 'auto_apply',
            'tasks', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from accounts.models import Student
        self.fields['student'].queryset = Student.objects.all()
        self.fields['student'].required = False
        self.fields['student'].allow_null = True

    def get_student_name(self, obj: ProgramTemplate) -> str | None:
        return obj.student.user.get_full_name() if obj.student_id else None

    def _eff(self, attrs: dict, field: str):
        """PATCH'te gönderilmeyen alan için mevcut değeri kullan."""
        if field in attrs:
            return attrs[field]
        return getattr(self.instance, field, None)

    def validate(self, attrs: dict) -> dict:
        user = getattr(self.context.get('request'), 'user', None)
        is_student = bool(getattr(user, 'is_student', False) and hasattr(user, 'student_profile'))

        if is_student:
            # Öğrenci yalnızca kendi rutinini kurar; gövdedeki student yok sayılır.
            own = user.student_profile
            if attrs.get('student') not in (None, own) and 'student' in attrs:
                raise serializers.ValidationError(
                    {'student': "Yalnızca kendi rutininizi tanımlayabilirsiniz."}
                )
            attrs['student'] = own
            student = own
        else:
            student = self._eff(attrs, 'student')

        auto_apply = self._eff(attrs, 'auto_apply') or False

        if auto_apply and student is None:
            raise serializers.ValidationError(
                {'student': "Otomatik uygulanacak rutin için öğrenci seçilmelidir."}
            )

        if not is_student:
            counselor = self.context.get('counselor')
            if student is not None and counselor is not None and student.counselor_id != counselor.id:
                raise serializers.ValidationError(
                    {'student': "Yalnızca kendi öğrenciniz için rutin tanımlayabilirsiniz."}
                )

        # Öğrenci başına tek otomatik rutin — DB kısıtı IntegrityError (500) verirdi.
        if auto_apply and student is not None:
            clash = ProgramTemplate.objects.filter(student=student, auto_apply=True)
            if self.instance is not None:
                clash = clash.exclude(pk=self.instance.pk)
            if clash.exists():
                who = "Zaten" if is_student else f"{student.user.get_full_name()} için zaten"
                raise serializers.ValidationError(
                    {'auto_apply': f"{who} bir otomatik rutin var ({clash.first().name}). "
                                   f"Önce onu kapatın."}
                )

        # Ad çakışması (DB kısıtı 500 verirdi): rutinde öğrenci içinde, genel
        # şablonda rehber içinde benzersiz.
        name = self._eff(attrs, 'name')
        if name:
            if student is not None:
                dupes = ProgramTemplate.objects.filter(student=student, name=name)
            else:
                counselor = self.context.get('counselor')
                dupes = ProgramTemplate.objects.filter(
                    counselor=counselor, name=name, student__isnull=True,
                )
            if self.instance is not None:
                dupes = dupes.exclude(pk=self.instance.pk)
            if dupes.exists():
                raise serializers.ValidationError(
                    {'name': f"'{name}' adında bir kayıt zaten var."}
                )
        return attrs

    def create(self, validated_data: dict) -> ProgramTemplate:
        tasks = validated_data.pop('tasks', [])
        template = ProgramTemplate.objects.create(**validated_data)
        TemplateTask.objects.bulk_create(
            [TemplateTask(template=template, **t) for t in tasks]
        )
        return template

    def update(self, instance: ProgramTemplate, validated_data: dict) -> ProgramTemplate:
        tasks = validated_data.pop('tasks', None)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()
        if tasks is not None:
            instance.tasks.all().delete()
            TemplateTask.objects.bulk_create(
                [TemplateTask(template=instance, **t) for t in tasks]
            )
        return instance


class ProgramAssignSerializer(serializers.Serializer):
    """Bir planı (şablon ya da doğrudan görev listesi) bir öğrencinin haftasına atar.

    `start_date` verilmezse öğrenciye program atanmamış ilk gün seçilir; `day_count`
    verilmezse 7 gün. Görevler weekday (0-6) ile gelir; sunucu bunları hedef
    pencerenin tarihlerine çevirir, pencereye düşmeyen günleri atlar."""
    student = serializers.PrimaryKeyRelatedField(queryset=Subject.objects.none())  # set in __init__
    start_date = serializers.DateField(required=False)
    day_count = serializers.IntegerField(required=False, min_value=1, max_value=31)
    template = serializers.PrimaryKeyRelatedField(
        queryset=ProgramTemplate.objects.all(), required=False,
    )
    tasks = TemplateTaskSerializer(many=True, required=False)
    schedule_type = serializers.ChoiceField(
        choices=WeeklyProgram.ScheduleType.choices, required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from accounts.models import Student
        self.fields['student'].queryset = Student.objects.all()

    def validate(self, attrs: dict) -> dict:
        if not attrs.get('template') and attrs.get('tasks') is None:
            raise serializers.ValidationError("template veya tasks verilmelidir.")
        return attrs


# === DENEMELER (ExamResult + SubjectNet) ===================================

class SubjectNetSerializer(serializers.ModelSerializer):
    """Bir denemede tek bir dersin sonucu. Öğrenci **doğru** ve **yanlış** girer;
    **boş** ve **net** sunucuda türetilir (net = doğru - yanlış/4)."""
    subject_label = serializers.SerializerMethodField()
    question_count = serializers.IntegerField(source='subject.question_count', read_only=True)
    blank = serializers.IntegerField(read_only=True)          # boş = soru - doğru - yanlış
    net = serializers.FloatField(read_only=True)              # net = doğru - yanlış/4

    class Meta:
        model = SubjectNet
        fields = ['id', 'subject', 'subject_label', 'correct', 'wrong', 'blank', 'net', 'question_count']

    def get_subject_label(self, obj: SubjectNet) -> str | None:
        return str(obj.subject) if obj.subject_id else None

    def validate(self, attrs: dict) -> dict:
        # Doğru + yanlış, dersin soru sayısını aşamaz (boş negatif olamaz).
        subject = attrs.get('subject')
        correct = attrs.get('correct', 0)
        wrong = attrs.get('wrong', 0)
        if subject is not None and subject.question_count:
            if correct + wrong > subject.question_count:
                raise serializers.ValidationError(
                    {'correct': f"{subject} için doğru+yanlış en fazla {subject.question_count} olabilir."}
                )
        return attrs


class ExamResultSerializer(serializers.ModelSerializer):
    """Bir deneme sonucu + içindeki ders netleri (iç içe / nested)."""
    subject_nets = SubjectNetSerializer(many=True)
    total_net = serializers.FloatField(read_only=True)
    student_name = serializers.SerializerMethodField()

    class Meta:
        model = ExamResult
        fields = [
            'id', 'student', 'student_name', 'exam_type', 'source', 'name',
            'exam_date', 'total_net', 'subject_nets',
        ]
        read_only_fields = ['student']

    def get_student_name(self, obj: ExamResult) -> str:
        return obj.student.user.get_full_name()

    def validate_subject_nets(self, value: list) -> list:
        subject_ids = [n['subject'].id for n in value]
        if len(subject_ids) != len(set(subject_ids)):
            raise serializers.ValidationError("Aynı ders birden fazla kez girilemez.")
        return value

    @staticmethod
    def _build_nets(exam: ExamResult, nets: list) -> list:
        # bulk_create save()'i atladığından net'i burada hesaplarız.
        return [
            SubjectNet(
                exam_result=exam,
                subject=n['subject'],
                correct=n.get('correct', 0),
                wrong=n.get('wrong', 0),
                net=SubjectNet.compute_net(n.get('correct', 0), n.get('wrong', 0)),
            )
            for n in nets
        ]

    def create(self, validated_data: dict) -> ExamResult:
        nets = validated_data.pop('subject_nets', [])
        exam = ExamResult.objects.create(**validated_data)
        SubjectNet.objects.bulk_create(self._build_nets(exam, nets))
        return exam

    def update(self, instance: ExamResult, validated_data: dict) -> ExamResult:
        nets = validated_data.pop('subject_nets', None)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()
        if nets is not None:
            instance.subject_nets.all().delete()
            SubjectNet.objects.bulk_create(self._build_nets(instance, nets))
        return instance


# === HEDEFLER (Goal) =======================================================

class GoalSerializer(serializers.ModelSerializer):
    """Öğrencinin kendine koyduğu hedef. `student` sunucuda atanır (salt-okunur).

    Türe göre farklı alanlar dolu gelir:
    - deneme_net → `exam_scope` (tyt/ayt) + opsiyonel `subject` (boş=toplam) + `target_net`
    - konu / kitap_* → şimdilik `title` (referanslar ileride)
    """
    student_name = serializers.SerializerMethodField()
    label = serializers.SerializerMethodField()
    subject_label = serializers.SerializerMethodField()

    class Meta:
        model = Goal
        fields = [
            'id', 'student', 'student_name', 'goal_type', 'title', 'label',
            'description', 'target_date', 'is_achieved',
            'exam_scope', 'subject', 'subject_label', 'target_net',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['student', 'created_at', 'updated_at']

    def get_student_name(self, obj: Goal) -> str:
        return obj.student.user.get_full_name()

    def get_label(self, obj: Goal) -> str:
        return obj.display_label()

    def get_subject_label(self, obj: Goal) -> str | None:
        return str(obj.subject) if obj.subject_id else None

    def _eff(self, attrs: dict, field: str):
        return attrs.get(field, getattr(self.instance, field, None))

    def validate(self, attrs: dict) -> dict:
        goal_type = self._eff(attrs, 'goal_type')
        net = self._eff(attrs, 'target_net')
        scope = self._eff(attrs, 'exam_scope')
        subject = self._eff(attrs, 'subject')
        if goal_type == Goal.GoalType.DENEME_NETI:
            if net is None:
                raise serializers.ValidationError(
                    {'target_net': "Deneme neti hedefi için net değeri gereklidir."}
                )
            if net < 0:
                raise serializers.ValidationError({'target_net': "Net negatif olamaz."})
            if not scope:
                raise serializers.ValidationError(
                    {'exam_scope': "Deneme neti hedefi için sınav türü (TYT/AYT) gereklidir."}
                )
        elif scope or net is not None or subject is not None:
            raise serializers.ValidationError(
                {'goal_type': "Deneme alanları yalnızca 'Deneme Neti' hedefinde kullanılır."}
            )
        return attrs


# === KİTAPLIK (Book) =======================================================

class BookSerializer(serializers.ModelSerializer):
    """Öğrencinin kitaplığındaki kitap. `student` sunucuda atanır (salt-okunur).

    Türe göre farklı alanlar dolu gelir:
    - ders  → `subject` (TYT/AYT/okul dersini kapsar) + `publisher` + `book_format`
    - okuma → `title` (+ opsiyonel `author`)
    """
    student_name = serializers.SerializerMethodField()
    label = serializers.SerializerMethodField()
    subject_label = serializers.SerializerMethodField()
    topic_count = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = [
            'id', 'student', 'student_name', 'kind', 'title', 'label',
            'description', 'status',
            'subject', 'subject_label', 'publisher', 'book_format',
            'author', 'topic_count', 'created_at', 'updated_at',
        ]
        read_only_fields = ['student', 'created_at', 'updated_at']

    def get_student_name(self, obj: Book) -> str:
        return obj.student.user.get_full_name()

    def get_label(self, obj: Book) -> str:
        return obj.display_label()

    def get_subject_label(self, obj: Book) -> str | None:
        return str(obj.subject) if obj.subject_id else None

    def get_topic_count(self, obj: Book) -> int:
        return obj.book_topics.count()

    def _eff(self, attrs: dict, field: str):
        return attrs.get(field, getattr(self.instance, field, None))

    def validate(self, attrs: dict) -> dict:
        kind = self._eff(attrs, 'kind')
        subject = self._eff(attrs, 'subject')
        publisher = self._eff(attrs, 'publisher')
        book_format = self._eff(attrs, 'book_format')
        title = self._eff(attrs, 'title')
        author = self._eff(attrs, 'author')
        if kind == Book.BookKind.DERS:
            if subject is None:
                raise serializers.ValidationError(
                    {'subject': "Ders kitabı için ders seçilmelidir."}
                )
            if not book_format:
                raise serializers.ValidationError(
                    {'book_format': "Ders kitabı için format seçilmelidir."}
                )
            if author:
                raise serializers.ValidationError(
                    {'author': "Yazar yalnızca okuma kitabında kullanılır."}
                )
        else:  # okuma
            if not title:
                raise serializers.ValidationError(
                    {'title': "Okuma kitabı için kitap adı gereklidir."}
                )
            if subject is not None or publisher or book_format:
                raise serializers.ValidationError(
                    {'kind': "Ders/yayınevi/format alanları yalnızca ders kitabında kullanılır."}
                )
        return attrs


class BookTopicSerializer(serializers.ModelSerializer):
    """Bir kitabın içindeki konu + öğrencinin o kitaptaki durumu/test sayısı.

    `add_tests` (opsiyonel, write-only): `tests_solved`'ı bu kadar ARTIRIR."""
    topic_name = serializers.CharField(source='topic.name', read_only=True)
    grade = serializers.CharField(source='topic.grade', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    add_tests = serializers.IntegerField(write_only=True, required=False, min_value=0)

    class Meta:
        model = BookTopic
        fields = [
            'id', 'book', 'topic', 'topic_name', 'grade', 'status', 'status_display',
            'tests_solved', 'add_tests', 'order',
        ]
        read_only_fields = ['book', 'topic', 'order']

    def update(self, instance: BookTopic, validated_data: dict) -> BookTopic:
        add = validated_data.pop('add_tests', None)
        instance = super().update(instance, validated_data)
        if add:
            instance.tests_solved += add
            instance.save(update_fields=['tests_solved'])
        return instance


class BookDetailSerializer(BookSerializer):
    """Kitap + içindeki konular (nested, salt-okunur). Kitap detay ucunda kullanılır."""
    topics = BookTopicSerializer(source='book_topics', many=True, read_only=True)

    class Meta(BookSerializer.Meta):
        fields = BookSerializer.Meta.fields + ['topics']


# === TAKVİM (CalendarEvent) ================================================

class CalendarEventSerializer(serializers.ModelSerializer):
    """Rehberin takvim etkinliği. `student` opsiyonel — doluysa görüşme/öğrenci
    etkinliği, boşsa kişisel not."""
    student_name = serializers.SerializerMethodField()
    is_all_day = serializers.BooleanField(read_only=True)

    class Meta:
        model = CalendarEvent
        fields = [
            'id', 'counselor', 'student', 'student_name', 'title', 'description',
            'date', 'start_time', 'end_time', 'is_all_day', 'created_at', 'updated_at',
        ]
        read_only_fields = ['counselor', 'created_at', 'updated_at']

    def get_student_name(self, obj: CalendarEvent) -> str | None:
        return obj.student.user.get_full_name() if obj.student_id else None

    def validate(self, attrs: dict) -> dict:
        start = attrs.get('start_time', getattr(self.instance, 'start_time', None))
        end = attrs.get('end_time', getattr(self.instance, 'end_time', None))
        # Bitiş saati verildiyse başlangıç da olmalı ve bitiş sonra gelmeli
        if end is not None and start is None:
            raise serializers.ValidationError(
                {'start_time': "Bitiş saati için başlangıç saati de gereklidir."}
            )
        if start is not None and end is not None and end <= start:
            raise serializers.ValidationError(
                {'end_time': "Bitiş saati başlangıçtan sonra olmalıdır."}
            )
        return attrs


# === KONULAR (Topic + TopicProgress) =======================================

class TopicSerializer(serializers.ModelSerializer):
    """Konu kataloğu (ders + sınıf + konu adı). İstek yapan öğrenciyse, o öğrencinin
    bu konudaki ilerlemesi `my_progress` içinde gömülü gelir (konular sayfası tek
    çağrıda dolsun diye)."""
    subject_label = serializers.SerializerMethodField()
    grade_display = serializers.CharField(source='get_grade_display', read_only=True)
    curriculum_display = serializers.CharField(source='get_curriculum_display', read_only=True)
    my_progress = serializers.SerializerMethodField()

    class Meta:
        model = Topic
        fields = [
            'id', 'subject', 'subject_label', 'grade', 'grade_display',
            'curriculum', 'curriculum_display', 'name', 'order', 'my_progress',
        ]

    def get_subject_label(self, obj: Topic) -> str:
        return str(obj.subject)

    def get_my_progress(self, obj: Topic) -> dict | None:
        """context['progress_map'] = {topic_id: TopicProgress} — öğrenci isteğinde dolar."""
        progress_map = self.context.get('progress_map')
        if progress_map is None:
            return None
        p = progress_map.get(obj.id)
        if p is None:
            return {'id': None, 'status': TopicProgress.Status.NOT_STARTED.value, 'tests_solved': 0}
        return {'id': p.id, 'status': p.status, 'tests_solved': p.tests_solved}


class TopicProgressSerializer(serializers.ModelSerializer):
    """Öğrencinin bir konudaki durumu + çözülen test sayısı. `student` sunucuda
    atanır. POST aynı konuya tekrar gelirse mevcut kaydı GÜNCELLER (upsert).

    `add_tests` (opsiyonel, yazılır-okunmaz): verilirse `tests_solved` bu kadar
    ARTIRILIR (ör. 'kombinasyondan 5 test daha çözdüm' → add_tests=5). Mutlak değer
    set etmek için `tests_solved` gönderilir."""
    student_name = serializers.SerializerMethodField()
    topic_name = serializers.CharField(source='topic.name', read_only=True)
    subject_label = serializers.SerializerMethodField()
    grade = serializers.CharField(source='topic.grade', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    add_tests = serializers.IntegerField(write_only=True, required=False, min_value=0)

    class Meta:
        model = TopicProgress
        fields = [
            'id', 'student', 'student_name', 'topic', 'topic_name', 'subject_label',
            'grade', 'status', 'status_display', 'level', 'tests_solved', 'add_tests',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['student', 'created_at', 'updated_at']

    def get_student_name(self, obj: TopicProgress) -> str:
        return obj.student.user.get_full_name()

    def get_subject_label(self, obj: TopicProgress) -> str:
        return str(obj.topic.subject)

    def create(self, validated_data: dict) -> TopicProgress:
        add = validated_data.pop('add_tests', None)
        student = validated_data.pop('student')
        topic = validated_data.pop('topic')
        # Aynı (öğrenci, konu) varsa güncelle; yoksa oluştur
        obj, _ = TopicProgress.objects.get_or_create(student=student, topic=topic)
        if 'status' in validated_data:
            obj.status = validated_data['status']
        if 'level' in validated_data:
            obj.level = validated_data['level']
        if 'tests_solved' in validated_data:
            obj.tests_solved = validated_data['tests_solved']
        if add:
            obj.tests_solved += add
        obj.save()
        return obj

    def update(self, instance: TopicProgress, validated_data: dict) -> TopicProgress:
        add = validated_data.pop('add_tests', None)
        instance = super().update(instance, validated_data)
        if add:
            instance.tests_solved += add
            instance.save(update_fields=['tests_solved', 'updated_at'])
        return instance


# === BAŞARIMLAR (Achievement) ==============================================

class AchievementSerializer(serializers.ModelSerializer):
    """Rehberin başarım tanımı — Ayarlar'dan düzenlenebilir (C3).

    `counselor` sunucuda atanır; bir rehber başkasının başarımını göremez/yazamaz."""
    metric_display = serializers.CharField(source='get_metric_display', read_only=True)

    class Meta:
        model = Achievement
        fields = [
            'id', 'name', 'description', 'metric', 'metric_display', 'scope',
            'threshold', 'is_active', 'order',
        ]

    def validate_name(self, value: str) -> str:
        """Ad rehber içinde tekil. `counselor` serileşmediği için DRF'in kendi
        tekillik doğrulaması devreye girmiyor; olmasa IntegrityError'la 500 dönerdi."""
        counselor = self.context.get('counselor')
        if counselor is None:
            return value
        clash = Achievement.objects.filter(counselor=counselor, name=value)
        if self.instance is not None:
            clash = clash.exclude(pk=self.instance.pk)
        if clash.exists():
            raise serializers.ValidationError("Bu adda bir başarımınız zaten var.")
        return value

    def validate(self, attrs: dict) -> dict:
        def eff(field, default=None):
            if field in attrs:
                return attrs[field]
            return getattr(self.instance, field, default)

        metric = eff('metric')
        scope = eff('scope') or ''
        threshold = eff('threshold')

        # Kapsam yalnız deneme netinde anlamlı: "konuların %50'si TYT" diye bir şey yok.
        if metric == AchievementMetric.EXAM_NET:
            if not scope:
                raise serializers.ValidationError(
                    {'scope': "Deneme neti başarımında kapsam (TYT/AYT) seçilmelidir."}
                )
        elif scope:
            raise serializers.ValidationError(
                {'scope': "Kapsam yalnızca deneme neti başarımlarında kullanılır."}
            )

        if threshold is not None:
            if threshold <= 0:
                raise serializers.ValidationError({'threshold': "Eşik pozitif olmalıdır."})
            # Yüzde ölçütlerinde 100'ün üstü ulaşılamaz bir başarım olurdu.
            if metric in (AchievementMetric.TOPIC_COMPLETION,
                          AchievementMetric.COMPLIANCE) and threshold > 100:
                raise serializers.ValidationError(
                    {'threshold': "Yüzde ölçütlerinde eşik en fazla 100 olabilir."}
                )
        return attrs
