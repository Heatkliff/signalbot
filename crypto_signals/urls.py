from django.urls import path
from .views import home_view,sent_messages_list, market_analysis_view

urlpatterns = [
    path('', home_view, name='home'),  # Главная страница
    path('status_market/', market_analysis_view, name='market_analysis'),
    path('api/sent_messages/', sent_messages_list, name='sent_messages_list'),
]
