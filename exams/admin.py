from django.contrib import admin

from .models import Answer, Attempt, Choice, Question, Test


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 0


class QuestionAdmin(admin.ModelAdmin):
    list_display = ("text", "test", "points")
    inlines = [ChoiceInline]


class QuestionInline(admin.StackedInline):
    model = Question
    extra = 0
    show_change_link = True


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ("title", "teacher", "subject", "is_published", "created_at")
    inlines = [QuestionInline]


admin.site.register(Question, QuestionAdmin)


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0


@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display = ("student", "test", "score", "max_score", "finished_at")
    list_filter = ("test",)
    inlines = [AnswerInline]
