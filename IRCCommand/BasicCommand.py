from time import strftime
import urllib.request
from Utils.Decorators import Decorators

class BasicCommand:

    @Decorators.allowedchannel
    def time(command):
        if not command.type == "action":
            command.result = "System time is: " + strftime("%H:%M:%S")
        return command

    @Decorators.allowedchannel
    def resolveURL(command):
        command.result = []
        for part in command.message.split(" "):
            if part.startswith("http://") or part.startswith("www.") or part.startswith("https://"):
                response = urllib.request.urlopen(part)
                command.result.append(str(response.read()).split("<title>")[1].split("</title>")[0])

        return command
    