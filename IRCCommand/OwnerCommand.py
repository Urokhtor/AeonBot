from time import sleep
from time import strftime
from re import match
from Utils.Decorators import Decorators

class OwnerCommand:
    
    @Decorators.owner
    def connect(command):
        tmp = command.message.split(" ")
        port = 6667
                
        if len(tmp) > 1:
            try: port = int(tmp[1])
            except ValueError: pass
 
        command.bot.irc.connect(command.bot.name, command.bot.login, command.bot.realname, tmp[0], port)
        command.result = "Connecting to " + tmp[0]
    
        return command
    
    @Decorators.owner
    def disconnect(command):
        command.bot.irc.disconnect(command.message)
        
        return command
    
    @Decorators.owner
    def join(command):
        command.bot.irc.join(command.server, command.message)
                
        return command
    
    @Decorators.owner
    def part(command):
        command.bot.irc.part(command.server, command.message)
                
        return command
    
    @Decorators.owner
    def quit(command):
        command.bot.irc.quit()
                
        return command
    
    @Decorators.owner
    def load(command):
        if command.bot.subsystems["modules"].loadModule(command.message):
            command.result = "Loaded module " + command.message
        else:
            command.result = "Couldn't load module " + command.message
        
        return command
    
    @Decorators.owner
    def reload(command):
        if command.bot.subsystems["modules"].reloadModule(command.message):
            command.result = "Reloaded module " + command.message
        else:
            command.result = "Couldn't reload module " + command.message
        
        return command
    
    @Decorators.owner
    def subsystem(command):
        command.result = []
        line = command.message.replace(",", "").split(" ")
        
        if line[0] == "reload" and len(line) > 1:
            command.type = "subsystem reload"
            
            for system in line:
                if system == "reload" or system == "list":
                    continue

                command.result.append(system)
                    
        elif line[0] == "list":
            command.result.append("Loaded subsystems: " + " ".join(command.bot.subsystems.keys()))
            return command
        
        return command
    
    @Decorators.owner
    def listloaded(command):
        command.result = "Loaded modules are: " + ", ".join(command.bot.subsystems["modules"].getModules())
        
        return command
    
    @Decorators.owner
    def nick(command):
        command.bot.irc.ConnectionManager[command.server].changeNick(command.message)
        
        return command
        
    @Decorators.owner
    def _userlev(command):
        if command.result == "":
            return command
            
        userType = command.result
        command.result = ""
        command.result = []
        line = command.message.replace(",", "").split(" ")
        
        if line[0] == "add" and len(line) > 1:
            users = command.bot.subsystems["conf"].getItem("users", {})
            
            for user in line:
                if user == "add" or user == "del" or user == "get":
                    continue
                    
                if user not in users:
                    command.result.append("User " + user + " doesn't exist")
                    continue

                if userType == "master":
                    if not command.bot.subsystems["access"].getUser(user).master:
                        command.bot.subsystems["access"].getUser(user).master = True
                        users[user]["master"] = True
                        command.result.append("Added user " + user + " to master list")
                        continue
                    
                    elif command.bot.subsystems["access"].getUser(user).master:
                        command.result.append("User " + user + " is already master")
                        continue
                
                elif userType == "trusted":
                    if not command.bot.subsystems["access"].getUser(user).trusted:
                        command.bot.subsystems["access"].getUser(user).trusted = True
                        users[user]["trusted"] = True
                        command.result.append("Added user " + user + " to trusted list")
                        continue
                    
                    elif command.bot.subsystems["access"].getUser(user).trusted:
                        command.result.append("User " + user + " is already trusted")
                        continue
                        
                elif userType == "blacklisted":
                    if not command.bot.subsystems["access"].getUser(user).blacklisted:
                        command.bot.subsystems["access"].getUser(user).blacklisted = True
                        users[user]["blacklisted"] = True
                        command.result.append("Added user " + user + " to blacklisted list")
                        continue
                    
                    elif command.bot.subsystems["access"].getUser(user).blacklisted:
                        command.result.append("User " + user + " is already blacklisted")
                        continue
                
                elif userType == "banned":
                    if not command.bot.subsystems["access"].getUser(user).banned:
                        command.bot.subsystems["access"].getUser(user).banned = True
                        users[user]["banned"] = True
                        command.result.append("Added user " + user + " to banned list")
                        continue
                    
                    elif command.bot.subsystems["access"].getUser(user).banned:
                        command.result.append("User " + user + " is already banned")
                        continue
                        
            command.bot.subsystems["conf"].setItem("users", users)
            
        elif line[0] == "get":
            if len(line) == 1:
                tmp = ""
                
                for user in command.bot.subsystems["access"].getUsers():
                
                    if userType == "master" and user.master:
                        tmp += user.nick + " "
                
                    if userType == "trusted" and user.trusted:
                        tmp += user.nick + " "
                
                    if userType == "blacklisted" and user.blacklisted:
                        tmp += user.nick + " "
                
                    if userType == "banned" and user.banned:
                        tmp += user.nick + " "
                
                command.result.append(userType[0].upper() + userType[1:] + " users are: " + tmp)
                return command
        
            for user in line:
                if user == "add" or user == "del" or user == "get":
                    continue
                    
                _user = command.bot.subsystems["access"].getUser(user)
                
                if userType == "master":
                    if _user: command.result.append("User " + user + " master: " + str(_user.master))
                    else: command.result.append("User " + user + " doesn't exist")
                    
                if userType == "trusted":
                    if _user: command.result.append("User " + user + " trusted: " + str(_user.trusted))
                    else: command.result.append("User " + user + " doesn't exist")
                
                if userType == "blacklisted":
                    if _user: command.result.append("User " + user + " blacklisted: " + str(_user.blacklisted))
                    else: command.result.append("User " + user + " doesn't exist")
                
                if userType == "banned":
                    if _user: command.result.append("User " + user + " banned: " + str(_user.banned))
                    else: command.result.append("User " + user + " doesn't exist")
                
                
        elif line[0] == "del":
            users = command.bot.subsystems["conf"].getItem("users", {})
            
            for user in line:
                if user == "add" or user == "del" or user == "get":
                    continue
                    
                if user not in users:
                    command.result.append("User " + user + " doesn't exist")
                    continue

                if userType == "master":
                    if command.bot.subsystems["access"].getUser(user).master:
                        command.bot.subsystems["access"].getUser(user).master = False
                        users[user]["master"] = False
                        command.result.append("Removed user " + user + " from master list")
                        continue
                    
                    elif not command.bot.subsystems["access"].getUser(user).master:
                        command.result.append("User " + user + " is already not master")
                        continue
                    
                elif userType == "trusted":
                    if command.bot.subsystems["access"].getUser(user).trusted:
                        command.bot.subsystems["access"].getUser(user).trusted = False
                        users[user]["trusted"] = False
                        command.result.append("Removed user " + user + " from trusted list")
                        continue
                    
                    elif not command.bot.subsystems["access"].getUser(user).blacklisted:
                        command.result.append("User " + user + " is already not blacklisted")
                        continue
                    
                elif userType == "blacklisted":
                    if command.bot.subsystems["access"].getUser(user).blacklisted:
                        command.bot.subsystems["access"].getUser(user).blacklisted = False
                        users[user]["blacklisted"] = False
                        command.result.append("Removed user " + user + " from blacklisted list")
                        continue
                    
                    elif not command.bot.subsystems["access"].getUser(user).blacklisted:
                        command.result.append("User " + user + " is already not blacklisted")
                        continue
                    
                elif userType == "banned":
                    if command.bot.subsystems["access"].getUser(user).banned:
                        command.bot.subsystems["access"].getUser(user).banned = False
                        users[user]["banned"] = False
                        command.result.append("Removed user " + user + " from banned list")
                        continue
                    
                    elif not command.bot.subsystems["access"].getUser(user).banned:
                        command.result.append("User " + user + " is already not banned")
                        continue
                    
            command.bot.subsystems["conf"].setItem("users", users)
    
        return command
    
    @Decorators.owner
    def master(command):
        command.result = "master"
        return OwnerCommand._userlev(command)
        
    @Decorators.owner
    def trusted(command):
        command.result = "trusted"
        return OwnerCommand._userlev(command)
        
    @Decorators.owner
    def blacklisted(command):
        command.result = "blacklisted"
        return OwnerCommand._userlev(command)
        
    @Decorators.owner
    def banned(command):
        command.result = "banned"
        return OwnerCommand._userlev(command)
    
    @Decorators.owner
    def user(command):
        command.result = []
        users = command.message.split(" ")
        _users = command.bot.subsystems["conf"].getItem("users", {})

        if users[0] == "add":
            for user in users:
                if user == "add" or user == "del" or user == "get":
                    continue
                    
                if not command.bot.subsystems["access"].getUser(user):
                    command.bot.subsystems["access"].addUser(user)
                    
                    if user not in _users: _users[user] = {}
                
                    command.result.append("Added user " + user)
                    continue
                
                elif command.bot.subsystems["access"].getUser(user):
                    command.result.append("User " + user + " already exists")
                    continue

            command.bot.subsystems["conf"].setItem("users", _users)
            
        elif users[0] == "get":
            if len(users) == 1:
                tmp = ""
                for user in command.bot.subsystems["access"].getUsers():
                    tmp += user.nick + " "
                    
                command.result.append("Users: " + tmp)
                return command
                
            for user in users:
                if user == "add" or user == "del" or user == "get":
                    continue
                    
                tmp = "Userinfo: hosts: "
                _user = command.bot.subsystems["access"].getUser(user)
                
                if _user:
                    for host in _user.hosts:
                        tmp += host + ", "
                    
                    command.result.append(tmp + "owner: " + str(_user.owner) + ", master: " + str(_user.master) + ", trusted: " + str(_user.trusted) + ", blacklisted: " + str(_user.blacklisted) + ", banned: " + str(_user.banned))
            
                else:
                    command.result.append("User " + user + " doesn't exist")
        
        elif users[0] == "del":
            for user in users:
                if user == "add" or user == "del" or user == "get":
                    continue
                    
                if command.bot.subsystems["access"].getUser(user):
                    command.bot.subsystems["access"].delUser(user)
                    
                    if user in users: del _users[user]

                    command.result.append("Removed user " + user)
                    continue
                    
                elif not command.bot.subsystems["access"].getUser(user):
                    command.result.append("User " + user + " doesn't exist")
                    
            command.bot.subsystems["conf"].setItem("users", _users)
        
        return command
    
    @Decorators.master
    def allow(command):
        command.result = []
        channels = command.message.split(" ")
        
        if channels[0] == "add":
            allowedchannels = command.bot.subsystems["conf"].getItem("allowedchannels", [])
            trustedchannels = command.bot.subsystems["conf"].getItem("trustedchannels", [])
            
            for channel in channels:
                if channel == "add" or channel == "del" or channel == "get":
                    continue
        
                if channel.startswith("#"):
                    if channels[1] == "trusted" and channel not in command.bot.subsystems["access"].trustedChannels:
                        command.bot.subsystems["access"].trustedChannels.append(channel)
                        command.result.append("Added channel " + channel + " to trusted channels")
                        
                        if channel not in trustedchannels:
                            trustedchannels.append(channel)
                        
                    elif channel not in command.bot.subsystems["access"].allowedChannels:
                        command.bot.subsystems["access"].allowedChannels.append(channel)
                        command.result.append("Added channel " + channel + " to allowed channels")
                        
                        if channel not in allowedchannels:
                            allowedchannels.append(channel)
                
                elif channel == "trusted":
                    continue
                    
                else:
                    command.result.append("Channel " + channel + " isn't named properly")
            
            if channels[1] == "trusted": command.bot.subsystems["conf"].setItem("trustedchannels", trustedchannels)
            else: command.bot.subsystems["conf"].setItem("allowedchannels", allowedchannels)
            
        elif channels[0] == "get":
            if len(channels) == 1:
                tmp = ""
                tmp2 = ""
                
                for channel in command.bot.subsystems["access"].allowedChannels:
                    tmp += channel + " "
                
                for channel in command.bot.subsystems["access"].trustedChannels:
                    tmp2 += channel + " "
                
                command.result.append("Allowed channels: " + tmp)
                command.result.append("Trusted channels: " + tmp2)
                return command
            
            elif len(channels) == 2 and channels[1] == "trusted":
                tmp = ""
                
                for channel in command.bot.subsystems["access"].trustedChannels:
                    tmp += channel + " "
                    
                command.result.append("Trusted channels: " + tmp)
                return command
            
            elif len(channels) == 2 and channels[1] == "allowed":
                tmp = ""
                
                for channel in command.bot.subsystems["access"].allowedChannels:
                    tmp += channel + " "
                    
                command.result.append("Allowed channels: " + tmp)
                return command
            
            else:
                for channel in channels:
                    if channel == "add" or channel == "del" or channel == "get":
                        continue
                        
                    tmp = ""
                    
                    if channel in command.bot.subsystems["access"].allowedChannels: tmp += "allowed: True, "
                    else: tmp += "allowed: False, "
                    if channel in command.bot.subsystems["access"].trustedChannels: tmp += "trusted: True "
                    else: tmp += "trusted: False "
                    
                    command.result.append("Channel: " + channel + ", " + tmp)
            
            
        elif channels[0] == "del":
            allowedchannels = command.bot.subsystems["conf"].getItem("allowedchannels", [])
            trustedchannels = command.bot.subsystems["conf"].getItem("trustedchannels", [])
            
            for channel in channels:
                if channel == "add" or channel == "del" or channel == "get":
                    continue
    
                if channel.startswith("#"):
                    if channels[1] == "trusted" and channel in command.bot.subsystems["access"].trustedChannels:
                        command.bot.subsystems["access"].trustedChannels.remove(channel)
                        command.result.append("Removed channel " + channel + " from trusted channels")
                        
                        if channel in trustedchannels:
                            trustedchannels.remove(channel)
                        
                    elif channel in command.bot.subsystems["access"].allowedChannels:
                        command.bot.subsystems["access"].allowedChannels.remove(channel)
                        command.result.append("Removed channel " + channel + " from allowed channels")
                        
                        if channel in allowedchannels:
                            allowedchannels.remove(channel)
                    
                    else:
                        command.result.append("Channel " + channel + " doesn't exist")
                
                elif channel == "trusted":
                    continue
                
                else:
                    command.result.append("Channel " + channel + " isn't named properly")
        
            if channels[1] == "trusted": command.bot.subsystems["conf"].setItem("trustedchannels", trustedchannels)
            else: command.bot.subsystems["conf"].setItem("allowedchannels", allowedchannels)
            
        return command
        
    @Decorators.master
    def timer(command):
        """
            Adds a timer that runs until system's time reaches the wanted time. It then sends back a
            message to the user who set the timer. The message that is returned is the part of the message
            that comes after the time.
            
            Syntax: !timer [name] [time] [message]
            Example: !timer hey 00:00:00 hello!
            
            Timer can be canceled by sending a message "[name] cancel".
        """
        
        if len(command.message) < 3:
            command.result = "Your message was not complete"
            return command
            
        register = command.message.split(" ", 2)
        
        # Make sure the given time is valid (24 h clock)
        if match("[0-2]\d+:[0-6]\d:[0-6]\d", register[1]) != None:
            tmp = register[1].split(":")
            
            if len(tmp) == 3:
                try:
                    if int(tmp[0]) > 23 or int(tmp[1]) > 60 or int(tmp[2]) > 60:
                        command.result = "Time is not valid"
                        return command
                        
                except:
                    command.result = "Time is not valid"
                    return command
        
        else:
            command.result = "Time is not valid"
            return command
        
        command.bot.registeredFunctions.append(register[0])
        command.bot.irc.sendMessage(command.server, command.channel, "Scheduled timer for " + register[1])
        running = True
        
        while running:
            currTime = strftime("%H:%M:%S")
            
            if currTime == register[1]:
                command.result = command.sender + ": " + register[2]
                command.bot.registeredFunctions.remove(register[0])
                running = False
        
            if not command.bot.messageInputQueue.empty():
                tmp = command.bot.messageInputQueue.get()
                
                if tmp[0] == register[0]:
                    if tmp[1].command == register[0]:
                        if tmp[1].message.lower() == "cancel":
                            command.bot.irc.sendMessage(tmp[1].server, tmp[1].channel, "Timer task " + register[0] + " canceled")
                            command.bot.registeredFunctions.remove(register)
                            running = False
        
                else: command.bot.messageInputQueue.put(tmp)
                
            sleep(0.3)
            
        return command
    