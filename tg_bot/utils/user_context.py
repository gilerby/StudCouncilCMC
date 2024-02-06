class mutex():
    def __init__(self):
        self.user_handler_flag = {}        
        
    def get_flag(self,user_id)->bool:
        if (user_id not in self.user_handler_flag) or self.user_handler_flag[user_id] == 0: 
            self.user_handler_flag[user_id] = 1
            return False
        else:
            return True
    
    def free_lock(self,user_id):
        self.user_handler_flag[user_id] = 0


