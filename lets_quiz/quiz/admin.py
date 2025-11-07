from django.contrib import admin

from .models import Question, Choice, Quiz, QuizQuestion, QuizAttempt
from .forms import QuestionForm, ChoiceForm, ChoiceInlineFormset
# Register your models here.

class QuizQuestionInline(admin.TabularInline):
    model = QuizQuestion
    extra = 1

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'is_published', 'time_limit_seconds', 'immediate_feedback')
    inlines = [QuizQuestionInline]

@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('quiz', 'user', 'started_at', 'finished_at', 'total_score', 'is_finished')

class ChoiceInline(admin.TabularInline):
    model = Choice
    can_delete = False
    max_num = Choice.MAX_CHOICES_COUNT
    min_num = Choice.MAX_CHOICES_COUNT
    form = ChoiceForm
    formset = ChoiceInlineFormset


class QuestionAdmin(admin.ModelAdmin):
    model = Question
    inlines = (ChoiceInline, )
    list_display = ['html', 'is_published']
    list_filter = ['is_published', 'is_multiple_choice']
    search_fields = ['html', 'choices__html']
    actions = None
    form = QuestionForm

    # def has_delete_permission(self, request, obj=None):
    #     return False

    # def has_change_permission(self, request, obj=None):
    #     if obj is not None and obj.pk is not None and obj.is_published is True:
    #         return False
    #     return True


admin.site.register(Question, QuestionAdmin)

