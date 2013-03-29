class Decorators:
    """
        This class contains decorator functions that control user/channel access.
        For example if you decorate a function in IRCCommand folder with @trusted, it lets
        only users that are trusted to use the function.
        
        Example usage:
        from Utils.Decorators import Decorators
        @trusted
        def myfunction(command):
            return command
    """
    
    def owner(deco_func):
        def controlAccess(arg1):
            user = arg1.bot.subsystems["access"].getUser(arg1.sender)
            
            if not user or not user.owner or arg1.host not in user.hosts:
                arg1.result = "NOTICE " + arg1.sender + " :You don't have the privilege to use this command"
                arg1.type = "raw"
                return arg1
                
            return deco_func(arg1)
                
        return controlAccess
    
    def master(deco_func):
        def controlAccess(arg1):
            user = arg1.bot.subsystems["access"].getUser(arg1.sender)

            if not user or not user.master or arg1.host not in user.hosts:
                arg1.result = "NOTICE " + arg1.sender + " :You don't have the privilege to use this command"
                arg1.type = "raw"
                return arg1
                
            return deco_func(arg1)
                
        return controlAccess
    
    def trusted(deco_func):
        def controlAccess(arg1):
            user = arg1.bot.subsystems["access"].getUser(arg1.sender)

            if not user or not user.trusted or arg1.host not in user.hosts:
                return arg1
                
            return deco_func(arg1)
                
        return controlAccess
    
    def blacklisted(deco_func):
        def controlAccess(arg1):
            user = arg1.bot.subsystems["access"].getUser(arg1.sender)

            if not user or user.blacklisted or arg1.host not in user.hosts:
                return arg1
                
            return deco_func(arg1)
                
        return controlAccess
        
    def allowedchannel(deco_func):
        def controlAccess(arg1):
            if arg1.channel in arg1.bot.subsystems["access"].allowedChannels or arg1.type == "query":
                return deco_func(arg1)
            
            return arg1
            
        return controlAccess
        
    def trustedchannel(deco_func):
        def controlAccess(arg1):
            if arg1.channel in arg1.bot.subsystems["access"].trustedChannels or arg1.type == "query":
                return deco_func(arg1)
            
            return arg1
            
        return controlAccess
        