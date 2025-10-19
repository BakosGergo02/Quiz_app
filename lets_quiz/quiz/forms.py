from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, get_user_model
from django.utils.translation import gettext as _
from .models import Question, Choice


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['html', 'is_published', 'is_multiple_choice']
        widgets = {
            'html': forms.Textarea(attrs={'rows': 3, 'cols': 80}),
        }


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


User = get_user_model()


class UserLoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

    def clean(self, *args, **kwargs):
        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")

        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise forms.ValidationError("This user does not exists")
            if not user.check_password(password):
                raise forms.ValidationError("Incorrect password")
            if not user.is_active:
                raise forms.ValidationError("This user is not active")
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
