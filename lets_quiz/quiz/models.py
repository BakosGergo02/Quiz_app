import random
from django.db import models
from django.contrib.auth.models import User, Group
from django.utils.translation import gettext as _
from model_utils.models import TimeStampedModel
from django.conf import settings
from django.utils import timezone
import logging
from decimal import Decimal
from django.db import models



logger = logging.getLogger(__name__)

User = settings.AUTH_USER_MODEL

class Quiz(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    time_limit_seconds = models.PositiveIntegerField(default=0)
    immediate_feedback = models.BooleanField(default=False)
    allow_multiple_attempts = models.BooleanField(default=True)
    is_published = models.BooleanField(default=False)


    allowed_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='quizzes_allowed',
        blank=True,
        help_text="Azok a felhasználók, akik kitölthetik ezt a kvízt."
    )

    allowed_groups = models.ManyToManyField(
        Group,
        related_name='quizzes_allowed',
        blank=True,
        help_text="Azok a csoportok, amelyek tagjai kitölthetik a kvízt."
    )
    
    def get_questions(self):
        return [qq.question for qq in self.quiz_questions.all()]

    def __str__(self):
        return self.title

    

class QuizQuestion(models.Model):
    """
    Egy QuizQuestion csupán a sorrendet és a kapcsolatot tárolja
    a Quiz és egy Question között.
    """
    quiz = models.ForeignKey(Quiz, related_name='quiz_questions', on_delete=models.CASCADE)
    question = models.ForeignKey('Question', related_name='quizquestions', on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('quiz', 'order')
        ordering = ['order']

    def __str__(self):
        return f"{self.quiz.title} - Q#{self.order} ({self.question.pk})"
    

class QuizAttempt(models.Model):
    """
    Egy felhasználó egy adott Quiz-el kapcsolatos futása (session).
    Itt nyomon követjük a kezdést, befejezést, összpontot, és ha kell, a hátralévő időt.
    """
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_attempts')
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    current_index = models.IntegerField(default=0)  # hányadik kérdésnél tart (0-based)
    total_score = models.DecimalField(default=Decimal('0.00'), decimal_places=2, max_digits=10)
    is_finished = models.BooleanField(default=False)

    def time_left(self):
        """Ha van time_limit a quiz-en, mennyi van még (másodperc)"""
        if self.quiz.time_limit_seconds <= 0:
            return None
        elapsed = (timezone.now() - self.started_at).total_seconds()
        remaining = self.quiz.time_limit_seconds - elapsed
        return max(0, int(remaining))

    def finish(self):
        self.is_finished = True
        self.finished_at = timezone.now()
        # összesítés: AttemptedQuestion-ök alapján (ha ilyeneket használsz)
        total = self.attempted_questions.aggregate(total=models.Sum('marks_obtained'))['total'] or 0
        self.total_score = total
        self.save(update_fields=['is_finished', 'finished_at', 'total_score'])

    def __str__(self):
        return f"{self.user.username} - {self.quiz.title} - started {self.started_at}"

class Question(TimeStampedModel):
    ALLOWED_NUMBER_OF_CORRECT_CHOICES = 1

    quiz = models.ForeignKey(
        Quiz,
        related_name='questions',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    html = models.TextField(_('Kérdés szövege'))
    is_published = models.BooleanField(_('Has been published?'), default=False, null=False)
    maximum_marks = models.DecimalField(_('Maximum Pontszám'), default=4, decimal_places=2, max_digits=6)

    is_multiple_choice = models.BooleanField(default=False)
    correct_text_answer = models.CharField(
        max_length=255, blank=True, null=True,
        help_text="Ha szöveges kérdés, ide írd a helyes választ."
    )

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
        return attempted_question

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

class MatchingPair(models.Model):
    question = models.ForeignKey(
        Question,
        related_name='matching_pairs',
        on_delete=models.CASCADE
    )
    left_text = models.CharField(max_length=255)
    right_text = models.CharField(max_length=255)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.left_text} ⇔ {self.right_text}"


class AttemptedQuestion(TimeStampedModel):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    quiz_profile = models.ForeignKey(QuizProfile, on_delete=models.CASCADE, related_name='attempts')
    selected_choices = models.ManyToManyField(Choice, blank=True)
    is_correct = models.BooleanField(_('Was this attempt correct?'), default=False, null=False)
    marks_obtained = models.DecimalField(_('Marks Obtained'), default=0, decimal_places=2, max_digits=6)

    text_answer = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.quiz_profile.user.username} - {self.question.html[:50]}"
    
    def get_absolute_url(self):
        return f'/submission-result/{self.pk}/'
    

class AttemptedMatch(models.Model):
    attempted_question = models.ForeignKey(
        AttemptedQuestion,
        related_name='attempted_matches',
        on_delete=models.CASCADE
    )
    left_pair = models.ForeignKey(
        MatchingPair,
        related_name='+',
        on_delete=models.CASCADE
    )
    chosen_right_pair = models.ForeignKey(
        MatchingPair,
        related_name='+',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        unique_together = ('attempted_question', 'left_pair')

    def __str__(self):
        return f"{self.attempted_question_id} – {self.left_pair_id} -> {self.chosen_right_pair_id}"


