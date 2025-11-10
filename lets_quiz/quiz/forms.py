from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import Group
from django.utils.translation import gettext as _
from .models import Question, Choice, Quiz
from django import forms

User = get_user_model()

class QuizSettingsForm(forms.Form):
    QUESTION_TYPES = (
        ('single', 'Egy választás (Single Choice)'),
        ('multiple', 'Több választás (Multiple Choice)'),
        # később jön: ('text', 'Szöveges válasz'), ('dragdrop', 'Drag & Drop')
    )

    FEEDBACK_TYPES = (
        ('instant', 'Azonnali visszajelzés'),
        ('final', 'Visszajelzés a végén'),
    )

    question_type = forms.ChoiceField(
        choices=QUESTION_TYPES,
        label="Kérdés típusa",
        widget=forms.RadioSelect
    )

    time_limit = forms.IntegerField(
        label="Időkorlát (másodperc)",
        min_value=0,
        required=False,
        help_text="Hagyd üresen, ha nincs időkorlát."
    )

    feedback_mode = forms.ChoiceField(
        choices=FEEDBACK_TYPES,
        label="Visszajelzés módja",
        widget=forms.RadioSelect
    )


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['html', 'is_published', 'is_multiple_choice']
        widgets = {
            'html': forms.Textarea(attrs={'rows': 3, 'cols': 80}),
        }

class BaseQuestionForm(forms.ModelForm):
    option1 = forms.CharField(label="1. válaszlehetőség", max_length=255)
    option2 = forms.CharField(label="2. válaszlehetőség", max_length=255)
    option3 = forms.CharField(label="3. válaszlehetőség", max_length=255, required=False)
    option4 = forms.CharField(label="4. válaszlehetőség", max_length=255, required=False)

    class Meta:
        model = Question
        fields = ['html', 'maximum_marks']

class SingleChoiceQuestionForm(BaseQuestionForm):
    correct_option = forms.ChoiceField(
        label="Helyes válasz",
        choices=[
            ('1', '1. válasz'),
            ('2', '2. válasz'),
            ('3', '3. válasz'),
            ('4', '4. válasz')
        ],
        widget=forms.RadioSelect
    )

class MultipleChoiceQuestionForm(BaseQuestionForm):
    correct_options = forms.MultipleChoiceField(
        label="Helyes válasz(ok)",
        choices=[
            ('1', '1. válasz'),
            ('2', '2. válasz'),
            ('3', '3. válasz'),
            ('4', '4. válasz')
        ],
        widget=forms.CheckboxSelectMultiple
    )

class ChoiceForm(forms.ModelForm):
    class Meta:
        model = Choice
        fields = ['html', 'is_correct']
        widgets = {
            'html': forms.Textarea(attrs={'rows': 2, 'cols': 80}),
        }


class ChoiceInlineFormset(forms.BaseInlineFormSet):
    def clean(self):
        super(ChoiceInlineFormset, self).clean()

        # Ha nincs még Question példány, nem validálunk
        if not hasattr(self, "instance"):
            return

        question = self.instance
        correct_choices_count = 0

        for form in self.forms:
            # csak érvényes, nem törölt sorokat nézünk
            if not form.is_valid() or form.cleaned_data.get('DELETE', False):
                continue
            if form.cleaned_data.get('is_correct', False):
                correct_choices_count += 1


        # 🔹 Validáció logika
        if not question.is_multiple_choice:
            # single choice -> pontosan 1 helyes válasz legyen
            if correct_choices_count != 1:
                raise forms.ValidationError(_('Egyszeres választású kérdéshez pontosan 1 helyes válasz szükséges.'))
        else:
            # multiple choice -> legalább 1 helyes válasz legyen
            if correct_choices_count < 1:
                raise forms.ValidationError(_('Többválaszos kérdéshez legalább 1 helyes válasz szükséges.'))


class QuizCreateForm(forms.ModelForm):

    allowed_users = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control', 'size': '10'}),
        label="Diákok, akik kitölthetik"
    )

    class Meta:
        model = Quiz
        fields = ['title', 'description', 'time_limit_seconds', 'immediate_feedback', 'allow_multiple_attempts']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Kvíz címe'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Kvíz leírása'}),
            'time_limit_seconds': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'immediate_feedback': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'allow_multiple_attempts': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super(QuizCreateForm, self).__init__(*args, **kwargs)
        # próbáljuk meg a "Tanár" csoportot kiszűrni -> ami marad, az diák
        try:
            teacher_group = Group.objects.get(name='Tanár')
            self.fields['allowed_users'].queryset = User.objects.exclude(groups=teacher_group)
        except Group.DoesNotExist:
            # ha nincs ilyen csoport, akkor minden user listázható
            self.fields['allowed_users'].queryset = User.objects.all()


class UserLoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

    def clean(self, *args, **kwargs):
        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")

        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise forms.ValidationError("Ez a felhasználó nem létezik!")
            if not user.check_password(password):
                raise forms.ValidationError("Helytelen jelszó!")
            if not user.is_active:
                raise forms.ValidationError("Ez a felhasználó nem aktív!")
        return super(UserLoginForm, self).clean(*args, **kwargs)


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)

    class Meta:
        model = User
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'password1',
            'password2',
        ]

    def save(self, commit=True):
        user = super(RegistrationForm, self).save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']

        if commit:
            user.save()

        return user
