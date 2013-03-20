from queue import Queue
import socket
from threading import Thread
from time import sleep, time

class Connection:
    """
        This class handles the connecting to a single server and provides the required communication
        interface between client and server.
    """
    
    def __init__(self, inputQueue, logging):
        self.running = True # This variable defines when input thread is running.
        self.IRCsocket = {} # We store the connection here.
        self.logging = logging
        self.inputQueue = inputQueue # We want to use one queue for all input operations that are handled by the core.
        self.outputQueue = Queue() # We want to have an outputqueue for each connection because otherwise with many servers handling output would be difficult and slow.
        self.ChannelManager = ChannelManager() # List of channels we are currently on this server.
        self.outputDelay = 0.5 # Output message delay. Prevents getting killed by server because of flooding.
        self.inputThread = Thread(target = self.fetchLine)
        self.outputThread = Thread(target = self.sendLine)
        
        self.isConnected = False
        self.isConnectedTimer = Timer()
        self.autoReconnect = True
        self.pingPongResponse = ""

        self.name = ""
        self.login = ""
        self.realname = ""
        self.server = ""
        self.port = 0
        self.password = ""
        
        self.encodings = ["utf-8", "iso-8859-1"]
        self.__maxLineLength = 510
    
    def getChannelManager(self):
        """
            Returns the list of channels we're on.
        """
        
        return self.ChannelManager
    
    def getOutputQueue(self):
        """
            Returns the queue that relays all the lines going from client to server.
        """
        
        return self.outputQueue
    
    def setOutputDelay(self, delay):
        """
            Sets the delay which defines the interval of messages sent to server. This works as a
            way for flooding prevention.
        """
        
        self.outputDelay = delay
    
    def getOutputDelay(self):
        """
            Returns the delay interval which works as a way for flooding prevention.
        """
        
        return self.outputDelay
    
    def getNick(self):
        """
            Returns the name we have on this specific server.
        """
        
        return self.name
    
    def getLogin(self):
        """
            Returns the login we have on this specific server.
        """
        
        return self.login
    
    def getRealname(self):
        """
            Returns the realname we have on this specific server.
        """
        
        return self.realname
    
    def getPort(self):
        """
            Returns the port we are connected to.
        """
        
        return self.port
    
    def getPassword(self):
        """
            Returns the server password that was used for connecting. Might contain something, or
            be just an empty string if no password was required.
        """
        
        return self.password
    
    def getMaxLineLength(self):
        """
            Returns the maximum length of one line that can be sent to server. It's protocol defined,
            so it should never be changed.
        """
        
        return self.__maxLineLength
    
    def setAutoReconnect(self, flag):
        """
            Enables or disables autoreconnection handling.
        """
        
        self.autoReconnect = flag
        
    def getAutoReconnect(self):
        """
            Returns whether the autoreconnection handling is enabled or disabled.
        """
        
        return self.autoReconnect
    
    def connect(self, name, login, realname, server, port = 6667, password = ""):
        """
            Attempts to establish a connection to an IRC server and supplies it with the basic info
            needed for establishing a successful connection, like nick, login and realname. Also input
            and output threads are started when the connection is ready.
        """
        
        self.name = name
        self.login = login
        self.realname = realname
        self.server = server
        self.port = port
        self.password = password
        
        # First we try to open a socket to the wanted server.
        try:
            self.logging.info(self.server, "Opening socket to %s:%s..." %(self.server, self.port))
            self.IRCsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.IRCsocket.settimeout(5)
            self.IRCsocket.connect(((self.server + " " + self.password).strip().encode(self.encodings[0]), self.port))
            
            if not self.inputThread.isAlive(): self.inputThread.start() # Start the input thread.
            if not self.outputThread.isAlive(): self.outputThread.start() # Start the output thread.
            
        except Exception as e:
            self.logging.error(self.server, "Failed to connect to server " + self.server + ", reason: " + str(e))
            self.IRCsocket.close()
            return False
        
        # If previous step was successful, identify with server.
        try:
            self.logging.info(self.server, "Connecting to %s:%s..." %(self.server, self.port))
            self.outputQueue.put("NICK %s" %(self.name)) # Request nick from server.
            self.outputQueue.put("USER %s 8 * :%s" %(self.login, self.realname)) # Tell user info. 8 request we are set invisible and * is discarded by server.
            
        except Exception as e:
            self.logging.error(self.server, "Failed to send information to server " + self.server + ", reason: " + str(e))
            self.IRCsocket.close()
            return False
        
        self.isConnected = True
        self.isConnectedTimer.Reset()
        self.logging.info(self.server, "Connection successfully established")
        return True
        
    def reconnect(self):
        """
            Just a simple method to make it easier to reconnect to a server if we get disconnected. Passes
            the user information to the connect() method instead of making user to re-input it all again.
        """
        
        return self.connect(self.name, self.login, self.realname, self.server, self.port, self.password)
        
    def join(self, channel, password = ""):
        """
            Attempts to join a channel. If we're already on that channel, the user is notified and attempt
            is aborted.
        """
        
        if channel in self.ChannelManager.getChannels():
            self.logging.error(self.server, "You are already on " + channel)
            return
        
        if password == "": self.outputQueue.put("JOIN " + channel) # Add exception handling if can't join
        else: self.outputQueue.put("JOIN " + channel + " " + password)
        
        self.ChannelManager.addChannel(channel)
    
    def part(self, channel):
        """
            Either parts a channel of notifies user if it tries to leave a channel we are not on.
        """
        
        if channel in self.ChannelManager.getChannels():
            self.outputQueue.put("PART " + channel)
            self.ChannelManager.removeChannel(channel)
        
        else:
            self.logging.error(self.server, "Can't part from " + channel + ": You are not on that channel!")
    
    def quit(self, reason = ""):
        """
            Shuts down the input and output threads and closes the socket connection.
        """
        
        self.sendRawLine("QUIT :" + reason) # MAKE THIS WORK
        self.running = False
        sleep(self.outputDelay) # Give threads some time to finish.
        self.IRCsocket.shutdown(socket.SHUT_RDWR)
        self.IRCsocket.close()
        
        return True
    
    def kick(self, channel, target, message):
        """
            Kicks someone from the channel, optionally with a kick message.
        """
        
        self.outputQueue.put("KICK " + channel + " " + target + " " + message)
    
    def sendVersion(self, sender, version):
        """
            Sends a VERSION CTCP command to the server.
        """
        
        self.outputQueue.put("NOTICE " + sender + " :\001VERSION " + version + "\001")
    
    def sendPong(self, sender, pingValue):
        """
            Sends a PING CTCP command to the server
        """
        
        self.outputQueue.put("NOTICE " + sender + " :\001PONG " + pingValue + "\001")
        
    def sendTime(self, sender, timeValue):
        """
            Sends a TIME CTCP command to the server.
        """
        
        self.outputQueue.put("NOTICE " + sender + " :\001TIME " + timeValue + "\001")
        
    def sendFinger(self, sender, fingerMessage):
        """
            Sends a FINGER CTCP command to the server
        """
        
        self.outputQueue.put("NOTICE " + sender + " :\001FINGER " + fingerMessage + "\001")
    
    def sendAction(self, channel, message):
        """
            Sends an action to the channel, which might also mean user.
        """
        
        self.outputQueue.put("PRIVMSG " + channel + " :\001ACTION " + message + "\001")
         
    def sendMessage(self, channel, message):
        """
            Sends a message to a channel, might also be a private message.
        """
        
        self.outputQueue.put("PRIVMSG " + channel + " :" + message)
         
    def sendRawLine(self, message):
        """
            Sends a raw line to the server.
        """
        
        self.outputQueue.put(message)
        
    def changeNick(self, newNick):
        """
            Sends NICK command to the server.
        """
        
        self.outputQueue.put("NICK " + newNick)
        self.name = newNick
    
    def sendLine(self):
        """
            This method processes the line to a suitable form for server and then relays it.
        """
        
        try:
            while self.running:
                try:
                    # Don't try to use socket while we're disconnected, check each second whether the
                    # connection has been resumed for us.
                    while not self.isConnected:
                        sleep(1)
                        
                    if not self.isConnectedTimer.getResponseWaitMode():
                        if (self.isConnectedTimer.getElapsedTime() - self.isConnectedTimer.getStartTime()) > self.isConnectedTimer.waitTime:
                            self.pingPongResponse = ":666"
                            success = self.IRCsocket.sendall(("PING " + self.pingPongResponse + "\r\n").encode(self.encodings[0]))
                            self.logging.debug(self.server, "PING " + self.pingPongResponse)
                            self.isConnectedTimer.toggleResponseWaitMode()
                    
                    if not self.outputQueue.empty():
                        line = self.outputQueue.get()
                        
                        # We don't want to send any null lines to server.
                        if line == "": continue
                        
                        # Discard spaces from both ends because we don't need them.
                        line.strip()
                        
                        # If line is longer than the server supports, discard rest of it. Just a quick hack
                        # FIX THIS LATER to support sending message in many parts.
                        if len(line) > self.__maxLineLength: line = line[:self.__maxLineLength]
                        
                        success = self.IRCsocket.sendall((line + "\r\n").encode(self.encodings[0]))
                        
                        if not success == None: self.logging.error(self.server, "The line '" + line + "' wasn't delivered properly.") 
                        elif line.startswith("PONG"): self.logging.debug(self.server, line) # We do not want to see the ping/pong spam when we're using the bot normally.
                        else: self.logging.info(self.server, line)
                            
                        sleep(self.outputDelay)
                
                    else:
                        sleep(0.1)
                
                except Exception as e:
                    self.logging.error(self.server, "Output handler encountered an error: " + str(e))
        
        finally:
            self.logging.error(self.server, "Closing output connection to server.")
    
    def fetchLine(self):
        """
            This method reads the socket's input buffer, decodes it, parses it into whole lines
            and dispatches the message to message handler.
        """
        
        try:
            tmp = ""
            
            while self.running:
                try:
                    # Update timer and then check if we have lost connection to the server. This check
                    # relies on isConnectedTimer's waitmode; if timer is waiting for server response and
                    # it doesn't arrive in set time (responseWaitTime), then we have lost connection to
                    # the server and we need to handle the routines for informing the user and possibly
                    # trying to autoreconnect.
                    self.isConnectedTimer.Update()
                    if self.isConnectedTimer.getResponseWaitMode() and (self.isConnectedTimer.getResponseElapsedTime() - self.isConnectedTimer.getResponseStartTime()) > self.isConnectedTimer.responseWaitTime:
                        self.isConnected = False
                        self.inputQueue.put(self.server + " DISCONNECTION") # Fix this!
                        
                        if self.autoReconnect:
                            while self.isConnected == False:
                                self.logging.error(self.server, "Lost connection to server. Attempting to reconnect in 15 seconds...")
                                sleep(15)
                                self.reconnect()
                    
                    # Try to read from socket and handle the timeout error that is raised if no
                    # data is received. Timeout is used to keep the timer happy.
                    try:
                        messageBuffer = self.IRCsocket.recv(4096)
                    
                    except socket.error as e:
                        continue
                    
                    # Try to decode the received line(s).
                    for encoding in self.encodings:
                        try:
                            messageBuffer = messageBuffer.decode(encoding)
                            break
                        
                        except UnicodeDecodeError:
                            pass
                    
                    # If line(s) couldn't be decoded, discard it and send an error message to the logger.
                    if type(messageBuffer) == bytes:
                        self.logging.error(self.server, "Couldn't decode line: " + messageBuffer.decode("iso-8859-1", "ignore"))
                        continue
                    
                    msg = messageBuffer.split("\r\n")
                    
                    # Loop through message array and process lines. Use tmp field to glue together
                    # lines that socket.recv() cut in half. Other messages than PING requests seem
                    # to have at least 4 spaces so that is a good indicator to whether the line
                    # was completely read by the buffer or not.
                    for line in msg:
                        line = tmp + line
                        tmp = ""
                            
                        if line == "": continue
                        elif not messageBuffer.endswith("\r\n") and messageBuffer.endswith(line): tmp = line
                        else:
                            self.inputQueue.put(self.server + " " + line)
                            
                            # OK I know this isn't pretty or anything, but who the fuck wants to see those
                            # continuous PING requests that are useless for the users?
                            if line.startswith("PING"): self.logging.debug(self.server, line)
                            elif line.find(self.pingPongResponse) != -1 and self.isConnectedTimer.getResponseWaitMode():
                                self.pingPongResponse = ""
                                self.logging.debug(self.server, line)
                                self.isConnectedTimer.toggleResponseWaitMode()
                            else: self.logging.info(self.server, line)
                        
                    sleep(0.1)
                    
                except socket.error as e:
                    self.logging.error(self.server, "Input handler encountered an error: %s"  %(str(e)))
                
                # If decoding fails, discard the line(s) and move on.
                except:
                    self.logging.error(self.server, "Couldn't decode a line, discarding it.")

        finally:
            self.logging.error(self.server, "Closing input connection to server.")

class ChannelManager:
    """
        A simple class for holding channels and accessing them and their users.
    """
    
    def __init__(self):
        self.channels = {}
    
    def getChannels(self):
        """
            Returns the dict holding all the channels.
        """
        
        return self.channels
    
    def getChannelsToString(self):
        """
            Returns a string presentation of the channel list.
        """
        
        return " ".join(self.channels)
    
    def getChannel(self, channel):
        """
            Returns the channel object with the specified name.
        """
        
        if channel in self.channels:
            return self.channels[channel]
    
    def addChannel(self, channel):
        """
            Adds channel to the channel list if it doesn't exist yet.
        """
        
        if channel in self.channels:
            return
        
        self.channels[channel] = Channel(channel)
    
    def removeChannel(self, channel):
        """
            Removes the channel with the specified name from the channel list.
        """
        
        if not channel in self.channels:
            return
        
        del self.channels[channel]
    
    def findChannel(self, channel):
        """
            Returns true if channel with given name exists in the channel list.
        """
        
        if channel in self.channels:
            return True
            
        else:
            return False
        
class Channel:
    """
        This class holds information of the channel name and the list of users on the channel.
    """
    
    def __init__(self, name):
        self.name = name
        self.users = []
    
    def getUsers(self):
        """
            Return the actual user list.
        """
        return self.users
    
    def getUser(self, user):
        """
            Return user by name. Be sure to use findUser() to check whether the wanted user exist because
            this function currently doesn't handle checking for user's existance.
        """
        
        if user.startswith("@") or user.find("+") != -1:
            user = user[1:]
        
        for existingUser in self.users:
            if existingUser.getNick() == user:
                return existingUser
    
    def getUsersToString(self):
        """
            Return the string representation of the user list.
        """
        
        users = ""
        
        for user in self.users:
            users += user.getPrefix() + user.getNick() + " "
        
        return users.strip()
    
    def addUser(self, user):
        """
            #Adds a new user to the channel's userlist. If user was already on the channel and we try to
            #add it again, method will return False, otherwise it will return True.
        """
        
        prefix = ""
        
        # Process the prefix separately.
        if user.startswith("@") or user.find("+") != -1:
            prefix = user[:1]
            user = user[1:]
        
        for existingUser in self.users:
            if existingUser.getNick() == user:
                if existingUser.getPrefix() != prefix: # User exists but prefix is different. Can happen if we enter an empty channel.
                    if prefix == "@": existingUser.addOp()
                    elif prefix == "+": existingUser.addVoice()
                    return True
                return False # User already exists and prefix is the same.
        
        self.users.append(User(user, prefix))
        return True # Successfully added user.
    
    def removeUser(self, user):
        """
            Removes an user from channel's list. Will return True if user was removed, and returns False if
            the user wasn't found.
        """
        
        # Process the prefix separately.
        if user.startswith("@") or user.find("+") != -1:
            user = user[1:]
        
        for existingUser in self.users:
            if existingUser.getNick() == user:
                self.users.remove(existingUser)
                return True # Found user and removed.
        
        return False # User not found.
    
    def findUser(self, user):
        """
            Searches for a given user in channel's userlist. If user was found, will return True, if not,
            will return False.
        """
        
        # Process the prefix separately.
        if user.startswith("@") or user.find("+") != -1:
            user = user[1:]
            
        for existingUser in self.users:     
            if existingUser.getNick() == user:
                return True # Found user.
        
        return False # User not found.

class User:
    """
        The user class that contains user's nick and prefix (op, voice). Please notice that this implementation
        is not completely safe because of the fact that an user might have voice AND op flag when we join
        a channel and there's no way for us to know about the voice flag at that point. If the user with both
        flags gets deopped, the only ways to acquire the knowledge about the voice are either whois the user or
        chek the user flag when it sends a message to the channel after the deop event. However implementing this
        safeguard would complicate things too much so we're just trusting that this event won't happen often.
    """
    
    def __init__(self, nick, prefix):
        self.nick = nick
        self.prefix = prefix
    
    def getNick(self):
        """
            Returns the user object.
        """
        
        return self.nick
    
    def setNick(self, nick):
        """
            Sets the nick of the user.
        """
        
        self.nick = nick
    
    def getPrefix(self):
        """
            Returns the nick of the user.
        """
        return self.prefix
    
    def isOp(self):
        """
            Returns true if user has op status and false it not.
        """
        
        return True if self.prefix == "@" else False
    
    def isVoiced(self):
        """
            Returns true if user has voice status and false if not.
        """
        
        return True if self.prefix == "+" else False
    
    def addOp(self):
        """
            Gives the user op status.
        """
        
        if not self.prefix.startswith("@"):
            self.prefix = "@" + self.prefix
    
    def removeOp(self):
        """
            Removes user's op status.
        """
        
        if self.prefix.startswith("@"):
            self.prefix = self.prefix[1:]

    def addVoice(self):
        """
            Gives the user voice status.
        """
        
        if not self.prefix.endswith("+"):
            self.prefix += "+"
    
    def removeVoice(self):
        """
            Removes user's voice status.
        """
        
        if self.prefix.endswith("+"):
            self.prefix = self.prefix[:1]
            
class Timer:
    
    def __init__(self):
        self.startTime = self.getTimeSeconds()
        self.elapsedTime = self.startTime
        self.responseStartTime = self.startTime
        self.responseElapsedTime = self.startTime
        self.waitingForResponse = False
        self.waitTime = 45
        self.responseWaitTime = 15
    
    def getStartTime(self):
        return self.startTime
        
    def getElapsedTime(self):
        return self.elapsedTime
    
    def getResponseStartTime(self):
        return self.responseStartTime
        
    def getResponseElapsedTime(self):
        return self.responseElapsedTime
    
    def toggleResponseWaitMode(self):
        tmp = self.waitingForResponse
        self.Reset()
        
        if not tmp:
            self.waitingForResponse = True
    
    def getResponseWaitMode(self):
        return self.waitingForResponse
    
    def Update(self):
        if not self.waitingForResponse: self.elapsedTime = self.getTimeSeconds()
        else: self.responseElapsedTime = self.getTimeSeconds()
    
    def Reset(self):
        self.startTime = self.getTimeSeconds()
        self.elapsedTime = self.startTime
        self.responseStartTime = self.startTime
        self.responseElapsedTime = self.startTime
        self.waitingForResponse = False
        
    def getTimeSeconds(self):
        return round(time())