from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User, Counselor, Student, Parent


class ParentLinkMixin:
    """Velinin bir öğrenciye bağlanma kuralı: **öğrenci id'si + hocanın davet kodu**.

    Karar (kullanıcı, 29 Ağu 2026, E3): veli artık öğrencinin `connect_code`'unu
    değil, çocuğunun id'sini ve o çocuğun rehberinin davet kodunu girer. Böylece
    veli, bağlandığı çocuğun gerçekten bir rehbere kayıtlı olduğunu da doğrulamış
    olur — rehbersiz öğrenciye veli bağlanamaz.

    Hata mesajı **tek ve ayrımsız** tutulur: "öğrenci yok" ile "kod yanlış"
    ayrı ayrı söylenirse, kodu eline geçiren biri id deneyerek o rehberin öğrenci
    listesini çıkarabilir. Tek mesaj bu ayrımı kapatır.
    """
    LINK_ERROR = "Öğrenci numarası ile rehber davet kodu eşleşmiyor."

    @staticmethod
    def resolve_student(student_id, counselor_code):
        """Verilen id + davet kodu ikilisine karşılık gelen öğrenciyi döner."""
        code = (counselor_code or "").strip().upper()
        if not code or student_id is None:
            return None
        return (
            Student.objects
            .filter(pk=student_id, counselor__invite_code=code)
            .select_related("user", "counselor__user")
            .first()
        )


def role_of(user):
    if user.is_counselor:
        return "counselor"
    if user.is_student:
        return "student"
    if user.is_parent:
        return "parent"
    return "user"


def profile_of(user):
    """auth-contract.md §4 — role'e göre profile objesi (TASLAK, genişleyebilir)."""
    if user.is_counselor and hasattr(user, "counselor_profile"):
        return {"invite_code": user.counselor_profile.invite_code}
    if user.is_student and hasattr(user, "student_profile"):
        s = user.student_profile
        return {
            "grade": s.grade,
            "study_field": s.study_field,
            "counselor": (
                {"id": s.counselor.id, "name": s.counselor.user.get_full_name()}
                if s.counselor else None
            ),
        }
    if user.is_parent and hasattr(user, "parent_profile"):
        return {
            "students": [
                {"id": st.id, "name": st.user.get_full_name()}
                for st in user.parent_profile.students.all()
            ]
        }
    return {}


class UserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name", "role", "profile")

    def get_role(self, obj):
        return role_of(obj)

    def get_profile(self, obj):
        return profile_of(obj)


class MeUpdateSerializer(serializers.ModelSerializer):
    """PATCH /api/auth/me/ — kullanıcının kendi ad/soyad/e-postasını düzenlemesi.

    `username` ve rol bayrakları buraya dahil değildir: kullanıcı adı giriş
    kimliğidir, roller kayıt akışında belirlenir. Gövdede gönderilseler bile
    ModelSerializer bilinmeyen alanları yok sayar."""

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")
        # Mesajlar burada açıkça Türkçe veriliyor: proje LANGUAGE_CODE'u hâlâ
        # 'en-us' ve bu metinler doğrudan kullanıcıya gösteriliyor.
        extra_kwargs = {
            "first_name": {
                "allow_blank": False,
                "error_messages": {"blank": "Ad boş bırakılamaz."},
            },
            "last_name": {
                "allow_blank": False,
                "error_messages": {"blank": "Soyad boş bırakılamaz."},
            },
            "email": {
                "allow_blank": False,
                "error_messages": {
                    "blank": "E-posta boş bırakılamaz.",
                    "invalid": "Geçerli bir e-posta adresi girin.",
                },
            },
        }

    def validate_email(self, value: str) -> str:
        """Kayıttaki kuralın aynısı, ama kullanıcının kendi e-postası hariç."""
        if User.objects.filter(email__iexact=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError("Bu e-posta ile zaten bir hesap var.")
        return value


class BaseRegisterSerializer(serializers.ModelSerializer):
    """Ortak kullanıcı alanları + şifre doğrulama. Alt sınıflar create()'i tamamlar."""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password", "first_name", "last_name")

    def validate_email(self, value: str) -> str:
        """Aynı e-posta ile ikinci hesap açılmasını engelle (harf duyarsız)."""
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Bu e-posta ile zaten bir hesap var.")
        return value

    def _create_user(self):
        data = self.validated_data
        user = User(
            username=data["username"],
            email=data["email"],
            first_name=data["first_name"],
            last_name=data["last_name"],
        )
        user.set_password(data["password"])
        return user


class CounselorRegisterSerializer(BaseRegisterSerializer):
    def create(self, validated_data):
        user = self._create_user()
        user.is_counselor = True
        user.save()
        Counselor.objects.create(user=user)
        return user


class StudentRegisterSerializer(BaseRegisterSerializer):
    grade = serializers.ChoiceField(choices=Student.GradeLevel.choices)
    study_field = serializers.ChoiceField(
        choices=Student.StudyField.choices, required=False, allow_null=True, allow_blank=True,
    )
    counselor_code = serializers.CharField(required=False, allow_blank=True, write_only=True)

    class Meta(BaseRegisterSerializer.Meta):
        fields = BaseRegisterSerializer.Meta.fields + ("grade", "study_field", "counselor_code")

    def validate(self, attrs):
        code = attrs.get("counselor_code", "").strip().upper()
        if code and not Counselor.objects.filter(invite_code=code).exists():
            raise serializers.ValidationError({"counselor_code": "Geçersiz rehber kodu."})
        attrs["counselor_code"] = code

        # Sınıf ↔ alan tutarlılığı (Student.clean ile aynı kural, API'de de zorunlu)
        grade = attrs.get("grade")
        study_field = attrs.get("study_field") or None
        selects_field = grade not in Student.NON_FIELD_GRADES
        if selects_field and not study_field:
            raise serializers.ValidationError(
                {"study_field": "11. sınıf ve üzeri öğrenciler alan seçmelidir."}
            )
        if not selects_field and study_field:
            raise serializers.ValidationError(
                {"study_field": "9 ve 10. sınıf öğrencileri alan seçemez."}
            )
        attrs["study_field"] = study_field
        return attrs

    def create(self, validated_data):
        code = validated_data.pop("counselor_code", "")
        grade = validated_data.pop("grade")
        study_field = validated_data.pop("study_field", None) or None
        user = self._create_user()
        user.is_student = True
        user.save()
        counselor = Counselor.objects.filter(invite_code=code).first() if code else None
        Student.objects.create(
            user=user, grade=grade, study_field=study_field, counselor=counselor,
        )
        return user


class ParentRegisterSerializer(ParentLinkMixin, BaseRegisterSerializer):
    """Veli kaydı. Çocuğa bağlanma **opsiyoneldir**; ikisi birlikte gönderilir.

    Bağlanmadan kaydolan veli sonradan `POST /api/parents/connect-student/`
    ile bağlanabilir — akış ve doğrulama birebir aynıdır.
    """
    student = serializers.IntegerField(required=False, allow_null=True, write_only=True)
    counselor_code = serializers.CharField(required=False, allow_blank=True, write_only=True)

    class Meta(BaseRegisterSerializer.Meta):
        fields = BaseRegisterSerializer.Meta.fields + ("student", "counselor_code")

    def validate(self, attrs):
        student_id = attrs.get("student")
        code = (attrs.get("counselor_code") or "").strip().upper()
        if not student_id and not code:
            attrs["_linked_student"] = None
            return attrs
        if bool(student_id) != bool(code):
            raise serializers.ValidationError(
                {"counselor_code": "Öğrenci numarası ve rehber davet kodu birlikte gönderilmelidir."}
            )
        student = self.resolve_student(student_id, code)
        if student is None:
            raise serializers.ValidationError({"counselor_code": self.LINK_ERROR})
        attrs["_linked_student"] = student
        return attrs

    def create(self, validated_data):
        student = validated_data.pop("_linked_student", None)
        validated_data.pop("student", None)
        validated_data.pop("counselor_code", None)
        user = self._create_user()
        user.is_parent = True
        user.save()
        parent = Parent.objects.create(user=user)
        if student is not None:
            parent.students.add(student)
        return user


class CounselorStudentSerializer(serializers.ModelSerializer):
    """Rehberin öğrenci listesi için sade gösterim (program/ödev açarken id lazım)."""
    full_name = serializers.SerializerMethodField()
    grade_display = serializers.CharField(source="get_grade_display", read_only=True)

    class Meta:
        model = Student
        fields = ["id", "full_name", "grade", "grade_display", "study_field"]

    def get_full_name(self, obj) -> str:
        return obj.user.get_full_name()


class RehberimTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Standart JWT yanıtına kullanıcı/rol bilgisini ekler (auth-contract.md §5.1)."""
    default_error_messages = {
        "no_active_account": "Kullanıcı adı veya şifre hatalı.",
    }

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data


class ConnectCounselorSerializer(serializers.Serializer):
    code = serializers.CharField()

    def validate_code(self, value):
        code = value.strip().upper()
        if not Counselor.objects.filter(invite_code=code).exists():
            raise serializers.ValidationError("Geçersiz rehber kodu.")
        return code


class ConnectStudentSerializer(ParentLinkMixin, serializers.Serializer):
    """Veli → çocuk bağlanması: öğrencinin id'si + o öğrencinin rehberinin kodu."""
    student = serializers.IntegerField()
    counselor_code = serializers.CharField()

    def validate(self, attrs):
        student = self.resolve_student(attrs["student"], attrs["counselor_code"])
        if student is None:
            raise serializers.ValidationError({"counselor_code": self.LINK_ERROR})
        attrs["student_obj"] = student
        return attrs
