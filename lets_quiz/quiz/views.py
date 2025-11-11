from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from .models import QuizProfile, Quiz, AttemptedQuestion, QuizQuestion, Choice
from .forms import UserLoginForm, RegistrationForm, QuizCreateForm, SingleChoiceQuestionForm, MultipleChoiceQuestionForm, TextQuestionForm
from django.db.models import Max
from django.db import models

@login_required
def create_quiz(request):

    user = request.user
    is_teacher = user.is_superuser or user.groups.filter(name='Tanár').exists()

    if not is_teacher:
        messages.error(request, "Nincs jogosultságod kvízt létrehozni.")
        return redirect('quiz:home')

    if request.method == 'POST':
        form = QuizCreateForm(request.POST)
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.created_by = request.user
            quiz.save()
            form.save_m2m()
            messages.success(request, f'A "{quiz.title}" kvíz sikeresen létrejött!')
            return redirect('quiz:quiz_settings', quiz_id=quiz.id)
    else:
        form = QuizCreateForm()

    return render(request, 'quiz/quiz_create.html', {'form': form})

@login_required
def quiz_list(request):
    # csak tanár vagy superuser
    is_teacher = request.user.is_superuser or request.user.groups.filter(name='Tanár').exists()
    if not is_teacher:
        messages.error(request, "Nincs jogosultságod a kvízek kezeléséhez.")
        return redirect('quiz:home')

    # ha akarod, itt lehetne szűrni created_by szerint is
    quizzes = Quiz.objects.all().order_by('-created_at')

    return render(request, 'quiz/quiz_list.html', {
        'quizzes': quizzes,
    })

from django.contrib.auth.models import User, Group

@login_required
def manage_user_groups(request):
    # csak tanár vagy superuser
    is_teacher = request.user.is_superuser or request.user.groups.filter(name='Tanár').exists()
    if not is_teacher:
        messages.error(request, "Nincs jogosultságod a felhasználók csoportjainak kezeléséhez.")
        return redirect('quiz:home')

    users = User.objects.all().order_by('username')
    groups = Group.objects.all().order_by('name')

    if request.method == 'POST':
        # azt várjuk, hogy minden userhez jön egy többes listamező:
        # name="groups_<user_id>"
        for user in users:
            field_name = f"groups_{user.id}"
            group_ids = request.POST.getlist(field_name)
            # beállítjuk az adott user csoportjait a beküldött listára
            user.groups.set(group_ids)
        messages.success(request, "Csoporttagságok mentve.")
        return redirect('quiz:manage_user_groups')

    return render(request, 'quiz/manage_user_groups.html', {
        'users': users,
        'groups': groups,
    })


@login_required
def select_question_type(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)

    if request.method == 'POST':
        q_type = request.POST.get('question_type')
        if q_type == 'single':
            return redirect('quiz:add_single_question', quiz_id=quiz.id)
        elif q_type == 'multiple':
            return redirect('quiz:add_multiple_question', quiz_id=quiz.id)
        elif q_type == 'text':
            return redirect('quiz:add_text_question', quiz_id=quiz.id)
        else:
            messages.error(request, "Ismeretlen kérdéstípus.")
    
    return render(request, 'quiz/select_question_type.html', {'quiz': quiz})

@login_required
def add_single_question(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)

    if request.method == "POST":
        form = SingleChoiceQuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.is_multiple_choice = False
            question.save()

            # --- ✅ Válaszok létrehozása ---
            options = [
                form.cleaned_data["option1"],
                form.cleaned_data["option2"],
                form.cleaned_data.get("option3"),
                form.cleaned_data.get("option4"),
            ]

            correct_index = int(form.cleaned_data["correct_option"])


            for index, opt_text in enumerate(options, start=1):
                if opt_text:
                    Choice.objects.create(
                        question=question,
                        html=opt_text,
                        is_correct=(index == correct_index)
                    )
            max_order = QuizQuestion.objects.filter(quiz=quiz).aggregate(Max('order'))['order__max'] or 0

            QuizQuestion.objects.create(
                quiz=quiz,
                question=question,
                order=max_order + 1
            )
            
            return redirect("quiz:quiz_settings", quiz_id=quiz.id)
    else:
        form = SingleChoiceQuestionForm()

    return render(request, "quiz/add_single_question.html", {"form": form, "quiz": quiz})



@login_required
def add_multiple_question(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)

    if request.method == "POST":
        form = MultipleChoiceQuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.is_multiple_choice = True
            question.save()

            # --- ✅ Válaszok létrehozása ---
            options = [
                form.cleaned_data["option1"],
                form.cleaned_data["option2"],
                form.cleaned_data.get("option3"),
                form.cleaned_data.get("option4"),
            ]

            correct_list = [int(i) for i in form.cleaned_data["correct_options"] or []]

            for index, opt_text in enumerate(options, start=1):
                if opt_text:
                    Choice.objects.create(
                        question=question,
                        html=opt_text,
                        is_correct=(index in correct_list)
                    )
            
            max_order = QuizQuestion.objects.filter(quiz=quiz).aggregate(Max('order'))['order__max'] or 0

            QuizQuestion.objects.create(
                quiz=quiz,
                question=question,
                order=max_order + 1
            )

            return redirect("quiz:quiz_settings", quiz_id=quiz.id)
    else:
        form = MultipleChoiceQuestionForm()

    return render(request, "quiz/add_multiple_question.html", {"form": form, "quiz": quiz})

@login_required
def add_text_question(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)

    if request.method == "POST":
        form = TextQuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.is_multiple_choice = False
            question.save()

            # kérdést hozzákapcsoljuk a kvízhez
            max_order = QuizQuestion.objects.filter(quiz=quiz).aggregate(Max('order'))['order__max'] or 0
            QuizQuestion.objects.create(quiz=quiz, question=question, order=max_order + 1)

            messages.success(request, "Szöveges kérdés hozzáadva!")
            return redirect("quiz:quiz_settings", quiz_id=quiz.id)
    else:
        form = TextQuestionForm()

    return render(request, "quiz/add_text_question.html", {"form": form, "quiz": quiz})

def home(request):
    quizzes = get_accessible_quizzes_for_user(request.user)
    return render(request, 'quiz/home.html', {'quizzes': quizzes})


@login_required()
def user_home(request):
    quizzes = get_accessible_quizzes_for_user(request.user)
    return render(request, 'quiz/user_home.html', {'quizzes': quizzes})


def leaderboard(request):

    top_quiz_profiles = QuizProfile.objects.order_by('-total_score')[:500]
    total_count = top_quiz_profiles.count()
    context = {
        'top_quiz_profiles': top_quiz_profiles,
        'total_count': total_count,
    }
    return render(request, 'quiz/leaderboard.html', context=context)


@login_required()
def play(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    has_user_limit = quiz.allowed_users.exists()
    has_group_limit = quiz.allowed_groups.exists()

    if has_user_limit or has_group_limit:
        user_allowed = quiz.allowed_users.filter(id=request.user.id).exists()
        group_allowed = quiz.allowed_groups.filter(id__in=request.user.groups.values_list('id', flat=True)).exists()

        if not (user_allowed or group_allowed or request.user.is_superuser):
            from django.contrib import messages
            messages.error(request, "Ehhez a kvízhez nincs hozzáférésed.")
            return redirect('quiz:home')
    # --- innen mehet a te eddigi kódod ---

    request.session['current_quiz_id'] = quiz.id
    quiz_profile, created = QuizProfile.objects.get_or_create(user=request.user)

    paused = request.session.get('quiz_paused', False)
    if paused:
        remaining = request.session.get('paused_remaining', 0)
    else:
        # eredeti logika
        if 'quiz_start_time' not in request.session:
            request.session['quiz_start_time'] = timezone.now().timestamp()

        start_time = request.session['quiz_start_time']
        elapsed = timezone.now().timestamp() - start_time
        remaining = max(0, quiz.time_limit_seconds - int(elapsed))

    # ha bárhogy is számoltuk, de elfogyott:
    if quiz.time_limit_seconds > 0 and remaining <= 0:
        return redirect('quiz:quiz_end', quiz_id=quiz.id)

    if request.method == 'POST':
        question_pk = request.POST.get('question_pk')

        try:
            attempted_question = quiz_profile.attempts.select_related('question').get(question__pk=question_pk)
        except AttemptedQuestion.DoesNotExist:
            raise Http404("Nincs ilyen kérdéskísérlet")

        question = attempted_question.question

        # ... POST ágban, miután megvan: question = attempted_question.question

# 🔴 ha szöveges kérdés
        if question.correct_text_answer:
            
            user_text = request.POST.get('text_answer', '').strip()
            correct_text = (question.correct_text_answer or '').strip()

            # kisbetű-független összehasonlítás
            is_correct = user_text.lower() == correct_text.lower()

            attempted_question.text_answer = user_text
            attempted_question.is_correct = is_correct
            attempted_question.marks_obtained = question.maximum_marks if is_correct else 0
            attempted_question.save(update_fields=['text_answer', 'is_correct', 'marks_obtained'])

            # pontszám frissítés
            quiz_profile.update_score()

            if quiz.immediate_feedback:
                request.session['quiz_paused'] = True
                request.session['paused_remaining'] = remaining
                return redirect('quiz:submission_result', attempted_question.pk)
            else:
                return redirect('quiz:play', quiz_id=quiz.id)


        if question.is_multiple_choice:
            choice_pks = request.POST.getlist('choices')
        else:
            choice_pks = [request.POST.get('choice_pk')] if request.POST.get('choice_pk') else []

        selected_choices = question.choices.filter(pk__in=choice_pks)
        quiz_profile.evaluate_attempt(attempted_question, selected_choices)

        if quiz.immediate_feedback:
            # eltesszük a maradék időt
            request.session['quiz_paused'] = True
            request.session['paused_remaining'] = remaining
            return redirect('quiz:submission_result', attempted_question.pk)
        else:
            return redirect('quiz:play', quiz_id=quiz.id)

    else:
        # ha eddig pause-oltunk, akkor MOST megszüntetjük a pause-t
        if request.session.get('quiz_paused', False):
            request.session.pop('quiz_paused', None)
            # a paused_remaining maradhat, de nem muszáj

        quiz_questions = quiz.quiz_questions.all()
        answered_ids = quiz_profile.attempts.values_list('question_id', flat=True)
        next_quiz_question = quiz_questions.exclude(question__id__in=answered_ids).first()

        if next_quiz_question:
            # store the created AttemptedQuestion (create_attempt most now returns it)
            attempted_question = quiz_profile.create_attempt(next_quiz_question.question)
            context = {
                'question': next_quiz_question.question,
                'quiz': quiz,
                'attempted_question': attempted_question,
                'remaining_time': remaining,
                'choices': next_quiz_question.question.choices.all(),   # Helyes attr
            }
        else:
            return redirect('quiz:quiz_end', quiz_id=quiz.id)
        
        return render(request, 'quiz/play.html', context)
        

from django.contrib.auth.models import User, Group

@login_required
def quiz_settings_view(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = [qq.question for qq in quiz.quiz_questions.all()]

    # összes user és csoport a kiválasztáshoz
    all_users = User.objects.all().order_by('username')
    all_groups = Group.objects.all().order_by('name')

    if request.method == 'POST':
        # user-ek
        selected_user_ids = request.POST.getlist('allowed_users')
        # csoportok
        selected_group_ids = request.POST.getlist('allowed_groups')

        quiz.allowed_users.set(selected_user_ids)
        quiz.allowed_groups.set(selected_group_ids)

        from django.contrib import messages
        messages.success(request, "Hozzáférési beállítások frissítve.")
        return redirect('quiz:quiz_settings', quiz_id=quiz.id)

    return render(request, 'quiz/quiz_settings.html', {
        'quiz': quiz,
        'questions': questions,
        'all_users': all_users,
        'all_groups': all_groups,
    })

def get_accessible_quizzes_for_user(user):
    """
    Visszaadja azokat a kvízeket, amiket a user láthat/tölthet.
    Logika:
    - ha a kvízhez NINCS felhasználó és NINCS csoport hozzárendelve → mindenki láthatja
    - ha VAN hozzárendelve user/csoport → csak az láthatja, aki érintett
    - superuser mindent lát
    """
    from .models import Quiz  # hogy ne legyen körkörös import

    if not user.is_authenticated:
        # nem belépett user csak a nyitott kvízeket lássa
        return Quiz.objects.filter(allowed_users__isnull=True, allowed_groups__isnull=True).distinct()

    # belépett user
    # nyitott kvízek
    qs_open = Quiz.objects.filter(
        allowed_users__isnull=True,
        allowed_groups__isnull=True
    )

    # userre engedélyezett kvízek
    qs_user = Quiz.objects.filter(
        allowed_users=user
    )

    # csoportra engedélyezett kvízek
    qs_group = Quiz.objects.filter(
        allowed_groups__in=user.groups.all()
    )

    # ha superuser → mindent lát
    if user.is_superuser:
        return Quiz.objects.all().distinct()

    # egyesítjük
    return (qs_open | qs_user | qs_group).distinct()

@login_required
def quiz_results(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    quiz_profile = QuizProfile.objects.get(user=request.user)

    # Csak az adott kvízhez tartozó AttemptedQuestion-ök
    attempts = AttemptedQuestion.objects.filter(
        quiz_profile=quiz_profile,
        question__quizquestions__quiz=quiz
    ).select_related('question').prefetch_related('selected_choices')

    # Összpontszám
    total_score = attempts.aggregate(total=models.Sum('marks_obtained'))['total'] or 0

    context = {
        'quiz': quiz,
        'attempts': attempts,
        'total_score': total_score,
    }
    return render(request, 'quiz/quiz_results.html', context)


@login_required()
def submission_result(request, attempted_question_pk):
    from .models import Quiz  # ha még nincs fent
    attempted_question = get_object_or_404(AttemptedQuestion, pk=attempted_question_pk)

    # 1) próbáljuk a sessionből kivenni, melyik kvízben volt a user
    quiz_id = request.session.get('current_quiz_id')

    if quiz_id:
        quiz = get_object_or_404(Quiz, id=quiz_id)
    else:
        # 2) fallback: ha valamiért nincs sessionben, marad a régi logika
        quiz = attempted_question.question.quizquestions.first().quiz

    context = {
        'attempted_question': attempted_question,
        'quiz': quiz,
    }
    return render(request, 'quiz/submission_result.html', context)


@login_required()
def restart_quiz(request, quiz_id=None):
    # Ha nincs quiz_id paraméter, próbáljuk a session-ből
    if not quiz_id:
        quiz_id = request.session.get('current_quiz_id')

    if not quiz_id:
        messages.error(request, "Nem található aktuális kvíz az újrakezdéshez.")
        return redirect('quiz:home')

    quiz = get_object_or_404(Quiz, id=quiz_id)

    # get_or_create visszaad egy tuple-t (obj, created) — ezt ki kell bontani
    quiz_profile, created = QuizProfile.objects.get_or_create(user=request.user)

    # Töröljük csak a kiválasztott kvízhez tartozó próbálkozásokat (ha van ilyen logika)
    # Ha a QuizQuestion model-t használod a quiz-hez tartozó kérdésekhez:
    question_ids = quiz.quiz_questions.values_list('question_id', flat=True)
    quiz_profile.attempts.filter(question__id__in=question_ids).delete()

    # Nullázzuk az összpontszámot (update_fields-t használva hatékonyabb)
    quiz_profile.total_score = 0
    quiz_profile.save(update_fields=['total_score'])

    messages.success(request, "A kvíz újrakezdve — az eddigi próbálkozások törölve, pontszám nullázva.")

    # Visszairányítás a play view-hoz: fontos a quiz_id átadása
    return redirect('quiz:play', quiz_id=quiz.id)

@login_required
def quiz_end(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    quiz_profile = QuizProfile.objects.get(user=request.user)

    if 'quiz_start_time' in request.session:
        del request.session['quiz_start_time']

    # Teljes pontszám összesítése AttemptedQuestion alapján
    total_score = quiz_profile.attempts.filter(
        question__in=quiz.get_questions()
    ).aggregate(total=models.Sum('marks_obtained'))['total'] or 0

    context = {
        'quiz': quiz,
        'total_score': total_score,
    }

    return render(request, 'quiz/quiz_end.html', context)



def login_view(request):
    title = "Login"
    form = UserLoginForm(request.POST or None)
    if form.is_valid():
        username = form.cleaned_data.get("username")
        password = form.cleaned_data.get("password")
        user = authenticate(username=username, password=password)
        login(request, user)
        return redirect('/user-home')
    return render(request, 'quiz/login.html', {"form": form, "title": title})


def register(request):
    title = "Create account"
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/login')
    else:
        form = RegistrationForm()

    context = {'form': form, 'title': title}
    return render(request, 'quiz/registration.html', context=context)


def logout_view(request):
    logout(request)
    return redirect('/')


def error_404(request):
    data = {}
    return render(request, 'quiz/error_404.html', data)


def error_500(request):
    data = {}
    return render(request, 'quiz/error_500.html', data)
