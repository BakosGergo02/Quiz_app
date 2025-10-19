import random
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext as _
from model_utils.models import TimeStampedModel
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)

class Question(TimeStampedModel):
    ALLOWED_NUMBER_OF_CORRECT_CHOICES = 1

    html = models.TextField(_('Question Text'))
    is_published = models.BooleanField(_('Has been published?'), default=False, null=False)
    maximum_marks = models.DecimalField(_('Maximum Marks'), default=4, decimal_places=2, max_digits=6)

    is_multiple_choice = models.BooleanField(default=False)

    def __str__(self):
        return self.html[:50]


class Choice(TimeStampedModel):
    MAX_CHOICES_COUNT = 4

    question = models.ForeignKey(Question, related_name='choices', on_delete=models.CASCADE)
    is_correct = models.BooleanField(_('Is this answer correct?'), default=False, null=False)
    html = models.TextField(_('Choice Text'))

    def __str__(self):
        return self.html


class QuizProfile(TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    total_score = models.DecimalField(_('Total Score'), default=0, decimal_places=2, max_digits=10)

    def __str__(self):
        return f'<QuizProfile: user={self.user}>'

    def get_new_question(self):
        used_questions_pk = AttemptedQuestion.objects.filter(quiz_profile=self).values_list('question__pk', flat=True)
        remaining_questions = Question.objects.exclude(pk__in=used_questions_pk)
        if not remaining_questions.exists():
            return
        return random.choice(remaining_questions)

    def create_attempt(self, question):
        attempted_question = AttemptedQuestion(question=question, quiz_profile=self)
        attempted_question.save()

    def evaluate_attempt(self, attempted_question, selected_choices):
        """
        selected_choices: iterable of Choice objects or QuerySet
        """
        question = attempted_question.question

        # Normalize selected_choices to a list
        try:
            selected_list = list(selected_choices)
        except Exception:
            selected_list = [selected_choices] if selected_choices else []

        chosen_ids = set(int(c.pk) for c in selected_list if c is not None)
        correct_ids = set(question.choices.filter(is_correct=True).values_list('pk', flat=True))

        # --- DEBUG prints ---
        print("### EVAL DEBUG: Question ID:", question.pk)
        print("### EVAL DEBUG: Correct IDs:", correct_ids)
        print("### EVAL DEBUG: Chosen IDs:", chosen_ids)

        # Save selected choices
        attempted_question.selected_choices.set(selected_list)

        # --- Evaluation logic ---
        if not question.is_multiple_choice:
            print("### EVAL DEBUG: SINGLE mode")
            if len(chosen_ids) == 1 and list(chosen_ids)[0] in correct_ids:
                attempted_question.is_correct = True
                attempted_question.marks_obtained = question.maximum_marks
            else:
                attempted_question.is_correct = False
                attempted_question.marks_obtained = 0
        else:
            print("### EVAL DEBUG: MULTIPLE mode")
            correct_selected = len(chosen_ids & correct_ids)
            incorrect_selected = len(chosen_ids - correct_ids)
            total_correct = len(correct_ids)

            print(f"### EVAL DEBUG: correct_selected={correct_selected}, incorrect_selected={incorrect_selected}, total_correct={total_correct}")

            if correct_selected == total_correct and incorrect_selected == 0:
                attempted_question.is_correct = True
                attempted_question.marks_obtained = question.maximum_marks
            else:
                ratio = (correct_selected / total_correct) if total_correct > 0 else 0
                attempted_question.is_correct = False
                attempted_question.marks_obtained = round(float(question.maximum_marks) * ratio, 2)

        attempted_question.save(update_fields=['is_correct', 'marks_obtained'])

        print(f"### EVAL DEBUG RESULT: is_correct={attempted_question.is_correct}, marks={attempted_question.marks_obtained}")
        self.update_score()

    def update_score(self):
        total_score = self.attempts.aggregate(
            total=models.Sum('marks_obtained')
        )['total'] or 0
        self.total_score = total_score
        self.save(update_fields=['total_score'])


class AttemptedQuestion(TimeStampedModel):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    quiz_profile = models.ForeignKey(QuizProfile, on_delete=models.CASCADE, related_name='attempts')
    selected_choices = models.ManyToManyField(Choice, blank=True)
    is_correct = models.BooleanField(_('Was this attempt correct?'), default=False, null=False)
    marks_obtained = models.DecimalField(_('Marks Obtained'), default=0, decimal_places=2, max_digits=6)
    def __str__(self):
        return f"{self.quiz_profile.user.username} - {self.question.html[:50]}"
    def get_absolute_url(self):
        return f'/submission-result/{self.pk}/'
