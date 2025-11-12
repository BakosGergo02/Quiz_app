from django.conf.urls import url
from django.contrib import admin
from . import views

app_name = 'quiz'

urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^user-home$', views.user_home, name='user_home'),
    url(r'^(?P<quiz_id>\d+)/play/$', views.play, name='play'),
    url(r'^(?P<quiz_id>\d+)/restart/$', views.restart_quiz, name='restart_quiz'),
    url(r'^leaderboard/$', views.leaderboard, name='leaderboard'),
    url(r'^login/$', views.login_view, name='login'),
    url(r'^logout/$', views.logout_view, name='logout'),
    url(r'^register/$', views.register, name='register'),
    url(r'^create-quiz/$', views.create_quiz, name='create_quiz'),

    url(r'^submission-result/(?P<attempted_question_pk>\d+)/$', views.submission_result, name='submission_result'),
    
    url(r'^(?P<quiz_id>\d+)/settings/$', views.quiz_settings_view, name='quiz_settings'),
    url(r'^(?P<quiz_id>\d+)/select-question-type/$', views.select_question_type, name='select_question_type'),
    url(r'^(?P<quiz_id>\d+)/add-single-question/$', views.add_single_question, name='add_single_question'),
    url(r'^(?P<quiz_id>\d+)/add-multiple-question/$', views.add_multiple_question, name='add_multiple_question'),
    url(r'^(?P<quiz_id>\d+)/add-text-question/$', views.add_text_question, name='add_text_question'),
    url(r'^(?P<quiz_id>\d+)/end/$', views.quiz_end, name='quiz_end'),
    url(r'^(?P<quiz_id>\d+)/results/$', views.quiz_results, name='quiz_results'),
    url(r'^quizzes/$', views.quiz_list, name='quiz_list'),
    url(r'^quizzes/user-groups/$', views.manage_user_groups, name='manage_user_groups'),
    url(r'^(?P<quiz_id>\d+)/add-matching-question/$', views.add_matching_question, name='add_matching_question'),
    url(r'^(?P<quiz_id>\d+)/question/(?P<question_id>\d+)/edit/$',views.edit_question,name='edit_question'),

    
]
