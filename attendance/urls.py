from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('register/', views.register_employee, name='register_employee'),
    path('checkin-checkout/', views.checkin_checkout, name='checkin_checkout'),
    path('schedule/', views.schedule_view, name='schedule'),
    path('train/', views.train_system, name='train_system'),
]