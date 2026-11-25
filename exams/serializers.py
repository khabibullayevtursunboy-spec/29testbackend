from django.db import transaction
from rest_framework import serializers

from accounts.models import User

from .models import Answer, Attempt, Choice, Question, Test


# ---------- Choices / Questions ----------
class ChoiceTeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ["id", "text", "is_correct"]


class ChoiceStudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ["id", "text"]


class QuestionTeacherSerializer(serializers.ModelSerializer):
    choices = ChoiceTeacherSerializer(many=True)

    class Meta:
        model = Question
        fields = ["id", "text", "order", "points", "choices"]
        extra_kwargs = {"order": {"required": False}}


class QuestionStudentSerializer(serializers.ModelSerializer):
    choices = ChoiceStudentSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ["id", "text", "order", "points", "choices"]


# ---------- Tests ----------
class TestListSerializer(serializers.ModelSerializer):
    teacher_name = serializers.SerializerMethodField()
    question_count = serializers.IntegerField(read_only=True)
    attempts_count = serializers.IntegerField(read_only=True)
    already_taken = serializers.SerializerMethodField()

    class Meta:
        model = Test
        fields = [
            "id", "title", "description", "subject", "duration_minutes", "is_published",
            "teacher_name", "question_count", "attempts_count", "already_taken", "created_at",
        ]

    def get_teacher_name(self, obj):
        return obj.teacher.full_name or obj.teacher.username

    def get_already_taken(self, obj):
        user = self.context["request"].user
        if not user.is_student:
            return False
        return obj.attempts.filter(student=user).exists()


class TestStudentSerializer(TestListSerializer):
    questions = QuestionStudentSerializer(many=True, read_only=True)

    class Meta(TestListSerializer.Meta):
        fields = TestListSerializer.Meta.fields + ["questions"]


class TestTeacherSerializer(TestListSerializer):
    questions = QuestionTeacherSerializer(many=True)

    class Meta(TestListSerializer.Meta):
        fields = TestListSerializer.Meta.fields + ["questions"]

    def validate_questions(self, questions):
        if not questions:
            raise serializers.ValidationError("Kamida bitta savol bo'lishi kerak.")
        for i, q in enumerate(questions, start=1):
            choices = q.get("choices", [])
            if len(choices) < 2:
                raise serializers.ValidationError(f"{i}-savolda kamida 2 ta variant bo'lishi kerak.")
            if not any(c.get("is_correct") for c in choices):
                raise serializers.ValidationError(f"{i}-savolda to'g'ri javob belgilanmagan.")
        return questions

    @staticmethod
    def _save_questions(test, questions_data):
        for i, q in enumerate(questions_data):
            choices = q.pop("choices")
            question = Question.objects.create(
                test=test,
                text=q["text"],
                order=q.get("order", i),
                points=q.get("points", 1),
            )
            Choice.objects.bulk_create([Choice(question=question, **c) for c in choices])

    @transaction.atomic
    def create(self, validated_data):
        questions_data = validated_data.pop("questions")
        test = Test.objects.create(**validated_data)
        self._save_questions(test, questions_data)
        return test

    @transaction.atomic
    def update(self, instance, validated_data):
        questions_data = validated_data.pop("questions", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if questions_data is not None:
            if instance.attempts.exists():
                raise serializers.ValidationError(
                    {"questions": "Bu testni o'quvchilar ishlagan, savollarni o'zgartirib bo'lmaydi."}
                )
            instance.questions.all().delete()
            self._save_questions(instance, questions_data)
        return instance


# ---------- Submit ----------
class SubmitAnswerSerializer(serializers.Serializer):
    question = serializers.IntegerField()
    choice = serializers.IntegerField(allow_null=True, required=False)


class SubmitSerializer(serializers.Serializer):
    answers = SubmitAnswerSerializer(many=True)


# ---------- Attempts ----------
class AttemptSerializer(serializers.ModelSerializer):
    test_title = serializers.CharField(source="test.title", read_only=True)
    student_name = serializers.SerializerMethodField()
    student_username = serializers.CharField(source="student.username", read_only=True)
    student_class = serializers.CharField(source="student.school_class", read_only=True)
    percent = serializers.SerializerMethodField()

    class Meta:
        model = Attempt
        fields = [
            "id", "test", "test_title", "student", "student_name", "student_username",
            "student_class", "score", "max_score", "percent", "started_at", "finished_at",
        ]

    def get_student_name(self, obj):
        return obj.student.full_name or obj.student.username

    def get_percent(self, obj):
        return round(obj.score * 100 / obj.max_score, 1) if obj.max_score else 0


class AnswerSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source="question.text", read_only=True)
    choice_text = serializers.SerializerMethodField()

    class Meta:
        model = Answer
        fields = ["question", "question_text", "choice", "choice_text", "is_correct"]

    def get_choice_text(self, obj):
        return obj.choice.text if obj.choice else None


class AttemptDetailSerializer(AttemptSerializer):
    answers = AnswerSerializer(many=True, read_only=True)

    class Meta(AttemptSerializer.Meta):
        fields = AttemptSerializer.Meta.fields + ["answers"]


# ---------- Students (teacher panel) ----------
class StudentSerializer(serializers.ModelSerializer):
    attempts_count = serializers.SerializerMethodField()
    average_percent = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "full_name", "school_class", "attempts_count", "average_percent"]

    def _attempts(self, obj):
        return list(obj.attempts.all())

    def get_attempts_count(self, obj):
        return len(self._attempts(obj))

    def get_average_percent(self, obj):
        attempts = [a for a in self._attempts(obj) if a.max_score]
        if not attempts:
            return 0
        return round(sum(a.score * 100 / a.max_score for a in attempts) / len(attempts), 1)


class StudentDetailSerializer(StudentSerializer):
    attempts = AttemptSerializer(many=True, read_only=True)

    class Meta(StudentSerializer.Meta):
        fields = StudentSerializer.Meta.fields + ["attempts"]
