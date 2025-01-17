from __future__ import unicode_literals
from uuid import uuid4

import six
from django.conf import settings
from django.db import models

from .signals import payment_process
from .signals import payment_completed


def get_default_as_uuid():
    return six.text_type(uuid4()).replace('-', '')


class Payment(models.Model):
    class STATUS:
        PROCESSED = 'processed'
        SUCCESS = 'success'
        FAIL = 'fail'

        CHOICES = (
            (PROCESSED, 'Processed'),
            (SUCCESS, 'Success'),
            (FAIL, 'Fail'),
        )

    class PAYMENT_TYPE:
        PC = 'PC'
        AC = 'AC'
        GP = 'GP'
        MC = 'MC'
        WM = 'WM'
        SB = 'SB'
        AB = 'AB'
        MA = 'MA'
        PB = 'PB'
        QW = 'QW'
        QP = 'QP'

        CHOICES = (
            (PC, 'Кошелек Яндекс.Деньги'),
            (AC, 'Банковская карта'),
            (GP, 'Наличными через кассы и терминалы'),
            (MC, 'Счет мобильного телефона'),
            (WM, 'Кошелек WebMoney'),
            (SB, 'Сбербанк: оплата по SMS или Сбербанк Онлайн'),
            (AB, 'Альфа-Клик'),
            (MA, 'MasterPass'),
            (PB, 'Интернет-банк Промсвязьбанка'),
            (QW, 'QIWI Wallet'),
            (QP, 'Доверительный платеж (Куппи.ру)'),
        )

    class CURRENCY:
        RUB = 643
        TEST = 10643

        CHOICES = (
            (RUB, 'Рубли'),
            (TEST, 'Тестовая валюта'),
        )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.CASCADE,
        verbose_name='Пользователь')
    pub_date = models.DateTimeField('Время создания', auto_now_add=True)

    # Required request fields
    shop_id = models.PositiveIntegerField(
        'ID магазина', default=settings.YANDEX_MONEY_SHOP_ID)
    scid = models.PositiveIntegerField(
        'Номер витрины', default=settings.YANDEX_MONEY_SCID)
    customer_number = models.CharField(
        'Идентификатор плательщика', max_length=64,
        default=get_default_as_uuid)
    order_amount = models.DecimalField(
        'Сумма заказа', max_digits=15, decimal_places=2)

    # Non-required fields
    article_id = models.PositiveIntegerField(
        'Идентификатор товара', blank=True, null=True)
    payment_type = models.CharField(
        'Способ платежа', max_length=2, default=PAYMENT_TYPE.PC,
        choices=PAYMENT_TYPE.CHOICES)
    order_number = models.CharField(
        'Номер заказа', max_length=64,
        default=get_default_as_uuid)
    cps_email = models.EmailField(
        'Email плательщика', max_length=100, blank=True, null=True)
    cps_phone = models.CharField(
        'Телефон плательщика', max_length=15, blank=True, null=True)
    success_url = models.URLField(
        'URL успешной оплаты', default=settings.YANDEX_MONEY_SUCCESS_URL)
    fail_url = models.URLField(
        'URL неуспешной оплаты', default=settings.YANDEX_MONEY_FAIL_URL)

    # Transaction info
    status = models.CharField(
        'Статус', max_length=16, choices=STATUS.CHOICES,
        default=STATUS.PROCESSED)
    invoice_id = models.PositiveIntegerField(
        'Номер транзакции оператора', blank=True, null=True)
    shop_amount = models.DecimalField(
        'Сумма полученная на р/с', max_digits=15, decimal_places=2, blank=True,
        null=True, help_text='За вычетом процента оператора')
    order_currency = models.PositiveIntegerField(
        'Валюта', default=CURRENCY.RUB, choices=CURRENCY.CHOICES)
    shop_currency = models.PositiveIntegerField(
        'Валюта полученная на р/с', blank=True, null=True,
        default=CURRENCY.RUB, choices=CURRENCY.CHOICES)
    performed_datetime = models.DateTimeField(
        'Время выполнение запроса', blank=True, null=True)

    @property
    def is_payed(self):
        return self.status == self.STATUS.SUCCESS

    def send_signals(self):
        status = self.status
        if status == self.STATUS.PROCESSED:
            payment_process.send(sender=self)
        if status == self.STATUS.SUCCESS:
            payment_completed.send(sender=self)

    @classmethod
    def get_used_shop_ids(cls):
        return cls.objects.values_list('shop_id', flat=True).distinct()

    @classmethod
    def get_used_scids(cls):
        return cls.objects.values_list('scid', flat=True).distinct()

    class Meta:
        ordering = ('-pub_date',)
        unique_together = (
            ('shop_id', 'order_number'),
        )
        verbose_name = 'платёж'
        verbose_name_plural = 'платежи'
        app_label = 'yandex_money'

    def __str__(self):
        return '[Payment id={}, order_number={}, payment_type={}, status={}]'.format(
            self.id, self.order_number, self.payment_type, self.status)
