class Event:
    """
        Simple class containing all kinds of relevant event information. Used to keep EventDispatcher
        cleaner.
    """
    
    def __init__(self, server, type, target, name, login, hostname, message, line):
        self.server = server
        self.type = type
        self.target = target
        self.name = name
        self.login = login
        self.hostname = hostname
        self.message = message
        self.line = line # The whole, non-parsed version of the event.