from .models import Quiz

def current_quiz(request):
    quiz_id = request.session.get('current_quiz_id')
    quiz = None
    if quiz_id:
        try:
            quiz = Quiz.objects.get(id=quiz_id)
        except Quiz.DoesNotExist:
            pass
    return {'quiz': quiz}
