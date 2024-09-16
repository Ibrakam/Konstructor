from asgiref.sync import sync_to_async
from django.db.models import Count, F
from django.utils import timezone
from modul.models import UserTG, Channels, Messages, Link_statistic, Answer_statistic, Rating_overall, Rating_today
import pytz

moscow_timezone = pytz.timezone('Europe/Moscow')


@sync_to_async
def get_channels_for_check():
    return list(Channels.objects.values_list('channel_id', 'channel_url'))


@sync_to_async
def check_user(tg_id):
    return UserTG.objects.filter(uid=tg_id).exists()


@sync_to_async
def add_user(tg_id, link):
    UserTG.objects.update_or_create(uid=tg_id, user_link=link, reg_date=timezone.now().astimezone(moscow_timezone), defaults={'reg_date': timezone.now().astimezone(moscow_timezone)})


@sync_to_async
def get_user_by_link(link):
    user = UserTG.objects.filter(user_link=link).first()
    return UserTG.uid if user else False


@sync_to_async
def add_messages_info(sender_id, receiver_id, sender_message_id, receiver_message_id):
    Messages.objects.create(
        sender_id=sender_id,
        receiver_id=receiver_id,
        sender_message_id=sender_message_id,
        receiver_message_id=receiver_message_id,
        reg_date=timezone.now().astimezone(moscow_timezone).date()
    )


@sync_to_async
def get_user_link(tg_id):
    user = UserTG.objects.filter(uid=tg_id).first()
    return UserTG.user_link if user else False


@sync_to_async
def check_reply(receiver_message_id):
    message = Messages.objects.filter(receiver_message_id=receiver_message_id).first()
    return [message.sender_id, message.sender_message_id] if message else False


@sync_to_async
def change_greeting_user(tg_id, greeting=None):
    UserTG.objects.filter(uid=tg_id).update(greeting=greeting)


@sync_to_async
def get_greeting(tg_id):
    user = UserTG.objects.filter(uid=tg_id).first()
    return UserTG.greeting if user else False


@sync_to_async
def check_link(link):
    return not UserTG.objects.filter(user_link=link).exists()


@sync_to_async
def change_link_db(tg_id, new_link):
    UserTG.objects.filter(uid=tg_id).update(user_link=new_link)


@sync_to_async
def add_rating_today(tg_id):
    actual_date = timezone.now().astimezone(moscow_timezone).date()
    rating, created = Rating_today.objects.get_or_create(
        user_id=tg_id,
        reg_date=actual_date,
        defaults={'amount': 1}
    )
    if not created:
        rating.amount = F('amount') + 1
        rating.save()


@sync_to_async
def add_rating_overall(tg_id):
    rating, created = Rating_overall.objects.get_or_create(
        user_id=tg_id,
        defaults={'amount': 1, 'reg_date': timezone.now().astimezone(moscow_timezone).date()}
    )
    if not created:
        rating.amount = F('amount') + 1
        rating.save()


@sync_to_async
def add_link_statistic(tg_id):
    Link_statistic.objects.create(
        user_id=tg_id,
        reg_date=timezone.now().astimezone(moscow_timezone).date()
    )
    add_rating_today(tg_id)
    add_rating_overall(tg_id)


@sync_to_async
def add_answer_statistic(tg_id):
    Answer_statistic.objects.create(
        user_id=tg_id,
        reg_date=timezone.now().astimezone(moscow_timezone).date()
    )


def value_handler(num):
    return num or 0


@sync_to_async
def get_all_statistic(tg_id: int):
    actual_date = timezone.now().astimezone(moscow_timezone).date()

    messages_today = Messages.objects.filter(receiver_id=tg_id, reg_date=actual_date).count()
    messages_overall = Messages.objects.filter(receiver_id=tg_id).count()
    answers_today = Answer_statistic.objects.filter(user_id=tg_id, reg_date=actual_date).count()
    answers_overall = Rating_overall.objects.filter(user_id=tg_id).count()
    links_today = Link_statistic.objects.filter(user_id=tg_id, reg_date=actual_date).count()
    links_overall = Link_statistic.objects.filter(user_id=tg_id).count()

    rating_today = Rating_today.objects.filter(reg_date=actual_date).order_by('-amount')
    rating_overall = Rating_overall.objects.order_by('-amount')

    position_today = next((i for i, r in enumerate(rating_today, 1) if r.user_id == tg_id), "1000+")
    position_overall = next((i for i, r in enumerate(rating_overall, 1) if r.user_id == tg_id), "1000+")

    return {
        "messages_today": value_handler(messages_today),
        "answers_today": value_handler(answers_today),
        "links_today": value_handler(links_today),
        "position_today": position_today,
        "messages_overall": messages_overall,
        "answers_overall": answers_overall,
        "links_overall": links_overall,
        "position_overall": position_overall
    }
