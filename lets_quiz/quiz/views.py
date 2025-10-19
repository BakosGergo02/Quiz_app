from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from .models import QuizProfile, Question, AttemptedQuestion
from .forms import UserLoginForm, RegistrationForm


def home(request):
    context = {}
    return render(request, 'quiz/home.html', context=context)


@login_required()
def user_home(request):
    context = {}
    return render(request, 'quiz/user_home.html', context=context)


def leaderboard(request):

    top_quiz_profiles = QuizProfile.objects.order_by('-total_score')[:500]
    total_count = top_quiz_profiles.count()
    context = {
        'top_quiz_profiles': top_quiz_profiles,
        'total_count': total_count,
    }
    return render(request, 'quiz/leaderboard.html', context=context)


@login_required()
def play(request):
    quiz_profile, created = QuizProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        question_pk = request.POST.get('question_pk')

        try:
            attempted_question = quiz_profile.attempts.select_related('question').get(question__pk=question_pk)
        except AttemptedQuestion.DoesNotExist:
            raise Http404("Nincs ilyen kérdéskísérlet")

        question = attempted_question.question

        # --- DEBUG: nézzük meg pontosan mi érkezik be a POST-ban ---
        print("### DEBUG: request.POST =", dict(request.POST))
        print("### DEBUG: is_multiple_choice =", question.is_multiple_choice)

        #  Többválaszos eset: checkboxok listában
        if question.is_multiple_choice:
            choice_pks = request.POST.getlist('choices')
        else:
            choice_pk = request.POST.get('choice_pk')
            choice_pks = [choice_pk] if choice_pk else []

        print("### DEBUG: raw choice_pks =", choice_pks)

        #  Lekérjük a választott Choice objektumokat
        try:
            selected_choices = question.choices.filter(pk__in=choice_pks)
        except ObjectDoesNotExist:
            raise Http404("A kiválasztott válasz nem létezik")

        print("### DEBUG: selected_choices from DB =", list(selected_choices.values_list('pk', flat=True)))

        #  Értékelés
        quiz_profile.evaluate_attempt(attempted_question, selected_choices)

        #  Eredmény oldalra irányítás
        return redirect(attempted_question)

    else:
        question = quiz_profile.get_new_question()
        if question is not None:
            quiz_profile.create_attempt(question)

        context = {'question': question}
        return render(request, 'quiz/play.html', context=context)




@login_required()
def submission_result(request, attempted_question_pk):
    attempted_question = get_object_or_404(AttemptedQuestion, pk=attempted_question_pk)
    context = {
        'attempted_question': attempted_question,
    }

    return render(request, 'quiz/submission_result.html', context)


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
