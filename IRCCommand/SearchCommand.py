import urllib.request
from Utils.Decorators import Decorators

class SearchCommand:

    @Decorators.trusted
    @Decorators.blacklisted
    @Decorators.allowedchannel
    @Decorators.trustedchannel
    def find(command):
        """
            Uses Bing to search the given search arguments and returns the first search result.
        """
        
        line = command.message.replace(" ", "+")
        url = "http://www.bing.com/search?q="
        response = urllib.request.urlopen(url+line)
        command.result = str(response.read()).split("<h3><a href=\"")[1].split("\"")[0].strip()
        response = urllib.request.urlopen(command.result)
        command.result += " - " + str(response.read()).split("<title>")[1].split("</title>")[0]
        
        return command
    
    @Decorators.trusted
    @Decorators.blacklisted
    @Decorators.allowedchannel
    @Decorators.trustedchannel
    def youtube(command):
        """
            Uses the YouTube API v.2.0 to query for the first search result for the given search
            arguments.
        """
        
        if command.message == "":
            return command
            
        url = "https://gdata.youtube.com/feeds/api/videos?q=" + command.message.replace(" ", "+") + "&max-results=1&key=" + command.bot.youtubeAPIKey
        
        try:
            response = urllib.request.urlopen(url)
            command.result = str(response.read()).split("<media:player url=", 1)[1].split("/>", 1)[0].split("&amp;", 1)[0].replace("'", "").replace("\\", "")
            response = urllib.request.urlopen(command.result)
            command.result += " - " + str(response.read()).split("<title>")[1].split("</title>")[0]
        
        except urllib.error.HTTPError:
            command.result = "Encountered a HTTPError"
            
        return command
    
    @Decorators.trusted
    @Decorators.blacklisted
    @Decorators.allowedchannel
    @Decorators.trustedchannel
    def lastfm(command):
        """
            Uses the LastFM API to query given user's latest played tracks and then parses and returns
            the track that was played last, or the track the user is currently playing.
        """
        
        if command.message != "":
            url = "http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user=" + command.message.split(" ")[0] + command.bot.lastFmAPIKey
            response = None
            
            try: response = urllib.request.urlopen(url)
            except urllib.error.HTTPError:
                command.result = "Couldn't find user " + command.message
                return command
            
            track = str(response.read())
            nowPlaying = False
            
            if track.find("nowplaying=\"true\">") != -1:
                track = track.split("<track nowplaying=\"true\">", 1)[1].split("</track>", 1)[0]
                nowPlaying = True
                
            elif track.find("<track>") != -1:
                track = track.split("<track>", 1)[1].split("</track>", 1)[0]
            
            else:
                command.result = "Couldn't find user " + command.message
                return command
                
            artist = track.split(">", 1)[1].split("</")[0]
            song = track.split("<name>", 1)[1].split("</name>", 1)[0]
            
            if nowPlaying: command.result = command.message + " is playing " + artist + " - " + song
            else: command.result = command.message + "'s last track was " + artist + " - " + song
            
        return command