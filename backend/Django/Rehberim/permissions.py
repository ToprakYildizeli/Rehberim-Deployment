from rest_framework.permissions import SAFE_METHODS, BasePermission


def _is_that_student(user, student_id) -> bool:
    return (
        getattr(user, 'is_student', False)
        and hasattr(user, 'student_profile')
        and student_id == user.student_profile.id
    )


def _is_that_students_parent(user, student_id) -> bool:
    return (
        student_id is not None
        and getattr(user, 'is_parent', False)
        and hasattr(user, 'parent_profile')
        and user.parent_profile.students.filter(pk=student_id).exists()
    )


def _owns_program(user, program) -> tuple[bool, bool]:
    """(öğrenci sahibi mi, rehber sahibi mi) çiftini döner."""
    is_student_owner = (
        getattr(user, 'is_student', False)
        and hasattr(user, 'student_profile')
        and program.student_id == user.student_profile.id
    )
    is_counselor_owner = (
        getattr(user, 'is_counselor', False)
        and hasattr(user, 'counselor_profile')
        and program.student.counselor_id == user.counselor_profile.id
    )
    return is_student_owner, is_counselor_owner


def _is_parent_of_program(user, program) -> bool:
    """Veli, çocuğunun **onaylanmış** programını görebilir; onaysızı hiç göremez."""
    return (
        program.is_approved
        and getattr(user, 'is_parent', False)
        and hasattr(user, 'parent_profile')
        and user.parent_profile.students.filter(pk=program.student_id).exists()
    )


class IsProgramParticipant(BasePermission):
    """İlgili öğrenci ya da onun rehberi erişebilir; veli onaylı programı salt-okur.

    Task üzerinde de çalışır; `obj.program` üzerinden çözer. Öğrenci kendi program
    görevlerini doğrudan düzenleyebilir — **ama program onaylandıktan sonra değil**:
    onay bir mühürdür, sonradan işaretlenen görev uyum yüzdesini kaydıramaz.
    """
    message = "Bu programa erişim yetkiniz yok."

    def has_object_permission(self, request, view, obj) -> bool:
        program = getattr(obj, 'program', obj)  # WeeklyProgram ya da Task
        is_student_owner, is_counselor_owner = _owns_program(request.user, program)
        if is_counselor_owner:
            return True
        if is_student_owner:
            if request.method in SAFE_METHODS or not program.is_approved:
                return True
            self.message = ("Onaylanmış programın görevleri değiştirilemez. "
                            "Değişiklik için rehberinize başvurun.")
            return False
        return request.method in SAFE_METHODS and _is_parent_of_program(request.user, program)


class IsExamOwnerStudentOrReadOnly(BasePermission):
    """Deneme: sahibi öğrenci tam yetki; öğrencinin rehberi ve **velisi** salt-okur.

    Veli erişimi E3 ile açıldı: veli çocuğunun deneme sonuçlarını ders ders
    (doğru/yanlış/boş/net) görür ama hiçbirini değiştiremez.
    """
    message = "Bu deneme sonucuna erişim yetkiniz yok."

    def has_object_permission(self, request, view, obj) -> bool:
        user = request.user
        # Sahibi öğrenci → her şey
        if _is_that_student(user, obj.student_id):
            return True
        # Öğrencinin rehberi ve velisi → yalnızca okuma (GET/HEAD/OPTIONS)
        if request.method in SAFE_METHODS:
            is_counselor = (
                getattr(user, 'is_counselor', False)
                and hasattr(user, 'counselor_profile')
                and obj.student.counselor_id == user.counselor_profile.id
            )
            return is_counselor or _is_that_students_parent(user, obj.student_id)
        return False


class CanModifyProgram(BasePermission):
    """Program nesnesi: okuma katılımcılara, program-seviyesi değişiklik yalnızca
    sahibi rehbere (öğrenci görevleri düzenler ama programın kendisini değil)."""
    message = "Program yalnızca sahibi rehber tarafından düzenlenebilir."

    def has_object_permission(self, request, view, obj) -> bool:
        is_student_owner, is_counselor_owner = _owns_program(request.user, obj)
        if request.method in SAFE_METHODS:
            return (is_student_owner or is_counselor_owner
                    or _is_parent_of_program(request.user, obj))
        return is_counselor_owner


class CanApproveProgram(BasePermission):
    """Haftalık onayı yalnızca programın sahibi rehber verebilir/geri alabilir."""
    message = "Programı yalnızca öğrencinin rehberi onaylayabilir."

    def has_object_permission(self, request, view, obj) -> bool:
        return _owns_program(request.user, obj)[1]


class IsGoalOwnerStudentOrReadOnly(BasePermission):
    """Hedef: sahibi öğrenci tam yetki; öğrencinin rehberi salt-okur.

    **Veli görmez** (E3 kapsam kararı, 29 Ağu 2026): hedef öğrencinin kendine
    koyduğu kişisel bir taahhüt; veli panelinde yer almıyor.
    """
    message = "Bu hedefe erişim yetkiniz yok."

    def has_object_permission(self, request, view, obj) -> bool:
        user = request.user
        # Sahibi öğrenci → her şey
        if _is_that_student(user, obj.student_id):
            return True
        # Öğrencinin rehberi → yalnızca okuma
        if request.method in SAFE_METHODS:
            return (
                getattr(user, 'is_counselor', False)
                and hasattr(user, 'counselor_profile')
                and obj.student.counselor_id == user.counselor_profile.id
            )
        return False


class IsBookOwnerStudentOrReadOnly(BasePermission):
    """Kitap: sahibi öğrenci tam yetki; öğrencinin rehberi salt-okur.

    **Veli görmez** (kullanıcı kararı, 29 Ağu 2026 — E3): kitaplık öğrencinin
    kendi çalışma alanıdır, veli panelinin kapsamı dışında.
    """
    message = "Bu kitaba erişim yetkiniz yok."

    def has_object_permission(self, request, view, obj) -> bool:
        user = request.user
        # Sahibi öğrenci → her şey
        if _is_that_student(user, obj.student_id):
            return True
        # Öğrencinin rehberi → yalnızca okuma
        if request.method in SAFE_METHODS:
            return (
                getattr(user, 'is_counselor', False)
                and hasattr(user, 'counselor_profile')
                and obj.student.counselor_id == user.counselor_profile.id
            )
        return False


class IsBookTopicOwnerStudentOrReadOnly(BasePermission):
    """Kitap konusu: kitabın sahibi öğrenci tam yetki; rehberi salt-okur.
    Veli, kitaplığın tamamı gibi bunu da görmez (E3)."""
    message = "Bu kitap konusuna erişim yetkiniz yok."

    def has_object_permission(self, request, view, obj) -> bool:
        user = request.user
        student_id = obj.book.student_id
        # Sahibi öğrenci → her şey
        if _is_that_student(user, student_id):
            return True
        # Öğrencinin rehberi → yalnızca okuma
        if request.method in SAFE_METHODS:
            return (
                getattr(user, 'is_counselor', False)
                and hasattr(user, 'counselor_profile')
                and obj.book.student.counselor_id == user.counselor_profile.id
            )
        return False


class IsTopicProgressOwnerStudentOrReadOnly(BasePermission):
    """Konu ilerlemesi: sahibi öğrenci ve öğrencinin rehberi tam yetki (rehber
    hâkimiyet seviyesini girer/düzenler); velisi salt-okur."""
    message = "Bu konu ilerlemesine erişim yetkiniz yok."

    def has_object_permission(self, request, view, obj) -> bool:
        user = request.user
        # Sahibi öğrenci → her şey
        if _is_that_student(user, obj.student_id):
            return True
        # Öğrencinin rehberi → tam yetki (seviye düzenleme dahil)
        if (getattr(user, 'is_counselor', False) and hasattr(user, 'counselor_profile')
                and obj.student.counselor_id == user.counselor_profile.id):
            return True
        # Velisi → yalnızca okuma
        if request.method in SAFE_METHODS:
            return _is_that_students_parent(user, obj.student_id)
        return False


class IsCalendarOwnerOrTargetRead(BasePermission):
    """Takvim etkinliği: sahibi rehber tam yetki; etkinliğe bağlı öğrenci (ve
    velisi) salt-okur. `student` boş etkinlikler yalnızca sahibi rehbere görünür."""
    message = "Bu takvim etkinliğine erişim yetkiniz yok."

    def has_object_permission(self, request, view, obj) -> bool:
        user = request.user
        is_owner = (
            getattr(user, 'is_counselor', False)
            and hasattr(user, 'counselor_profile')
            and obj.counselor_id == user.counselor_profile.id
        )
        if is_owner:
            return True
        if request.method in SAFE_METHODS:
            return _is_that_student(user, obj.student_id) or \
                _is_that_students_parent(user, obj.student_id)
        return False
