from abc import ABCMeta
from abc import abstractmethod
from time import strftime

class EventHandler:
    """
        EventHandler is the interface used to relay events to the user. The user must override the functions
        described here in order to catch all the events, because the functions described here are called by
        EventDispatcher.
    """
    
    __metaclass__ = ABCMeta
    
    def __init__(self, irc, logging):
        self.irc = irc
        self.logging = logging
        self.finger = "Stop fingering me you, you freaking pervert!"
        self.version = 0.7
        self.versionMessage = "AeonBot version " + str(self.version)
    
    @abstractmethod
    def onConnect(self, server):
        """
            This method is called when we have successfully established a connection to the server in
            question. This happens when we get a RPL_ENDOFMOTD reply from the server. This method is called
            always when a new connection is established.
        """
        
        pass
    
    @abstractmethod
    def onDisconnect(self, server):
        """
            This method is called when connection detects it doesn't receive a ping response back from server.
            The autoreconnection is enabled by default and it tries to engage a new connection after waiting
            for a brief time. Before user attempts their own reconnection methods, autoreconnection should be
            disabled for the connection.
        """
        
        pass
    
    @abstractmethod
    def onAction(self, server, channel, sender, login, hostname, message):
        """
            This method is called when someone performs a /me.
        """
        
        pass
    
    @abstractmethod
    def onMessage(self, server, channel, sender, login, hostname, message):
        """
            Called when someone sends a message to the channel.
        """
        
        pass
    
    @abstractmethod
    def onPrivateMessage(self, server, sender, login, hostname, message):
        """
            Like onMessage(), but called when the message doesn't come from a channel.
        """
        
        pass
    
    @abstractmethod
    def onJoin(self, server, channel, name, login, hostname):
        pass
    
    @abstractmethod
    def onPart(self, server, channel, name, login, hostname):
        pass
    
    @abstractmethod
    def onNick(self, server, name, login, hostname, target):
        pass
    
    @abstractmethod
    def onNotice(self, server, target, name, login, hostname, message):
        pass
    
    @abstractmethod
    def onQuit(self, server, name, login, hostname, message):
        pass
    
    @abstractmethod
    def onKick(self, server, channel, name, login, hostname, recipient, message):
        pass
    
    @abstractmethod
    def onMode(self, server, target, name, login, hostname, message):
        pass
    
    @abstractmethod
    def onTopic(self, server, target, name, login, hostname, message):
        pass
    
    @abstractmethod
    def onInvite(self, server, target, name, login, hostname):
        pass
    
    @abstractmethod
    def onVersion(self, server, sender, login, hostname, target):
        self.irc.ConnectionManager[server].sendVersion(sender, self.versionMessage)
    
    def onPing(self, server, sender, login, hostname, target, pingValue):
        self.irc.ConnectionManager[server].sendPong(sender, pingValue)
    
    def onTime(self, server, sender, login, hostname, target):
        self.irc.ConnectionManager[server].sendTime(sender, strftime("%a, %d %b %Y %H:%M:%S"))
    
    def onFinger(self, server, sender, login, hostname, target):
        self.irc.ConnectionManager[server].sendFinger(sender, self.finger)
    
    @abstractmethod
    def onUnknown(self, line):
        pass
    
    def onServerPing(self, server, pingValue):
        """
            This method is vital, no sense really to tweak it. Here we respond to the server ping request.
            We can not connect to some networks without handling this event so do not remove this behaviour.
        """
        
        self.irc.ConnectionManager[server].sendRawLine("PONG " + pingValue)
    
    def onNickInUse(self, server):
        """
            The default method for handling NickInUse events. User may simply override this method to
            replace the default handler.
        """
        
        self.logging.info(server, "Nick in use, attempting with alternative.")
        self.irc.ConnectionManager[server].changeNick(self.irc.ConnectionManager[server].getNick() + self.nickInUseSuffix)
    
    @abstractmethod
    def onServerResponse(self, server, code, response):
        pass
        
    """
    def onOp(server, channel, name, login, hostname, parameters):
        
    
    def onDeOp(server, channel, name, login, hostname, parameters):
        
    
    def onVoice(server, channel, name, login, hostname, parameters):
        
    
    def onDeVoice(server, channel, name, login, hostname, parameters):
        
    
    def onSetChannelKey(server, channel, name, login, hostname, parameters):
        
        
    def onRemoveChannelKey(server, channel, name, login, hostname, parameters):
        
            
    def onSetChannelLimit(server, channel, name, login, hostname, parameters):
        
    
    def onRemoveChannelLimit(server, channel, name, login, hostname):
        
    
    def onSetChannelBan(server, channel, name, login, hostname, parameters):
        
        
    def onRemoveChannelBan(server, channel, name, login, hostname, parameters):
        
            
    def onSetTopicProtection(server, channel, name, login, hostname):
           
           
    def onRemoveTopicProtection(server, channel, name, login, hostname):
        
            
    def onSetNoExternalMessages(server, channel, name, login, hostname):
            
            
    def onRemoveNoExternalMessages(server, channel, name, login, hostname):
            
            
    def onSetInviteOnly(server, channel, name, login, hostname):
            
            
    def onRemoveInviteOnly(server, channel, name, login, hostname):
            
            
    def onSetModerated(server, channel, name, login, hostname):
            
            
    def onSetPrivate(server, channel, name, login, hostname):
            
            
    def onRemovePrivate(server, channel, name, login, hostname):
            
            
    def onSetSecret(server, channel, name, login, hostname):
            
            
    def onRemoveSecret(server, channel, name, login, hostname):
            
            
    #def on(server, channel, name, login, hostname):
        
    """