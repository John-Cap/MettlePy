
import os

class ChatDebugLogging:
    def __init__(self):
        self._cntr=1
        self.baseDir = os.path.dirname(os.path.abspath(__file__))
        self.filePath = os.path.join(self.baseDir, 'chat_logging', 'log_def.txt')

    def writeDump(self,text,heading="|Chat report",cntr=None):
        with open(self.filePath, 'a', encoding='utf-8') as file:
            if not cntr:
                cntr=self._cntr
                self._cntr+=1
                
            file.write(f"{cntr} - {heading}\n")
            file.write(text)
            file.write("\n----\n")
