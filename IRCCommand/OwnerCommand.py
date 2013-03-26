
class OwnerCommand:

    def connect(command):
        for user in command.bot.owners:
            if user == command.sender:
                tmp = command.message.split(" ")
                port = 6667
                
                if len(tmp) > 1:
                    try: port = int(tmp[1])
                    except ValueError: pass
                
                command.bot.irc.connect(command.bot.name, command.bot.login, command.bot.realname, tmp[0], port)
                command.result = "Connecting to " + tmp[0]
    
        return command
    
    def disconnect(command):
        for user in command.bot.owners:
            if user == command.sender:
                command.bot.irc.disconnect(command.message)
        
        return command
    
    def join(command):
        for user in command.bot.owners:
            if user == command.sender:
                command.bot.irc.join(command.server, command.message)
                
        return command
    
    def part(command):
        for user in command.bot.owners:
            if user == command.sender:
                command.bot.irc.part(command.server, command.message)
                
        return command
    
    def quit(command):
        for user in command.bot.owners:
            if user == command.sender:
                command.bot.irc.quit()
                
        return command