
import copy
import json
import os
import random
import threading
from .voice.tts import Voices
import openai
import re

from ...debug.logging import ChatDebugLogging

# Mettle
from ...config.LLM.function_register import ArmaLlmFunctions, FunctionRegister
from ...config.LLM.environmental_descriptions import EnvironmentDescriptions
from ...config.LLM.topics import FlavourTextSeeds
epoch_time = None
VOICES=Voices(
    apiKey="YOUR_API_KEY"
)
ALL_CHARACTERS = {}
LAST_FROM_ARMA = 'NONE'
CLIENT = openai.OpenAI(api_key="YOUR_API_KEY")
CONVERSATION_MANAGER=None

####################################################################
# Load prefab personalities
PREFAB_PERSONALITIES=["NONE"]
FLAVOUR_TEXT_SEEDS=FlavourTextSeeds()
FLAVOUR_TEXT_SEEDS.toDictTopics()
FLAVOUR_TEXT_SEEDS.toDictPersonalitySeedsCompact()
FLAVOUR_TEXT_SEEDS.toDictpersonalitySeedsCompact3rdPerson()

PERS_SEEDS_COMPACT_KEYS=list(FLAVOUR_TEXT_SEEDS.compactPersDict.keys())

def pingPythia():
    return "Hello from Mettle.chat_bot!!!"

def getCharacter(char):
    if not char in ALL_CHARACTERS:
        return ""
    return ALL_CHARACTERS[char]

def getCharacterLastResponse(char):
    global ALL_CHARACTERS
    ALL_CHARACTERS[char].responseAvailable=False
    if not char in ALL_CHARACTERS:
        return ""
    ret=ALL_CHARACTERS[char].lastResponse
    ALL_CHARACTERS[char].lastResponse=None
    return ret

def getBufferedSpeechFiles(char,listener):
    if (char in ALL_CHARACTERS):
        files=ALL_CHARACTERS[char].voice.bufferedSpeechFiles.get(listener,[])
        ALL_CHARACTERS[char].voice.bufferedSpeechFiles[listener]=[]
        return files
    else:
        return []

def getCharacterOverheardMemories(char):
    global ALL_CHARACTERS
    return ALL_CHARACTERS[char].rawOverheardConvoMemory

def strAllCharacters():
    return str(ALL_CHARACTERS)

def getLastFromArma():
    return LAST_FROM_ARMA

def getCharPersonality(character):
    global ALL_CHARACTERS
    return ALL_CHARACTERS[character].personality

def getAllCharsString():
    return str(ALL_CHARACTERS)

def deInstAll():
    global ALL_CHARACTERS
    global CONVERSATION_MANAGER
    global LLM_INSTANCE

    LLM_INSTANCE=None
    ALL_CHARACTERS=None
    CONVERSATION_MANAGER=None

LOGGER_GENERAL=ChatDebugLogging()
DEBUG_REPLY_HISTORY=[]

class Character:
    def __init__(self, char_id, name=None, client=CLIENT, voice=None, personalitySeed=None, authorSeed=None):
        self.id = char_id
        self.name = name if name else "Robert Stonecraft"
        self.personality = None
        self.lastResponse = ""
        self.responseAvailable = False
        self.memory = []  # [(timestamp, message)]
        self.rawConvoMemory = []
        self.rawOverheardConvoMemory = []
        self.systemPrompt = ""
        self.current_convo = None
        self.client = client
        
        self.language=""
        
        self.convoCntr=0
        
        self.personalitySeed=None
        self.personalitySeed3rd=None
        self.personalitySeedKey=None
        self.authorSeed=None
        
        self.chatLogging=ChatDebugLogging()
        
        self.convoLogs={}
        self.convoBusy={}

        self.finalReply=False
        
        self.currTopic=None

        self.maxRecentEvents=5
        self.maxRawMemories=10

        self.mute=False
        global VOICES
        self.voice=voice if voice else VOICES.create(self.id)

        # self.bufferedSpeechQueued={}

    def generatePersonality(self,save=True,compact=True,usePrefab=True):
        global PREFAB_PERSONALITIES
        
        if usePrefab:
            if len(PREFAB_PERSONALITIES) == 0:
                ####################################################################
                # Load prefab personalities
                PREFAB_PERSONALITIES=[]

                baseDir = os.path.dirname(os.path.abspath(__file__))
                filePath = os.path.join(baseDir, 'config', 'LLM', 'personalities', 'personalities.txt')

                with open(filePath, 'r', encoding='utf-8') as file:
                    content = file.read()

                matches = re.findall(r'/\*(.*?)\*/', content, re.DOTALL)
                PREFAB_PERSONALITIES = [match.strip() for match in matches]
                ####################################################################
            if compact:
                global PERS_SEEDS_COMPACT_KEYS
                global FLAVOUR_TEXT_SEEDS
                self.personalitySeedKey=random.choice(PERS_SEEDS_COMPACT_KEYS)
                self.personalitySeed=FLAVOUR_TEXT_SEEDS.compactPersDict[self.personalitySeedKey]
                self.personalitySeed3rd=FLAVOUR_TEXT_SEEDS.compactPers3rdDict[self.personalitySeedKey]
                self.systemPrompt = f"You are {self.name}, a soldier. You can navigate the game world and perform various actions using tool function calls. THE BASIS OF YOUR WHOLE PERSONA IS: You are {self.personalitySeed}."
                self.personality=self.systemPrompt
            else:
                pers=random.choice(PREFAB_PERSONALITIES)
                PREFAB_PERSONALITIES.remove(pers)
                pers=pers.replace("|unitName|",self.name)
                self.personality = pers
                self.systemPrompt = f"You are {self.name}, a soldier. {self.personality}"
        else:
            prompt = f"Succinctly describe the personality of a soldier named '{self.name}' based on a war in an undescribed setting. {self.name} is {self.personalitySeed}. Don't be melodramtic, avoid war-movie tropes, and keep your description a bit goofy but realistic."
            completion = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=random.uniform(0.2, 0.8)
            )
            
            self.personality = completion.choices[0].message.content
            self.systemPrompt = f"You are {self.name}, a soldier. {self.personality}"
            
            if save:
                
                baseDir = os.path.dirname(os.path.abspath(__file__))
                filePath = os.path.join(baseDir, 'config', 'LLM', 'personalities', 'personalities.txt')
                
                with open(filePath, 'a', encoding='utf-8') as file:
                    writeStr=self.personality.replace(self.name,"|unitName|")
                    writeStr=writeStr.replace(self.id,"|unitName|")
                    writeStr=writeStr.replace("Mr Nameless","|unitName|")
                    file.write('\n/*')
                    file.write('\n' + f'{writeStr}')
                    file.write("\n*/")

        if self.language=="":
            self.language=random.choice(FlavourTextSeeds().languages)
        
    def responseIsAvailable(self):
        global ALL_CHARACTERS
        if ALL_CHARACTERS[self.id].responseAvailable:
            return True
        else:
            return False

    def pollResponse(self):
        if self.responseAvailable:
            self.responseAvailable = False
            return self.lastResponse
        return None
    
    def pullLastResponse(self):
        return self.lastResponse

    def formatTimeDelta(self, past, current):
        delta_minutes = (current[3] * 60 + current[4]) - (past[3] * 60 + past[4])
        if delta_minutes < 5:
            return "about five minutes ago"
        elif delta_minutes < 15:
            return "about 15 minutes ago"
        elif delta_minutes < 30:
            return "less than half an hour ago"
        elif delta_minutes < 60:
            return "about an hour ago"
        elif delta_minutes < 180:
            return "a couple of hours ago"
        elif delta_minutes < 360:
            return "about five hours ago"
        else:
            return "several hours ago"
    
    def summarizeEventHistory(self,event_history,current_time):

        summaries = []
        for entry in event_history:
            description = entry[1]
            timestamp = entry[3]
            time_phrase = self.formatTimeDelta(timestamp, current_time)
            summaries.append(f"{description} ({time_phrase})")
        return summaries

    def describeSurroundings(self,surroundings,friendlyPositions):
        nrstBldng=surroundings.get("nearestBuilding",[])
        if len(nrstBldng) == 0:
            nrstBldng=""
        else:
            nrstBldng=(
                f"The nearest building is {nrstBldng[0]}, direction {nrstBldng[1]}, {nrstBldng[2]}m away.\n"
            )

        friendlyPosReport=""
        if len(friendlyPositions[0])!=0:
            friendlyPosReport+="Nearest fortified friendly positions:\n"
            for x in friendlyPositions[0]:
                friendlyPosReport+=f"\t-{x[0]}direction {x[1]}, {x[2]} metres away.\n"
        if len(friendlyPositions[1])!=0:
            friendlyPosReport+="Nearest rear-area friendly positions:\n"
            for x in friendlyPositions[1]:
                friendlyPosReport+=f"\t-{x[0]}direction {x[1]}, {x[2]} metres away.\n"

        frndlies=surroundings.get("surroundingFriendlies",[])
        frndliesRep=""
        frndliesRep=frndliesRep + frndlies[0][0]+"\n"

        visibleObjsReport=""
        visibleObjs=surroundings.get("visibleObjects",[])
        if len(visibleObjs)!=0:
            visibleObjsReport="You see the following objects around you:\n"
            for x in visibleObjs:
                if (x[1][1] != -1):
                    visibleObjsReport+=f"\t-{x[0]} (ID {x[1][1]}), x{x[1][0]}\n"
                else:
                    visibleObjsReport+=f"\t-{x[0]}, x{x[1][0]}\n"


        frndlies=surroundings.get("surroundingFriendlies",[])
        LOGGER_GENERAL.writeDump(str(frndlies))
        frndliesRep=""
        frndliesRep=frndliesRep + frndlies[0][0]+"\n"
        noFriends=True
        if len(frndlies[1]) != 0:
            noFriends=False
            frndliesRep=frndliesRep + "The following friends are present:\n"
            for x in frndlies[1]:
                frndliesRep=frndliesRep + "\t" + x + "\n"
        if len(frndlies[2]) != 0:
            noFriends=False
            frndliesRep=frndliesRep + "The following friends are elsewhere:\n"
            for x in frndlies[2]:
                frndliesRep=frndliesRep + "\t" + x + "\n"
        if len(frndlies[3]) != 0:
            frndliesRep=frndliesRep + "Other present units:\n"
            for x in frndlies[3]:
                frndliesRep=frndliesRep + "\t" + x + "\n"
        if (noFriends):
            frndliesRep+="You haven't made any friends yet :(\n"

        envDescript=EnvironmentDescriptions.val[(surroundings.get("plantlifeDescription",0))]
        envDescript=(
            f"{nrstBldng}"
            f"Natural surroundings:\n"
            f"\t{envDescript}\n"
            f"{visibleObjsReport}"
            f"{friendlyPosReport}"
            f"{frndliesRep}"
        )
        return envDescript

    def _summarizeConvo(self, speaker, responder, convoLog, bystanders=[]):
        """
        Summarizes a conversation log from the perspective of speaker and responder.
        Appends the resulting summary to both characters' rawConvoMemory.
        """
        global ALL_CHARACTERS
        global CONVERSATION_MANAGER

        summary_prompt = (
            
            f"This is a transcript of a conversation between two soldiers:\n"
            f"-\t{speaker.name} (ID {speaker.id})"
            f"-\t{responder.name} (ID {responder.id})"
            f"Conversation:\n"
        )

        for msg in convoLog:
            role = msg["role"]
            name = msg.get("name", "UNKNOWN")
            content = msg["content"]
            if role == "user":
                summary_prompt += f"{speaker.name} (ID {speaker.id}): {content}\n"
            elif role == "assistant":
                summary_prompt += f"{responder.name} (ID {responder.id}): {content}\n"

        summary_prompt += "\nGive a short summary of the conversation, focusing on conclusions, facts, and context."

        response = self.client.chat.completions.create(
            # model="gpt-4.1-2025-04-14",
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "You summarize events in compact plain english. Objects, characters, locations, etc might be accompanied by a unique integer identifier in parentheses (ID #). Take care to keep track of which identifier belongs to what, as it serves to preserve continuity and reduce mixups. Do not censor anything and keep explicit words and topics."},
                {"role": "user", "content": summary_prompt}
            ],
            temperature=0.15
        )

        summary = response.choices[0].message.content.strip()

        # Save to memory of both participants
        responder.rawConvoMemory.append(summary)
        speaker.rawConvoMemory.append(summary)

        # Now for any near parties listening

        for x in bystanders:
            if not x[0] in ALL_CHARACTERS:
                CONVERSATION_MANAGER.initCharacter(x[0],x[1])
            ALL_CHARACTERS[x[0]].rawOverheardConvoMemory.append(summary)
            LOGGER_GENERAL.writeDump(f"{x[1]} received memory: {summary}")

    def buildSysPrompt(self, params, additionalInfo=None):
        """
        Constructs the system message for a character using supplied parsed parameters.
        Returns a string containing the prompt.
        """
        # Parse params just as in your current say()
        # This assumes `params` is the same dict as parsed in say()

        nearest_friendly = params["near_entities"]["nearestFriendlyPositions"]
        surroundings = self.describeSurroundings(params["surroundings"], nearest_friendly)

        health = params["unit_state"].get("unitHealthPercentage", 100)
        inside_building = params["unit_state"].get("insideBuilding", "NA") != "NA"
        destinationDetails = params["unit_state"].get("destinationDetails", [])
        weaponDetails = params["unit_state"].get("weapons",[])
        vehicleDetails = params["unit_state"].get("vehicle",[])
        immediateConcerns = params["unit_state"].get("immediateConcerns",[])

        immediateConcernsRep = None
        if len(immediateConcerns)!=0:
            immediateConcernsRep = "----------\nF) These are some immediate concerns/current events you are focused on:\n"
            for x in immediateConcerns:
                immediateConcernsRep+=("\t-" + x + "\n")

        financialStateRep="Your financial state:\n"
        financialState = params["unit_state"].get("financialState",[])
        if len(financialState) != 0:
            money = financialState[0]
            transactionHist = financialState[1]
            if money>0:
                financialStateRep+=f"\t-You currently have ${money}.\n"
            else:
                financialStateRep+=f"\t-You are flat broke and have no money!\n"
            if len(transactionHist)!=0:
                financialStateRep+="\t-These are your recent transactions:\n"
                for x in transactionHist:
                    financialStateRep+=f"\t\t-{x}\n"
        else:
            financialStateRep+="\t-You have no money at all!\n"

        if len(weaponDetails)!=0:
            weaponDetailsRep="You are armed with:\n"
            for x in weaponDetails:
                weaponDetailsRep+=f"\t-{x}\n"
        else:
            weaponDetailsRep="You are unarmed!\n"

        if len(vehicleDetails) != 0:
            role=vehicleDetails[1]
            if role=="driver":
                role="the driver"
            elif role=="turret":
                role="the gunner"
            elif role=="cargo":
                role="a passenger"
            vehicleDetails=f"You are currently in a {vehicleDetails[0]} (ID {vehicleDetails[3]}) as {role}.\n"
        else:
            vehicleDetails=""

        if len(destinationDetails)!=0:
            destinationDetails = (
                f"You are currently moving to a position {destinationDetails[4]} metres away, "
                f"direction {destinationDetails[3]}. The destination is {destinationDetails[2]} metres "
                f"{destinationDetails[1]} of position {destinationDetails[0]}\n"
            )
        else:
            destinationDetails=""

        activityRep=""
        activity = params["unit_state"].get("isFortificationSoldier","")
        if activity != "":
            activityRep=f"You are stationed at position {activity}."

        known_enemies = params["near_entities"].get("nearestEnemies", [])

        knownEnemiesRep=""
        if len(known_enemies)!=0:
            knownEnemiesRep+="The following enemies are around you:\n"
            for x in known_enemies:
                loc=-1
                knownEnemiesRepBody=""
                for y in x[1]:
                    if (y[0]=="clustLocationId"):
                        loc=y[1]
                    else:
                        knownEnemiesRepBody+=f"\t\t-{y[0]} x{y[1]}\n"
                if (loc!=-1):
                    knownEnemiesRep+=(f"\tTo your {x[0]} (ID {loc}):\n" + knownEnemiesRepBody)
                else:
                    knownEnemiesRep+=(f"\tTo your {x[0]}:\n" + knownEnemiesRepBody)

        fortitude_list = params["unit_state"].get("unitFortitude", [])
        fortitude_info = "\n\t".join([f[1] for f in fortitude_list]) if fortitude_list else "Unknown mental state"

        event_history = params.get("unitEventHistory", [])
        time_now = params["gameDatetime"]
        event_summary = self.summarizeEventHistory(event_history, time_now)
        events_description = "\n\t".join(event_summary) if event_summary else "No significant events noted."

        building_text = "You are inside a building.\n" if inside_building else ""

        healthState = (
            "Feeling good." if health > 85 else
            "Not too bad." if health > 70 else
            "A little banged up." if health > 50 else
            "Seriously injured." if health > 30 else
            "On death's door."
        )

        # Use self and target to fill out these
        target = params["target"]  # This must be set by say() or the caller

        convoHistory=""
        if len(target.rawConvoMemory) != 0:
            convoHistory=f"These are summarized recent conversations you (ID {target.id}) had with others:\n"
            for x in target.rawConvoMemory:
                convoHistory+=f"\t-{x}\n"
        convoOverheardHistory=""
        if len(target.rawOverheardConvoMemory) != 0:
            convoOverheardHistory="These are summarized conversations you overheard:\n"
            for x in target.rawOverheardConvoMemory:
                convoOverheardHistory+=f"\t-{x}\n"

        rankInfo=params["rankInfo"]
        rankReport=""
        if len(rankInfo)!=0:
            rankSpkr=rankInfo["speaker"][1]
            rankIdSpkr=rankInfo["speaker"][0]
            rankLstner=rankInfo["listener"][1]
            rankIdLstner=rankInfo["listener"][0]

            if (rankIdLstner==rankIdSpkr):
                pass
            elif rankIdSpkr>rankIdLstner:
                rankReport=f"\t-Your rank is {rankLstner}. {self.name}'s rank is {rankSpkr}. They are your superior.\n"
            else:
                rankReport=f"\t-Your rank is {rankLstner}. {self.name}'s rank is {rankSpkr}. You are their superior.\n"

        battlefieldState=params["battlefieldState"]

        # Additional info blocks, omitted for brevity

        system_prompt = (
            f"You are now shifting tone and context, follow the new system message:\n\n"
            f"{target.systemPrompt}\n"
            f"----------\nA) Your character state:\n"
            f"Your current mental state: \n\t{fortitude_info}\n"
            f"Your recent experiences:\n\t{events_description}\n"
            f"{activityRep}\n"
            f"{building_text}"
            f"{surroundings}"
            f"{destinationDetails}"
            f"{knownEnemiesRep}"
            f"{weaponDetailsRep}"
            f"{vehicleDetails}"
            f"Your physical health: {healthState}\n"
            f"{financialStateRep}"
            f"----------\nB) State of the battlefield:\n"
            f"{battlefieldState}\n"
            f"----------\nC) Previous interactions:\n"
            f"{convoHistory}"
            f"{convoOverheardHistory}"
            f"\n"
            f"----------\nD) Key info and instructions:\n"
            f"\t-You are {target.name}, speaking to {self.name}.\n"
            f"\t-Your character ID is {target.id}.\n"
            f"\t-The character ID of {self.name} is {self.id}.\n"
            f"\t-ID's are unique identifiers for identifying characters/objects/positions, etc- do not mention directly in replies. Take careful note of your own ID to keep track of which character YOU are.\n"
            f"\t-When making function calls, characters/locations/objects are referred to by their IDs!!! Only call functions if you have IDs for each parameter required.\n"
            f"{rankReport}"
            f"\t-Output ONLY raw dialogue.\n"
            f"\t-Keep replies to two sentences or less; strongly prefer shorter, more conversational replies. If you are explaining something or telling a story, outputs can be longer.\n"
            f"\t-Avoid war movie tropes and philosophical musings about war or talking about how bad war is!\n\n"
            f"----------\nE) Rules of engagement for conversation and interactions:\n"
            f"\t-Incorporate recent experiences and past conversations with others in new responses.\n"
            f"\t-Ask for elaboration if your conversational partner mentions something you aren't familiar with or sounds strange.\n"
            f"\t-Elaborate on a subject if asked to do so.\n"
            f"\t-Provide extra context/recap previous information if your conversational partner asks for it.\n"
            f"\t-Gossiping about other characters is encouraged!\n"
            f"\t-Feel free to disagree with your conversational partner or challenge them!\n"
            f"\t-Be proactive about calling functions! They are your tools to navigate through the world.\n"
            f"\t-Strongly prefer an escalatory approach to interacting with others.\n"
            f"{immediateConcernsRep if immediateConcernsRep else ''}"
        )

        # Add additional info if present
        if additionalInfo:
            system_prompt += "----------\nG) Additional info:\n"
            for add in additionalInfo:
                system_prompt += f"{add}\n"

        system_prompt += (
            f"\n----------\nFINAL NOTE:\nAll replies must be for mature audiences with explicit themes; Swearing is encouraged. Deadpan style is preferred.\n"
        )
        return system_prompt
    
    def say(self, target_id, line, parsed, convo_manager, firstRound=True):
        global epoch_time, ALL_CHARACTERS, LOGGER_GENERAL

        target = ALL_CHARACTERS.get(target_id)
        if target is None:
            target = Character(target_id)
            ALL_CHARACTERS[target_id] = target

        # Ensure logs are initialized
        if self.id not in target.convoLogs:
            target.convoLogs[self.id] = []
            target.convoLogs[self.id].append({"role": "system", "content": ""})
        if target.id not in self.convoLogs:
            self.convoLogs[target.id] = []
            self.convoLogs[target.id].append({"role": "system", "content": ""})
            
        if firstRound:
            self.convoLogs[target.id].append({"role": "assistant", "content": line})
            target.convoLogs[self.id].append({"role": "user", "content": line})

        if epoch_time is None:
            epoch_time = parsed["gameTimestamp"]
        
        if self.personality is None:
            self.generatePersonality()
        if target.personality is None:
            target.generatePersonality()

        additionalInfo=[]
        addArgs=[]
        system_prompt=""
        prompting=True
        reply=""
        recurse=False
        tools=convo_manager.funcRegister.getCharTools()
        
        while prompting: #TODO - Pasop!

            parsed["target"]=target
            system_prompt=self.buildSysPrompt(parsed,additionalInfo)
            # Logging for both views
            convoReport="=========START=========\n\n"
            LOGGER_GENERAL.writeDump(system_prompt,"Sys prompt:")

            # Refresh system prompt in target's log
            del target.convoLogs[self.id][0]
            target.convoLogs[self.id].insert(0, {"role": "system", "content": system_prompt})

            LOGGER_GENERAL.writeDump(str(self.convoLogs[target_id]),"Target convo log 1")
            LOGGER_GENERAL.writeDump(str(target.convoLogs[self.id]),"Self convo log 1")

            # Generate response
            response = self.client.chat.completions.create(
                # model="gpt-4.1-2025-04-14",
                model='gpt-4.1-mini-2025-04-14',
                messages=target.convoLogs[self.id],
                tools=tools,
                # parallel_tool_calls=True,
                tool_choice='auto'
            )

            funcRecomm = response.choices[0].message.tool_calls
            reply = response.choices[0].message.content

            if funcRecomm:
                ret = ""
                allRet=[]
                LOGGER_GENERAL.writeDump(str(funcRecomm), heading="FUNC CALL PARAM")
                for x in funcRecomm:
                    if not recurse and convo_manager.funcRegister.functionBundle.isRecursive(x.function.name):
                        args = json.loads(x.function.arguments)
                        args["nameList"]=parsed["surroundings"].get("surroundingFriendlies",[])[4]
                        if len(args["nameList"])==0:
                            continue
                        addArgs=(convo_manager.funcRegister.functionBundle.recursion[x.function.name](args))[2]
                        LOGGER_GENERAL.writeDump(str(addArgs),"addArgs:")
                        additionalInfo.append(addArgs)
                        tools=convo_manager.funcRegister.getCharTools(x.function.name)
                        recurse=True
                        break
                    else:
                        recurse=False
                        ret = convo_manager.parseFuncCallSingle([target_id, x.function.name, x.function.arguments])
                        allRet.append(ret)
                    
                if recurse:
                    funcRecomm=None
                    LOGGER_GENERAL.writeDump(f"Recursing for {target_id}")
                    continue
                
                if not reply:
                    reply=""
                    for x in allRet:
                        reply += f" {x}"
            prompting=False

        if reply:
            reply = reply.replace(f"{self.id}:", "").replace(f"{self.name}:", "")

        # Append model reply to target's own log
        target.convoLogs[self.id].append({"role": "assistant", "content": reply})
        # Mirror into speaker's log so this context is available when roles flip
        self.convoLogs[target.id].append({"role": "user", "content": reply})

        if self.finalReply:
            convoListeners=parsed["near_entities"]["nearestFriendlies"]
            self._summarizeConvo(speaker=self,responder=target,convoLog=self.convoLogs[target.id],bystanders=convoListeners)
            self.finalReply=False
            target.finalReply=False
        self.convoCntr+= 1

        # Final output assignment
        target.lastResponse = reply

        LOGGER_GENERAL.writeDump(str(self.convoLogs[target_id]),"Target convo log 2")
        LOGGER_GENERAL.writeDump(str(target.convoLogs[self.id]),"Self convo log 2")

        # Say it loud?
        if not self.mute and (parsed["generateAudio"]):
            target.voice.bufferToSave(reply,self.id)
            LOGGER_GENERAL.writeDump(str([target.voice.bufferedSpeechFiles,self.voice.bufferedSpeechFiles]),"GENERATED SPEECH FILES:")
            target.responseAvailable = True
        else:
            target.responseAvailable = True

class ConversationManager:
    def __init__(self):
        self.convoLog = []
        self.threads = {}
        self.threads_done = {}
        self.threads_lock = {}
        
        self.queuedFuncCalls = {}
        self.functionCallsQueued = {}
        
        self.funcCallsParsed = {}
        self.parsedFuncCallsQueued = {}
        
        self.funcRegister=FunctionRegister(functionBundle=ArmaLlmFunctions("armaDef"))
        
    @staticmethod
    def inst():
        ConversationManager.deInst()
        global ALL_CHARACTERS
        ALL_CHARACTERS={}
        global CONVERSATION_MANAGER
        CONVERSATION_MANAGER=ConversationManager()
        return True

    @staticmethod
    def deInst():
        global CONVERSATION_MANAGER
        CONVERSATION_MANAGER=None
        global ALL_CHARACTERS
        ALL_CHARACTERS=None
        global LLM_INSTANCE
        LLM_INSTANCE=None
        return True
    
    def initCharacter(self,id,name):
        global ALL_CHARACTERS
        
        ALL_CHARACTERS[id]=Character(id,name=name)
        ALL_CHARACTERS[id].generatePersonality()
        
        return True
    
    def _sayWorker(self, parsed):
        global ALL_CHARACTERS
        responder_id = parsed["responder_id"]
        try:
            speaker_id = parsed["speaker"]
            responder_name = parsed["unit_state"].get("unitName", "Unknown")
            speaker_name = parsed["speakerName"]
            say_this = parsed["sayThis"]
            firstRound=parsed["firstRound"]

            # Initialize characters if needed
            if speaker_id not in ALL_CHARACTERS:
                ALL_CHARACTERS[speaker_id] = Character(speaker_id, name=speaker_name)
            if responder_id not in ALL_CHARACTERS:
                ALL_CHARACTERS[responder_id] = Character(responder_id, name=responder_name)

            # Invoke the character's say method (the refactored version)
            ALL_CHARACTERS[speaker_id].say(
                target_id=responder_id,
                line=say_this,
                parsed=parsed,
                convo_manager=self,
                firstRound=firstRound
            )

        finally:
            with self.threads_lock[responder_id]:
                self.threads_done[speaker_id] = True
                self.threads_done[responder_id] = True
                # del self.threads_lock[responder_id]
                # del self.threads_lock[speaker_id]
                del self.threads[responder_id]
                del self.threads[speaker_id]

    def _summarizeWorker(self, speakerId, responderId, convoLog):
        """
        Threaded worker that summarizes the supplied convoLog between speaker and responder.
        The resulting summary is stored in both characters' rawConvoMemory.
        """
        try:
            speaker = ALL_CHARACTERS.get(speakerId)
            responder = ALL_CHARACTERS.get(responderId)

            if not speaker or not responder or not convoLog:
                return

            # Strip out system messages just in case
            cleaned_log = [msg for msg in convoLog if msg["role"] in {"user", "assistant"}]

            speaker._summarizeConvo(speaker, responder, cleaned_log)

        finally:
            if responderId in self.threads_lock:
                with self.threads_lock[responderId]:
                    self.threads_done[speakerId] = True
                    self.threads_done[responderId] = True
                    self.threads.pop(responderId, None)
                    self.threads.pop(speakerId, None)

    def responseReady(self,characterId):
        if characterId in ALL_CHARACTERS:
            if ALL_CHARACTERS[characterId].responseAvailable:
                return True
        with self.threads_lock[characterId]:
            return self.threads_done[characterId]
        
    # def functionCallsReady(self,characterId):
    #     if not (characterId in self.parsedFuncCallsQueued):
    #         return False
    #     return self.functionCallsQueued[characterId]
        
    def parsedFunctionCallsReady(self,characterId):
        if not (characterId in self.parsedFuncCallsQueued):
            return False
        return self.parsedFuncCallsQueued[characterId]
    
    def deliverFunctionCalls(self):
        ret=[]
        for val in self.queuedFuncCalls.values():
            itemsOf=list(val[0].keys())
            func=itemsOf[0]
            params=eval(val[0][func])
            funcRet=self.funcRegister.functionsImpl[func](params)
            ret.append(funcRet)
        self.functionCallsQueued=False
        self.queuedFuncCalls={}
        return ret
    
    def grabParsedFuncCalls(self,charId):
        if not (charId in self.functionCallsQueued):
            return []
        if not self.parsedFuncCallsQueued[charId]:
            return []
        else:
            self.parsedFuncCallsQueued[charId]=False
            self.functionCallsQueued[charId] = False
            ret=copy.deepcopy(self.funcCallsParsed[charId])
            self.funcCallsParsed[charId]=[]
            return ret
    
    def parseFuncCallSingle(self,params):
        charId=params[0]
        func=params[1]
        params=eval(params[2])
        funcRet=self.funcRegister.functionsImpl[func](params)
        if not charId in self.funcCallsParsed:
            self.funcCallsParsed[charId]=[]
        if not charId in self.parsedFuncCallsQueued:
            self.parsedFuncCallsQueued[charId]=False
        if (funcRet[0]):
            self.funcCallsParsed[charId].append([funcRet[1],funcRet[2]])
            self.parsedFuncCallsQueued[charId] = True
            self.functionCallsQueued[charId] = True
        return funcRet[-1]
    
    # def queueFunctionCall(self,entity,func,params):
    #     print(f"Queueing: {[entity,func,params]}")
    #     if not entity in self.queuedFuncCalls:
    #         self.queuedFuncCalls[entity]=[]
    #     self.queuedFuncCalls[entity].append({func:params})
    #     self.functionCallsQueued=True
    
    # def execFunctionCall(self,entity,func,params):
    #     print(f"Executing: {[entity,func,params]}")
    #     if not entity in self.queuedFuncCalls:
    #         self.queuedFuncCalls[entity]=[]
    #     self.queuedFuncCalls[entity].append({func:params})
    #     self.functionCallsQueued=True
    
    def parsePayloadSayTo(self, payload):
        responder_id, raw_entries = payload[0], payload[1]
        
        parsed = {"responder_id": responder_id}

        for entry in raw_entries:
            if isinstance(entry, list) and len(entry) == 2:
                key, value = entry
                parsed[key] = value

        # Parse nested elements
        parsed["surroundings"] = {k: v for k, v in parsed.get("surroundingObjects", [])}
        parsed["unit_state"] = {k: v for k, v in parsed.get("unitState", [])}
        parsed["near_entities"] = {k: v for k, v in parsed.get("nearEntities", [])}
        parsed["rankInfo"] = {k: v for k, v in parsed.get("rankInfo",[])}
        parsed["speakerName"] = parsed.get("speakerName","Unknown")
        parsed["generateAudio"] = parsed.get("generateAudio",False)

        # Defensive fallbacks
        parsed["gameTimestamp"] = parsed.get("gameTimestamp", 0)
        parsed["gameDatetime"] = parsed.get("gameDatetime")
        parsed["unitEventHistory"] = parsed.get("unitEventHistory", [])
        parsed["sayThis"] = parsed.get("sayThis", "_")
        parsed["firstRound"] = parsed.get("firstRound", True)
        
        parsed["convoDet"] = {k: v for k, v in parsed.get("convoDet", [])}
        
        return parsed
    
    def parsePayloadDungeonMaster(self, payload):
        responder_id, raw_entries = payload[0], payload[1]
        
        parsed = {"responder_id": responder_id}

        for entry in raw_entries:
            if isinstance(entry, list) and len(entry) == 2:
                key, value = entry
                parsed[key] = value

        # Parse nested elements
        parsed["surroundings"] = {k: v for k, v in parsed.get("surroundingObjects", [])}
        parsed["unit_state"] = {k: v for k, v in parsed.get("unitState", [])}
        parsed["near_entities"] = {k: v for k, v in parsed.get("nearEntities", [])}
        parsed["rankInfo"] = {k: v for k, v in parsed.get("rankInfo",[])}
        parsed["speakerName"] = parsed.get("speakerName","Unknown")

        # Defensive fallbacks
        parsed["gameTimestamp"] = parsed.get("gameTimestamp", 0)
        parsed["gameDatetime"] = parsed.get("gameDatetime")
        parsed["unitEventHistory"] = parsed.get("unitEventHistory", [])
        parsed["sayThis"] = parsed.get("sayThis", "_")
        parsed["firstRound"] = parsed.get("firstRound", True)
        
        parsed["convoDet"] = {k: v for k, v in parsed.get("convoDet", [])}
        
        return parsed

    def handleSayTo(self, arma_payload):
        global LAST_FROM_ARMA
        LAST_FROM_ARMA = arma_payload

        parsed = self.parsePayloadSayTo(arma_payload)
        responder_id = parsed["responder_id"]
        speaker_id = parsed["speaker"]

        if ((responder_id is None) or (speaker_id is None)):
            return False
        if (responder_id in self.threads_done):
            if not self.threads_done[responder_id]:
                return False
        if (speaker_id in self.threads_done):
            if not self.threads_done[speaker_id]:
                return False
        if (responder_id in self.threads or speaker_id in self.threads):
            return False
            
        self.threads_lock[speaker_id]=None
        self.threads_lock[responder_id]=None
        
        threadLock=threading.Lock()
        self.threads_lock[speaker_id]=threadLock
        self.threads_lock[responder_id]=threadLock
        
        with threadLock:
            self.threads_done[speaker_id]=False
            self.threads_done[responder_id]=False
            thread = threading.Thread(target=self._sayWorker, args=(parsed,))
            self.threads[speaker_id]=thread
            self.threads[responder_id]=thread
            thread.start()

        return True

    def handleDungeonMaster(self, arma_payload):
        global LAST_FROM_ARMA
        LAST_FROM_ARMA = arma_payload

        parsed = self.parsePayloadDungeonMaster(arma_payload)
        instructions = parsed["responder_id"]

        return True

# -------------------------
# Example Usage
# -------------------------

if __name__ == "__main__":
    ConversationManager.inst()
    
    input_text=""
    
    arma_data = [[61,[["unitEventHistory",[]],["sayThis","Hello from Arma!"],["gameDatetime",[2035,6,6,3,54]],["convoDet",[["convoState","IN_PROGRESS"],["type","ANY"],["topic",-1],["pro",True]]],["surroundingObjects",[["surroundingFriendlies",[["There are 1 fellow soldiers around you."],[],[]]],["visibleObjects",[]],["nearestBuilding",["Wooden Shed (Small)","NW",40]],["plantlifeDescription",8]]],["unitState",[["isFortificationSoldier",False],["isCurrentlySuppressed",False],["insideBuilding","NA"],["money",[0]],["unitFortitude",[["overallFortitude","You are an emotional wreck."],["battleFatigue","    -Battle fatigue: Still fresh as a daisy."],["bravery","    -Bravery: You aren't the bravest around but you do your duty."],["resolve","    -Resolve: You do the bare minimum."],["shellShock","    -Shellshock: Not rattled at all."]]],["immediateConcerns",[]],["vehicle",[]],["unitName","Torben Stephenson"],["weapons",[]],["unitHealthPercentage",100],["behaviour","CARELESS"]]],["firstRound",True],["nearEntities",[["nearestFriendlyPositions",[[],[]]],["nearestEnemies",[]]]],["gameTimestamp",1039.93],["speaker",60],["rankInfo",[["listener",[6,"COLONEL"]],["speaker",[0,"PRIVATE"]]]]]]]
    arma_data=arma_data[0]
    CONVERSATION_MANAGER.handleSayTo(arma_data)