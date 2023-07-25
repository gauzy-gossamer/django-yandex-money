from django.urls import path

from .views import NoticeFormView
from .views import CheckOrderFormView


urlpatterns = [
    path(r'check/', CheckOrderFormView.as_view(), name='yandex_money_check'),
    path(r'aviso/', NoticeFormView.as_view(), name='yandex_money_notice'),
]
