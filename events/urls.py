from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [
    path('', views.event_list, name='list'),
    path('<int:event_id>/', views.event_detail, name='detail'),
    path('<int:event_id>/register/', views.event_registration, name='register'),
    path('form-fields/', views.get_conditional_fields, name='get_conditional_fields'),
    path('qr/<str:data>/', views.generate_qr, name='generate_qr'),
]