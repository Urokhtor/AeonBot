from threading import Lock

class Logging:
    """
        This class stores different types of logging information in buffers and also displays
        the information on screen if verbose level defines so.
    """
    
    def __init__(self):
        # These flags work as verbose flags.
        self.infoLoggingVerbose = True
        self.debugLoggingVerbose = False
        self.errorLoggingVerbose = True
        
        self.infoBuffer = []
        self.debugBuffer = []
        self.errorBuffer = []
        
        self.infoBufferSize = 100
        self.debugBufferSize = 100
        self.errorBufferSize = 100
        
        self.infoLock = Lock()
        self.debugLock = Lock()
        self.errorLock = Lock()
    
    def setInfoLogging(self, flag):
        """
            Sets info message logging either on or off.
        """
        
        self.infoLoggingVerbose = flag
    
    def getInfoLogging(self):
        """
            Returns whether info logging is on or off.
        """
        
        return self.infoLoggingVerbose
    
    def info(self, server, message):
        """
            Handles logging of info level messages, that contain normal server and channel
            traffic. These messages will be logged in terminal if infoLoggingVerbose has
            value True, which it has by default. Independent from this, info messages are
            always logged in infoBuffer. In case of buffer filling up, the oldest line is
            always discarded.
        """
        
        self.infoLock.acquire()
        if len(self.infoBuffer) >= self.infoBufferSize:
            del self.infoBuffer[0]
        
        self.infoBuffer.append(server + " " + message)
        self.infoLock.release()
        
        if self.infoLoggingVerbose:
            self.logLine(server, message)
    
    def getInfo(self):
        """
            Returns a copy of infoBuffer.
        """
        
        tmp = self.infoBuffer
        return tmp
    
    def setInfoBufferSize(self, size):
        """
            Sets the info buffer size in lines stored to the buffer.
        """
        
        self.infoBufferSize = size
    
    def getInfoBufferSize(self):
        """
            Returns the size of info buffer. The value represents number of lines that
            buffer may contain.
        """
        
        return self.infoBufferSize
    
    def setDebugLogging(self, flag):
        self.debugLoggingVerbose = flag
    
    def getDebugLogging(self):
        return self.debugLoggingVerbose
        
    def debug(self, server, message):
        self.debugLock.acquire()
        if len(self.debugBuffer) >= self.debugBufferSize:
            del self.debugBuffer[0]
            
        self.debugBuffer.append(server + " " + message)        
        self.debugLock.release()
        
        if self.debugLoggingVerbose:
            self.logLine(server, message)
    
    def getDebug(self):
        tmp = self.debugBuffer
        return tmp
        
    def setDebugBufferSize(self, size):
        self.debugBufferSize = size
    
    def getDebugBufferSize(self):
        return self.debuBufferSize
    
    def setErrorLogging(self, flag):
        self.errorLoggingVerbose = flag
    
    def getErrorLogging(self):
        return self.errorLoggingVerbose
    
    def error(self,server, message):
        self.errorLock.acquire()
        if len(self.errorBuffer) >= self.errorBufferSize:
            del self.errorBuffer[0]
            
        self.errorBuffer.append(server + " " + message)
        self.errorLock.release()
        
        if self.errorLoggingVerbose:
            self.logLine(server, message)
    
    def getError(self):
        tmp = self.errorBuffer
        return tmp
            
    def setErrorBufferSize(self, size):
        self.errorBufferSize = size
    
    def getErrorBufferSize(self):
        return self.errorBufferSize
    
    def logLine(self, server, message):
        print(server + " " + message)