from datetime import timedelta

from django.utils import timezone
from rest_framework.test import APITestCase

from accounts.models import Counselor, Parent, Student, User
from Rehberim.models import (
    Achievement, BlockDurationDefault, BlockKind, Book, BookTopic, CalendarEvent,
    ExamResult, Goal, ProgramTemplate, Publisher, Subject, SubjectNet, Task,
    TaskType, TemplateTask, Topic, TopicProgress, WeeklyProgram,
)


def make_counselor(username: str) -> Counselor:
    user = User.objects.create_user(username=username, password="pass1234", is_counselor=True)
    return Counselor.objects.create(user=user)


def make_student(
    username: str, counselor: Counselor | None = None,
    grade: str = "12", study_field: str | None = "say",
) -> Student:
    user = User.objects.create_user(username=username, password="pass1234", is_student=True)
    return Student.objects.create(
        user=user, counselor=counselor, grade=grade, study_field=study_field,
    )


def make_parent(username: str, *students: Student) -> Parent:
    user = User.objects.create_user(username=username, password="pass1234", is_parent=True)
    parent = Parent.objects.create(user=user)
    if students:
        parent.students.set(students)
    return parent


class ProgramAndTaskAPITests(APITestCase):
    def setUp(self) -> None:
        self.counselor = make_counselor("hoca1")
        self.student = make_student("ogr1", counselor=self.counselor)
        self.other_counselor = make_counselor("hoca2")
        self.other_student = make_student("ogr2", counselor=self.other_counselor)
        self.today = timezone.localdate()
        self.subject = Subject.objects.get(name="Matematik", category=Subject.Category.TYT)
        self.fiz = Subject.objects.get(name="Fizik", category=Subject.Category.TYT)
        self.method = TaskType.objects.get(name="Konu Çalışması")

    # --- Program oluşturma / izinler ---

    def test_counselor_creates_timed_program(self) -> None:
        self.client.force_authenticate(self.counselor.user)
        resp = self.client.post("/api/programs/", {
            "student": self.student.id, "start_date": self.today.isoformat(),
            "schedule_type": "timed",
        })
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual(resp.data["schedule_type"], "timed")
        self.assertEqual(resp.data["end_date"], (self.today + timedelta(days=6)).isoformat())

    def test_counselor_creates_untimed_program(self) -> None:
        self.client.force_authenticate(self.counselor.user)
        resp = self.client.post("/api/programs/", {
            "student": self.student.id, "start_date": self.today.isoformat(),
            "schedule_type": "untimed",
        })
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual(resp.data["schedule_type"], "untimed")

    def test_counselor_cannot_create_for_other_students(self) -> None:
        self.client.force_authenticate(self.counselor.user)
        resp = self.client.post("/api/programs/", {
            "student": self.other_student.id, "start_date": self.today.isoformat(),
        })
        self.assertEqual(resp.status_code, 403, resp.content)

    def test_student_cannot_create_program(self) -> None:
        self.client.force_authenticate(self.student.user)
        resp = self.client.post("/api/programs/", {
            "student": self.student.id, "start_date": self.today.isoformat(),
        })
        self.assertEqual(resp.status_code, 403, resp.content)

    def test_student_sees_only_own_program(self) -> None:
        WeeklyProgram.objects.create(student=self.student, counselor=self.counselor, start_date=self.today)
        WeeklyProgram.objects.create(student=self.other_student, counselor=self.other_counselor, start_date=self.today)
        self.client.force_authenticate(self.student.user)
        resp = self.client.get("/api/programs/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]["student"], self.student.id)

    def test_current_program_for_student(self) -> None:
        WeeklyProgram.objects.create(student=self.student, counselor=self.counselor, start_date=self.today)
        self.client.force_authenticate(self.student.user)
        resp = self.client.get("/api/programs/current/")
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertEqual(resp.data["start_date"], self.today.isoformat())

    def test_other_student_cannot_read_program(self) -> None:
        program = WeeklyProgram.objects.create(student=self.student, counselor=self.counselor, start_date=self.today)
        self.client.force_authenticate(self.other_student.user)
        resp = self.client.get(f"/api/programs/{program.id}/")
        self.assertEqual(resp.status_code, 403, resp.content)

    # --- Yardımcılar ---

    def _program(self, schedule_type: str = "timed") -> WeeklyProgram:
        return WeeklyProgram.objects.create(
            student=self.student, counselor=self.counselor,
            start_date=self.today, schedule_type=schedule_type)

    def _timed_payload(self, **over) -> dict:
        data = {
            "subject": self.subject.id, "task_type": self.method.id,
            "title": "20 soru", "date": self.today.isoformat(),
            "start_time": "09:00", "duration_minutes": 60,
        }
        data.update(over)
        return data

    def _url(self, program) -> str:
        return f"/api/programs/{program.id}/tasks/"

    # --- Saatli görevler ---

    def test_student_adds_timed_task_and_completes(self) -> None:
        program = self._program("timed")
        self.client.force_authenticate(self.student.user)
        resp = self.client.post(self._url(program), self._timed_payload())
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual(resp.data["created_by"], self.student.user.id)
        self.assertEqual(resp.data["end_time"], "10:00:00")  # 09:00 + 60
        patch = self.client.patch(f"/api/tasks/{resp.data['id']}/", {"is_completed": True})
        self.assertEqual(patch.status_code, 200, patch.content)
        self.assertTrue(patch.data["is_completed"])

    def test_counselor_adds_task_to_own_student(self) -> None:
        program = self._program("timed")
        self.client.force_authenticate(self.counselor.user)
        resp = self.client.post(self._url(program), self._timed_payload())
        self.assertEqual(resp.status_code, 201, resp.content)

    def test_timed_task_requires_time(self) -> None:
        program = self._program("timed")
        self.client.force_authenticate(self.counselor.user)
        # saat/süre hiç gönderilmez → saatli programda zorunlu
        resp = self.client.post(self._url(program), {
            "subject": self.subject.id, "title": "20 soru",
            "date": self.today.isoformat(),
        })
        self.assertEqual(resp.status_code, 400, resp.content)
        self.assertIn("start_time", resp.data)

    def test_task_date_outside_week_rejected(self) -> None:
        program = self._program("timed")
        self.client.force_authenticate(self.counselor.user)
        resp = self.client.post(self._url(program),
                                self._timed_payload(date=(self.today + timedelta(days=10)).isoformat()))
        self.assertEqual(resp.status_code, 400, resp.content)
        self.assertIn("date", resp.data)

    def test_outsider_cannot_add_task(self) -> None:
        program = self._program("timed")
        self.client.force_authenticate(self.other_student.user)
        resp = self.client.post(self._url(program), self._timed_payload())
        self.assertEqual(resp.status_code, 403, resp.content)

    def test_overlapping_task_rejected(self) -> None:
        program = self._program("timed")
        self.client.force_authenticate(self.counselor.user)
        a = self.client.post(self._url(program), self._timed_payload(start_time="09:00", duration_minutes=60))
        self.assertEqual(a.status_code, 201, a.content)
        b = self.client.post(self._url(program), self._timed_payload(start_time="09:30", duration_minutes=60))
        self.assertEqual(b.status_code, 400, b.content)
        self.assertIn("start_time", b.data)

    def test_adjacent_tasks_allowed(self) -> None:
        program = self._program("timed")
        self.client.force_authenticate(self.counselor.user)
        a = self.client.post(self._url(program), self._timed_payload(start_time="09:00", duration_minutes=60))
        b = self.client.post(self._url(program), self._timed_payload(start_time="10:00", duration_minutes=60))
        self.assertEqual(a.status_code, 201, a.content)
        self.assertEqual(b.status_code, 201, b.content)

    def test_move_task_to_another_day(self) -> None:
        program = self._program("timed")
        self.client.force_authenticate(self.student.user)
        resp = self.client.post(self._url(program), self._timed_payload())
        task_id = resp.data["id"]
        # Salı → Çarşamba: date'i değiştir
        new_day = (self.today + timedelta(days=1)).isoformat()
        patch = self.client.patch(f"/api/tasks/{task_id}/", {"date": new_day})
        self.assertEqual(patch.status_code, 200, patch.content)
        self.assertEqual(patch.data["date"], new_day)

    # --- Saatsiz görevler ---

    def test_untimed_task_without_time_ok(self) -> None:
        program = self._program("untimed")
        self.client.force_authenticate(self.student.user)
        resp = self.client.post(self._url(program), {
            "subject": self.subject.id, "title": "Konu tekrarı",
            "date": self.today.isoformat(),
        })
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertIsNone(resp.data["end_time"])
        self.assertIsNone(resp.data["start_time"])

    def test_untimed_task_with_time_rejected(self) -> None:
        program = self._program("untimed")
        self.client.force_authenticate(self.counselor.user)
        resp = self.client.post(self._url(program), self._timed_payload())  # saat gönderir
        self.assertEqual(resp.status_code, 400, resp.content)
        self.assertIn("start_time", resp.data)

    # --- Referans veri ---

    def test_student_subjects_filtered_by_grade(self) -> None:
        self.client.force_authenticate(self.student.user)
        resp = self.client.get("/api/subjects/")
        self.assertEqual(resp.status_code, 200)
        categories = {s["category"] for s in resp.data}
        self.assertTrue(categories <= {"tyt", "ayt"})

    def test_task_types_endpoint(self) -> None:
        self.client.force_authenticate(self.counselor.user)
        resp = self.client.get("/api/task-types/")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(any(t["name"] == "Konu Çalışması" for t in resp.data))


class TaskReorderTests(APITestCase):
    """Drag & drop: görev eklenince/taşınınca gün içi `order` tutarlı kayar."""

    def setUp(self) -> None:
        self.counselor = make_counselor("rhoca1")
        self.student = make_student("rogr1", counselor=self.counselor)
        self.mon = timezone.localdate()
        self.tue = self.mon + timedelta(days=1)
        self.method = TaskType.objects.get(name="Konu Çalışması")
        self.subject = Subject.objects.get(name="Matematik", category=Subject.Category.TYT)
        self.program = WeeklyProgram.objects.create(
            student=self.student, counselor=self.counselor,
            start_date=self.mon, schedule_type="untimed")
        self.client.force_authenticate(self.student.user)

    def _add(self, title, date, **over):
        data = {"subject": self.subject.id, "task_type": self.method.id,
                "title": title, "date": date.isoformat()}
        data.update(over)
        r = self.client.post(f"/api/programs/{self.program.id}/tasks/", data, format="json")
        self.assertEqual(r.status_code, 201, r.content)
        return r.data

    def _orders(self, date):
        """O güne ait (title, order) çiftleri, order'a göre sıralı."""
        qs = Task.objects.filter(program=self.program, date=date).order_by("order")
        return [(t.title, t.order) for t in qs]

    def test_append_assigns_sequential_orders(self) -> None:
        self._add("A", self.mon)
        self._add("B", self.mon)
        self._add("C", self.mon)
        self.assertEqual(self._orders(self.mon), [("A", 0), ("B", 1), ("C", 2)])

    def test_insert_at_position_shifts_rest(self) -> None:
        self._add("A", self.mon)  # 0
        self._add("B", self.mon)  # 1
        self._add("C", self.mon)  # 2
        self._add("X", self.mon, order=1)  # araya
        self.assertEqual(self._orders(self.mon),
                         [("A", 0), ("X", 1), ("B", 2), ("C", 3)])

    def test_reorder_within_day_move_up(self) -> None:
        a = self._add("A", self.mon)  # 0
        self._add("B", self.mon)      # 1
        self._add("C", self.mon)      # 2
        # C'yi (id) başa al: aslında A'yı 2'ye taşıyoruz
        self.client.patch(f"/api/tasks/{a['id']}/", {"order": 2}, format="json")
        self.assertEqual(self._orders(self.mon),
                         [("B", 0), ("C", 1), ("A", 2)])

    def test_move_to_another_day_between_tasks(self) -> None:
        # Pazartesi: A0, B1  |  Salı: C0, D1
        self._add("A", self.mon)
        b = self._add("B", self.mon)
        self._add("C", self.tue)
        self._add("D", self.tue)
        # B'yi Salı'da 0 ile 1 arasına (pozisyon 1) taşı
        r = self.client.patch(f"/api/tasks/{b['id']}/",
                              {"date": self.tue.isoformat(), "order": 1}, format="json")
        self.assertEqual(r.status_code, 200, r.content)
        # Pazartesi'de boşluk kapandı: sadece A0
        self.assertEqual(self._orders(self.mon), [("A", 0)])
        # Salı'da B araya girdi, D kaydı
        self.assertEqual(self._orders(self.tue), [("C", 0), ("B", 1), ("D", 2)])


class ExamResultAPITests(APITestCase):
    def setUp(self) -> None:
        self.counselor = make_counselor("ehoca1")
        self.student = make_student("eogr1", counselor=self.counselor)
        self.other_counselor = make_counselor("ehoca2")
        self.other_student = make_student("eogr2", counselor=self.other_counselor)
        self.today = timezone.localdate()
        self.mat = Subject.objects.get(name="Matematik", category=Subject.Category.TYT)
        self.fiz = Subject.objects.get(name="Fizik", category=Subject.Category.TYT)

    def _payload(self, **over) -> dict:
        data = {
            "exam_type": "tyt", "name": "Deneme 1", "exam_date": self.today.isoformat(),
            "subject_nets": [
                {"subject": self.mat.id, "correct": 25, "wrong": 4},   # net 24
                {"subject": self.fiz.id, "correct": 5, "wrong": 2},    # net 4.5
            ],
        }
        data.update(over)
        return data

    def test_student_creates_exam_with_nets(self) -> None:
        self.client.force_authenticate(self.student.user)
        resp = self.client.post("/api/exams/", self._payload(), format="json")
        self.assertEqual(resp.status_code, 201, resp.content)
        # net = doğru - yanlış/4 → mat 24, fiz 4.5, toplam 28.5
        self.assertEqual(resp.data["total_net"], 28.5)
        self.assertEqual(len(resp.data["subject_nets"]), 2)
        mat_net = next(n for n in resp.data["subject_nets"] if n["subject"] == self.mat.id)
        self.assertEqual(mat_net["net"], 24)
        self.assertEqual(mat_net["blank"], 1)   # 30 - 25 - 4

    def test_counselor_cannot_create_exam(self) -> None:
        self.client.force_authenticate(self.counselor.user)
        resp = self.client.post("/api/exams/", self._payload(), format="json")
        self.assertEqual(resp.status_code, 403, resp.content)

    def test_duplicate_subject_rejected(self) -> None:
        self.client.force_authenticate(self.student.user)
        resp = self.client.post("/api/exams/", self._payload(subject_nets=[
            {"subject": self.mat.id, "correct": 20, "wrong": 0},
            {"subject": self.mat.id, "correct": 25, "wrong": 0},
        ]), format="json")
        self.assertEqual(resp.status_code, 400, resp.content)

    def test_negative_correct_rejected(self) -> None:
        self.client.force_authenticate(self.student.user)
        resp = self.client.post("/api/exams/", self._payload(subject_nets=[
            {"subject": self.mat.id, "correct": -5, "wrong": 0},
        ]), format="json")
        self.assertEqual(resp.status_code, 400, resp.content)

    def test_correct_plus_wrong_above_question_count_rejected(self) -> None:
        # TYT Matematik 30 soru → 28 doğru + 8 yanlış = 36 geçersiz.
        self.client.force_authenticate(self.student.user)
        resp = self.client.post("/api/exams/", self._payload(subject_nets=[
            {"subject": self.mat.id, "correct": 28, "wrong": 8},
        ]), format="json")
        self.assertEqual(resp.status_code, 400, resp.content)

    def test_student_sees_only_own_exams(self) -> None:
        ExamResult.objects.create(student=self.student, exam_date=self.today)
        ExamResult.objects.create(student=self.other_student, exam_date=self.today)
        self.client.force_authenticate(self.student.user)
        resp = self.client.get("/api/exams/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)

    def test_counselor_reads_but_cannot_edit(self) -> None:
        exam = ExamResult.objects.create(student=self.student, exam_date=self.today)
        self.client.force_authenticate(self.counselor.user)
        self.assertEqual(self.client.get(f"/api/exams/{exam.id}/").status_code, 200)
        patch = self.client.patch(f"/api/exams/{exam.id}/", {"name": "X"}, format="json")
        self.assertEqual(patch.status_code, 403, patch.content)

    def test_other_student_cannot_read(self) -> None:
        exam = ExamResult.objects.create(student=self.student, exam_date=self.today)
        self.client.force_authenticate(self.other_student.user)
        self.assertEqual(self.client.get(f"/api/exams/{exam.id}/").status_code, 403)


class GoalAPITests(APITestCase):
    def setUp(self) -> None:
        self.counselor = make_counselor("ghoca1")
        self.student = make_student("gogr1", counselor=self.counselor)
        self.parent = make_parent("gveli1", self.student)
        self.other_counselor = make_counselor("ghoca2")
        self.other_student = make_student("gogr2", counselor=self.other_counselor)
        self.today = timezone.localdate()

    def _net_payload(self, **over) -> dict:
        data = {"goal_type": "deneme_net", "exam_scope": "tyt", "target_net": 110,
                "target_date": self.today.isoformat()}
        data.update(over)
        return data

    def test_student_creates_net_goal(self) -> None:
        self.client.force_authenticate(self.student.user)
        resp = self.client.post("/api/goals/", self._net_payload(), format="json")
        self.assertEqual(resp.status_code, 201, resp.content)
        # student sunucuda atanır, istemciden gelmez
        self.assertEqual(resp.data["student"], self.student.id)
        self.assertEqual(resp.data["label"], "TYT Toplam 110 net")

    def test_student_creates_reading_goal(self) -> None:
        self.client.force_authenticate(self.student.user)
        resp = self.client.post("/api/goals/",
                                {"goal_type": "kitap_okuma", "title": "Suç ve Ceza"},
                                format="json")
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual(resp.data["label"], "Suç ve Ceza")

    def test_net_goal_requires_target_net(self) -> None:
        self.client.force_authenticate(self.student.user)
        resp = self.client.post("/api/goals/",
                                {"goal_type": "deneme_net", "exam_scope": "tyt"},
                                format="json")
        self.assertEqual(resp.status_code, 400, resp.content)
        self.assertIn("target_net", resp.data)

    def test_non_net_goal_rejects_net_fields(self) -> None:
        self.client.force_authenticate(self.student.user)
        resp = self.client.post("/api/goals/",
                                {"goal_type": "konu", "target_net": 20},
                                format="json")
        self.assertEqual(resp.status_code, 400, resp.content)
        self.assertIn("goal_type", resp.data)

    def test_counselor_cannot_create_goal(self) -> None:
        self.client.force_authenticate(self.counselor.user)
        resp = self.client.post("/api/goals/", self._net_payload(), format="json")
        self.assertEqual(resp.status_code, 403, resp.content)

    def test_student_sees_own_goals(self) -> None:
        Goal.objects.create(student=self.student, goal_type="kitap_okuma", title="A")
        Goal.objects.create(student=self.other_student, goal_type="kitap_okuma", title="B")
        self.client.force_authenticate(self.student.user)
        resp = self.client.get("/api/goals/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)

    def test_counselor_reads_but_cannot_edit(self) -> None:
        goal = Goal.objects.create(student=self.student, goal_type="kitap_okuma", title="A")
        self.client.force_authenticate(self.counselor.user)
        self.assertEqual(self.client.get(f"/api/goals/{goal.id}/").status_code, 200)
        patch = self.client.patch(f"/api/goals/{goal.id}/", {"is_achieved": True}, format="json")
        self.assertEqual(patch.status_code, 403, patch.content)

    def test_parent_cannot_read_child_goal(self) -> None:
        """E3 kapsam kararı (29 Ağu 2026): hedefler veli panelinin dışında."""
        goal = Goal.objects.create(student=self.student, goal_type="kitap_okuma", title="A")
        self.client.force_authenticate(self.parent.user)
        self.assertEqual(self.client.get(f"/api/goals/{goal.id}/").status_code, 403)
        self.assertEqual(self.client.get("/api/goals/").data, [])

    def test_student_marks_achieved(self) -> None:
        goal = Goal.objects.create(student=self.student, goal_type="kitap_okuma", title="A")
        self.client.force_authenticate(self.student.user)
        patch = self.client.patch(f"/api/goals/{goal.id}/", {"is_achieved": True}, format="json")
        self.assertEqual(patch.status_code, 200, patch.content)
        self.assertTrue(patch.data["is_achieved"])

    def test_other_counselor_cannot_read(self) -> None:
        goal = Goal.objects.create(student=self.student, goal_type="kitap_okuma", title="A")
        self.client.force_authenticate(self.other_counselor.user)
        self.assertEqual(self.client.get(f"/api/goals/{goal.id}/").status_code, 403)


class CalendarEventAPITests(APITestCase):
    def setUp(self) -> None:
        self.counselor = make_counselor("choca1")
        self.student = make_student("cogr1", counselor=self.counselor)
        self.parent = make_parent("cveli1", self.student)
        self.other_counselor = make_counselor("choca2")
        self.other_student = make_student("cogr2", counselor=self.other_counselor)
        self.today = timezone.localdate()

    def test_counselor_creates_meeting_with_student(self) -> None:
        self.client.force_authenticate(self.counselor.user)
        resp = self.client.post("/api/calendar/", {
            "title": "Görüşme", "student": self.student.id,
            "date": self.today.isoformat(), "start_time": "14:00", "end_time": "15:00",
        }, format="json")
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual(resp.data["counselor"], self.counselor.id)
        self.assertFalse(resp.data["is_all_day"])

    def test_counselor_creates_personal_all_day_event(self) -> None:
        self.client.force_authenticate(self.counselor.user)
        resp = self.client.post("/api/calendar/", {
            "title": "Özdebir TYT", "date": self.today.isoformat(),
        }, format="json")
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertIsNone(resp.data["student"])
        self.assertTrue(resp.data["is_all_day"])

    def test_student_cannot_create_event(self) -> None:
        self.client.force_authenticate(self.student.user)
        resp = self.client.post("/api/calendar/", {
            "title": "X", "date": self.today.isoformat(),
        }, format="json")
        self.assertEqual(resp.status_code, 403, resp.content)

    def test_end_before_start_rejected(self) -> None:
        self.client.force_authenticate(self.counselor.user)
        resp = self.client.post("/api/calendar/", {
            "title": "Görüşme", "date": self.today.isoformat(),
            "start_time": "15:00", "end_time": "14:00",
        }, format="json")
        self.assertEqual(resp.status_code, 400, resp.content)

    def test_cannot_link_other_counselors_student(self) -> None:
        self.client.force_authenticate(self.counselor.user)
        resp = self.client.post("/api/calendar/", {
            "title": "Görüşme", "student": self.other_student.id,
            "date": self.today.isoformat(),
        }, format="json")
        self.assertEqual(resp.status_code, 403, resp.content)

    def test_student_sees_own_events_only(self) -> None:
        CalendarEvent.objects.create(counselor=self.counselor, student=self.student,
                                     title="Görüşme", date=self.today)
        CalendarEvent.objects.create(counselor=self.counselor, title="Kişisel not",
                                     date=self.today)  # student bağlı değil
        self.client.force_authenticate(self.student.user)
        resp = self.client.get("/api/calendar/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)

    def test_parent_reads_child_event_but_cannot_edit(self) -> None:
        ev = CalendarEvent.objects.create(counselor=self.counselor, student=self.student,
                                          title="Görüşme", date=self.today)
        self.client.force_authenticate(self.parent.user)
        self.assertEqual(self.client.get(f"/api/calendar/{ev.id}/").status_code, 200)
        patch = self.client.patch(f"/api/calendar/{ev.id}/", {"title": "Y"}, format="json")
        self.assertEqual(patch.status_code, 403, patch.content)

    def test_counselor_filters_by_date_range(self) -> None:
        CalendarEvent.objects.create(counselor=self.counselor, title="Bugün", date=self.today)
        CalendarEvent.objects.create(counselor=self.counselor, title="Gelecek ay",
                                     date=self.today + timedelta(days=40))
        self.client.force_authenticate(self.counselor.user)
        to = (self.today + timedelta(days=7)).isoformat()
        resp = self.client.get(f"/api/calendar/?from={self.today.isoformat()}&to={to}")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)

    def test_other_student_cannot_read_event(self) -> None:
        ev = CalendarEvent.objects.create(counselor=self.counselor, student=self.student,
                                          title="Görüşme", date=self.today)
        self.client.force_authenticate(self.other_student.user)
        self.assertEqual(self.client.get(f"/api/calendar/{ev.id}/").status_code, 403)


# === YAYINEVLERİ (Publisher) ===============================================

class PublisherAPITests(APITestCase):
    def setUp(self) -> None:
        self.student = make_student("pogr1")

    def test_requires_auth(self) -> None:
        self.assertEqual(self.client.get("/api/publishers/").status_code, 401)

    def test_lists_seeded_publishers(self) -> None:
        self.client.force_authenticate(self.student.user)
        resp = self.client.get("/api/publishers/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), Publisher.objects.count())
        names = [p["name"] for p in resp.data]
        self.assertTrue(any("345" in n for n in names))


# === KİTAPLIK (Book) =======================================================

class BookAPITests(APITestCase):
    def setUp(self) -> None:
        # 12. sınıf öğrenci → 'eski' müfredat, sınav dersleri görür
        self.counselor = make_counselor("bhoca1")
        self.student = make_student("bogr1", counselor=self.counselor)
        self.parent = make_parent("bveli1", self.student)
        self.other_counselor = make_counselor("bhoca2")
        self.other_student = make_student("bogr2", counselor=self.other_counselor)
        # 10. sınıf (okul) öğrenci → 'maarif' müfredat, alan seçmez
        self.school_student = make_student("bogr10", counselor=self.counselor,
                                           grade="10", study_field=None)
        self.tyt_bio = Subject.objects.get(name="Biyoloji", category=Subject.Category.TYT)
        self.ayt_mat = Subject.objects.get(name="Matematik", category=Subject.Category.AYT)
        self.tyt_turkce = Subject.objects.get(name="Türkçe", category=Subject.Category.TYT)
        self.okul_bio = Subject.objects.get(name="Biyoloji", category=Subject.Category.SCHOOL)

    def _ders(self, **over) -> dict:
        data = {"kind": "ders", "subject": self.tyt_bio.id,
                "book_format": "soru_bankasi", "publisher": "345"}
        data.update(over)
        return data

    # --- Oluşturma + otomatik konu doldurma ---

    def test_student_creates_course_book_autofills_topics(self) -> None:
        self.client.force_authenticate(self.student.user)
        resp = self.client.post("/api/books/", self._ders(), format="json")
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual(resp.data["student"], self.student.id)  # sunucuda atanır
        # TYT → 9+10; öğrenci 12 → 'eski' müfredat
        beklenen = Topic.objects.filter(
            subject=self.okul_bio, grade__in=["9", "10"], curriculum="eski").count()
        self.assertGreater(beklenen, 0)
        self.assertEqual(resp.data["topic_count"], beklenen)

    def test_course_book_detail_lists_topics_grade9_first(self) -> None:
        self.client.force_authenticate(self.student.user)
        book_id = self.client.post("/api/books/", self._ders(), format="json").data["id"]
        resp = self.client.get(f"/api/books/{book_id}/")
        self.assertEqual(resp.status_code, 200, resp.content)
        topics = resp.data["topics"]
        self.assertTrue(len(topics) > 0)
        self.assertEqual(topics[0]["grade"], "9")  # 9. sınıf önce
        self.assertEqual({t["grade"] for t in topics}, {"9", "10"})

    def test_ayt_book_uses_grades_11_12(self) -> None:
        self.client.force_authenticate(self.student.user)
        book_id = self.client.post(
            "/api/books/", self._ders(subject=self.ayt_mat.id, book_format="konu_anlatimi"),
            format="json").data["id"]
        resp = self.client.get(f"/api/books/{book_id}/")
        self.assertEqual({t["grade"] for t in resp.data["topics"]}, {"11", "12"})

    def test_school_book_uses_student_grade(self) -> None:
        # 10. sınıf öğrenci okul dersi kitabı → kendi sınıfının (10) konuları
        self.client.force_authenticate(self.school_student.user)
        book_id = self.client.post(
            "/api/books/", self._ders(subject=self.okul_bio.id), format="json").data["id"]
        resp = self.client.get(f"/api/books/{book_id}/")
        grades = {t["grade"] for t in resp.data["topics"]}
        self.assertEqual(grades, {"10"})

    def test_tyt_turkce_maps_to_edebiyat_topics(self) -> None:
        # TYT "Türkçe" → okul "Türk Dili ve Edebiyatı" konularına eşlenir
        self.client.force_authenticate(self.student.user)
        resp = self.client.post(
            "/api/books/", self._ders(subject=self.tyt_turkce.id, book_format="paragraf"),
            format="json")
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertGreater(resp.data["topic_count"], 0)

    def test_reading_book_has_no_topics(self) -> None:
        self.client.force_authenticate(self.student.user)
        resp = self.client.post("/api/books/",
                                {"kind": "okuma", "title": "Suç ve Ceza", "author": "Dostoyevski"},
                                format="json")
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual(resp.data["topic_count"], 0)

    # --- Validasyon ---

    def test_course_book_requires_subject(self) -> None:
        self.client.force_authenticate(self.student.user)
        resp = self.client.post("/api/books/",
                                {"kind": "ders", "book_format": "deneme"}, format="json")
        self.assertEqual(resp.status_code, 400, resp.content)
        self.assertIn("subject", resp.data)

    def test_course_book_requires_format(self) -> None:
        self.client.force_authenticate(self.student.user)
        resp = self.client.post("/api/books/",
                                {"kind": "ders", "subject": self.tyt_bio.id}, format="json")
        self.assertEqual(resp.status_code, 400, resp.content)
        self.assertIn("book_format", resp.data)

    def test_reading_book_requires_title(self) -> None:
        self.client.force_authenticate(self.student.user)
        resp = self.client.post("/api/books/", {"kind": "okuma"}, format="json")
        self.assertEqual(resp.status_code, 400, resp.content)
        self.assertIn("title", resp.data)

    def test_reading_book_rejects_course_fields(self) -> None:
        self.client.force_authenticate(self.student.user)
        resp = self.client.post("/api/books/",
                                {"kind": "okuma", "title": "X", "subject": self.tyt_bio.id},
                                format="json")
        self.assertEqual(resp.status_code, 400, resp.content)

    # --- İzinler / görünürlük ---

    def test_counselor_cannot_create_book(self) -> None:
        self.client.force_authenticate(self.counselor.user)
        resp = self.client.post("/api/books/", self._ders(), format="json")
        self.assertEqual(resp.status_code, 403, resp.content)

    def test_student_sees_only_own_books(self) -> None:
        Book.objects.create(student=self.student, kind="okuma", title="A")
        Book.objects.create(student=self.other_student, kind="okuma", title="B")
        self.client.force_authenticate(self.student.user)
        resp = self.client.get("/api/books/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)

    def test_counselor_reads_but_cannot_edit(self) -> None:
        book = Book.objects.create(student=self.student, kind="okuma", title="A")
        self.client.force_authenticate(self.counselor.user)
        self.assertEqual(self.client.get(f"/api/books/{book.id}/").status_code, 200)
        patch = self.client.patch(f"/api/books/{book.id}/", {"status": "devam"}, format="json")
        self.assertEqual(patch.status_code, 403, patch.content)

    def test_parent_cannot_read_child_book(self) -> None:
        """Kullanıcı kararı (29 Ağu 2026, E3): kitaplık veliye kapalı."""
        book = Book.objects.create(student=self.student, kind="okuma", title="A")
        self.client.force_authenticate(self.parent.user)
        self.assertEqual(self.client.get(f"/api/books/{book.id}/").status_code, 403)
        self.assertEqual(self.client.get("/api/books/").data, [])

    def test_other_student_cannot_read(self) -> None:
        book = Book.objects.create(student=self.student, kind="okuma", title="A")
        self.client.force_authenticate(self.other_student.user)
        self.assertEqual(self.client.get(f"/api/books/{book.id}/").status_code, 403)


# === KİTAP İÇİ KONULAR (BookTopic) =========================================

class BookTopicAPITests(APITestCase):
    def setUp(self) -> None:
        self.counselor = make_counselor("bthoca1")
        self.student = make_student("btogr1", counselor=self.counselor)
        self.parent = make_parent("btveli1", self.student)
        self.other_student = make_student("btogr2", counselor=make_counselor("bthoca2"))
        self.tyt_bio = Subject.objects.get(name="Biyoloji", category=Subject.Category.TYT)
        # Konuları otomatik dolan bir ders kitabı oluştur
        self.client.force_authenticate(self.student.user)
        self.book_id = self.client.post("/api/books/", {
            "kind": "ders", "subject": self.tyt_bio.id, "book_format": "soru_bankasi",
        }, format="json").data["id"]
        self.bt = self.client.get(f"/api/books/{self.book_id}/").data["topics"][0]
        self.client.force_authenticate(None)

    def test_student_marks_status_and_tests(self) -> None:
        self.client.force_authenticate(self.student.user)
        resp = self.client.patch(f"/api/book-topics/{self.bt['id']}/",
                                 {"status": "devam", "tests_solved": 5}, format="json")
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertEqual(resp.data["status"], "devam")
        self.assertEqual(resp.data["tests_solved"], 5)

    def test_add_tests_increments(self) -> None:
        self.client.force_authenticate(self.student.user)
        self.client.patch(f"/api/book-topics/{self.bt['id']}/",
                          {"tests_solved": 5}, format="json")
        resp = self.client.patch(f"/api/book-topics/{self.bt['id']}/",
                                 {"add_tests": 3}, format="json")
        self.assertEqual(resp.data["tests_solved"], 8)  # 5 + 3

    def test_topic_and_book_are_readonly(self) -> None:
        self.client.force_authenticate(self.student.user)
        other_topic = Topic.objects.exclude(id=self.bt["topic"]).first()
        resp = self.client.patch(f"/api/book-topics/{self.bt['id']}/",
                                 {"topic": other_topic.id}, format="json")
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertEqual(resp.data["topic"], self.bt["topic"])  # değişmedi

    def test_counselor_reads_but_cannot_edit(self) -> None:
        self.client.force_authenticate(self.counselor.user)
        self.assertEqual(self.client.get(f"/api/book-topics/{self.bt['id']}/").status_code, 200)
        patch = self.client.patch(f"/api/book-topics/{self.bt['id']}/",
                                  {"status": "tamamlandi"}, format="json")
        self.assertEqual(patch.status_code, 403, patch.content)

    def test_parent_cannot_read_child_book_topic(self) -> None:
        """Kitaplık veliye kapalı olduğu için kitap içi konular da kapalı (E3)."""
        self.client.force_authenticate(self.parent.user)
        self.assertEqual(self.client.get(f"/api/book-topics/{self.bt['id']}/").status_code, 403)

    def test_other_student_cannot_read(self) -> None:
        self.client.force_authenticate(self.other_student.user)
        self.assertEqual(self.client.get(f"/api/book-topics/{self.bt['id']}/").status_code, 403)


# === KONULAR (Topic kataloğu + müfredat) ===================================

class TopicCatalogAPITests(APITestCase):
    def setUp(self) -> None:
        self.counselor = make_counselor("tchoca1")
        self.student12 = make_student("tcogr12", counselor=self.counselor)  # eski
        self.student10 = make_student("tcogr10", counselor=self.counselor,
                                      grade="10", study_field=None)          # maarif
        self.mat = Subject.objects.get(name="Matematik", category=Subject.Category.SCHOOL)

    def test_requires_auth(self) -> None:
        self.assertEqual(self.client.get("/api/topics/").status_code, 401)

    def test_grade10_student_gets_maarif_by_default(self) -> None:
        self.client.force_authenticate(self.student10.user)
        resp = self.client.get(f"/api/topics/?subject={self.mat.id}&grade=10")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(len(resp.data) > 0)
        self.assertEqual({t["curriculum"] for t in resp.data}, {"maarif"})

    def test_grade12_student_gets_eski_by_default(self) -> None:
        self.client.force_authenticate(self.student12.user)
        resp = self.client.get(f"/api/topics/?subject={self.mat.id}&grade=10")
        self.assertEqual({t["curriculum"] for t in resp.data}, {"eski"})

    def test_explicit_curriculum_overrides_default(self) -> None:
        self.client.force_authenticate(self.student12.user)  # normalde eski
        resp = self.client.get(f"/api/topics/?subject={self.mat.id}&grade=10&curriculum=maarif")
        self.assertEqual({t["curriculum"] for t in resp.data}, {"maarif"})

    def test_my_progress_default_when_unmarked(self) -> None:
        self.client.force_authenticate(self.student10.user)
        resp = self.client.get(f"/api/topics/?subject={self.mat.id}&grade=10")
        mp = resp.data[0]["my_progress"]
        self.assertIsNone(mp["id"])
        self.assertEqual(mp["status"], "baslanmadi")
        self.assertEqual(mp["tests_solved"], 0)

    def test_my_progress_reflects_marking(self) -> None:
        self.client.force_authenticate(self.student10.user)
        topic = Topic.objects.filter(subject=self.mat, grade="10", curriculum="maarif").first()
        self.client.post("/api/topic-progress/",
                         {"topic": topic.id, "status": "devam", "tests_solved": 4}, format="json")
        resp = self.client.get(f"/api/topics/?subject={self.mat.id}&grade=10")
        marked = next(t for t in resp.data if t["id"] == topic.id)
        self.assertEqual(marked["my_progress"]["status"], "devam")
        self.assertEqual(marked["my_progress"]["tests_solved"], 4)


class TopicProgressAPITests(APITestCase):
    def setUp(self) -> None:
        self.counselor = make_counselor("tphoca1")
        self.student = make_student("tpogr1", counselor=self.counselor)
        self.parent = make_parent("tpveli1", self.student)
        self.other_student = make_student("tpogr2", counselor=make_counselor("tphoca2"))
        mat = Subject.objects.get(name="Matematik", category=Subject.Category.SCHOOL)
        self.topic = Topic.objects.filter(subject=mat, curriculum="eski").first()

    def test_student_creates_progress(self) -> None:
        self.client.force_authenticate(self.student.user)
        resp = self.client.post("/api/topic-progress/",
                                {"topic": self.topic.id, "status": "devam", "tests_solved": 3},
                                format="json")
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual(resp.data["student"], self.student.id)  # sunucuda atanır
        self.assertEqual(resp.data["tests_solved"], 3)

    def test_repeat_post_upserts_same_record(self) -> None:
        self.client.force_authenticate(self.student.user)
        first = self.client.post("/api/topic-progress/",
                                 {"topic": self.topic.id, "tests_solved": 5}, format="json")
        second = self.client.post("/api/topic-progress/",
                                  {"topic": self.topic.id, "add_tests": 3}, format="json")
        self.assertEqual(second.data["id"], first.data["id"])  # yeni kayıt açmaz
        self.assertEqual(second.data["tests_solved"], 8)       # 5 + 3
        self.assertEqual(TopicProgress.objects.filter(student=self.student).count(), 1)

    def test_student_marks_completed(self) -> None:
        self.client.force_authenticate(self.student.user)
        pid = self.client.post("/api/topic-progress/",
                               {"topic": self.topic.id}, format="json").data["id"]
        resp = self.client.patch(f"/api/topic-progress/{pid}/",
                                 {"status": "tamamlandi"}, format="json")
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertEqual(resp.data["status"], "tamamlandi")

    def test_counselor_creates_for_own_student_not_foreign(self) -> None:
        self.client.force_authenticate(self.counselor.user)
        # Kendi öğrencisi için seviye girer (student payload'da zorunlu)
        resp = self.client.post(
            "/api/topic-progress/",
            {"student": self.student.id, "topic": self.topic.id, "level": 4}, format="json")
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual(resp.data["level"], 4)
        # Başka rehberin öğrencisi için yazamaz
        forb = self.client.post(
            "/api/topic-progress/",
            {"student": self.other_student.id, "topic": self.topic.id, "level": 3}, format="json")
        self.assertEqual(forb.status_code, 403, forb.content)

    def test_student_sees_only_own(self) -> None:
        TopicProgress.objects.create(student=self.student, topic=self.topic)
        TopicProgress.objects.create(student=self.other_student, topic=self.topic)
        self.client.force_authenticate(self.student.user)
        resp = self.client.get("/api/topic-progress/")
        self.assertEqual(len(resp.data), 1)

    def test_counselor_edits_level_parent_cannot(self) -> None:
        p = TopicProgress.objects.create(student=self.student, topic=self.topic)
        # Rehber okur ve seviyeyi düzenler
        self.client.force_authenticate(self.counselor.user)
        self.assertEqual(self.client.get(f"/api/topic-progress/{p.id}/").status_code, 200)
        patch = self.client.patch(f"/api/topic-progress/{p.id}/",
                                  {"level": 5}, format="json")
        self.assertEqual(patch.status_code, 200, patch.content)
        self.assertEqual(patch.data["level"], 5)
        # Veli yalnızca okur, düzenleyemez
        self.client.force_authenticate(self.parent.user)
        forb = self.client.patch(f"/api/topic-progress/{p.id}/",
                                 {"level": 2}, format="json")
        self.assertEqual(forb.status_code, 403, forb.content)

    def test_parent_reads_child_progress(self) -> None:
        p = TopicProgress.objects.create(student=self.student, topic=self.topic)
        self.client.force_authenticate(self.parent.user)
        self.assertEqual(self.client.get(f"/api/topic-progress/{p.id}/").status_code, 200)

    def test_other_student_cannot_read(self) -> None:
        p = TopicProgress.objects.create(student=self.student, topic=self.topic)
        self.client.force_authenticate(self.other_student.user)
        self.assertEqual(self.client.get(f"/api/topic-progress/{p.id}/").status_code, 403)

    def test_booktopic_completion_bumps_level(self) -> None:
        """Kitap konusu 'tamamlandı'ya geçince TopicProgress.level otomatik +1 (tavan 5)."""
        from Rehberim.models import Book, BookTopic
        mat = Subject.objects.get(name="Matematik", category=Subject.Category.SCHOOL)
        book = Book.objects.create(
            student=self.student, kind=Book.BookKind.DERS, subject=mat,
            book_format=Book.BookFormat.SORU_BANKASI)
        bt = BookTopic.objects.create(book=book, topic=self.topic)
        # Başlangıçta kayıt yok (kavramsal seviye 1)
        self.assertFalse(
            TopicProgress.objects.filter(student=self.student, topic=self.topic).exists())
        bt.status = BookTopic.Status.COMPLETED
        bt.save()
        tp = TopicProgress.objects.get(student=self.student, topic=self.topic)
        self.assertEqual(tp.level, 2)   # 1 → 2
        bt.save()                       # tekrar completed → çift artış yok
        tp.refresh_from_db()
        self.assertEqual(tp.level, 2)


class ProgramTemplateAPITests(APITestCase):
    def setUp(self) -> None:
        self.counselor = make_counselor("thoca1")
        self.student = make_student("togr1", counselor=self.counselor)
        self.other_counselor = make_counselor("thoca2")
        self.other_student = make_student("togr2", counselor=self.other_counselor)
        self.today = timezone.localdate()
        self.mat = Subject.objects.get(name="Matematik", category=Subject.Category.TYT)
        self.fiz = Subject.objects.get(name="Fizik", category=Subject.Category.TYT)
        self.method = TaskType.objects.get(name="Konu Çalışması")

    def _tpl_payload(self, **over) -> dict:
        data = {
            "name": "Sayısal 1", "schedule_type": "timed",
            "tasks": [
                {"subject": self.mat.id, "task_type": self.method.id, "title": "Mat",
                 "weekday": 0, "start_time": "09:00", "duration_minutes": 60, "order": 0},
                {"subject": self.fiz.id, "task_type": self.method.id, "title": "Fizik",
                 "weekday": 2, "start_time": "10:00", "duration_minutes": 60, "order": 0},
            ],
        }
        data.update(over)
        return data

    def test_counselor_creates_template(self) -> None:
        self.client.force_authenticate(self.counselor.user)
        resp = self.client.post("/api/program-templates/", self._tpl_payload(), format="json")
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual(len(resp.data["tasks"]), 2)
        self.assertEqual(ProgramTemplate.objects.get().counselor, self.counselor)

    def test_student_post_becomes_own_routine_not_general_template(self) -> None:
        """Öğrenci de kayıt oluşturabilir ama bu her zaman KENDİ rutinidir —
        rehberin genel şablon havuzuna kayıt ekleyemez."""
        self.client.force_authenticate(self.student.user)
        resp = self.client.post("/api/program-templates/", self._tpl_payload(), format="json")
        self.assertEqual(resp.status_code, 201, resp.content)
        created = ProgramTemplate.objects.get(pk=resp.data["id"])
        self.assertEqual(created.student_id, self.student.id)   # kendine bağlandı
        self.assertFalse(
            ProgramTemplate.objects.filter(student__isnull=True).exists(),
            "Öğrenci genel şablon oluşturamamalı",
        )

    def test_list_returns_only_own_templates(self) -> None:
        ProgramTemplate.objects.create(counselor=self.other_counselor, name="Başkası")
        self.client.force_authenticate(self.counselor.user)
        self.client.post("/api/program-templates/", self._tpl_payload(), format="json")
        resp = self.client.get("/api/program-templates/")
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]["name"], "Sayısal 1")

    def _make_template(self) -> ProgramTemplate:
        tpl = ProgramTemplate.objects.create(counselor=self.counselor, name="T1", schedule_type="timed")
        TemplateTask.objects.create(template=tpl, subject=self.mat, task_type=self.method,
                                    weekday=0, start_time="09:00", duration_minutes=60)
        TemplateTask.objects.create(template=tpl, subject=self.fiz, task_type=self.method,
                                    weekday=2, start_time="10:00", duration_minutes=60)
        return tpl

    def test_assign_template_to_next_free_week(self) -> None:
        tpl = self._make_template()
        self.client.force_authenticate(self.counselor.user)
        resp = self.client.post("/api/programs/assign/",
                                {"student": self.student.id, "template": tpl.id}, format="json")
        self.assertEqual(resp.status_code, 201, resp.content)
        # program yoksa hedef = bugün; görevler weekday'e göre haftaya yerleşir
        self.assertEqual(resp.data["start_date"], self.today.isoformat())
        self.assertEqual(len(resp.data["tasks"]), 2)
        for t in resp.data["tasks"]:
            wd = 0 if t["subject"] == self.mat.id else 2
            from datetime import date as _d
            y, m, d = map(int, t["date"].split("-"))
            self.assertEqual(_d(y, m, d).weekday(), wd)

    def test_assign_shifts_when_week_occupied(self) -> None:
        tpl = self._make_template()
        WeeklyProgram.objects.create(student=self.student, counselor=self.counselor,
                                     start_date=self.today, schedule_type="timed")
        self.client.force_authenticate(self.counselor.user)
        resp = self.client.post("/api/programs/assign/",
                                {"student": self.student.id, "template": tpl.id}, format="json")
        self.assertEqual(resp.status_code, 201, resp.content)
        # bugün dolu → sıradaki hafta (bugün + 7)
        self.assertEqual(resp.data["start_date"], (self.today + timedelta(days=7)).isoformat())

    def test_assign_explicit_start_date(self) -> None:
        tpl = self._make_template()
        target = self.today + timedelta(days=14)
        self.client.force_authenticate(self.counselor.user)
        resp = self.client.post("/api/programs/assign/",
                                {"student": self.student.id, "template": tpl.id,
                                 "start_date": target.isoformat()}, format="json")
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual(resp.data["start_date"], target.isoformat())

    def test_assign_from_tasks_without_template(self) -> None:
        self.client.force_authenticate(self.counselor.user)
        resp = self.client.post("/api/programs/assign/", {
            "student": self.student.id,
            "tasks": [{"subject": self.mat.id, "task_type": self.method.id,
                       "weekday": 1, "start_time": "11:00", "duration_minutes": 60}],
        }, format="json")
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual(len(resp.data["tasks"]), 1)

    def test_cannot_assign_to_other_students(self) -> None:
        tpl = self._make_template()
        self.client.force_authenticate(self.counselor.user)
        resp = self.client.post("/api/programs/assign/",
                                {"student": self.other_student.id, "template": tpl.id}, format="json")
        self.assertEqual(resp.status_code, 403, resp.content)

    def test_cannot_assign_other_counselors_template(self) -> None:
        tpl = ProgramTemplate.objects.create(counselor=self.other_counselor, name="Başka")
        self.client.force_authenticate(self.counselor.user)
        resp = self.client.post("/api/programs/assign/",
                                {"student": self.student.id, "template": tpl.id}, format="json")
        self.assertEqual(resp.status_code, 403, resp.content)


class RoutineAPITests(APITestCase):
    """Rutin = öğrenciye bağlanmış + auto_apply açık ProgramTemplate.

    Yeni hafta açıldığında görevler kendiliğinden materyalize olur; öğrenci
    uygulaması bunları /programs/ üzerinden zaten okuduğu için ayrı uç yok."""

    def setUp(self) -> None:
        self.counselor = make_counselor("rhoca1")
        self.student = make_student("rogr1", counselor=self.counselor)
        self.other_counselor = make_counselor("rhoca2")
        self.other_student = make_student("rogr2", counselor=self.other_counselor)
        self.today = timezone.localdate()
        self.mat = Subject.objects.get(name="Matematik", category=Subject.Category.TYT)
        self.method = TaskType.objects.get(name="Konu Çalışması")

    def _routine_payload(self, **over) -> dict:
        data = {
            "name": "Hafta rutini", "schedule_type": "timed",
            "student": self.student.id, "auto_apply": True,
            "tasks": [
                {"subject": self.mat.id, "task_type": self.method.id, "title": "Mat tekrar",
                 "weekday": 0, "start_time": "09:00", "duration_minutes": 60, "order": 0},
                {"subject": self.mat.id, "task_type": self.method.id, "title": "Mat soru",
                 "weekday": 3, "start_time": "09:00", "duration_minutes": 60, "order": 0},
            ],
        }
        data.update(over)
        return data

    def _make_routine(self, **over):
        self.client.force_authenticate(self.counselor.user)
        resp = self.client.post("/api/program-templates/", self._routine_payload(**over),
                                format="json")
        self.assertEqual(resp.status_code, 201, resp.content)
        return ProgramTemplate.objects.get(pk=resp.data["id"])

    # --- Rutin tanımlama ---------------------------------------------------

    def test_counselor_creates_routine(self) -> None:
        routine = self._make_routine()
        self.assertEqual(routine.student_id, self.student.id)
        self.assertTrue(routine.auto_apply)
        self.assertEqual(routine.tasks.count(), 2)

    def test_auto_apply_without_student_rejected(self) -> None:
        self.client.force_authenticate(self.counselor.user)
        resp = self.client.post(
            "/api/program-templates/",
            self._routine_payload(student=None, auto_apply=True), format="json")
        self.assertEqual(resp.status_code, 400, resp.content)
        self.assertIn("student", resp.data)

    def test_routine_for_other_counselors_student_rejected(self) -> None:
        self.client.force_authenticate(self.counselor.user)
        resp = self.client.post(
            "/api/program-templates/",
            self._routine_payload(student=self.other_student.id), format="json")
        self.assertEqual(resp.status_code, 400, resp.content)
        self.assertIn("student", resp.data)

    def test_second_auto_routine_for_same_student_rejected(self) -> None:
        self._make_routine()
        self.client.force_authenticate(self.counselor.user)
        resp = self.client.post(
            "/api/program-templates/",
            self._routine_payload(name="İkinci rutin"), format="json")
        self.assertEqual(resp.status_code, 400, resp.content)
        self.assertIn("auto_apply", resp.data)

    def test_plain_template_still_allowed_without_student(self) -> None:
        """Genel şablon (öğrencisiz, auto_apply kapalı) davranışı bozulmamalı."""
        self.client.force_authenticate(self.counselor.user)
        resp = self.client.post(
            "/api/program-templates/",
            self._routine_payload(student=None, auto_apply=False), format="json")
        self.assertEqual(resp.status_code, 201, resp.content)

    # --- Yeni haftaya uygulanması ------------------------------------------

    def test_routine_materializes_on_new_program(self) -> None:
        self._make_routine()
        self.client.force_authenticate(self.counselor.user)
        resp = self.client.post("/api/programs/", {
            "student": self.student.id, "start_date": self.today.isoformat(),
            "schedule_type": "timed",
        }, format="json")
        self.assertEqual(resp.status_code, 201, resp.content)
        program = WeeklyProgram.objects.get(pk=resp.data["id"])
        self.assertEqual(program.tasks.count(), 2)
        titles = set(program.tasks.values_list("title", flat=True))
        self.assertEqual(titles, {"Mat tekrar", "Mat soru"})

    def test_weekday_maps_into_program_window(self) -> None:
        self._make_routine()
        monday = self.today - timedelta(days=self.today.weekday())
        self.client.force_authenticate(self.counselor.user)
        resp = self.client.post("/api/programs/", {
            "student": self.student.id, "start_date": monday.isoformat(),
            "schedule_type": "timed",
        }, format="json")
        self.assertEqual(resp.status_code, 201, resp.content)
        program = WeeklyProgram.objects.get(pk=resp.data["id"])
        by_title = {t.title: t.date for t in program.tasks.all()}
        self.assertEqual(by_title["Mat tekrar"], monday)                    # weekday 0
        self.assertEqual(by_title["Mat soru"], monday + timedelta(days=3))  # weekday 3
        for date in by_title.values():
            self.assertTrue(program.start_date <= date <= program.end_date)

    def test_no_routine_means_empty_program(self) -> None:
        self.client.force_authenticate(self.counselor.user)
        resp = self.client.post("/api/programs/", {
            "student": self.student.id, "start_date": self.today.isoformat(),
            "schedule_type": "timed",
        }, format="json")
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual(WeeklyProgram.objects.get(pk=resp.data["id"]).tasks.count(), 0)

    def test_disabled_routine_does_not_apply(self) -> None:
        routine = self._make_routine()
        self.client.force_authenticate(self.counselor.user)
        patch = self.client.patch(f"/api/program-templates/{routine.pk}/",
                                  {"auto_apply": False}, format="json")
        self.assertEqual(patch.status_code, 200, patch.content)
        resp = self.client.post("/api/programs/", {
            "student": self.student.id, "start_date": self.today.isoformat(),
            "schedule_type": "timed",
        }, format="json")
        self.assertEqual(WeeklyProgram.objects.get(pk=resp.data["id"]).tasks.count(), 0)

    def test_routine_of_other_student_not_applied(self) -> None:
        self._make_routine()
        self.client.force_authenticate(self.other_counselor.user)
        resp = self.client.post("/api/programs/", {
            "student": self.other_student.id, "start_date": self.today.isoformat(),
            "schedule_type": "timed",
        }, format="json")
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual(WeeklyProgram.objects.get(pk=resp.data["id"]).tasks.count(), 0)

    # --- Geçmiş korunur -----------------------------------------------------

    def test_editing_routine_does_not_touch_existing_weeks(self) -> None:
        routine = self._make_routine()
        self.client.force_authenticate(self.counselor.user)
        first = self.client.post("/api/programs/", {
            "student": self.student.id, "start_date": self.today.isoformat(),
            "schedule_type": "timed",
        }, format="json")
        program = WeeklyProgram.objects.get(pk=first.data["id"])
        self.assertEqual(program.tasks.count(), 2)

        # Rutini tek göreve indir
        patch = self.client.patch(f"/api/program-templates/{routine.pk}/", {
            "tasks": [{"subject": self.mat.id, "task_type": self.method.id,
                       "title": "Yalnız bu", "weekday": 1, "start_time": "11:00",
                       "duration_minutes": 45, "order": 0}],
        }, format="json")
        self.assertEqual(patch.status_code, 200, patch.content)

        program.refresh_from_db()
        self.assertEqual(program.tasks.count(), 2)          # geçmiş hafta dokunulmadı
        titles = set(program.tasks.values_list("title", flat=True))
        self.assertEqual(titles, {"Mat tekrar", "Mat soru"})

    def test_assign_does_not_double_apply_routine(self) -> None:
        """Açıkça şablon atanırken rutin ayrıca uygulanmamalı (çift yazma olurdu)."""
        self._make_routine()
        tpl = ProgramTemplate.objects.create(counselor=self.counselor, name="Elle şablon")
        TemplateTask.objects.create(template=tpl, subject=self.mat, task_type=self.method,
                                    title="Elle", weekday=4, start_time="14:00",
                                    duration_minutes=30, order=0)
        self.client.force_authenticate(self.counselor.user)
        resp = self.client.post("/api/programs/assign/",
                                {"student": self.student.id, "template": tpl.id},
                                format="json")
        self.assertEqual(resp.status_code, 201, resp.content)
        program = WeeklyProgram.objects.get(pk=resp.data["id"])
        self.assertEqual(program.tasks.count(), 1)
        self.assertEqual(program.tasks.first().title, "Elle")

    # --- Öğrenci tarafı -----------------------------------------------------

    def test_student_sees_routine_tasks_in_program(self) -> None:
        """Mobil tarafta ek uç yok: rutin görevleri /programs/ içinde geliyor."""
        self._make_routine()
        self.client.force_authenticate(self.counselor.user)
        self.client.post("/api/programs/", {
            "student": self.student.id, "start_date": self.today.isoformat(),
            "schedule_type": "timed",
        }, format="json")

        self.client.force_authenticate(self.student.user)
        resp = self.client.get("/api/programs/")
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(len(resp.data[0]["tasks"]), 2)


    def test_student_can_delete_own_routine_task_for_that_week(self) -> None:
        """Karar: öğrenci o haftaki görevi silebilir; rutin bozulmaz."""
        routine = self._make_routine()
        self.client.force_authenticate(self.counselor.user)
        created = self.client.post("/api/programs/", {
            "student": self.student.id, "start_date": self.today.isoformat(),
            "schedule_type": "timed",
        }, format="json")
        program = WeeklyProgram.objects.get(pk=created.data["id"])
        task = program.tasks.first()

        self.client.force_authenticate(self.student.user)
        resp = self.client.delete(f"/api/tasks/{task.pk}/")
        self.assertEqual(resp.status_code, 204, resp.content)
        self.assertEqual(program.tasks.count(), 1)
        routine.refresh_from_db()
        self.assertEqual(routine.tasks.count(), 2)       # rutin olduğu gibi duruyor


class StudentRoutineAPITests(APITestCase):
    """Öğrenci kendi rutinini kurabilir; rehberi bunu görür."""

    def setUp(self) -> None:
        self.counselor = make_counselor("srhoca1")
        self.student = make_student("srogr1", counselor=self.counselor)
        self.peer = make_student("srogr2", counselor=self.counselor)
        self.today = timezone.localdate()
        self.mat = Subject.objects.get(name="Matematik", category=Subject.Category.TYT)
        self.method = TaskType.objects.get(name="Konu Çalışması")

    def _payload(self, **over) -> dict:
        data = {
            "name": "Kendi rutinim", "schedule_type": "timed", "auto_apply": True,
            "tasks": [
                {"subject": self.mat.id, "task_type": self.method.id, "title": "Sabah matematik",
                 "weekday": 0, "start_time": "08:00", "duration_minutes": 60, "order": 0},
            ],
        }
        data.update(over)
        return data

    def test_student_creates_own_routine(self) -> None:
        self.client.force_authenticate(self.student.user)
        resp = self.client.post("/api/program-templates/", self._payload(), format="json")
        self.assertEqual(resp.status_code, 201, resp.content)
        routine = ProgramTemplate.objects.get(pk=resp.data["id"])
        self.assertEqual(routine.student_id, self.student.id)
        self.assertTrue(routine.auto_apply)
        # Rehberine de bağlanır ki rehber görebilsin
        self.assertEqual(routine.counselor_id, self.counselor.id)

    def test_student_cannot_create_routine_for_peer(self) -> None:
        self.client.force_authenticate(self.student.user)
        resp = self.client.post("/api/program-templates/",
                                self._payload(student=self.peer.id), format="json")
        self.assertEqual(resp.status_code, 400, resp.content)
        self.assertIn("student", resp.data)

    def test_student_lists_only_own_routines(self) -> None:
        self.client.force_authenticate(self.student.user)
        self.client.post("/api/program-templates/", self._payload(), format="json")
        # Rehberin genel şablonu öğrenciye görünmemeli
        ProgramTemplate.objects.create(counselor=self.counselor, name="Rehber şablonu")
        resp = self.client.get("/api/program-templates/")
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]["name"], "Kendi rutinim")

    def test_student_cannot_see_peers_routine(self) -> None:
        ProgramTemplate.objects.create(
            counselor=self.counselor, student=self.peer, name="Arkadaşın rutini",
            auto_apply=True)
        self.client.force_authenticate(self.student.user)
        resp = self.client.get("/api/program-templates/")
        self.assertEqual(len(resp.data), 0)

    def test_counselor_sees_student_created_routine(self) -> None:
        self.client.force_authenticate(self.student.user)
        self.client.post("/api/program-templates/", self._payload(), format="json")
        self.client.force_authenticate(self.counselor.user)
        resp = self.client.get("/api/program-templates/")
        self.assertEqual(resp.status_code, 200, resp.content)
        names = {t["name"]: t["student_name"] for t in resp.data}
        self.assertIn("Kendi rutinim", names)
        self.assertEqual(names["Kendi rutinim"], self.student.user.get_full_name())

    def test_student_routine_applies_on_new_week(self) -> None:
        self.client.force_authenticate(self.student.user)
        self.client.post("/api/program-templates/", self._payload(), format="json")
        # Haftayı rehber açar
        self.client.force_authenticate(self.counselor.user)
        resp = self.client.post("/api/programs/", {
            "student": self.student.id, "start_date": self.today.isoformat(),
            "schedule_type": "timed",
        }, format="json")
        self.assertEqual(resp.status_code, 201, resp.content)
        program = WeeklyProgram.objects.get(pk=resp.data["id"])
        self.assertEqual(program.tasks.count(), 1)
        self.assertEqual(program.tasks.first().title, "Sabah matematik")

    def test_student_edits_and_deletes_own_routine(self) -> None:
        self.client.force_authenticate(self.student.user)
        created = self.client.post("/api/program-templates/", self._payload(), format="json")
        rid = created.data["id"]
        patch = self.client.patch(f"/api/program-templates/{rid}/",
                                  {"name": "Yeni ad"}, format="json")
        self.assertEqual(patch.status_code, 200, patch.content)
        self.assertEqual(self.client.delete(f"/api/program-templates/{rid}/").status_code, 204)
        self.assertFalse(ProgramTemplate.objects.filter(pk=rid).exists())

    def test_student_cannot_edit_peers_routine(self) -> None:
        peer_routine = ProgramTemplate.objects.create(
            counselor=self.counselor, student=self.peer, name="Arkadaşın rutini")
        self.client.force_authenticate(self.student.user)
        resp = self.client.patch(f"/api/program-templates/{peer_routine.pk}/",
                                 {"name": "Ele geçirdim"}, format="json")
        self.assertEqual(resp.status_code, 404, resp.content)

    def test_second_auto_routine_rejected_for_student_too(self) -> None:
        self.client.force_authenticate(self.student.user)
        self.client.post("/api/program-templates/", self._payload(), format="json")
        resp = self.client.post("/api/program-templates/",
                                self._payload(name="İkincisi"), format="json")
        self.assertEqual(resp.status_code, 400, resp.content)
        self.assertIn("auto_apply", resp.data)

    def test_counselor_and_student_routines_can_share_a_name(self) -> None:
        """Aynı rehberin iki öğrencisi rutinine aynı adı verebilmeli."""
        ProgramTemplate.objects.create(
            counselor=self.counselor, student=self.peer, name="Kendi rutinim")
        self.client.force_authenticate(self.student.user)
        resp = self.client.post("/api/program-templates/", self._payload(), format="json")
        self.assertEqual(resp.status_code, 201, resp.content)

    def test_duplicate_name_for_same_student_rejected(self) -> None:
        self.client.force_authenticate(self.student.user)
        self.client.post("/api/program-templates/", self._payload(), format="json")
        resp = self.client.post("/api/program-templates/",
                                self._payload(auto_apply=False), format="json")
        self.assertEqual(resp.status_code, 400, resp.content)
        self.assertIn("name", resp.data)

    def test_parent_cannot_touch_routines(self) -> None:
        parent_user = User.objects.create_user("srveli", password="x", is_parent=True)
        self.client.force_authenticate(parent_user)
        self.assertEqual(self.client.get("/api/program-templates/").status_code, 403)


class AchievementTests(APITestCase):
    """C3 — başarımlar: varsayılan set, rehberin düzenleyebilmesi, öğrenci durumu."""

    def setUp(self) -> None:
        self.counselor = make_counselor("basarihoca")
        self.other_counselor = make_counselor("basarihoca2")
        self.student = make_student("basariogr", counselor=self.counselor)
        self.parent = make_parent("basariveli", self.student)
        self.today = timezone.localdate()
        self.tyt_mat = Subject.objects.get(name="Matematik", category=Subject.Category.TYT)
        self.method = TaskType.objects.get(name="Konu Çalışması")

    # --- Varsayılanlar -------------------------------------------------------

    def test_new_counselor_gets_defaults(self) -> None:
        """Rehber kaydolunca varsayılan set kendisine kopyalanır."""
        fresh = make_counselor("yenihoca")
        self.assertEqual(fresh.achievements.count(), len(Achievement.DEFAULTS))
        names = set(fresh.achievements.values_list('name', flat=True))
        self.assertIn("TYT 60 Net", names)
        self.assertIn("TYT 110 Net", names)
        self.assertIn("Tam Uyum", names)

    def test_defaults_are_per_counselor_copies(self) -> None:
        """Bir rehberin sildiği başarım diğerini etkilemez."""
        self.counselor.achievements.filter(name="TYT 60 Net").delete()
        self.assertEqual(self.counselor.achievements.filter(name="TYT 60 Net").count(), 0)
        self.assertEqual(self.other_counselor.achievements.filter(name="TYT 60 Net").count(), 1)

    def test_seeding_does_not_rerun_on_save(self) -> None:
        """Silinen bir varsayılan, rehber kaydı güncellenince geri gelmemeli."""
        self.counselor.achievements.filter(name="TYT 60 Net").delete()
        self.counselor.save()
        self.assertEqual(self.counselor.achievements.filter(name="TYT 60 Net").count(), 0)

    # --- Rehberin düzenlemesi (Ayarlar) -------------------------------------

    def test_counselor_lists_only_own(self) -> None:
        self.client.force_authenticate(self.counselor.user)
        resp = self.client.get("/api/achievements/")
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertEqual(len(resp.data), len(Achievement.DEFAULTS))

    def test_counselor_can_add_custom(self) -> None:
        self.client.force_authenticate(self.counselor.user)
        resp = self.client.post("/api/achievements/", {
            "name": "AYT 40 Net", "metric": "exam_net", "scope": "ayt", "threshold": 40,
        }, format="json")
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual(
            Achievement.objects.get(pk=resp.data["id"]).counselor_id, self.counselor.id)

    def test_counselor_can_change_threshold(self) -> None:
        target = self.counselor.achievements.get(name="TYT 60 Net")
        self.client.force_authenticate(self.counselor.user)
        resp = self.client.patch(f"/api/achievements/{target.id}/", {"threshold": 70},
                                 format="json")
        self.assertEqual(resp.status_code, 200, resp.content)
        target.refresh_from_db()
        self.assertEqual(target.threshold, 70)

    def test_counselor_can_delete(self) -> None:
        target = self.counselor.achievements.first()
        self.client.force_authenticate(self.counselor.user)
        self.assertEqual(self.client.delete(f"/api/achievements/{target.id}/").status_code, 204)

    def test_cannot_touch_another_counselors_achievement(self) -> None:
        target = self.other_counselor.achievements.first()
        self.client.force_authenticate(self.counselor.user)
        self.assertEqual(self.client.get(f"/api/achievements/{target.id}/").status_code, 404)
        self.assertEqual(
            self.client.patch(f"/api/achievements/{target.id}/", {"threshold": 5},
                              format="json").status_code, 404)

    def test_student_cannot_manage_definitions(self) -> None:
        self.client.force_authenticate(self.student.user)
        self.assertEqual(self.client.get("/api/achievements/").status_code, 403)

    def test_duplicate_name_rejected(self) -> None:
        self.client.force_authenticate(self.counselor.user)
        resp = self.client.post("/api/achievements/", {
            "name": "TYT 60 Net", "metric": "exam_net", "scope": "tyt", "threshold": 60,
        }, format="json")
        self.assertEqual(resp.status_code, 400, resp.content)

    def test_exam_net_requires_scope(self) -> None:
        self.client.force_authenticate(self.counselor.user)
        resp = self.client.post("/api/achievements/", {
            "name": "Net eşiği", "metric": "exam_net", "threshold": 50,
        }, format="json")
        self.assertEqual(resp.status_code, 400, resp.content)
        self.assertIn("scope", resp.data)

    def test_percent_metric_rejects_scope_and_over_100(self) -> None:
        self.client.force_authenticate(self.counselor.user)
        with_scope = self.client.post("/api/achievements/", {
            "name": "Konu TYT", "metric": "topic_completion", "scope": "tyt", "threshold": 50,
        }, format="json")
        self.assertEqual(with_scope.status_code, 400, with_scope.content)
        too_big = self.client.post("/api/achievements/", {
            "name": "Konu 120", "metric": "topic_completion", "threshold": 120,
        }, format="json")
        self.assertEqual(too_big.status_code, 400, too_big.content)
        self.assertIn("threshold", too_big.data)

    # --- Öğrencinin durumu ---------------------------------------------------

    def _exam(self, exam_type: str, correct: int) -> ExamResult:
        exam = ExamResult.objects.create(
            student=self.student, exam_type=exam_type, exam_date=self.today)
        SubjectNet.objects.create(exam_result=exam, subject=self.tyt_mat,
                                  correct=correct, wrong=0)
        return exam

    def _progress(self, student=None):
        sid = (student or self.student).id
        return self.client.get(f"/api/achievements/progress/?student={sid}")

    def test_net_achievement_earned(self) -> None:
        self._exam("tyt", 85)
        self.client.force_authenticate(self.counselor.user)
        data = self._progress().data
        by_name = {a["name"]: a for a in data["achievements"]}
        self.assertTrue(by_name["TYT 60 Net"]["earned"])
        self.assertTrue(by_name["TYT 80 Net"]["earned"])
        self.assertFalse(by_name["TYT 90 Net"]["earned"])
        self.assertEqual(data["facts"]["exam_net_tyt"], 85)

    def test_best_exam_counts_not_latest(self) -> None:
        """Başarım 'bir kez ulaştı' demektir; sonraki kötü deneme geri almaz."""
        self._exam("tyt", 95)
        later = self._exam("tyt", 30)
        later.exam_date = self.today
        later.save()
        self.client.force_authenticate(self.counselor.user)
        by_name = {a["name"]: a for a in self._progress().data["achievements"]}
        self.assertTrue(by_name["TYT 90 Net"]["earned"])

    def test_ayt_exam_does_not_satisfy_tyt_threshold(self) -> None:
        self._exam("ayt", 100)
        self.client.force_authenticate(self.counselor.user)
        by_name = {a["name"]: a for a in self._progress().data["achievements"]}
        self.assertFalse(by_name["TYT 60 Net"]["earned"])

    def test_progress_percent_towards_threshold(self) -> None:
        self._exam("tyt", 40)
        self.client.force_authenticate(self.counselor.user)
        by_name = {a["name"]: a for a in self._progress().data["achievements"]}
        self.assertEqual(by_name["TYT 80 Net"]["progress"], 50)
        self.assertFalse(by_name["TYT 80 Net"]["earned"])

    def test_compliance_achievement_uses_approved_only(self) -> None:
        approved = WeeklyProgram.objects.create(
            student=self.student, counselor=self.counselor,
            start_date=self.today - timedelta(days=30), day_count=7)
        Task.objects.create(program=approved, subject=self.tyt_mat, task_type=self.method,
                            title="Konu", date=approved.start_date, start_time="09:00",
                            duration_minutes=120, is_completed=True)
        approved.approve(self.counselor)
        sloppy = WeeklyProgram.objects.create(
            student=self.student, counselor=self.counselor,
            start_date=self.today - timedelta(days=60), day_count=7)
        Task.objects.create(program=sloppy, subject=self.tyt_mat, task_type=self.method,
                            title="Konu", date=sloppy.start_date, start_time="09:00",
                            duration_minutes=600, is_completed=False)
        self.client.force_authenticate(self.counselor.user)
        data = self._progress().data
        self.assertEqual(data["facts"]["compliance"], 100.0)
        by_name = {a["name"]: a for a in data["achievements"]}
        self.assertTrue(by_name["Tam Uyum"]["earned"])

    def test_topic_completion_counts_level_five(self) -> None:
        topics = list(Topic.objects.filter(
            subject=self.tyt_mat, curriculum=self.student.curriculum)[:4])
        self.assertGreaterEqual(len(topics), 4, "seed'de yeterli konu yok")
        TopicProgress.objects.create(student=self.student, topic=topics[0], level=5)
        TopicProgress.objects.create(student=self.student, topic=topics[1], level=3)
        self.client.force_authenticate(self.counselor.user)
        facts = self._progress().data["facts"]
        self.assertEqual(facts["topics_done"], 1)
        self.assertGreater(facts["topics_total"], 1)
        self.assertEqual(
            facts["topic_completion"],
            round(1 / facts["topics_total"] * 100, 1))

    def test_inactive_achievement_hidden_from_progress(self) -> None:
        self.counselor.achievements.filter(name="TYT 60 Net").update(is_active=False)
        self.client.force_authenticate(self.counselor.user)
        names = [a["name"] for a in self._progress().data["achievements"]]
        self.assertNotIn("TYT 60 Net", names)

    def test_earned_listed_first(self) -> None:
        self._exam("tyt", 85)
        self.client.force_authenticate(self.counselor.user)
        rows = self._progress().data["achievements"]
        earned_flags = [r["earned"] for r in rows]
        self.assertEqual(earned_flags, sorted(earned_flags, reverse=True))

    def test_student_reads_own_progress_without_param(self) -> None:
        self._exam("tyt", 65)
        self.client.force_authenticate(self.student.user)
        resp = self.client.get("/api/achievements/progress/")
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertEqual(resp.data["earned_count"], 1)

    def test_parent_can_read(self) -> None:
        self.client.force_authenticate(self.parent.user)
        self.assertEqual(self._progress().status_code, 200)

    def test_other_counselor_gets_404(self) -> None:
        self.client.force_authenticate(self.other_counselor.user)
        self.assertEqual(self._progress().status_code, 404)

    def test_student_without_counselor_gets_empty_list(self) -> None:
        lone = make_student("yalnizogr")
        self.client.force_authenticate(lone.user)
        resp = self.client.get("/api/achievements/progress/")
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertEqual(resp.data["achievements"], [])
        self.assertEqual(resp.data["total_count"], 0)

    def test_counselors_edit_changes_what_student_sees(self) -> None:
        """Ayarlar'dan eşik değişince öğrencinin durumu da değişir."""
        self._exam("tyt", 70)
        self.client.force_authenticate(self.counselor.user)
        by_name = {a["name"]: a for a in self._progress().data["achievements"]}
        self.assertFalse(by_name["TYT 80 Net"]["earned"])
        target = self.counselor.achievements.get(name="TYT 80 Net")
        self.client.patch(f"/api/achievements/{target.id}/", {"threshold": 65}, format="json")
        by_name = {a["name"]: a for a in self._progress().data["achievements"]}
        self.assertTrue(by_name["TYT 80 Net"]["earned"])


class ExamSourceTests(APITestCase):
    """E1 — deneme kişisel mi kurumsal mı."""

    def setUp(self) -> None:
        self.counselor = make_counselor("kaynakhoca")
        self.student = make_student("kaynakogr", counselor=self.counselor)
        self.subject = Subject.objects.get(name="Matematik", category=Subject.Category.TYT)
        self.today = timezone.localdate()

    def _post(self, **over):
        data = {"exam_type": "tyt", "name": "Deneme", "exam_date": self.today.isoformat(),
                "subject_nets": [{"subject": self.subject.id, "correct": 20, "wrong": 4}]}
        data.update(over)
        self.client.force_authenticate(self.student.user)
        return self.client.post("/api/exams/", data, format="json")

    def test_defaults_to_personal(self) -> None:
        resp = self._post()
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual(resp.data["source"], "personal")
        self.assertFalse(ExamResult.objects.get(pk=resp.data["id"]).is_institutional)

    def test_institutional_can_be_set(self) -> None:
        resp = self._post(source="institutional")
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual(resp.data["source"], "institutional")
        self.assertTrue(ExamResult.objects.get(pk=resp.data["id"]).is_institutional)

    def test_invalid_source_rejected(self) -> None:
        self.assertEqual(self._post(source="okulda").status_code, 400)

    def test_source_filter(self) -> None:
        self._post()
        self._post(source="institutional", exam_date=(self.today - timedelta(days=1)).isoformat())
        self.client.force_authenticate(self.counselor.user)
        base = f"/api/exams/?student={self.student.id}"
        self.assertEqual(len(self.client.get(base).data), 2)
        self.assertEqual(len(self.client.get(f"{base}&source=personal").data), 1)
        self.assertEqual(len(self.client.get(f"{base}&source=institutional").data), 1)

    def test_unknown_filter_value_is_ignored(self) -> None:
        """Bilinmeyen süzgeç sessizce yok sayılır, boş liste döndürmez."""
        self._post()
        self.client.force_authenticate(self.counselor.user)
        resp = self.client.get(f"/api/exams/?student={self.student.id}&source=zzz")
        self.assertEqual(len(resp.data), 1)

    def test_source_can_be_corrected_later(self) -> None:
        exam_id = self._post().data["id"]
        resp = self.client.patch(f"/api/exams/{exam_id}/", {"source": "institutional"},
                                 format="json")
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertEqual(resp.data["source"], "institutional")


class StudyStatsTests(APITestCase):
    """E2 — öğrencinin tamamladığı çalışmanın saat ve dağılım özeti."""

    def setUp(self) -> None:
        self.counselor = make_counselor("istathoca")
        self.other_counselor = make_counselor("istathoca2")
        self.student = make_student("istatogr", counselor=self.counselor)
        self.parent = make_parent("istatveli", self.student)
        self.today = timezone.localdate()
        self.tyt_mat = Subject.objects.get(name="Matematik", category=Subject.Category.TYT)
        self.tyt_turkce = Subject.objects.get(name="Türkçe", category=Subject.Category.TYT)
        self.ayt_mat = Subject.objects.get(name="Matematik", category=Subject.Category.AYT)
        self.method = TaskType.objects.get(name="Konu Çalışması")

    def _program(self, days_ago: int, approved: bool = False) -> WeeklyProgram:
        p = WeeklyProgram.objects.create(
            student=self.student, counselor=self.counselor,
            start_date=self.today - timedelta(days=days_ago), day_count=7,
        )
        if approved:
            p.approve(self.counselor)
        return p

    def _task(self, program, subject, minutes, *, completed=True, hour=9,
              kind=BlockKind.STUDY, day=0):
        return Task.objects.create(
            program=program, subject=subject,
            task_type=None if kind == BlockKind.EXTERNAL else self.method,
            kind=kind, title="Antrenman" if kind == BlockKind.EXTERNAL else "Konu",
            date=program.start_date + timedelta(days=day),
            start_time=f"{hour:02d}:00", duration_minutes=minutes, is_completed=completed,
        )

    def _get(self, **params):
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return self.client.get(f"/api/study-stats/{'?' + query if query else ''}")

    def test_only_completed_work_counts(self) -> None:
        p = self._program(30)
        self._task(p, self.tyt_mat, 120)
        self._task(p, self.tyt_mat, 60, completed=False, hour=13)
        self.client.force_authenticate(self.student.user)
        data = self._get().data
        self.assertEqual(data["total_minutes"], 120)
        self.assertEqual(data["total_hours"], 2.0)

    def test_external_blocks_excluded(self) -> None:
        p = self._program(30)
        self._task(p, self.tyt_mat, 60)
        self._task(p, None, 180, hour=18, kind=BlockKind.EXTERNAL)
        self.client.force_authenticate(self.student.user)
        self.assertEqual(self._get().data["total_minutes"], 60)

    def test_category_split_tyt_vs_ayt(self) -> None:
        p = self._program(30)
        self._task(p, self.tyt_mat, 180)
        self._task(p, self.ayt_mat, 60, hour=13)
        self.client.force_authenticate(self.student.user)
        cats = {c["category"]: c for c in self._get().data["by_category"]}
        self.assertEqual(cats["tyt"]["minutes"], 180)
        self.assertEqual(cats["tyt"]["percent"], 75.0)
        self.assertEqual(cats["ayt"]["percent"], 25.0)

    def test_general_exam_block_counts_under_its_scope(self) -> None:
        """Ders seçilmemiş genel TYT denemesi 'tyt' kovasına düşer."""
        p = self._program(30)
        Task.objects.create(program=p, kind=BlockKind.EXAM, exam_scope='tyt',
                            title="Genel TYT", date=p.start_date,
                            start_time="09:00", duration_minutes=150, is_completed=True)
        self.client.force_authenticate(self.student.user)
        cats = {c["category"]: c for c in self._get().data["by_category"]}
        self.assertEqual(cats["tyt"]["minutes"], 150)

    def test_subject_breakdown_sorted_desc(self) -> None:
        p = self._program(30)
        self._task(p, self.tyt_turkce, 60)
        self._task(p, self.tyt_mat, 240, hour=13)
        self.client.force_authenticate(self.student.user)
        rows = self._get().data["by_subject"]
        self.assertEqual([r["subject"] for r in rows], [self.tyt_mat.id, self.tyt_turkce.id])
        self.assertEqual(rows[0]["subject_label"], "TYT Matematik")
        self.assertEqual(rows[0]["percent"], 80.0)

    def test_date_range_filter(self) -> None:
        old = self._program(90)
        recent = self._program(10)
        self._task(old, self.tyt_mat, 300)
        self._task(recent, self.tyt_mat, 60)
        self.client.force_authenticate(self.student.user)
        cutoff = (self.today - timedelta(days=30)).isoformat()
        self.assertEqual(self._get(**{"from": cutoff}).data["total_minutes"], 60)

    def test_untimed_tasks_do_not_break_totals(self) -> None:
        p = WeeklyProgram.objects.create(
            student=self.student, counselor=self.counselor,
            start_date=self.today - timedelta(days=30), day_count=7,
            schedule_type="untimed",
        )
        Task.objects.create(program=p, subject=self.tyt_mat, task_type=self.method,
                            title="Konu", date=p.start_date, is_completed=True)
        self.client.force_authenticate(self.student.user)
        data = self._get().data
        self.assertEqual(data["total_minutes"], 0)
        self.assertEqual(data["by_category"], [])

    def test_no_work_yields_zeros(self) -> None:
        self.client.force_authenticate(self.student.user)
        data = self._get().data
        self.assertEqual(data["total_minutes"], 0)
        self.assertEqual(data["by_subject"], [])

    # --- Yetki ---------------------------------------------------------------

    def test_counselor_needs_student_param(self) -> None:
        self.client.force_authenticate(self.counselor.user)
        self.assertEqual(self._get().status_code, 400)

    def test_counselor_reads_own_student(self) -> None:
        p = self._program(30)
        self._task(p, self.tyt_mat, 90)
        self.client.force_authenticate(self.counselor.user)
        self.assertEqual(self._get(student=self.student.id).data["total_minutes"], 90)

    def test_other_counselor_gets_404(self) -> None:
        self.client.force_authenticate(self.other_counselor.user)
        self.assertEqual(self._get(student=self.student.id).status_code, 404)

    def test_student_cannot_read_another_student(self) -> None:
        other = make_student("istatogr2", counselor=self.counselor)
        self.client.force_authenticate(self.student.user)
        self.assertEqual(self._get(student=other.id).data["student"], self.student.id)

    def test_parent_sees_only_approved_programs(self) -> None:
        approved = self._program(60, approved=True)
        self._task(approved, self.tyt_mat, 120)
        unapproved = self._program(30)
        self._task(unapproved, self.tyt_mat, 300)
        self.client.force_authenticate(self.parent.user)
        resp = self._get(student=self.student.id)
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertEqual(resp.data["total_minutes"], 120)

    def test_stranger_parent_gets_404(self) -> None:
        self.client.force_authenticate(make_parent("istatyabanci").user)
        self.assertEqual(self._get(student=self.student.id).status_code, 404)


class ComplianceTests(APITestCase):
    """B2 — uyum yüzdesi **süre** üzerinden; dönemsel özet yalnız onaylı haftalardan."""

    def setUp(self) -> None:
        self.counselor = make_counselor("uyumhoca")
        self.other_counselor = make_counselor("uyumhoca2")
        self.student = make_student("uyumogr", counselor=self.counselor)
        self.parent = make_parent("uyumveli", self.student)
        self.today = timezone.localdate()
        self.subject = Subject.objects.get(name="Matematik", category=Subject.Category.TYT)
        self.method = TaskType.objects.get(name="Konu Çalışması")

    def _program(self, *, days_ago: int, day_count: int = 7, approved: bool = False,
                 schedule_type: str = "timed") -> WeeklyProgram:
        p = WeeklyProgram.objects.create(
            student=self.student, counselor=self.counselor,
            start_date=self.today - timedelta(days=days_ago), day_count=day_count,
            schedule_type=schedule_type,
        )
        if approved:
            p.approve(self.counselor)
        return p

    def _task(self, program, minutes, *, completed=False, kind=BlockKind.STUDY,
              hour=9, title="20 soru"):
        return Task.objects.create(
            program=program,
            subject=None if kind == BlockKind.EXTERNAL else self.subject,
            task_type=None if kind == BlockKind.EXTERNAL else self.method,
            kind=kind, title=title, date=program.start_date,
            start_time=f"{hour:02d}:00", duration_minutes=minutes,
            is_completed=completed,
        )

    def _url(self) -> str:
        return f"/api/programs/compliance/?student={self.student.id}"

    # --- Süre üzerinden hesap ------------------------------------------------

    def test_percent_uses_duration_not_task_count(self) -> None:
        """3 görevden 1'i bitti ama o 1'i sürenin çoğu: sayıya göre %33, süreye göre %75."""
        p = self._program(days_ago=30)
        self._task(p, 180, completed=True, hour=9)
        self._task(p, 30, hour=13)
        self._task(p, 30, hour=15)
        c = p.compliance()
        self.assertEqual(c["basis"], "duration")
        self.assertEqual(c["percent"], 75)
        self.assertEqual(c["completed_minutes"], 180)
        self.assertEqual(c["total_minutes"], 240)

    def test_external_blocks_excluded_from_both_sides(self) -> None:
        """Okul/antrenman çalışma değildir: ne paya ne paydaya girer."""
        p = self._program(days_ago=30)
        self._task(p, 60, completed=True, hour=9)
        self._task(p, 180, kind=BlockKind.EXTERNAL, hour=13, title="Okul")
        c = p.compliance()
        self.assertEqual(c["total_minutes"], 60)
        self.assertEqual(c["percent"], 100)

    def test_exam_blocks_are_counted(self) -> None:
        """Deneme çalışmadır — B3'ün haftalık saat hesabıyla aynı küme."""
        p = self._program(days_ago=30)
        self._task(p, 60, completed=True, hour=9)
        self._task(p, 60, kind=BlockKind.EXAM, hour=13)
        self.assertEqual(p.compliance()["total_minutes"], 120)
        self.assertEqual(p.compliance()["percent"], 50)

    def test_untimed_program_falls_back_to_task_count(self) -> None:
        p = self._program(days_ago=30, schedule_type="untimed")
        for i, done in enumerate([True, False, False, False]):
            Task.objects.create(program=p, subject=self.subject, task_type=self.method,
                                title=f"g{i}", date=p.start_date, is_completed=done)
        c = p.compliance()
        self.assertEqual(c["basis"], "count")
        self.assertEqual(c["percent"], 25)

    def test_empty_program_has_no_percent(self) -> None:
        c = self._program(days_ago=30).compliance()
        self.assertEqual(c["basis"], "empty")
        self.assertIsNone(c["percent"])

    def test_weekly_hours_normalizes_short_window(self) -> None:
        """4 günlük programda 8 saat = haftalık 14 saat hızında."""
        p = self._program(days_ago=30, day_count=4)
        self._task(p, 480, hour=9)
        self.assertEqual(p.compliance()["study_hours"], 8.0)
        self.assertEqual(p.compliance()["weekly_hours"], 14.0)

    def test_compliance_in_program_payload(self) -> None:
        p = self._program(days_ago=30)
        self._task(p, 60, completed=True)
        self.client.force_authenticate(self.counselor.user)
        resp = self.client.get(f"/api/programs/{p.id}/")
        self.assertEqual(resp.data["compliance"]["percent"], 100)

    # --- Dönemsel özet ucu ---------------------------------------------------

    def test_series_only_contains_finished_programs(self) -> None:
        finished = self._program(days_ago=30)
        self._task(finished, 60, completed=True)
        running = self._program(days_ago=0, day_count=7)
        self._task(running, 60)
        self.client.force_authenticate(self.counselor.user)
        resp = self.client.get(self._url())
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertEqual([r["id"] for r in resp.data["programs"]], [finished.id])

    def test_series_is_chronological(self) -> None:
        old = self._program(days_ago=60)
        new = self._program(days_ago=20)
        self.client.force_authenticate(self.counselor.user)
        ids = [r["id"] for r in self.client.get(self._url()).data["programs"]]
        self.assertEqual(ids, [old.id, new.id])

    def test_aggregates_use_only_approved_programs(self) -> None:
        good = self._program(days_ago=60, approved=True)
        self._task(good, 100, completed=True)
        sloppy = self._program(days_ago=30)          # onaysız, hepsi boş
        self._task(sloppy, 100)
        self.client.force_authenticate(self.counselor.user)
        data = self.client.get(self._url()).data
        self.assertEqual(data["overall"]["percent"], 100)      # onaysız hafta kirletmedi
        self.assertEqual(data["overall"]["program_count"], 1)
        self.assertEqual(data["pending_approval"], 1)
        self.assertEqual(len(data["programs"]), 2)             # seride ikisi de var

    def test_overall_is_minute_weighted_not_average_of_percents(self) -> None:
        """%100'lük 1 saatlik hafta + %0'lık 9 saatlik hafta = %10, %50 değil."""
        a = self._program(days_ago=60, approved=True)
        self._task(a, 60, completed=True)
        b = self._program(days_ago=30, approved=True)
        self._task(b, 540)
        self.client.force_authenticate(self.counselor.user)
        self.assertEqual(self.client.get(self._url()).data["overall"]["percent"], 10)

    def test_months_grouped_by_start_date(self) -> None:
        a = self._program(days_ago=90, approved=True)
        self._task(a, 60, completed=True)
        b = self._program(days_ago=20, approved=True)
        self._task(b, 60)
        self.client.force_authenticate(self.counselor.user)
        months = self.client.get(self._url()).data["months"]
        self.assertEqual(len(months), 2)
        self.assertEqual(months[0]["month"], (self.today - timedelta(days=90)).strftime("%Y-%m"))
        self.assertEqual(months[0]["percent"], 100)
        self.assertEqual(months[1]["percent"], 0)
        self.assertLess(months[0]["month"], months[1]["month"])

    def test_no_programs_yields_null_percent(self) -> None:
        self.client.force_authenticate(self.counselor.user)
        data = self.client.get(self._url()).data
        self.assertEqual(data["programs"], [])
        self.assertIsNone(data["overall"]["percent"])

    # --- Yetki ---------------------------------------------------------------

    def test_counselor_must_name_a_student(self) -> None:
        self.client.force_authenticate(self.counselor.user)
        self.assertEqual(self.client.get("/api/programs/compliance/").status_code, 400)

    def test_other_counselor_cannot_read(self) -> None:
        self.client.force_authenticate(self.other_counselor.user)
        self.assertEqual(self.client.get(self._url()).status_code, 404)

    def test_student_reads_own_without_query_param(self) -> None:
        p = self._program(days_ago=30)
        self._task(p, 60, completed=True)
        self.client.force_authenticate(self.student.user)
        resp = self.client.get("/api/programs/compliance/")
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertEqual(resp.data["student"], self.student.id)

    def test_student_cannot_read_another_student(self) -> None:
        other = make_student("uyumogr2", counselor=self.counselor)
        self.client.force_authenticate(self.student.user)
        resp = self.client.get(f"/api/programs/compliance/?student={other.id}")
        self.assertEqual(resp.data["student"], self.student.id)   # kendi verisi döner

    def test_parent_sees_only_approved_programs_in_series(self) -> None:
        approved = self._program(days_ago=60, approved=True)
        self._task(approved, 60, completed=True)
        unapproved = self._program(days_ago=30)
        self._task(unapproved, 60)
        self.client.force_authenticate(self.parent.user)
        resp = self.client.get(self._url())
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertEqual([r["id"] for r in resp.data["programs"]], [approved.id])

    def test_stranger_parent_gets_404(self) -> None:
        self.client.force_authenticate(make_parent("yabanci2").user)
        self.assertEqual(self.client.get(self._url()).status_code, 404)


class WeeklyApprovalTests(APITestCase):
    """B1 — haftalık onay akışı: kim onaylar, ne zaman, sonrasında ne değişir."""

    def setUp(self) -> None:
        self.counselor = make_counselor("onayhoca")
        self.other_counselor = make_counselor("onayhoca2")
        self.student = make_student("onayogr", counselor=self.counselor)
        self.parent = make_parent("onayveli", self.student)
        self.today = timezone.localdate()
        self.subject = Subject.objects.get(name="Matematik", category=Subject.Category.TYT)
        self.method = TaskType.objects.get(name="Konu Çalışması")

    def _finished_program(self, day_count: int = 7) -> WeeklyProgram:
        """Penceresi dün kapanmış bir program (onaylanabilir durumda)."""
        start = self.today - timedelta(days=day_count)
        return WeeklyProgram.objects.create(
            student=self.student, counselor=self.counselor,
            start_date=start, day_count=day_count,
        )

    def _running_program(self) -> WeeklyProgram:
        return WeeklyProgram.objects.create(
            student=self.student, counselor=self.counselor,
            start_date=self.today, day_count=7,
        )

    def _task(self, program: WeeklyProgram, day_offset: int = 0) -> Task:
        return Task.objects.create(
            program=program, subject=self.subject, task_type=self.method,
            title="20 soru", date=program.start_date + timedelta(days=day_offset),
            start_time="09:00", duration_minutes=60,
        )

    def _url(self, program: WeeklyProgram) -> str:
        return f"/api/programs/{program.id}/approve/"

    # --- Onaylama -----------------------------------------------------------

    def test_counselor_approves_finished_program(self) -> None:
        program = self._finished_program()
        self.client.force_authenticate(self.counselor.user)
        resp = self.client.post(self._url(program))
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertTrue(resp.data["is_approved"])
        self.assertEqual(resp.data["approved_by"], self.counselor.id)
        program.refresh_from_db()
        self.assertIsNotNone(program.approved_at)

    def test_cannot_approve_before_window_ends(self) -> None:
        program = self._running_program()
        self.client.force_authenticate(self.counselor.user)
        resp = self.client.post(self._url(program))
        self.assertEqual(resp.status_code, 400, resp.content)
        program.refresh_from_db()
        self.assertFalse(program.is_approved)

    def test_program_ending_today_not_yet_approvable(self) -> None:
        """Son gün henüz bitmemiştir; onay yarından itibaren verilebilir."""
        program = WeeklyProgram.objects.create(
            student=self.student, counselor=self.counselor,
            start_date=self.today - timedelta(days=6), day_count=7,
        )
        self.assertEqual(program.end_date, self.today)
        self.client.force_authenticate(self.counselor.user)
        self.assertEqual(self.client.post(self._url(program)).status_code, 400)

    def test_other_counselor_cannot_approve(self) -> None:
        program = self._finished_program()
        self.client.force_authenticate(self.other_counselor.user)
        self.assertEqual(self.client.post(self._url(program)).status_code, 403)

    def test_student_cannot_approve_own_program(self) -> None:
        program = self._finished_program()
        self.client.force_authenticate(self.student.user)
        self.assertEqual(self.client.post(self._url(program)).status_code, 403)

    def test_approving_twice_is_idempotent(self) -> None:
        program = self._finished_program()
        self.client.force_authenticate(self.counselor.user)
        first = self.client.post(self._url(program))
        second = self.client.post(self._url(program))
        self.assertEqual(second.status_code, 200, second.content)
        self.assertEqual(first.data["approved_at"], second.data["approved_at"])

    def test_approval_can_be_revoked(self) -> None:
        program = self._finished_program()
        self.client.force_authenticate(self.counselor.user)
        self.client.post(self._url(program))
        resp = self.client.delete(self._url(program))
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertFalse(resp.data["is_approved"])
        program.refresh_from_db()
        self.assertIsNone(program.approved_by)

    # --- Veli görünürlüğü ---------------------------------------------------

    def test_parent_does_not_see_unapproved_program(self) -> None:
        program = self._finished_program()
        self.client.force_authenticate(self.parent.user)
        listing = self.client.get("/api/programs/")
        self.assertEqual(listing.status_code, 200, listing.content)
        self.assertEqual(listing.data, [])
        self.assertEqual(self.client.get(f"/api/programs/{program.id}/").status_code, 403)

    def test_parent_sees_program_after_approval(self) -> None:
        program = self._finished_program()
        program.approve(self.counselor)
        self.client.force_authenticate(self.parent.user)
        listing = self.client.get("/api/programs/")
        self.assertEqual([p["id"] for p in listing.data], [program.id])
        self.assertEqual(self.client.get(f"/api/programs/{program.id}/").status_code, 200)

    def test_parent_of_another_student_sees_nothing(self) -> None:
        program = self._finished_program()
        program.approve(self.counselor)
        stranger = make_parent("yabanciveli")
        self.client.force_authenticate(stranger.user)
        self.assertEqual(self.client.get("/api/programs/").data, [])
        self.assertEqual(self.client.get(f"/api/programs/{program.id}/").status_code, 403)

    def test_parent_cannot_write_to_approved_program(self) -> None:
        program = self._finished_program()
        task = self._task(program)
        program.approve(self.counselor)
        self.client.force_authenticate(self.parent.user)
        self.assertEqual(
            self.client.patch(f"/api/tasks/{task.id}/", {"is_completed": True},
                              format="json").status_code, 403)

    # --- Onay sonrası kilit -------------------------------------------------

    def test_student_can_complete_task_before_approval(self) -> None:
        program = self._finished_program()
        task = self._task(program)
        self.client.force_authenticate(self.student.user)
        resp = self.client.patch(f"/api/tasks/{task.id}/", {"is_completed": True},
                                 format="json")
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_student_cannot_change_task_after_approval(self) -> None:
        program = self._finished_program()
        task = self._task(program)
        program.approve(self.counselor)
        self.client.force_authenticate(self.student.user)
        resp = self.client.patch(f"/api/tasks/{task.id}/", {"is_completed": True},
                                 format="json")
        self.assertEqual(resp.status_code, 403, resp.content)
        task.refresh_from_db()
        self.assertFalse(task.is_completed)
        self.assertEqual(self.client.delete(f"/api/tasks/{task.id}/").status_code, 403)
        self.assertEqual(self.client.post(f"/api/programs/{program.id}/tasks/", {
            "subject": self.subject.id, "task_type": self.method.id, "title": "yeni",
            "date": program.start_date.isoformat(), "start_time": "14:00",
            "duration_minutes": 30,
        }).status_code, 403)

    def test_student_still_reads_approved_program(self) -> None:
        program = self._finished_program()
        self._task(program)
        program.approve(self.counselor)
        self.client.force_authenticate(self.student.user)
        resp = self.client.get(f"/api/programs/{program.id}/")
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertTrue(resp.data["is_approved"])

    def test_counselor_can_still_edit_after_approval(self) -> None:
        """Onay rehberin beyanı; yanlış bir işareti sonradan düzeltebilmeli."""
        program = self._finished_program()
        task = self._task(program)
        task.is_completed = True
        task.save(update_fields=['is_completed'])
        program.approve(self.counselor)
        self.client.force_authenticate(self.counselor.user)
        resp = self.client.patch(f"/api/tasks/{task.id}/", {"is_completed": False},
                                 format="json")
        self.assertEqual(resp.status_code, 200, resp.content)
        task.refresh_from_db()
        self.assertFalse(task.is_completed)

    def test_student_can_complete_task_again_after_revocation(self) -> None:
        program = self._finished_program()
        task = self._task(program)
        program.approve(self.counselor)
        program.revoke_approval()
        self.client.force_authenticate(self.student.user)
        self.assertEqual(
            self.client.patch(f"/api/tasks/{task.id}/", {"is_completed": True},
                              format="json").status_code, 200)

    # --- Serileşme ----------------------------------------------------------

    def test_approval_fields_are_read_only_on_patch(self) -> None:
        program = self._finished_program()
        self.client.force_authenticate(self.counselor.user)
        resp = self.client.patch(f"/api/programs/{program.id}/",
                                 {"approved_at": timezone.now().isoformat()},
                                 format="json")
        self.assertEqual(resp.status_code, 200, resp.content)
        program.refresh_from_db()
        self.assertFalse(program.is_approved)

    def test_is_finished_flag_in_payload(self) -> None:
        running = self._running_program()
        self.client.force_authenticate(self.counselor.user)
        resp = self.client.get(f"/api/programs/{running.id}/")
        self.assertFalse(resp.data["is_finished"])
        self.assertFalse(resp.data["is_approved"])
        self.assertIsNone(resp.data["approved_by_name"])


class FlexibleProgramWindowTests(APITestCase):
    """A1 — program penceresi esnek: başlangıç + gün sayısı seçilebilir, pencereler
    örtüşemez."""

    def setUp(self) -> None:
        self.counselor = make_counselor("esnekhoca")
        self.student = make_student("esnekogr", counselor=self.counselor)
        self.today = timezone.localdate()
        self.subject = Subject.objects.get(name="Matematik", category=Subject.Category.TYT)
        self.method = TaskType.objects.get(name="Konu Çalışması")
        self.client.force_authenticate(self.counselor.user)

    def _post_program(self, **over) -> "object":
        data = {"student": self.student.id, "start_date": self.today.isoformat(),
                "schedule_type": "timed"}
        data.update(over)
        return self.client.post("/api/programs/", data, format="json")

    # --- Gün sayısı ---------------------------------------------------------

    def test_default_window_is_seven_days(self) -> None:
        resp = self._post_program()
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual(resp.data["day_count"], 7)
        self.assertEqual(resp.data["end_date"], (self.today + timedelta(days=6)).isoformat())

    def test_five_day_program(self) -> None:
        resp = self._post_program(day_count=5)
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual(resp.data["day_count"], 5)
        self.assertEqual(resp.data["end_date"], (self.today + timedelta(days=4)).isoformat())

    def test_day_count_must_be_positive(self) -> None:
        self.assertEqual(self._post_program(day_count=0).status_code, 400)

    def test_past_start_date_allowed(self) -> None:
        """Yol haritası kabul kriteri: bugün Salı ise dünden (Pzt) başlayan 5 günlük
        program atanabilmeli."""
        monday = self.today - timedelta(days=1)
        resp = self._post_program(start_date=monday.isoformat(), day_count=5)
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual(resp.data["end_date"], (monday + timedelta(days=4)).isoformat())

    # --- Örtüşme ------------------------------------------------------------

    def test_overlapping_program_rejected(self) -> None:
        self.assertEqual(self._post_program().status_code, 201)          # today..today+6
        resp = self._post_program(start_date=(self.today + timedelta(days=3)).isoformat())
        self.assertEqual(resp.status_code, 400, resp.content)
        self.assertIn("start_date", resp.data)

    def test_program_enclosing_existing_one_rejected(self) -> None:
        self._post_program(start_date=(self.today + timedelta(days=2)).isoformat(), day_count=2)
        resp = self._post_program(start_date=self.today.isoformat(), day_count=10)
        self.assertEqual(resp.status_code, 400, resp.content)

    def test_back_to_back_programs_allowed(self) -> None:
        first = self._post_program(day_count=5)
        self.assertEqual(first.status_code, 201, first.content)
        second = self._post_program(start_date=(self.today + timedelta(days=5)).isoformat(),
                                    day_count=2)
        self.assertEqual(second.status_code, 201, second.content)

    def test_other_students_program_does_not_block(self) -> None:
        other = make_student("esnekogr2", counselor=self.counselor)
        self._post_program()
        resp = self.client.post("/api/programs/", {
            "student": other.id, "start_date": self.today.isoformat(),
        }, format="json")
        self.assertEqual(resp.status_code, 201, resp.content)

    def test_patch_extending_into_next_program_rejected(self) -> None:
        first = self._post_program(day_count=5)
        self._post_program(start_date=(self.today + timedelta(days=5)).isoformat(), day_count=3)
        patch = self.client.patch(f"/api/programs/{first.data['id']}/",
                                  {"day_count": 7}, format="json")
        self.assertEqual(patch.status_code, 400, patch.content)

    def test_patch_shrinking_own_window_allowed(self) -> None:
        first = self._post_program(day_count=7)
        patch = self.client.patch(f"/api/programs/{first.data['id']}/",
                                  {"day_count": 3}, format="json")
        self.assertEqual(patch.status_code, 200, patch.content)
        self.assertEqual(patch.data["end_date"], (self.today + timedelta(days=2)).isoformat())

    def _add_task(self, program_id: int, day_offset: int, hour: str = "09:00"):
        return self.client.post(f"/api/programs/{program_id}/tasks/", {
            "subject": self.subject.id, "task_type": self.method.id, "title": "20 soru",
            "date": (self.today + timedelta(days=day_offset)).isoformat(),
            "start_time": hour, "duration_minutes": 60,
        })

    def test_patch_shrinking_window_over_existing_task_rejected(self) -> None:
        """Pencere daraltmak, dışarıda kalacak görev varsa reddedilir — yoksa görev
        hiçbir programa düşmeden öksüz kalıyordu."""
        program = self._post_program(day_count=7)
        pid = program.data["id"]
        self.assertEqual(self._add_task(pid, 4).status_code, 201)
        patch = self.client.patch(f"/api/programs/{pid}/", {"day_count": 4}, format="json")
        self.assertEqual(patch.status_code, 400, patch.content)
        self.assertIn("day_count", patch.data)
        program_obj = WeeklyProgram.objects.get(pk=pid)
        self.assertEqual(program_obj.day_count, 7)

    def test_patch_shrinking_window_keeping_all_tasks_allowed(self) -> None:
        program = self._post_program(day_count=7)
        pid = program.data["id"]
        self.assertEqual(self._add_task(pid, 2).status_code, 201)
        patch = self.client.patch(f"/api/programs/{pid}/", {"day_count": 3}, format="json")
        self.assertEqual(patch.status_code, 200, patch.content)

    def test_patch_sliding_start_date_over_existing_task_rejected(self) -> None:
        """Aynı kural başlangıcı ileri kaydırmak için de geçerli."""
        program = self._post_program(day_count=7)
        pid = program.data["id"]
        self.assertEqual(self._add_task(pid, 0).status_code, 201)
        patch = self.client.patch(
            f"/api/programs/{pid}/",
            {"start_date": (self.today + timedelta(days=2)).isoformat()}, format="json")
        self.assertEqual(patch.status_code, 400, patch.content)
        self.assertIn("day_count", patch.data)

    # --- Görev doğrulaması pencereye göre -----------------------------------

    def test_task_outside_short_window_rejected(self) -> None:
        program = self._post_program(day_count=5)
        url = f"/api/programs/{program.data['id']}/tasks/"
        payload = {"subject": self.subject.id, "task_type": self.method.id,
                   "title": "20 soru", "start_time": "09:00", "duration_minutes": 60}
        inside = self.client.post(url, {**payload,
                                        "date": (self.today + timedelta(days=4)).isoformat()})
        self.assertEqual(inside.status_code, 201, inside.content)
        outside = self.client.post(url, {**payload,
                                         "date": (self.today + timedelta(days=5)).isoformat()})
        self.assertEqual(outside.status_code, 400, outside.content)
        self.assertIn("date", outside.data)

    # --- /programs/current/ -------------------------------------------------

    def test_current_program_finds_long_window(self) -> None:
        """14 günlük bir program 8 gün önce başlamış olsa da bugünü kapsıyor."""
        program = WeeklyProgram.objects.create(
            student=self.student, counselor=self.counselor,
            start_date=self.today - timedelta(days=8), day_count=14,
        )
        self.client.force_authenticate(self.student.user)
        resp = self.client.get("/api/programs/current/")
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertEqual(resp.data["id"], program.id)

    # --- Atama --------------------------------------------------------------

    def _template(self, *weekdays) -> ProgramTemplate:
        template = ProgramTemplate.objects.create(counselor=self.counselor, name="Plan")
        for i, wd in enumerate(weekdays):
            TemplateTask.objects.create(
                template=template, subject=self.subject, task_type=self.method,
                title=f"gun{wd}", weekday=wd, start_time="09:00", duration_minutes=60, order=i,
            )
        return template

    def test_assign_defaults_to_first_free_day(self) -> None:
        self._post_program(day_count=5)                       # today..today+4
        resp = self.client.post("/api/programs/assign/", {
            "student": self.student.id, "template": self._template(0).id,
        }, format="json")
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual(resp.data["start_date"], (self.today + timedelta(days=5)).isoformat())

    def test_assign_with_overlapping_start_rejected(self) -> None:
        self._post_program(day_count=5)
        resp = self.client.post("/api/programs/assign/", {
            "student": self.student.id, "template": self._template(0).id,
            "start_date": (self.today + timedelta(days=2)).isoformat(),
        }, format="json")
        self.assertEqual(resp.status_code, 400, resp.content)
        self.assertIn("start_date", resp.data)

    def test_assign_skips_weekdays_outside_window(self) -> None:
        """5 günlük Pzt–Cum programında şablonun Cumartesi bloğu materyalize olmaz."""
        monday = self.today + timedelta(days=(7 - self.today.weekday()))
        template = self._template(0, 5)                        # Pazartesi + Cumartesi
        resp = self.client.post("/api/programs/assign/", {
            "student": self.student.id, "template": template.id,
            "start_date": monday.isoformat(), "day_count": 5,
        }, format="json")
        self.assertEqual(resp.status_code, 201, resp.content)
        program = WeeklyProgram.objects.get(pk=resp.data["id"])
        self.assertEqual([t.title for t in program.tasks.all()], ["gun0"])

    def test_routine_respects_short_window(self) -> None:
        routine = ProgramTemplate.objects.create(
            counselor=self.counselor, student=self.student, name="Rutin", auto_apply=True,
        )
        monday = self.today + timedelta(days=(7 - self.today.weekday()))
        for wd in (0, 6):
            TemplateTask.objects.create(
                template=routine, subject=self.subject, task_type=self.method,
                title=f"gun{wd}", weekday=wd, start_time="10:00", duration_minutes=60,
            )
        resp = self._post_program(start_date=monday.isoformat(), day_count=3)
        self.assertEqual(resp.status_code, 201, resp.content)
        program = WeeklyProgram.objects.get(pk=resp.data["id"])
        self.assertEqual([t.title for t in program.tasks.all()], ["gun0"])


class BlockKindTests(APITestCase):
    """A3 — blok türleri: dış meşguliyet (çalışma saatine sayılmaz) ve genel
    TYT/AYT deneme bloğu (ders seçmeden)."""

    def setUp(self) -> None:
        self.counselor = make_counselor("blokhoca")
        self.student = make_student("blokogr", counselor=self.counselor)
        self.today = timezone.localdate()
        self.subject = Subject.objects.get(name="Matematik", category=Subject.Category.TYT)
        self.method = TaskType.objects.get(name="Konu Çalışması")
        self.program = WeeklyProgram.objects.create(
            student=self.student, counselor=self.counselor, start_date=self.today,
        )
        self.url = f"/api/programs/{self.program.id}/tasks/"
        self.client.force_authenticate(self.counselor.user)

    def _post(self, **over):
        data = {"date": self.today.isoformat(), "start_time": "09:00", "duration_minutes": 60}
        data.update(over)
        return self.client.post(self.url, data, format="json")

    # --- Varsayılan ---------------------------------------------------------

    def test_study_is_default_and_counts(self) -> None:
        resp = self._post(subject=self.subject.id, task_type=self.method.id, title="20 soru")
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual(resp.data["kind"], "study")
        self.assertTrue(resp.data["counts_as_study"])

    def test_study_block_rejects_exam_scope(self) -> None:
        resp = self._post(subject=self.subject.id, kind="study", exam_scope="tyt")
        self.assertEqual(resp.status_code, 400, resp.content)
        self.assertIn("exam_scope", resp.data)

    # --- Dış meşguliyet -----------------------------------------------------

    def test_external_block_does_not_count_as_study(self) -> None:
        resp = self._post(kind="external", title="Antrenman", start_time="17:00",
                          duration_minutes=90)
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertFalse(resp.data["counts_as_study"])
        self.assertIsNone(resp.data["subject"])

    def test_external_block_rejects_subject(self) -> None:
        resp = self._post(kind="external", title="Okul", subject=self.subject.id)
        self.assertEqual(resp.status_code, 400, resp.content)
        self.assertIn("kind", resp.data)

    def test_external_block_requires_title(self) -> None:
        resp = self._post(kind="external")
        self.assertEqual(resp.status_code, 400, resp.content)
        self.assertIn("title", resp.data)

    def test_external_block_still_blocks_that_time(self) -> None:
        first = self._post(kind="external", title="Okul", start_time="08:00",
                           duration_minutes=180)
        self.assertEqual(first.status_code, 201, first.content)
        clash = self._post(subject=self.subject.id, title="Soru", start_time="09:00",
                           duration_minutes=60)
        self.assertEqual(clash.status_code, 400, clash.content)
        self.assertIn("start_time", clash.data)

    # --- Deneme bloğu -------------------------------------------------------

    def test_general_tyt_exam_block_without_subject(self) -> None:
        resp = self._post(kind="exam", exam_scope="tyt", duration_minutes=135)
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual(resp.data["exam_scope"], "tyt")
        self.assertIsNone(resp.data["subject"])
        self.assertTrue(resp.data["counts_as_study"])

    def test_subject_based_exam_block(self) -> None:
        resp = self._post(kind="exam", subject=self.subject.id, title="Mat denemesi")
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual(resp.data["exam_scope"], "")

    def test_exam_block_needs_subject_or_scope(self) -> None:
        resp = self._post(kind="exam", title="Deneme")
        self.assertEqual(resp.status_code, 400, resp.content)
        self.assertIn("exam_scope", resp.data)

    def test_exam_block_rejects_both_subject_and_scope(self) -> None:
        resp = self._post(kind="exam", subject=self.subject.id, exam_scope="ayt")
        self.assertEqual(resp.status_code, 400, resp.content)
        self.assertIn("exam_scope", resp.data)

    # --- Şablon/rutin blok türünü taşır -------------------------------------

    def test_template_carries_block_kind_into_program(self) -> None:
        template = ProgramTemplate.objects.create(counselor=self.counselor, name="Blok plan")
        TemplateTask.objects.create(
            template=template, kind="external", title="Antrenman", weekday=self.today.weekday(),
            start_time="17:00", duration_minutes=90,
        )
        TemplateTask.objects.create(
            template=template, kind="exam", exam_scope="tyt", weekday=self.today.weekday(),
            start_time="09:00", duration_minutes=135,
        )
        resp = self.client.post("/api/programs/assign/", {
            "student": self.student.id, "template": template.id,
            "start_date": (self.today + timedelta(days=7)).isoformat(),
        }, format="json")
        self.assertEqual(resp.status_code, 201, resp.content)
        program = WeeklyProgram.objects.get(pk=resp.data["id"])
        by_kind = {t.kind: t for t in program.tasks.all()}
        self.assertFalse(by_kind["external"].counts_as_study)
        self.assertEqual(by_kind["exam"].exam_scope, "tyt")

    def test_template_task_block_rules_validated(self) -> None:
        resp = self.client.post("/api/program-templates/", {
            "name": "Hatalı", "tasks": [
                {"kind": "external", "subject": self.subject.id, "title": "Okul",
                 "weekday": 0, "start_time": "08:00", "duration_minutes": 60},
            ],
        }, format="json")
        self.assertEqual(resp.status_code, 400, resp.content)


class FieldSubjectsAPITests(APITestCase):
    """Alan bazlı ders listesi: /api/subjects/?student=<id>&scope=field.

    Ders programı tahtasında varsayılan ders satırlarını açmak için; kısıt değil,
    başlangıç kümesi (öğrenci alanı dışından da ders çalışabilir)."""

    def setUp(self) -> None:
        self.counselor = make_counselor("alanhoca")
        self.say = make_student("alan_say", counselor=self.counselor, grade="12", study_field="say")
        self.ea = make_student("alan_ea", counselor=self.counselor, grade="12", study_field="ea")
        self.soz = make_student("alan_soz", counselor=self.counselor, grade="12", study_field="soz")
        self.other = make_student("alan_baska", counselor=make_counselor("alanhoca2"))

    def _field_labels(self, student) -> set[str]:
        resp = self.client.get(f"/api/subjects/?student={student.id}&scope=field")
        self.assertEqual(resp.status_code, 200, resp.content)
        return {s["label"] for s in resp.data}

    def test_sayisal_gets_own_ayt_subjects(self) -> None:
        self.client.force_authenticate(self.counselor.user)
        labels = self._field_labels(self.say)
        self.assertIn("AYT Fizik", labels)
        self.assertIn("AYT Matematik", labels)
        self.assertNotIn("AYT Türk Dili ve Edebiyatı", labels)
        self.assertNotIn("AYT Tarih-2", labels)

    def test_esit_agirlik_gets_own_ayt_subjects(self) -> None:
        self.client.force_authenticate(self.counselor.user)
        labels = self._field_labels(self.ea)
        self.assertIn("AYT Matematik", labels)
        self.assertIn("AYT Türk Dili ve Edebiyatı", labels)
        self.assertIn("AYT Tarih-1", labels)
        self.assertNotIn("AYT Fizik", labels)
        self.assertNotIn("AYT Tarih-2", labels)

    def test_sozel_gets_own_ayt_subjects(self) -> None:
        self.client.force_authenticate(self.counselor.user)
        labels = self._field_labels(self.soz)
        self.assertIn("AYT Türk Dili ve Edebiyatı", labels)
        self.assertIn("AYT Tarih-2", labels)
        self.assertIn("AYT Felsefe", labels)
        self.assertNotIn("AYT Matematik", labels)
        self.assertNotIn("AYT Fizik", labels)

    def test_all_fields_get_every_tyt_subject(self) -> None:
        self.client.force_authenticate(self.counselor.user)
        tyt = {str(s) for s in Subject.objects.filter(category=Subject.Category.TYT)}
        for student in (self.say, self.ea, self.soz):
            self.assertTrue(tyt <= self._field_labels(student))

    def test_without_scope_returns_all_exam_subjects(self) -> None:
        """scope verilmezse alan süzgeci uygulanmaz (eski davranış)."""
        self.client.force_authenticate(self.counselor.user)
        resp = self.client.get(f"/api/subjects/?student={self.say.id}")
        labels = {s["label"] for s in resp.data}
        self.assertIn("AYT Türk Dili ve Edebiyatı", labels)

    def test_plain_list_still_returns_everything(self) -> None:
        self.client.force_authenticate(self.counselor.user)
        resp = self.client.get("/api/subjects/")
        self.assertEqual(len(resp.data), Subject.objects.count())

    def test_counselor_cannot_query_other_students(self) -> None:
        self.client.force_authenticate(self.counselor.user)
        resp = self.client.get(f"/api/subjects/?student={self.other.id}&scope=field")
        self.assertEqual(resp.status_code, 404, resp.content)

    def test_student_can_ask_for_own_field_subjects(self) -> None:
        self.client.force_authenticate(self.say.user)
        resp = self.client.get("/api/subjects/?scope=field")
        labels = {s["label"] for s in resp.data}
        self.assertIn("AYT Fizik", labels)
        self.assertNotIn("AYT Tarih-2", labels)

    def test_lower_grade_falls_back_to_school_subjects(self) -> None:
        junior = make_student("alan_9", counselor=self.counselor, grade="9", study_field=None)
        self.client.force_authenticate(self.counselor.user)
        resp = self.client.get(f"/api/subjects/?student={junior.id}&scope=field")
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertTrue(all(s["category"] == "okul" for s in resp.data))


class BlockDurationMemoryTests(APITestCase):
    """A4 — süre hafızası: rehber × (ders, metod, konu) → son kullanılan süre.

    Hafıza rehber özelinde tutulur (öğrenciden bağımsız) ve konu kombinasyonuna
    özeldir: "Matematik denemesi 1 saat" demek, "Matematik soru çözümü de 1 saat"
    demek değildir."""

    def setUp(self) -> None:
        self.counselor = make_counselor("surehoca")
        self.other_counselor = make_counselor("surehoca2")
        self.ali = make_student("sure_ali", counselor=self.counselor)
        self.ayse = make_student("sure_ayse", counselor=self.counselor)
        self.today = timezone.localdate()
        self.turkce = Subject.objects.get(name="Türkçe", category=Subject.Category.TYT)
        self.mat = Subject.objects.get(name="Matematik", category=Subject.Category.TYT)
        self.test_tipi = TaskType.objects.get(name="Test")
        self.deneme = TaskType.objects.get(name="Deneme")
        self.programs = {
            s.pk: WeeklyProgram.objects.create(
                student=s, counselor=self.counselor, start_date=self.today,
            )
            for s in (self.ali, self.ayse)
        }
        self.client.force_authenticate(self.counselor.user)

    # --- Yardımcılar ---------------------------------------------------------

    def _post(self, student, *, minutes, start="09:00", **over):
        data = {
            "date": self.today.isoformat(), "start_time": start,
            "duration_minutes": minutes,
            "subject": self.turkce.id, "task_type": self.test_tipi.id, "title": "Paragraf",
        }
        data.update(over)
        return self.client.post(f"/api/programs/{self.programs[student.pk].id}/tasks/",
                                data, format="json")

    def _memory(self, **filters):
        return BlockDurationDefault.objects.filter(counselor=self.counselor, **filters)

    # --- Temel davranış ------------------------------------------------------

    def test_saving_block_records_duration(self) -> None:
        resp = self._post(self.ali, minutes=20)
        self.assertEqual(resp.status_code, 201, resp.content)
        row = self._memory(subject=self.turkce, task_type=self.test_tipi, topic="Paragraf").get()
        self.assertEqual(row.duration_minutes, 20)

    def test_memory_is_per_counselor_not_per_student(self) -> None:
        """Kabul kriteri: Ali'ye 20 dk girilince Ayşe'de de aynı kombinasyon 20 dk."""
        self._post(self.ali, minutes=20)
        self._post(self.ayse, minutes=20, start="11:00")
        rows = self._memory(subject=self.turkce, task_type=self.test_tipi, topic="Paragraf")
        self.assertEqual(rows.count(), 1)          # öğrenci başına satır açılmaz
        self.assertEqual(rows.get().duration_minutes, 20)

    def test_last_used_wins(self) -> None:
        self._post(self.ali, minutes=20)
        self._post(self.ayse, minutes=45, start="11:00")
        self.assertEqual(
            self._memory(topic="Paragraf").get().duration_minutes, 45)

    # --- Kombinasyon ayrımı --------------------------------------------------

    def test_different_topic_is_a_different_memory(self) -> None:
        self._post(self.ali, minutes=20)
        self._post(self.ali, minutes=60, start="11:00", title="Sözcükte Anlam")
        self.assertEqual(self._memory(topic="Paragraf").get().duration_minutes, 20)
        self.assertEqual(self._memory(topic="Sözcükte Anlam").get().duration_minutes, 60)

    def test_different_method_is_a_different_memory(self) -> None:
        """'Matematik denemesi 1 saat' ≠ 'Matematik soru çözümü 1 saat'."""
        self._post(self.ali, minutes=20, subject=self.mat.id, task_type=self.test_tipi.id, title="")
        self._post(self.ali, minutes=60, start="11:00",
                   subject=self.mat.id, task_type=self.deneme.id, title="")
        self.assertEqual(self._memory(task_type=self.test_tipi).get().duration_minutes, 20)
        self.assertEqual(self._memory(task_type=self.deneme).get().duration_minutes, 60)

    def test_topicless_block_has_its_own_memory(self) -> None:
        self._post(self.ali, minutes=20)                       # konu: "Paragraf"
        self._post(self.ali, minutes=90, start="11:00", title="")  # konusuz
        self.assertEqual(self._memory(topic="Paragraf").get().duration_minutes, 20)
        self.assertEqual(self._memory(topic="").get().duration_minutes, 90)

    # --- Kapsam dışı bloklar -------------------------------------------------

    def test_external_block_is_not_remembered(self) -> None:
        resp = self._post(self.ali, minutes=120, kind="external", title="Antrenman",
                          subject=None, task_type=None)
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertFalse(self._memory().exists())

    def test_general_exam_block_without_subject_is_not_remembered(self) -> None:
        resp = self._post(self.ali, minutes=180, kind="exam", exam_scope="tyt",
                          subject=None, task_type=None, title="")
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertFalse(self._memory().exists())

    def test_subject_exam_block_is_remembered(self) -> None:
        resp = self._post(self.ali, minutes=40, kind="exam", title="")
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual(self._memory(subject=self.turkce).get().duration_minutes, 40)

    # --- Kim yazar -----------------------------------------------------------

    def test_student_saving_does_not_touch_counselor_memory(self) -> None:
        self._post(self.ali, minutes=20)
        self.client.force_authenticate(self.ali.user)
        resp = self.client.post(
            f"/api/programs/{self.programs[self.ali.pk].id}/tasks/",
            {"date": self.today.isoformat(), "start_time": "14:00", "duration_minutes": 90,
             "subject": self.turkce.id, "task_type": self.test_tipi.id, "title": "Paragraf"},
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual(self._memory(topic="Paragraf").get().duration_minutes, 20)

    def test_moving_a_block_does_not_rewrite_memory(self) -> None:
        """Eski bir bloğu tahtada sürüklemek, daha yeni girilmiş süreyi geri almamalı.

        Blok tanımı (ders, metod, konu, süre) değişmediği sürece taşımak hafızaya
        dokunmaz — taşımak bloğun *nerede* durduğudur, *ne olduğu* değil."""
        old_id = self._post(self.ali, minutes=60).data["id"]      # eski blok: 60 dk
        self._post(self.ali, minutes=20, start="16:00")           # yeni karar: 20 dk
        self.assertEqual(self._memory(topic="Paragraf").get().duration_minutes, 20)

        # Sadece taşı: web tam gövde PATCH'ler, süre aynı kalır.
        resp = self.client.patch(
            f"/api/tasks/{old_id}/",
            {"date": self.today.isoformat(), "start_time": "10:00",
             "duration_minutes": 60, "subject": self.turkce.id,
             "task_type": self.test_tipi.id, "title": "Paragraf"},
            format="json",
        )
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertEqual(self._memory(topic="Paragraf").get().duration_minutes, 20)

    def test_changing_topic_records_the_new_combination(self) -> None:
        """Konu değişikliği bloğun tanımını değiştirir; yeni kombinasyon hatırlanır."""
        task_id = self._post(self.ali, minutes=25).data["id"]
        resp = self.client.patch(
            f"/api/tasks/{task_id}/", {"title": "Sözcükte Anlam"}, format="json")
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertEqual(self._memory(topic="Sözcükte Anlam").get().duration_minutes, 25)

    def test_completing_a_task_does_not_touch_memory(self) -> None:
        task_id = self._post(self.ali, minutes=20).data["id"]
        self._post(self.ali, minutes=45, start="16:00", title="Sözcükte Anlam")
        self.client.patch(f"/api/tasks/{task_id}/", {"is_completed": True}, format="json")
        self.assertEqual(self._memory(topic="Paragraf").get().duration_minutes, 20)

    def test_editing_duration_updates_memory(self) -> None:
        task_id = self._post(self.ali, minutes=20).data["id"]
        resp = self.client.patch(f"/api/tasks/{task_id}/", {"duration_minutes": 35},
                                 format="json")
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertEqual(self._memory(topic="Paragraf").get().duration_minutes, 35)

    # --- Uç ------------------------------------------------------------------

    def test_endpoint_lists_only_own_memory(self) -> None:
        self._post(self.ali, minutes=20)
        BlockDurationDefault.objects.create(
            counselor=self.other_counselor, subject=self.turkce,
            task_type=self.test_tipi, topic="Paragraf", duration_minutes=99,
        )
        resp = self.client.get("/api/block-durations/")
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]["duration_minutes"], 20)
        self.assertEqual(resp.data[0]["topic"], "Paragraf")

    def test_student_cannot_read_endpoint(self) -> None:
        self.client.force_authenticate(self.ali.user)
        resp = self.client.get("/api/block-durations/")
        self.assertEqual(resp.status_code, 403, resp.content)


class ParentAccessTests(APITestCase):
    """E3 — velinin ne görüp ne göremediği.

    Karar (kullanıcı, 29 Ağu 2026): veli **denemeleri** (ders kırılımıyla),
    **onaylanmış** haftalık programları ve uyum yüzdelerini, **konu takip
    listesini**, **haftalık çalışma saatini** ve rehberle olan **takvimini**
    görür. **Kitaplık ve hedefler veliye kapalıdır.**
    """

    def setUp(self) -> None:
        self.counselor = make_counselor("velihoca")
        self.student = make_student("veliogr", counselor=self.counselor)
        self.other_student = make_student("veliogr2", counselor=self.counselor)
        self.parent = make_parent("veli1", self.student)
        self.today = timezone.localdate()
        self.tyt_turkce = Subject.objects.get(name="Türkçe", category=Subject.Category.TYT)
        self.tyt_mat = Subject.objects.get(name="Matematik", category=Subject.Category.TYT)
        self.method = TaskType.objects.get(name="Konu Çalışması")
        self.client.force_authenticate(self.parent.user)

    def _program(self, days_ago: int, *, approved: bool, student=None) -> WeeklyProgram:
        p = WeeklyProgram.objects.create(
            student=student or self.student, counselor=self.counselor,
            start_date=self.today - timedelta(days=days_ago), day_count=7,
        )
        if approved:
            p.approve(self.counselor)
        return p

    def _task(self, program, minutes, *, completed=True, hour=9, day=0):
        return Task.objects.create(
            program=program, subject=self.tyt_mat, task_type=self.method,
            kind=BlockKind.STUDY, title="Konu",
            date=program.start_date + timedelta(days=day),
            start_time=f"{hour:02d}:00", duration_minutes=minutes, is_completed=completed,
        )

    # --- Denemeler: GÖRÜR, ders kırılımıyla ---------------------------------

    def _exam(self, student=None, *, correct=6, wrong=1):
        exam = ExamResult.objects.create(
            student=student or self.student, exam_type="tyt",
            name="Deneme 1", exam_date=self.today,
        )
        SubjectNet.objects.create(
            exam_result=exam, subject=self.tyt_turkce, correct=correct, wrong=wrong,
        )
        return exam

    def test_parent_sees_child_exams(self) -> None:
        self._exam()
        res = self.client.get("/api/exams/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)

    def test_parent_sees_exam_subject_detail(self) -> None:
        """'Türkçe 6 doğru 1 yanlış' kırılımı veliye de dönmeli."""
        exam = self._exam(correct=6, wrong=1)
        row = self.client.get(f"/api/exams/{exam.id}/").data
        net = row["subject_nets"][0]
        self.assertEqual(net["subject_label"], "TYT Türkçe")
        self.assertEqual((net["correct"], net["wrong"]), (6, 1))
        self.assertEqual(net["net"], 5.75)          # 6 - 1/4
        self.assertEqual(net["blank"], self.tyt_turkce.question_count - 7)

    def test_parent_cannot_edit_or_delete_exam(self) -> None:
        exam = self._exam()
        self.assertEqual(self.client.patch(f"/api/exams/{exam.id}/", {"name": "X"}).status_code, 403)
        self.assertEqual(self.client.delete(f"/api/exams/{exam.id}/").status_code, 403)

    def test_parent_cannot_see_other_students_exam(self) -> None:
        exam = self._exam(student=self.other_student)
        self.assertEqual(self.client.get("/api/exams/").data, [])
        self.assertEqual(self.client.get(f"/api/exams/{exam.id}/").status_code, 403)

    def test_unapproved_program_does_not_hide_exams(self) -> None:
        """Deneme programa bağlı değil — onay şartı denemelere uygulanmaz."""
        self._program(30, approved=False)
        self._exam()
        self.assertEqual(len(self.client.get("/api/exams/").data), 1)

    # --- Programlar: yalnız ONAYLI ------------------------------------------

    def test_parent_sees_only_approved_programs(self) -> None:
        approved = self._program(30, approved=True)
        self._program(10, approved=False)
        rows = self.client.get("/api/programs/").data
        self.assertEqual([r["id"] for r in rows], [approved.id])

    def test_parent_can_filter_programs_by_student(self) -> None:
        self.parent.students.add(self.other_student)
        mine = self._program(30, approved=True)
        self._program(10, approved=True, student=self.other_student)
        rows = self.client.get(f"/api/programs/?student={self.student.id}").data
        self.assertEqual([r["id"] for r in rows], [mine.id])

    # --- Uyum yüzdesi + haftalık saat ---------------------------------------

    def test_parent_sees_compliance_of_approved_weeks_only(self) -> None:
        approved = self._program(30, approved=True)
        self._task(approved, 120)                       # yapıldı
        self._task(approved, 120, completed=False, hour=13)
        unapproved = self._program(10, approved=False)
        self._task(unapproved, 600)

        data = self.client.get(f"/api/programs/compliance/?student={self.student.id}").data
        self.assertEqual([r["id"] for r in data["programs"]], [approved.id])
        self.assertEqual(data["overall"]["percent"], 50)

    def test_compliance_reports_completed_hours(self) -> None:
        """'Bu hafta kaç saat çalıştı' — planlanan değil, tamamlanan saat."""
        p = self._program(30, approved=True)
        self._task(p, 120)
        self._task(p, 60, completed=False, hour=13)
        row = self.client.get(f"/api/programs/compliance/?student={self.student.id}").data
        row = row["programs"][0]
        self.assertEqual(row["study_hours"], 3.0)       # planlanan 180 dk
        self.assertEqual(row["completed_hours"], 2.0)   # yapılan 120 dk

    def test_parent_study_stats_counts_approved_only(self) -> None:
        approved = self._program(30, approved=True)
        self._task(approved, 180)
        unapproved = self._program(10, approved=False)
        self._task(unapproved, 300)
        data = self.client.get(f"/api/study-stats/?student={self.student.id}").data
        self.assertEqual(data["total_hours"], 3.0)

    # --- Konu takip listesi: GÖRÜR, salt-okunur -----------------------------

    def test_parent_sees_topic_progress_read_only(self) -> None:
        topic = Topic.objects.filter(subject=self.tyt_mat).first()
        progress = TopicProgress.objects.create(student=self.student, topic=topic, level=4)
        rows = self.client.get("/api/topic-progress/").data
        self.assertEqual([r["id"] for r in rows], [progress.id])
        res = self.client.patch(f"/api/topic-progress/{progress.id}/", {"level": 1})
        self.assertEqual(res.status_code, 403)
        progress.refresh_from_db()
        self.assertEqual(progress.level, 4)

    # --- Kitaplık: GÖRMEZ ---------------------------------------------------

    def test_parent_cannot_see_books(self) -> None:
        book = Book.objects.create(
            student=self.student, kind="ders", subject=self.tyt_mat,
            title="TYT Matematik Soru Bankası",
        )
        self.assertEqual(self.client.get("/api/books/").data, [])
        self.assertEqual(self.client.get(f"/api/books/{book.id}/").status_code, 403)

    def test_parent_cannot_see_book_topics(self) -> None:
        book = Book.objects.create(
            student=self.student, kind="ders", subject=self.tyt_mat, title="Soru Bankası",
        )
        topic = Topic.objects.filter(subject=self.tyt_mat).first()
        bt = BookTopic.objects.create(book=book, topic=topic)
        self.assertEqual(self.client.get(f"/api/book-topics/{bt.id}/").status_code, 403)

    # --- Hedefler: GÖRMEZ ---------------------------------------------------

    def test_parent_cannot_see_goals(self) -> None:
        goal = Goal.objects.create(
            student=self.student, goal_type="deneme_net", exam_scope="tyt", target_net=90,
        )
        self.assertEqual(self.client.get("/api/goals/").data, [])
        self.assertEqual(self.client.get(f"/api/goals/{goal.id}/").status_code, 403)

    # --- Takvim: GÖRÜR (kapsam kararı) --------------------------------------

    def test_parent_still_sees_calendar(self) -> None:
        event = CalendarEvent.objects.create(
            counselor=self.counselor, student=self.student,
            title="Toplantı", date=self.today,
        )
        rows = self.client.get("/api/calendar/").data
        self.assertEqual([r["id"] for r in rows], [event.id])
