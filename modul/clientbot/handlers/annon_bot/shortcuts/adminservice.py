from asgiref.sync import sync_to_async
from modul.models import UserTG, Channels, Bot


@sync_to_async
def get_admin_id(bot_token):
    owner = Bot.objects.filter(token=bot_token).first()
    return owner.owner.uid if owner else False


@sync_to_async
def get_channels_for_admin():
    all_channels = Channels.objects.all()
    if all_channels:
        return [[channel.id, channel.channel_url, channel.channel_id] for channel in all_channels]
    return []


@sync_to_async
def add_new_channel_db(url, id):
    Channels.objects.create(channel_url=url, channel_id=id)
    return True


@sync_to_async
def delete_channel_db(id):
    try:
        channel = Channels.objects.get(id=id)
        channel.delete()
        return True
    except not Channels:
        return False


@sync_to_async
def get_all_users_tg_id():
    return list(UserTG.objects.values_list('uid', flat=True))


@sync_to_async
def get_users_count():
    return UserTG.objects.count()
