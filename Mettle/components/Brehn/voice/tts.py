import random
from elevenlabs.client import ElevenLabs as el
import os
from elevenlabs import save
import subprocess
import os

# Get the absolute path to this script/module
MODULE_DIR = os.path.dirname(os.path.abspath(__file__))

QUEUED_SPEECH_PATH = os.path.join(
    MODULE_DIR, "..", "..", "..", "..",  # step back to project root as needed
    "Mettle", "audio", "temp_files", "speech", "buffered_to_save"
)
QUEUED_SPEECH_PATH = os.path.abspath(QUEUED_SPEECH_PATH)  # normalize

class Voices:
    def __init__(self, apiKey= "", outputFormat="ogg"):
        self.apiKey=apiKey
        self.elevenlabsClient=el(api_key=self.apiKey)
        self.outputFormat=outputFormat
        self.voiceKeys=[]
        self.all=[]
        self.removeOnUse=True

    def _fetchDefaultVoices(self):
        self.voiceKeys=[x.voice_id for x in self.elevenlabsClient.voices.get_all().voices]

    def create(self,speakerId,voiceKey=None):
        if not voiceKey:
            if len(self.voiceKeys)==0:
                self._fetchDefaultVoices()
            voiceKey=random.choice(self.voiceKeys)
            if self.removeOnUse:
                self.voiceKeys.remove(voiceKey)
        self.all.append(
            Voice(elevenlabsClient=self.elevenlabsClient,voiceId=speakerId,voiceKey=voiceKey)
        )
        return self.all[-1]
      
class Voice:
    def __init__(self, elevenlabsClient, voiceKey, voiceId, modelId="eleven_multilingual_v2", outputFormat="mp3_44100_128"):
        self.elevenlabsClient = elevenlabsClient
        self.voiceId = voiceId
        self.voiceKey = voiceKey
        self.modelId = modelId
        self.outputFormat = outputFormat
        self._buffered = []
        self.bufferedSpeechFiles = {} #{to:["file_1.ogg","file_2.ogg",...]}
        self._outputCntr = 0

    def buffer(self,text):
        self._buffered = self.elevenlabsClient.text_to_speech.convert(
            text=text,
            voice_id=self.voiceKey,
            model_id=self.modelId,
            output_format=self.outputFormat
        )
        return True

    def bufferToSave(self, text, listener):
        self._buffered = self.elevenlabsClient.text_to_speech.convert(
            text=text,
            voice_id=self.voiceKey,
            model_id=self.modelId,
            output_format=self.outputFormat
        )
        if not os.path.exists(QUEUED_SPEECH_PATH):
            os.makedirs(QUEUED_SPEECH_PATH, exist_ok=True)
        base_filename = f"bufferedSpeech_{self.voiceId}_to_{listener}_{self._outputCntr}"
        intermediate_file = os.path.join(QUEUED_SPEECH_PATH, f"{base_filename}_raw.ogg")
        final_file = os.path.join(QUEUED_SPEECH_PATH, f"{base_filename}.ogg")
        self._outputCntr += 1

        # Save raw ElevenLabs audio
        save(self._buffered, intermediate_file)
        # Re-encode for compatibility
        creationflags = 0
        # Suppress lose-focus
        if os.name == 'nt':
            creationflags = subprocess.CREATE_NO_WINDOW
        subprocess.run([
            "ffmpeg", "-y", "-i", intermediate_file,
            "-acodec", "libvorbis", "-ar", "44100", "-ac", "1", final_file
        ], check=True, creationflags=creationflags)
        if not listener in self.bufferedSpeechFiles:
            self.bufferedSpeechFiles[listener]=[]
        self.bufferedSpeechFiles[listener].append(base_filename + ".ogg")
        # Optionally delete intermediate file
        os.remove(intermediate_file)
        return True
    
if __name__ == "__main__":
    vcs=Voices(apiKey="YOUR_API_KEY")
    voice=vcs.create(1)
    voice.bufferToSave("This sure looked a lot more fun on the recruitment poster...",5)
    print(str(voice.bufferedSpeechFiles))