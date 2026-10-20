"""Views for self-registration and admin approval workflow."""
from drf_spectacular.utils import extend_schema
from rest_framework import generics, serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts import registration_services as svc
from accounts.models import RegistrationRequest, RegistrationStatus
from accounts.permissions import IsAdminOrSubAdmin


# ── Serializers ───────────────────────────────────────────────────────────────

class RegistrationSubmitSerializer(serializers.ModelSerializer):
    password         = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model  = RegistrationRequest
        fields = [
            "first_name", "last_name", "email", "phone_number",
            "requested_role", "department", "position", "message",
            "password", "confirm_password",
        ]

    def validate_email(self, value):
        from accounts.models import User
        if User.objects.filter(email=value.lower().strip()).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        if RegistrationRequest.objects.filter(email=value.lower().strip(), status=RegistrationStatus.PENDING).exists():
            raise serializers.ValidationError("A pending registration request already exists for this email.")
        return value.lower().strip()

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("confirm_password"):
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return attrs


class RegistrationRequestSerializer(serializers.ModelSerializer):
    department_name  = serializers.CharField(source="department.name",  read_only=True)
    position_name    = serializers.CharField(source="position.name",    read_only=True)
    reviewed_by_name = serializers.SerializerMethodField()

    class Meta:
        model  = RegistrationRequest
        fields = [
            "id", "first_name", "last_name", "email", "phone_number",
            "requested_role", "department", "department_name",
            "position", "position_name", "message",
            "status", "reviewed_by", "reviewed_by_name",
            "reviewed_at", "rejection_reason",
            "submitted_at", "updated_at",
        ]
        read_only_fields = fields

    def get_reviewed_by_name(self, obj):
        return obj.reviewed_by.get_full_name() if obj.reviewed_by else None


class ApproveRegistrationSerializer(serializers.Serializer):
    pass   # no extra body needed


class RejectRegistrationSerializer(serializers.Serializer):
    reason = serializers.CharField(min_length=5, help_text="Reason for rejection")


# ── Views ─────────────────────────────────────────────────────────────────────

@extend_schema(tags=["registration"])
class RegisterView(APIView):
    """Public — anyone can submit a registration request."""
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        s = RegistrationSubmitSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        req = svc.submit_registration(
            first_name=d["first_name"],
            last_name=d["last_name"],
            email=d["email"],
            phone_number=d.get("phone_number", ""),
            requested_role=d.get("requested_role", "EMPLOYEE"),
            department=d.get("department"),
            position=d.get("position"),
            message=d.get("message", ""),
            raw_password=d["password"],
        )
        return Response(
            {
                "detail": "Registration request submitted successfully. "
                          "You will be notified once an administrator reviews it.",
                "request_id": req.pk,
                "email": req.email,
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=["registration"])
class RegistrationRequestListView(generics.ListAPIView):
    """List all registration requests. Admin/Sub-Admin only."""
    permission_classes   = [IsAuthenticated, IsAdminOrSubAdmin]
    serializer_class     = RegistrationRequestSerializer
    filterset_fields     = ["status", "requested_role"]
    search_fields        = ["first_name", "last_name", "email"]
    ordering             = ["-submitted_at"]

    def get_queryset(self):
        return RegistrationRequest.objects.select_related(
            "department", "position", "reviewed_by", "created_user"
        ).all()


@extend_schema(tags=["registration"])
class RegistrationRequestDetailView(generics.RetrieveAPIView):
    """Retrieve a single registration request. Admin/Sub-Admin only."""
    permission_classes = [IsAuthenticated, IsAdminOrSubAdmin]
    serializer_class   = RegistrationRequestSerializer
    queryset           = RegistrationRequest.objects.select_related(
        "department", "position", "reviewed_by"
    ).all()


@extend_schema(tags=["registration"])
class ApproveRegistrationView(APIView):
    """Approve a pending registration → creates User account. Admin/Sub-Admin only."""
    permission_classes = [IsAuthenticated, IsAdminOrSubAdmin]

    def post(self, request: Request, pk: int) -> Response:
        try:
            reg_req = RegistrationRequest.objects.get(pk=pk)
        except RegistrationRequest.DoesNotExist:
            return Response({"detail": "Not found."}, status=404)
        req = svc.approve_registration(reg_req, request.user)
        return Response(
            {
                "detail": f"Registration approved. User account created for {req.email}.",
                "created_user_id": req.created_user_id,
            }
        )


@extend_schema(tags=["registration"])
class RejectRegistrationView(APIView):
    """Reject a pending registration. Admin/Sub-Admin only."""
    permission_classes = [IsAuthenticated, IsAdminOrSubAdmin]

    def post(self, request: Request, pk: int) -> Response:
        try:
            reg_req = RegistrationRequest.objects.get(pk=pk)
        except RegistrationRequest.DoesNotExist:
            return Response({"detail": "Not found."}, status=404)
        s = RejectRegistrationSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        svc.reject_registration(reg_req, request.user, s.validated_data["reason"])
        return Response({"detail": "Registration request rejected."})


@extend_schema(tags=["registration"])
class PendingRegistrationCountView(APIView):
    """Quick count of pending requests for the badge on nav. Admin/Sub-Admin only."""
    permission_classes = [IsAuthenticated, IsAdminOrSubAdmin]

    def get(self, request: Request) -> Response:
        count = RegistrationRequest.objects.filter(status=RegistrationStatus.PENDING).count()
        return Response({"pending_count": count})
