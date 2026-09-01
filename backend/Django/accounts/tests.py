from django.db import IntegrityError
from django.test import TestCase
from rest_framework.test import APITestCase

from accounts.models import Counselor, Parent, Student, User


class RegisterEmailUniquenessTests(APITestCase):
    URL = "/api/auth/register/counselor/"

    def _payload(self, username: str, email: str) -> dict:
        return {
            "username": username, "email": email,
            "password": "Passw0rd!234", "first_name": "A", "last_name": "B",
        }

    def test_first_registration_succeeds(self) -> None:
        resp = self.client.post(self.URL, self._payload("user_a", "ayni@x.com"))
        self.assertEqual(resp.status_code, 201, resp.content)

    def test_duplicate_email_rejected(self) -> None:
        self.client.post(self.URL, self._payload("user_a", "ayni@x.com"))
        resp = self.client.post(self.URL, self._payload("user_b", "ayni@x.com"))
        self.assertEqual(resp.status_code, 400, resp.content)
        self.assertIn("email", resp.data)

    def test_duplicate_email_is_case_insensitive(self) -> None:
        self.client.post(self.URL, self._payload("user_a", "ayni@x.com"))
        resp = self.client.post(self.URL, self._payload("user_b", "AYNI@X.com"))
        self.assertEqual(resp.status_code, 400, resp.content)

    def test_duplicate_email_across_roles(self) -> None:
        # Rehber bu maili aldıysa öğrenci de aynı maille kayıt olamaz
        self.client.post(self.URL, self._payload("hoca", "paylasik@x.com"))
        resp = self.client.post("/api/auth/register/student/", {
            "username": "ogr", "email": "paylasik@x.com", "password": "Passw0rd!234",
            "first_name": "O", "last_name": "G", "grade": "12", "study_field": "say",
        })
        self.assertEqual(resp.status_code, 400, resp.content)
        self.assertFalse(User.objects.filter(username="ogr").exists())


class StudentRegisterGradeFieldTests(APITestCase):
    URL = "/api/auth/register/student/"

    def _payload(self, **over) -> dict:
        data = {
            "username": "ogr", "email": "ogr@x.com", "password": "Passw0rd!234",
            "first_name": "O", "last_name": "G", "grade": "12", "study_field": "say",
        }
        data.update(over)
        return data

    def test_exam_grade_without_field_rejected(self) -> None:
        resp = self.client.post(self.URL, self._payload(grade="12", study_field=""))
        self.assertEqual(resp.status_code, 400, resp.content)
        self.assertIn("study_field", resp.data)

    def test_lower_grade_with_field_rejected(self) -> None:
        resp = self.client.post(self.URL, self._payload(grade="9", study_field="say"))
        self.assertEqual(resp.status_code, 400, resp.content)
        self.assertIn("study_field", resp.data)

    def test_lower_grade_without_field_ok(self) -> None:
        resp = self.client.post(self.URL, self._payload(grade="9", study_field=""))
        self.assertEqual(resp.status_code, 201, resp.content)

    def test_exam_grade_with_field_ok(self) -> None:
        resp = self.client.post(self.URL, self._payload(grade="12", study_field="say"))
        self.assertEqual(resp.status_code, 201, resp.content)


class CounselorStudentsListTests(APITestCase):
    def setUp(self) -> None:
        from accounts.models import Counselor, Student
        self.counselor = Counselor.objects.create(
            user=User.objects.create_user("clist1", password="x", is_counselor=True))
        self.other = Counselor.objects.create(
            user=User.objects.create_user("clist2", password="x", is_counselor=True))
        self.s1 = Student.objects.create(
            user=User.objects.create_user("slist1", password="x", is_student=True),
            counselor=self.counselor, grade="12", study_field="say")
        Student.objects.create(
            user=User.objects.create_user("slist2", password="x", is_student=True),
            counselor=self.other, grade="12", study_field="say")

    def test_counselor_sees_only_own_students(self) -> None:
        self.client.force_authenticate(self.counselor.user)
        resp = self.client.get("/api/students/")
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]["id"], self.s1.id)
        self.assertIn("full_name", resp.data[0])

    def test_student_cannot_list_students(self) -> None:
        self.client.force_authenticate(self.s1.user)
        resp = self.client.get("/api/students/")
        self.assertEqual(resp.status_code, 403, resp.content)


class MeUpdateTests(APITestCase):
    URL = "/api/auth/me/"

    def setUp(self) -> None:
        from accounts.models import Counselor
        self.counselor = Counselor.objects.create(
            user=User.objects.create_user(
                "me_hoca", password="x", is_counselor=True,
                first_name="Ayşe", last_name="Kaya", email="ayse@x.com"))
        self.user = self.counselor.user

    def test_updates_own_name_and_email(self) -> None:
        self.client.force_authenticate(self.user)
        resp = self.client.patch(self.URL, {
            "first_name": "Ayşegül", "last_name": "Kaya Demir", "email": "yeni@x.com",
        }, format="json")
        self.assertEqual(resp.status_code, 200, resp.content)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Ayşegül")
        self.assertEqual(self.user.email, "yeni@x.com")
        # Yanıt GET ile aynı şekilde olmalı (rol + profil gömülü)
        self.assertEqual(resp.data["role"], "counselor")
        self.assertIn("profile", resp.data)

    def test_partial_update_leaves_other_fields(self) -> None:
        self.client.force_authenticate(self.user)
        resp = self.client.patch(self.URL, {"first_name": "Zehra"}, format="json")
        self.assertEqual(resp.status_code, 200, resp.content)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Zehra")
        self.assertEqual(self.user.last_name, "Kaya")
        self.assertEqual(self.user.email, "ayse@x.com")

    def test_username_and_roles_are_not_editable(self) -> None:
        self.client.force_authenticate(self.user)
        resp = self.client.patch(self.URL, {
            "username": "baskaisim", "is_student": True, "first_name": "Ayşe",
        }, format="json")
        self.assertEqual(resp.status_code, 200, resp.content)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "me_hoca")
        self.assertFalse(self.user.is_student)
        self.assertTrue(self.user.is_counselor)

    def test_blank_first_name_rejected(self) -> None:
        self.client.force_authenticate(self.user)
        resp = self.client.patch(self.URL, {"first_name": ""}, format="json")
        self.assertEqual(resp.status_code, 400, resp.content)
        self.assertIn("first_name", resp.data)

    def test_invalid_email_rejected(self) -> None:
        self.client.force_authenticate(self.user)
        resp = self.client.patch(self.URL, {"email": "duz-metin"}, format="json")
        self.assertEqual(resp.status_code, 400, resp.content)
        self.assertIn("email", resp.data)

    def test_email_taken_by_another_user_rejected(self) -> None:
        User.objects.create_user("baskasi", password="x", email="dolu@x.com")
        self.client.force_authenticate(self.user)
        resp = self.client.patch(self.URL, {"email": "dolu@x.com"}, format="json")
        self.assertEqual(resp.status_code, 400, resp.content)
        self.assertIn("email", resp.data)

    def test_keeping_own_email_is_allowed(self) -> None:
        """Kendi e-postasını değiştirmeden göndermek çakışma sayılmamalı."""
        self.client.force_authenticate(self.user)
        resp = self.client.patch(self.URL, {"email": "AYSE@x.com"}, format="json")
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_anonymous_cannot_update(self) -> None:
        resp = self.client.patch(self.URL, {"first_name": "X"}, format="json")
        self.assertEqual(resp.status_code, 401, resp.content)


class InviteCodeTests(TestCase):
    """E3 — rehberin davet kodu **benzersiz** ve **değişmez** olmalı."""

    def _counselor(self, username: str) -> Counselor:
        user = User.objects.create_user(
            username=username, password="pass1234", is_counselor=True)
        return Counselor.objects.create(user=user)

    def test_code_generated_on_create(self) -> None:
        c = self._counselor("kod1")
        self.assertEqual(len(c.invite_code), 6)
        self.assertTrue(c.invite_code.isupper() or c.invite_code.isdigit())

    def test_codes_are_unique_across_counselors(self) -> None:
        codes = {self._counselor(f"kod{i}").invite_code for i in range(25)}
        self.assertEqual(len(codes), 25)

    def test_duplicate_code_rejected_by_database(self) -> None:
        first = self._counselor("kodA")
        user = User.objects.create_user(
            username="kodB", password="pass1234", is_counselor=True)
        with self.assertRaises(IntegrityError):
            Counselor.objects.create(user=user, invite_code=first.invite_code)

    def test_code_cannot_be_changed(self) -> None:
        c = self._counselor("kodsabit")
        original = c.invite_code
        c.invite_code = "ZZZZZZ"
        with self.assertRaises(ValueError):
            c.save()
        c.refresh_from_db()
        self.assertEqual(c.invite_code, original)

    def test_code_survives_other_field_updates(self) -> None:
        c = self._counselor("kodkalici")
        original = c.invite_code
        c.user.first_name = "Yeni"
        c.user.save()
        c.save()
        c.refresh_from_db()
        self.assertEqual(c.invite_code, original)

    def test_clearing_code_does_not_regenerate_silently(self) -> None:
        """Boşaltıp kaydetmek de bir değişikliktir — sessizce yeni kod üretmez."""
        c = self._counselor("kodbosalt")
        c.invite_code = ""
        with self.assertRaises(ValueError):
            c.save()


class ParentConnectTests(APITestCase):
    """E3 — veli, öğrencinin id'si + rehberin davet kodu ile bağlanır."""

    def setUp(self) -> None:
        cu = User.objects.create_user(username="pchoca", password="pass1234", is_counselor=True)
        self.counselor = Counselor.objects.create(user=cu)
        other_cu = User.objects.create_user(username="pchoca2", password="pass1234", is_counselor=True)
        self.other_counselor = Counselor.objects.create(user=other_cu)

        su = User.objects.create_user(
            username="pcogr", password="pass1234", is_student=True,
            first_name="Ali", last_name="Yılmaz")
        self.student = Student.objects.create(
            user=su, counselor=self.counselor, grade="12", study_field="say")

        lonely = User.objects.create_user(username="pcyalniz", password="pass1234", is_student=True)
        self.unlinked_student = Student.objects.create(
            user=lonely, counselor=None, grade="12", study_field="say")

        pu = User.objects.create_user(username="pcveli", password="pass1234", is_parent=True)
        self.parent = Parent.objects.create(user=pu)
        self.client.force_authenticate(pu)

    URL = "/api/parents/connect-student/"

    def test_connects_with_student_id_and_counselor_code(self) -> None:
        res = self.client.post(self.URL, {
            "student": self.student.id, "counselor_code": self.counselor.invite_code,
        })
        self.assertEqual(res.status_code, 200, res.content)
        self.assertEqual(res.data["student"]["name"], "Ali Yılmaz")
        self.assertEqual(res.data["counselor"]["id"], self.counselor.id)
        self.assertTrue(self.parent.students.filter(pk=self.student.pk).exists())

    def test_code_is_case_insensitive(self) -> None:
        res = self.client.post(self.URL, {
            "student": self.student.id,
            "counselor_code": self.counselor.invite_code.lower(),
        })
        self.assertEqual(res.status_code, 200, res.content)

    def test_wrong_counselor_code_rejected(self) -> None:
        res = self.client.post(self.URL, {
            "student": self.student.id,
            "counselor_code": self.other_counselor.invite_code,
        })
        self.assertEqual(res.status_code, 400)
        self.assertFalse(self.parent.students.exists())

    def test_unknown_student_gives_same_message_as_wrong_code(self) -> None:
        """İki hata ayırt edilemesin — yoksa id denenerek öğrenci listesi çıkar."""
        unknown = self.client.post(self.URL, {
            "student": 999999, "counselor_code": self.counselor.invite_code,
        })
        wrong = self.client.post(self.URL, {
            "student": self.student.id, "counselor_code": "ZZZZZZ",
        })
        self.assertEqual(unknown.status_code, 400)
        self.assertEqual(unknown.data, wrong.data)

    def test_student_without_counselor_cannot_be_linked(self) -> None:
        res = self.client.post(self.URL, {
            "student": self.unlinked_student.id,
            "counselor_code": self.counselor.invite_code,
        })
        self.assertEqual(res.status_code, 400)

    def test_old_connect_code_flow_no_longer_works(self) -> None:
        res = self.client.post(self.URL, {"code": self.student.connect_code})
        self.assertEqual(res.status_code, 400)
        self.assertFalse(self.parent.students.exists())

    def test_student_cannot_use_parent_endpoint(self) -> None:
        self.client.force_authenticate(self.student.user)
        res = self.client.post(self.URL, {
            "student": self.student.id, "counselor_code": self.counselor.invite_code,
        })
        self.assertEqual(res.status_code, 403)


class ParentRegisterLinkTests(APITestCase):
    """E3 — veli kaydında bağlanma opsiyonel ama ikili birlikte gönderilmeli."""

    URL = "/api/auth/register/parent/"

    def setUp(self) -> None:
        cu = User.objects.create_user(username="prhoca", password="pass1234", is_counselor=True)
        self.counselor = Counselor.objects.create(user=cu)
        su = User.objects.create_user(username="progr", password="pass1234", is_student=True)
        self.student = Student.objects.create(
            user=su, counselor=self.counselor, grade="12", study_field="say")

    def _payload(self, username: str, **extra) -> dict:
        return {
            "username": username, "email": f"{username}@x.com",
            "password": "Passw0rd!234", "first_name": "V", "last_name": "Eli",
            **extra,
        }

    def test_registers_and_links(self) -> None:
        res = self.client.post(self.URL, self._payload(
            "veli_bagli", student=self.student.id,
            counselor_code=self.counselor.invite_code))
        self.assertEqual(res.status_code, 201, res.content)
        parent = Parent.objects.get(user__username="veli_bagli")
        self.assertEqual(list(parent.students.all()), [self.student])
        self.assertEqual(res.data["user"]["profile"]["students"][0]["id"], self.student.id)

    def test_registers_without_linking(self) -> None:
        res = self.client.post(self.URL, self._payload("veli_bagsiz"))
        self.assertEqual(res.status_code, 201, res.content)
        self.assertFalse(Parent.objects.get(user__username="veli_bagsiz").students.exists())

    def test_half_filled_pair_rejected(self) -> None:
        only_id = self.client.post(self.URL, self._payload("veli_yarim1", student=self.student.id))
        only_code = self.client.post(self.URL, self._payload(
            "veli_yarim2", counselor_code=self.counselor.invite_code))
        self.assertEqual(only_id.status_code, 400)
        self.assertEqual(only_code.status_code, 400)

    def test_bad_pair_does_not_create_user(self) -> None:
        res = self.client.post(self.URL, self._payload(
            "veli_hatali", student=self.student.id, counselor_code="ZZZZZZ"))
        self.assertEqual(res.status_code, 400)
        self.assertFalse(User.objects.filter(username="veli_hatali").exists())
