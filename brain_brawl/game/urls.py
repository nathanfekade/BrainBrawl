from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.UserList.as_view(), name='user-list'),
    path('profile/', views.UserDetail.as_view(), name='user-detail'),
    path('groups/', views.GroupList.as_view(), name='group-list'),
    path('groups/<int:pk>/', views.GroupDetail.as_view(), name='group-detail'),
    path('group-members/', views.GroupMemberList.as_view(), name='group-member-list'),
    path('group-members/<int:group_id>/<int:user_id>/', views.GroupMemberDetail.as_view(), name='group-member-detail'),    
    path('quizzes/', views.QuizList.as_view(), name='quiz-list'),
    path('quizzes/<int:pk>/', views.QuizDetail.as_view(), name='quiz-detail'),
    path('user-group-scores/', views.UserGroupScoreList.as_view(), name='user-group-score-list'),
    path('get-user-id/', views.UserIdByEmail.as_view(), name='user-id-by-email'),



]