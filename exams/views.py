from django.db import IntegrityError, transaction
from django.db.models import Count
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.models import User

from .models import Answer, Attempt, Test
from .permissions import IsStudent, IsTeacher
from .serializers import (
    AttemptDetailSerializer,
    AttemptSerializer,
    StudentDetailSerializer,
    StudentSerializer,
    SubmitSerializer,
    TestListSerializer,
    TestStudentSerializer,
    TestTeacherSerializer,
)


class TestViewSet(viewsets.ModelViewSet):
    """
    O'qituvchi: o'z testlarini yaratadi / tahrirlaydi / o'chiradi / natijalarini ko'radi.
    O'quvchi: e'lon qilingan testlarni ko'radi va ishlaydi (submit).
    """

    def get_queryset(self):
        user = self.request.user
        qs = (
            Test.objects.select_related("teacher")
            .annotate(
                question_count=Count("questions", distinct=True),
                attempts_count=Count("attempts", distinct=True),
            )
            .prefetch_related("questions__choices")
        )
        if user.is_teacher:
            return qs.filter(teacher=user)
        return qs.filter(is_published=True)

    def get_serializer_class(self):
        if self.action == "list":
            return TestListSerializer
        if self.request.user.is_teacher:
            return TestTeacherSerializer
        return TestStudentSerializer

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy", "results"):
            return [IsAuthenticated(), IsTeacher()]
        if self.action == "submit":
            return [IsAuthenticated(), IsStudent()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(teacher=self.request.user)

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        test = self.get_object()
        if Attempt.objects.filter(test=test, student=request.user).exists():
            return Response({"detail": "Siz bu testni allaqachon ishlagansiz."}, status=400)

        serializer = SubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        given = {a["question"]: a.get("choice") for a in serializer.validated_data["answers"]}

        questions = list(test.questions.prefetch_related("choices"))
        score = 0
        max_score = sum(q.points for q in questions)
        answers = []
        for q in questions:
            choices = {c.id: c for c in q.choices.all()}
            choice = choices.get(given.get(q.id))
            correct = bool(choice and choice.is_correct)
            if correct:
                score += q.points
            answers.append(Answer(question=q, choice=choice, is_correct=correct))

        try:
            with transaction.atomic():
                attempt = Attempt.objects.create(
                    test=test,
                    student=request.user,
                    score=score,
                    max_score=max_score,
                    finished_at=timezone.now(),
                )
                for a in answers:
                    a.attempt = attempt
                Answer.objects.bulk_create(answers)
        except IntegrityError:
            return Response({"detail": "Siz bu testni allaqachon ishlagansiz."}, status=400)

        return Response(AttemptSerializer(attempt).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"])
    def results(self, request, pk=None):
        test = self.get_object()
        attempts = test.attempts.select_related("student", "test")
        return Response(AttemptSerializer(attempts, many=True).data)


class AttemptViewSet(viewsets.ReadOnlyModelViewSet):
    """O'qituvchi: o'z testlari bo'yicha barcha natijalar. O'quvchi: faqat o'ziniki."""

    def get_queryset(self):
        user = self.request.user
        qs = Attempt.objects.select_related("student", "test")
        qs = qs.filter(test__teacher=user) if user.is_teacher else qs.filter(student=user)
        test_id = self.request.query_params.get("test")
        student_id = self.request.query_params.get("student")
        if test_id:
            qs = qs.filter(test_id=test_id)
        if student_id and user.is_teacher:
            qs = qs.filter(student_id=student_id)
        return qs

    def get_serializer_class(self):
        return AttemptDetailSerializer if self.action == "retrieve" else AttemptSerializer


class StudentViewSet(viewsets.ReadOnlyModelViewSet):
    """O'qituvchi paneli: o'quvchilar ro'yxati va ularning natijalari."""

    permission_classes = [IsAuthenticated, IsTeacher]

    def get_queryset(self):
        qs = User.objects.filter(role=User.STUDENT).prefetch_related("attempts__test")
        school_class = self.request.query_params.get("school_class")
        if school_class:
            qs = qs.filter(school_class=school_class)
        return qs.order_by("school_class", "full_name")

    def get_serializer_class(self):
        return StudentDetailSerializer if self.action == "retrieve" else StudentSerializer
