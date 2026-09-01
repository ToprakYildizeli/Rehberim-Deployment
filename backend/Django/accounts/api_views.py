from rest_framework import status
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import Counselor
from .permissions import IsCounselor, IsParent, IsStudent
from .serializers import (
    ConnectCounselorSerializer,
    ConnectStudentSerializer,
    CounselorRegisterSerializer,
    CounselorStudentSerializer,
    MeUpdateSerializer,
    ParentRegisterSerializer,
    RehberimTokenObtainPairSerializer,
    StudentRegisterSerializer,
    UserSerializer,
)


def tokens_for(user):
    """Bir kullanıcı için access+refresh üretir ve kullanıcı objesiyle döner."""
    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "user": UserSerializer(user).data,
    }


class LoginView(TokenObtainPairView):
    """POST /api/auth/login/ — access+refresh+user döner."""
    serializer_class = RehberimTokenObtainPairSerializer


class LogoutView(APIView):
    """POST /api/auth/logout/ — refresh token'ı blacklist'e alır."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            RefreshToken(request.data["refresh"]).blacklist()
        except (KeyError, TokenError):
            return Response(
                {"detail": "Geçersiz veya eksik refresh token."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_205_RESET_CONTENT)


class MeView(APIView):
    """GET /api/auth/me/ — giriş yapan kullanıcı + rol + profil.
    PATCH /api/auth/me/ — kendi ad/soyad/e-postasını günceller."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        serializer = MeUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        # GET ile aynı gövdeyi döndür ki istemci tek şekil bilsin.
        return Response(UserSerializer(request.user).data)


class BaseRegisterView(CreateAPIView):
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(tokens_for(user), status=status.HTTP_201_CREATED)


class CounselorRegisterView(BaseRegisterView):
    serializer_class = CounselorRegisterSerializer


class StudentRegisterView(BaseRegisterView):
    serializer_class = StudentRegisterSerializer


class ParentRegisterView(BaseRegisterView):
    serializer_class = ParentRegisterSerializer


class CounselorStudentsView(ListAPIView):
    """GET /api/students/ — rehberin kendi öğrencileri (program/ödev için seçim listesi)."""
    serializer_class = CounselorStudentSerializer
    permission_classes = [IsCounselor]

    def get_queryset(self):
        return self.request.user.counselor_profile.students.select_related('user').all()


class ConnectCounselorView(APIView):
    """POST /api/students/connect-counselor/ — öğrenci rehbere bağlanır."""
    permission_classes = [IsStudent]

    def post(self, request):
        serializer = ConnectCounselorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        counselor = Counselor.objects.get(invite_code=serializer.validated_data["code"])
        student = request.user.student_profile
        student.counselor = counselor
        student.save()
        return Response({
            "counselor": {"id": counselor.id, "name": counselor.user.get_full_name()},
        })


class ConnectStudentView(APIView):
    """POST /api/parents/connect-student/ — veli çocuğuna bağlanır (E3).

    Gövde: `{"student": <öğrenci id>, "counselor_code": "<rehberin davet kodu>"}`.
    Eskiden öğrencinin `connect_code`'u isteniyordu; artık kimlik ikilisi
    öğrenci numarası + rehber kodudur (bkz. `ParentLinkMixin`).
    """
    permission_classes = [IsParent]

    def post(self, request):
        serializer = ConnectStudentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        student = serializer.validated_data["student_obj"]
        request.user.parent_profile.students.add(student)
        return Response({
            "student": {"id": student.id, "name": student.user.get_full_name()},
            "counselor": {
                "id": student.counselor_id,
                "name": student.counselor.user.get_full_name(),
            },
        })
