from AeonBot.AeonBot import AeonBot
from time import sleep
from queue import Queue
from threading import Thread
from Utils.Modules import Modules

class DefaultBot(AeonBot):

    def __init__(self):
        AeonBot.__init__(self)
        
        # Set which messages are logged.
        self.logging.setInfoLogging(False)
        self.logging.setDebugLogging(False)
        #self.logging.setErrorLogging(False)
        
        self.subsystems = {}
        
        # Subsystem handling loading modules.
        self.subsystems["modules"] = Modules()
        self.subsystems["modules"].loadModule("Utils.Config")
        
        # Load the conf file into memory.
        self.subsystems["conf"] = self.subsystems["modules"].getModule("Utils.Config")("config.json")
        
        # Load command modules.
        for module in self.subsystems["conf"].getItem("modules", ""):
            self.subsystems["modules"].loadModule(module)
            
        # Read some IRC arguments from conf.
        self.name = self.subsystems["conf"].getItem("name", "Default")
        self.login = self.subsystems["conf"].getItem("login", "aeonbot")
        self.realname = self.subsystems["conf"].getItem("realname", "AeonBot")
        
        # Authpassword is the password used to authenticate on a network.
        # API keys are used to access certain sites' API functionality.
        self.authPasswords = {}
        self.lastFmAPIKey = self.subsystems["conf"].getItem("lastfmAPI", "")
        self.youtubeAPIKey = self.subsystems["conf"].getItem("youtubeAPI", "")
        
        # Loop through all the networks and connect them, also store auth
        # password in memory if one is found.
        if self.subsystems["conf"].data["networks"] is None: self.subsystems["conf"].data["networks"] = {}
        for name, data in self.subsystems["conf"].getItem("networks", {}).items():
            server = ""
            port = 6667
            authpass = ""
            
            for key, val in data.items():
                if key == "hostname": server = val
                elif key == "port":
                    try: port = int(val)
                    except ValueError: pass
                elif key == "authpass": authpass = val
            
            if server != "":
                self.authPasswords[server] = authpass
                self.irc.connect(self.name, self.login, self.realname, server, port)
        
        # Functions can register here to receive messages.
        self.registeredFunctions = []
        self.messageInputQueue = Queue()
        
        # Set up the IRCCommand interface and command output queue which listens to
        # return values from executed commands.
        self.commandPrefix = self.subsystems["conf"].getItem("commandprefix", "!")
        self.commandOutputQueue = Queue()
        self.commandOutputThread = Thread(target = self.commandOutputHandler).start()
        self.subsystems["IRCCommand"] = self.subsystems["modules"].getModule("IRCCommand.IRCCommand")(self)
        
        # Set up user privilege systems.
        self.subsystems["access"] = self.subsystems["modules"].getModule("Utils.AccessControl")(self.subsystems["conf"])
    
    # This method is automatically called when bot establishes a connection to some server.
    def onConnect(self, server):
        self.logging.setInfoLogging(True)
        for network, data in self.subsystems["conf"].getItem("networks", {}).items():
            if network == "Quakenet":
                self.irc.sendMessage(server, "Q@CServe.quakenet.org", "auth " + self.name + " " + self.authPasswords[server])
                self.irc.sendRawLine(server, "MODE " + self.irc.ConnectionManager[server].getNick() + " :+x")
            
                for key, value in data.items():
                    if key == "channels":
                        for channel in value:
                            self.irc.join(server, channel)
    
    # Normal channel messages call this method.
    def onMessage(self, server, channel, sender, login, hostname, message):
        # Check if user is banned, if so don't let bot even try to call any function.
        user = self.subsystems["access"].getUser(sender)
        
        if user:
            if user.banned:
                return
        
        # Call command dispatcher if message starts with commandprefix and doesn't consist
        # only of it. (If command prefix is "!", don't call command dispather if message == "!")
        if message[0] == self.commandPrefix and len(message) > 1:
            self.subsystems["IRCCommand"].dispatchCommand(server, channel, sender, login, hostname, message.split(self.commandPrefix, 1)[1], "message")
        
        # Bypass command prefix if message contains URL(s) and isn't a command. Calls resolveURL from
        # BasicCommand.
        elif message.find("http://") != -1 or message.find("https://") != -1 or message.find("www.") != -1:
            self.subsystems["IRCCommand"].dispatchCommand(server, channel, sender, login, hostname, "resolveURL " + message, "message")
        
        # If there are registered functions and message hasn't been dispatched yet, do it now.
        elif len(self.registeredFunctions) > 0:
            self.subsystems["IRCCommand"].dispatchCommand(server, channel, sender, login, hostname, message, "message")
        
    # Just like with messages, if bot receives a private message, it calls this function.
    def onPrivateMessage(self, server, sender, login, hostname, message):
        user = self.subsystems["access"].getUser(sender)
        
        if user:
            if user.banned:
                return
                
        if message[0] == self.commandPrefix and len(message) > 1:
            self.subsystems["IRCCommand"].dispatchCommand(server, sender, sender, login, hostname, message.split(self.commandPrefix, 1)[1], "query")
        
        elif message.find("http://") != -1 or message.find("https://") != -1 or message.find("www.") != -1:
            self.subsystems["IRCCommand"].dispatchCommand(server, sender, sender, login, hostname, "resolveURL " + message, "query")
    
        elif len(self.registeredFunctions) > 0:
            self.subsystems["IRCCommand"].dispatchCommand(server, sender, sender, login, hostname, message, "query")
    
    # This function is called when someone does a /me.
    def onAction(self, server, channel, sender, login, hostname, message):
        user = self.subsystems["access"].getUser(sender)
        
        if user:
            if user.banned:
                return
                
        self.subsystems["IRCCommand"].dispatchCommand(server, channel, sender, login, hostname, message, "action")
    
    # All server actions call this function. It lets the user read the bot's raw message queue.
    # Useful for things like if you need to /whois a user. Just register a function and grab the
    # whois stream.
    def onServerResponse(self, server, code, response):
        # Placeholder
        pass
    
    # When bot reseives an invite.
    def onInvite(self, server, target, sender, login, hostname):
        if command.bot.subsystems["access"].getUser(sender).owner:
            self.irc.join(server, target)
    
    def commandOutputHandler(self):
        """
            Polls for responses from command handles and then sends the resulting messages to the server
            accordingly. The handler should be capable of handling any type that can be converted to string.
            Also lists are allowed, they will simply be looped through and sent to the server separately.
        """
        
        try:
            while self.running:
                # If all registered functions have exited and there's still something left in the queue,
                # flush it empty.
                if not self.messageInputQueue.empty() and len(self.registeredFunctions) == 0:
                    while not self.messageInputQueue.empty():
                        self.messageInputQueue.get()
                    
                if not self.commandOutputQueue.empty():
                    command = self.commandOutputQueue.get()
                    
                    try:
                        if command.result != "":
                            if command.type == "subsystem reload" and command.command == "subsystem":
                                if isinstance(command.result, list):
                                    for line in command.result:
                                        line = str(line)
                                        
                                        if line in self.subsystems:
                                            if line == "access":
                                                self.subsystems["access"] = self.subsystems["modules"].getModule("Utils.AccessControl")(self.subsystems["conf"])
                            
                                            # Not working DAMMIT!
                                            elif line == "IRCCommand":
                                                self.irc.sendMessage(command.server, command.channel, "Reloading IRCCommand isn't supported at this time")
                                                continue
                                            #    self.subsystems["IRCCommand"] = self.subsystems["modules"].getModule("IRCCommand.IRCCommand")(self)
                                                
                                            elif line == "conf":
                                                self.subsystems["conf"] = self.subsystems["modules"].getModule("Utils.Config")("config.json")
                                            
                                            elif line == "modules":
                                                self.subsystems["modules"] = Modules()
                                                self.subsystems["modules"].loadModule("Utils.Config")
                                                
                                                # Load command modules.
                                                for module in self.subsystems["conf"].getItem("modules", ""):
                                                    self.subsystems["modules"].loadModule(module)
                                            
                                            self.irc.sendMessage(command.server, command.channel, "Reloaded subsystem " + line)
                                        
                                        else:
                                            self.irc.sendMessage(command.server, command.channel, "Subsystem " + line + " doesn't exist")

                            elif command.type == "message" or command.type == "query":
                                if isinstance(command.result, list):
                                    for line in command.result:
                                        self.irc.sendMessage(command.server, command.channel, str(line))
                                    
                                else:
                                    self.irc.sendMessage(command.server, command.channel, str(command.result))
                                        
                            elif command.type == "action":
                                # Because if action comes from a private message, the channel is the bot itself
                                # and sender is the "channel", we need to correct it here so we don't send actions
                                # to ourselves.
                                if command.channel == self.irc.ConnectionManager[command.server].getNick():
                                    command.channel = command.sender
                                    
                                if isinstance(command.result, list):
                                    for line in command.result:
                                        self.irc.sendAction(command.server, command.channel, str(line))
                                
                                else:
                                    self.irc.sendAction(command.server, command.channel, str(command.result))
                                        
                            elif command.type == "raw":
                                if isinstance(command.result, list):
                                    for line in command.result:
                                        self.irc.sendRawLine(command.server, str(line))
                                
                                else:
                                    self.irc.sendRawLine(command.server, str(command.result))
                                        
                            else: self.logging.error(command.server, "CommandOutputHandler could not identify the command type " + command.type + ".")
                        
                    except:
                        pass
                
                else:
                    sleep(0.2)
        
        finally:
            self.logging.error("Core message", "Command output handler has crashed.")
            
def main():
    bot = DefaultBot()

    while bot.running:
        sleep(0.1)

if __name__ == "__main__":
    main()