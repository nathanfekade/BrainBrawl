from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.UserList.as_view(), name='user-list'),
    path('profile/', views.UserDetail.as_view(), name='user-detail')


]