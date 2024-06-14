import asyncio
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.utils import timezone

from admin_panel.telegram.forms import MailingForm
from admin_panel.telegram.models import (
    Mailing, TradingPoint, ReceivingReport, ReceivingReportPhoto, TgUser, Feed,
    FeedAmount,
)


@login_required
def mailing(request):
    if request.method == 'POST':
        form = MailingForm(request.POST, request.FILES)
        if not form.is_valid():
            for error in form.errors.values():
                messages.error(request, error.data[0].message)
            return redirect('admin:telegram_mailing_add')

        data = form.cleaned_data
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        if data.get('schedule_checkbox'):
            date_malling = data.get('schedule_datetime')
            text_success = 'Рассылка успешно зарегистрирована'
        else:
            date_malling = timezone.now()
            text_success = 'Рассылка успешно зарегистрирована и будет запущена в течении 1 минуты.'

        Mailing.objects.create(
            media_type=data['media_type'],
            text=data['message_text'],
            date_malling=date_malling,
            file=data.get('file')
        )
        messages.success(request, text_success)
    return redirect('admin:telegram_mailing_changelist')


def create_receiving_report(request, user_id):
    tg_user = get_object_or_404(TgUser, id=user_id)
    feeds = Feed.objects.all()
    points = TradingPoint.objects.all()
    if request.method == 'POST':
        data = request.POST
        feeds_report = list()
        trading_point = get_object_or_404(
            TradingPoint, id=data.get('trading_point')
        )
        for feed in feeds:
            amount = int(data.get(f'feed_{feed.id}'))
            if amount > 0:
                amount_feed = FeedAmount.objects.create(
                    feed=feed,
                    amount=amount,
                )
                feeds_report.append(amount_feed)

        comment = data.get('comment')

        report = ReceivingReport.objects.create(
            user=tg_user,
            comment=comment,
            trading_point=trading_point,
        )
        report.report.set(feeds_report)

        for file in request.FILES.getlist('images'):
            ReceivingReportPhoto.objects.create(
                report=report, photo=file,
            )
    #         return HttpResponse('Успешно!')

    context = {
        'points': points,
        'feeds': feeds,
    }

    return render(request, 'take_food.html', context)
