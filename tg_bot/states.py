from aiogram.fsm.state import State, StatesGroup


#menu
class Start(StatesGroup):
    menu = State()
#election
class Voting(StatesGroup):
    waiting_for_name       = State()        # name should be entered
    checking_the_name      = State()        # wainting for the acknowledgement that name is correct
    checking_the_studid    = State()        # wainting for the acknowledgement that stud_id is correct
    waiting_for_studid     = State()        # student ID should be entered
    waiting_for_refuse     = State()
    waiting_for_choises    = State()


    
