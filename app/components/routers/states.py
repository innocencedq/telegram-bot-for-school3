from aiogram.fsm.state import State, StatesGroup

#Состояния
class TechSup(StatesGroup):
    waiting_idea = State()
    waiting_bug = State()