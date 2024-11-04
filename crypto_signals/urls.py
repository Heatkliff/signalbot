from django.urls import path
from .views import home_view,sent_messages_list

urlpatterns = [
    path('', home_view, name='home'),  # Главная страница
    path('api/sent_messages/', sent_messages_list, name='sent_messages_list'),
]
