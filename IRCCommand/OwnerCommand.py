class OwnerCommand:

    def connect(command):
        if command.sender in command.bot.owners:
            tmp = command.message.split(" ")
            port = 6667
                
            if len(tmp) > 1:
                try: port = int(tmp[1])
                except ValueError: pass
                
            command.bot.irc.connect(command.bot.name, command.bot.login, command.bot.realname, tmp[0], port)
            command.result = "Connecting to " + tmp[0]
    
        return command
    
    def disconnect(command):
        if command.sender in command.bot.owners:
            command.bot.irc.disconnect(command.message)
        
        return command
    
    def join(command):
        if command.sender in command.bot.owners:
            command.bot.irc.join(command.server, command.message)
                
        return command
    
    def part(command):
        if command.sender in command.bot.owners:
            command.bot.irc.part(command.server, command.message)
                
        return command
    
    def quit(command):
        if command.sender in command.bot.owners:
            command.bot.irc.quit()
                
        return command
    
    def load(command):
        if command.sender in command.bot.owners and command.message != "":
            if command.bot.IRCCommand.loadModule(command.message):
                command.result = "Loaded module " + command.message
            else:
                command.result = "Couldn't load module " + command.message
        
        return command
        
    def reload(command):
        if command.sender in command.bot.owners and command.message != "":
            if command.bot.IRCCommand.reloadModule(command.message):
                command.result = "Reloaded module " + command.message
            else:
                command.result = "Couldn't reload module " + command.message
        
        return command