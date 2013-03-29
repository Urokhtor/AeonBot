class AccessControl:
    
    def __init__(self, config):
        self.users = []
        self.allowedChannels = []
        self.trustedChannels = []
        self.load(config)
    
    def load(self, config):
        for channel in config.getItem("allowedchannels", []):
            self.allowedChannels.append(channel)
            
        for channel in config.getItem("trustedchannels", []):
            self.trustedChannels.append(channel)
            
        for nick, data in config.getItem("users", {}).items():
            if not self.hasUser(nick):
                self.addUser(nick)
            
            for key, value in data.items():
                if key == "hosts":
                        for user in self.users:
                            if user.nick == nick:
                                for host in value:
                                    user.hosts.append(host)
                elif key == "owner":
                    if str(value).lower() == "true":
                        for user in self.users:
                            if user.nick == nick:
                                user.owner = True
                elif key == "trusted":
                    if str(value).lower() == "true":
                        for user in self.users:
                            if user.nick == nick:
                                user.trusted = True
                elif key == "blacklisted":
                    if str(value).lower() == "true":
                        for user in self.users:
                            if user.nick == nick:
                                user.blacklisted = True
                elif key == "master":
                    if str(value).lower() == "true":
                        for user in self.users:
                            if user.nick == nick:
                                user.master = True
                elif key == "banned":
                    if str(value).lower() == "true":
                        for user in self.users:
                            if user.nick == nick:
                                user.banned = True
                        
    def reload(self, config):
        self.users[:] = []
        self.load(config)
    
    def addUser(self, nick):
        if not self.hasUser(nick):
            self.users.append(User(nick))
            return True
        
        return False
    
    def hasUser(self, nick):
        for user in self.users:
            if user.nick == nick:
                return True
        
        return False
    
    def getUser(self, nick):
        for user in self.users:
            if user.nick == nick:
                return user
        
        return None
    
    def getUsers(self):
        return self.users
        
    def delUser(self, nick):
        if self.hasUser(nick):
            self.users.remove(self.getUser(nick))
            return True
                
        return False
            
class User:
    
    def __init__(self, nick):
        self.nick = nick
        self.hosts = []
        self.owner = False
        self.master = False
        self.trusted = False
        self.blacklisted = False
        self.banned = False
        