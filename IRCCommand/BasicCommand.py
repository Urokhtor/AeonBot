from time import strftime
from random import uniform

class BasicCommand:

    def herp(command):
        command.result = "herp!"
        return command
    
    def time(command):
        command.result = "System time is: " + strftime("%H:%M:%S")
        return command
    
    def duckey(command):
        command.result = "https://www.msu.edu/course/isb/202/tsao/images/DuckPenis%2042.5cm.JPG"
        return command
    
    def penis(command):
        tmp = "'s penis is " + str(round(uniform(3, 35), 2)) + " cm long and has circumference of " + str(round(uniform(4, 22), 2)) + " cm."
        
        if command.message == "": command.result = command.sender + tmp
        else: command.result = command.message + tmp
            
        return command