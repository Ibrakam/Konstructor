from aiogram.fsm.state import State, StatesGroup

class Links(StatesGroup):
    send_st = State()
    answer_st = State()
    change_greeting = State()
    change_link = State()

class ChangeAdminInfo(StatesGroup):
    get_channel_id = State()
    get_channel_url = State()
    delete_channel = State()
    mailing = State()
