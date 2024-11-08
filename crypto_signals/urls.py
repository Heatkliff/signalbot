from django.urls import path
from .views import home_view, sent_messages_list, market_analysis_view, get_market_currency_info, web_generate_signal

urlpatterns = [
    path('', home_view, name='home'),  # Главная страница
    path('status_market/', market_analysis_view, name='market_analysis'),
    path('status_market/<currency>', get_market_currency_info, name='currency_info'),
    path('api/sent_messages/', sent_messages_list, name='sent_messages_list'),
    path('generate_signals/', web_generate_signal, name='web_generate_signal'),
]
