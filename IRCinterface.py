from AeonBot.Connection import Connection

class IRCinterface:
    """
        This class handles different connections and interfacing IRC commands with Connection class.
    """
    
    def __init__(self, inputQueue, logging, running):
        self.running = running
        
        self.servers = []
        self.ConnectionManager = {}
        self.inputQueue = inputQueue
        self.logging = logging
        
        self.quitMessage = "Test message"
    
    def connect(self, name, login, realname, server, port = 6667, password = ""):
        """
            Creates a new connection object and passes the input queue and logger to it, also the
            new connection is added to the ConnectionManager which is used to access the connection.
        """
        
        con = Connection(self.inputQueue, self.logging)
        flag = con.connect(name, login, realname, server, port, password)
        
        if flag:
            self.ConnectionManager[server] = con
            self.servers.append(server)
    
    def disconnect(self, server):
        """
            Disconnects from the defined server and removes the connection.
        """
        
        if self.ConnectionManager[server].quit(self.quitMessage):
            del self.ConnectionManager[server]
            self.servers.remove(server)
        
        self.logging.info(server, "Disconnected from the server.")
        
    def quit(self):
        """
            Closes all the connections and quits us.
        """
        
        for server in self.servers[:]:
            self.disconnect(server)
        
        self.logging.info("Core message:", "All servers closed, exiting program.")
        from os import _exit
        _exit(0)
    
    def join(self, server, channel, password = ""):
        """
            Calls the wanted server connection's join command using ConnectionManager.
        """
        
        self.ConnectionManager[server].join(channel, password)
    
    def part(self, server, channel):
        """
            Calls the wanted server connection's part command using ConnectionManager.
        """
        
        self.ConnectionManager[server].part(channel)
    
    def getConnectionManager(self):
        """
            Returns the connection manager that holds all the server connections. Use
            getConnectionManager()[server] to access the wanted server.
        """
        
        return self.ConnectionManager
        
    def getServers(self):
        """
            Returns the list containing all server connections. To access the actual ConnectionManager,
            use self.irc.getConnectionManager().
        """
        
        return self.servers
    
    def getServersToString(self):
        """
            Returns the list of servers as a single string object.
        """
        
        return " ".join(self.servers)
    
    def getChannels(self, server):
        """
            Returns the list containing all the channels we are on at a particular server.
        """
        
        return self.ConnectionManager[server].getChannelManager().getChannels()
    
    def getQuitMessage(self):
        """
            Returns the quit message which is sent to the server when disconnect is called.
        """
        
        return self.quitMessage
    
    def setQuitMessage(self, quitMessage):
        """
            Sets the quit message which is sent to the server when disconnect is called.
        """
        
        self.quitMessage = quitMessage
    
    def setOutputDelay(self, server, delay):
        """
            Sets the delay of outgoing messages on a particular server. Used as a self-flood protection so
            we don't get kicked out of the server if outputqueue gets filled up with multiple messages.
        """
        self.ConnectionManager[server].setOutputDelay(delay)
    
    def getOutputDelay(self, server):
        """
            Sets the outgoing message queue delay for a particular server.
        """
        
        return self.ConnectionManager[server].getOutputDelay()
    
    def sendAction(self, server, channel, message):
        """
            Sends a /me action on defined target (channel/user).
        """
        
        self.ConnectionManager[server].sendAction(channel, message)
    
    def sendMessage(self, server, channel, message):
        """
            Sends a normal message to channel or query.
        """
        
        self.ConnectionManager[server].sendMessage(channel, message)
    
    def sendRawLine(self, server, message):
        """
            Sends a raw line to the server.
        """
        
        self.ConnectionManager[server].sendRawLine(message)
    
    def setMode(self, server, channel, mode, parameters = ""):
        """
            Sets from one to multiple channelmodes.
        """
        
        self.ConnectionManager[server].sendRawLine("MODE " + channel + " " + mode + " " + parameters) 
    