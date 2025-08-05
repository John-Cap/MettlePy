
import difflib

import json
import random
import openai

class ArmaLlmMissionTypes:
    def __init__(self):
        pass

class FunctionBundle:
    def __init__(self,functionBundleName) -> None:
        self.functionBundleName=functionBundleName

class ArmaLlmFunctions(FunctionBundle):
    def __init__(self, functionBundleName) -> None:
        super().__init__(functionBundleName)
        self.client=openai.OpenAI(api_key="YOUR_API_KEY")
        self.recursion={
            "getCharacterInfo":self.getCharacterInfo
        }
        
    def isRecursive(self,func):
        return (func in self.recursion)
        
    def getCharacterInfo(self,args):
        queryName = args["name"]
        nameList = args["nameList"]

        names = [entry[0] for entry in nameList]
        closeMatches = difflib.get_close_matches(queryName, names, n=5, cutoff=0.6)

        candidates = [[name, id_] for name, id_ in nameList if name in closeMatches]
        ret=""

        if candidates:
            ret=f"You were asked if you know '{queryName}'. These are such names you recognise:\n"
            for x in candidates:
                ret+=f"\t-{x[0]} - ID {x[1]}\n"
            return [True,"doesKnowCharacter",ret]
        else:
            # return [True,"doesKnowCharacter",f"You were asked if you know '{queryName}'. You know no such person."]
            # Escalate to LLM if fuzzy match failed
            candidates=self._idFromPrompt(queryName=queryName,list=nameList)
            if candidates:
                ret=f"You were asked if you know '{queryName}'. These are such names you recognise:\n"
                for x in candidates:
                    ret+=f"\t-{x[0]} - ID {x[1]}\n"
                return [True,"doesKnowCharacter",ret]
            return [False,"doesKnowCharacter",f"You were asked if you know '{queryName}'. You know no such person."]

    def getIdFromName(self,args):
        queryName = args["queryName"]
        nameList = args["nameList"]

        names = [entry[0] for entry in nameList]
        closeMatches = difflib.get_close_matches(queryName, names, n=5, cutoff=0.6)

        candidates = [[name, id_] for name, id_ in nameList if name in closeMatches]

        if candidates:
            return [True,"getIdFromName",candidates]
        else:
            # Escalate to LLM if fuzzy match failed
            candidates=self._idFromPrompt(queryName=queryName,list=nameList)
            if candidates:
                return [True,"getIdFromName",candidates]
            return [False,"getIdFromName",[]]

    def _idFromPrompt(self, queryName, list):
        ret = self.client.chat.completions.create(
            model='gpt-4.1-mini-2025-04-14',
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful assistant tasked with resolving a name (possibly partial or misspelled) "
                        "to one or more matching full names and their corresponding IDs from a list."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"The user has supplied the name: \"{queryName}\".\n\n"
                        f"Here is the list of known name-ID pairs:\n\n"
                        f"{list}\n\n"
                        "Find the most relevant matches. The name may be incomplete or misspelled. "
                        "Use the supplied tool to return your result as a list of objects like: "
                        "[{\"name\": \"Full Name\", \"id\": 123}]."
                    )
                }
            ],
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": "returnIdFromName",
                        "description": "Use to return an array of name-ID objects matching the input name.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "nameListReturn": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "name": { "type": "string" },
                                            "id": { "type": "integer" }
                                        },
                                        "required": ["name", "id"],
                                        "additionalProperties": False
                                    },
                                    "description": "List of matched name-ID objects."
                                }
                            },
                            "required": ["nameListReturn"],
                            "additionalProperties": False
                        },
                        "strict": True
                    }
                }
            ],
            tool_choice={"type": "function", "function": {"name": "returnIdFromName"}}
        )
        print(ret)
        args = json.loads(ret.choices[0].message.tool_calls[0].function.arguments)
        return [[entry["name"], entry["id"]] for entry in args["nameListReturn"]]

    def loanMoney(self,args):
        requester=args["requester"]
        loaner=args["loaner"]
        amount=args["amount"]
        return [True,"payMoneyLLM",[loaner,requester,amount],f"Here you go then, {amount} bucks."]
            
    def demandPossessionBack(self,args):
        thief=args["thief"]
        victim=args["victim"]
        amount=args["amount"]
        return [True,"demandPossessionBack",[thief,victim,amount],f"Fine, fine. Take it back."]
        
    def provideAmmo(self,args):
        requester=args["requester"]
        return [True,"provideAmmo",[requester],f"You want some ammo? Have some ammo."]
    
    def moveToOrder(self,args):
        mover=args["mover"]
        destination=args["destination"]
        return [True,"moveToOrder",[mover,destination],f"Fine, heading out."]

    def leadTheWay(self,args):
        requester=args["requester"]
        leader=args["leader"]
        dest=args["destination"]
        return [True,"leadTheWay",[requester,leader,dest],f"Okay then. Follow me."]
    
    def follow(self,args):
        requester=args["requester"]
        follower=args["follower"]
        return [True,"follow",[requester,follower],f"Okay then. Lead the way."]

    def takeItem(self,args):
        taker=args["taker"]
        item=args["item"]
        amount=args["amount"]
        return [True,"takeObjectByTypeLLM",[taker,item,amount],f"Grabbing it!"]

    def requestSupport(self,args):
        rqstr = args["requester"]
        trgt = args["target"]
        type = args["type"]

        return [True,"requestSupport",[rqstr,trgt,type],random.choice([f"Hocus pocus hope I can focus!",f"Let's see where this parks its ass."])]

    '''
    
    @staticmethod
    def startFight(self,args):
        belligerent=args["belligerent"]
        offendedParty=args["offendedParty"]
        complyChance=args["complyChance"]
        if random.randrange(0,1) < complyChance:
            return [True,"startFight",[belligerent,offendedParty],f"Son of a bitch..."]
        else:
            return [False,f"Troublemakers are energy takers. You're not worth the hassle."]
    
    '''
    #Force fight
    def startFight(self,args):
        belligerent=args["belligerent"]
        offendedParty=args["offendedParty"]
        return [True,"startFight",[belligerent,offendedParty],f"You son of a bitch..."]
    
    def talkTo(self,args):
        talker=args["talker"]
        listener=args["listener"]
        openingLine=args["openingLine"]
        return [True,"talkTo",[talker,listener,openingLine],f"Time for a chat."]

    def findUnit(self,args):
        '''
        Not implimented
        '''
        requester=args["belligerent"]
        return [True,"startFight",[requester],f"Son of a bitch..."]

    def getUnitIdByName(self,args):
        requester=args["belligerent"]
        return [True,"startFight",[requester],f"Son of a bitch..."]

    def endConversation(self,args):
        finalReply=args["finalReply"]
        return [True,"finalReply",[finalReply],finalReply]

    def createMission(self,args):
        taskId=args["taskId"]
        taskType=args["taskType"]
        taskProviderId=args["providerId"]
        taskExecutorId=args["executorId"]

    def fetchQuest(self,args):
        fetchWhat=args["fetchWhat"]
        taskProvider=args["taskProviderId"]
        taskExecutorId=args["taskExecutorId"]
        rewardType=args["rewardType"]
        taskTitle=args["taskTitle"]
        taskDescription=args["taskDescript"]

    def fetchUnit(self,args):
        fetchWho=args["fetchWhoId"]
        taskProvider=args["taskProviderId"]
        taskExecutorId=args["taskExecutorId"]
        rewardType=args["rewardType"]
        taskTitle=args["taskTitle"]
        taskDescription=args["taskDescript"]

class UtilityTools:
    def __init__(self,functionBundleName):
        self.functionBundleName=functionBundleName
    
class FunctionRegister:
    def __init__(self,functionBundle):
        self.functionBundle=functionBundle
        self.toolsUtility = [
            {
                "type": "function",
                "function":{
                    "name": "getIdFromName",
                    "description": "Take the provided conversation log and make a short summary of what was said or concluded.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "convoLog": {
                                "type": "array",
                                "description": "Id of unit being asked to loan money."
                            }
                        },
                        "required": [
                            "loaner",
                            "requester",
                            "amount"
                        ],
                        "additionalProperties": False
                    },
                    "strict":True
                }
            }
        ]
        self.toolsCharacter = {
            
            "endConversation":{
                "type": "function",
                "function":{
                    "name": "endConversation",
                    "description": "Call this function when you wish to end an ongoing conversation.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "finalReply": {
                                "type": "string",
                                "description": "Terminate your exchange with this phrase."
                            }
                        },
                        "required": [
                            "finalReply"
                        ],
                        "additionalProperties": False
                    },
                    "strict":True
                }
            },
            "requestSupport":{
                "type": "function",
                "function":{
                    "name": "requestSupport",
                    "description": "Use this to call in heavy fire support on an enemy, group of enemies, or position, provided you have the neccessary IDs for all parameters.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "requester": {
                                "type": "integer",
                                "description": "The ID of the person requesting support."
                            },
                            "target": {
                                "type": "integer",
                                "description": "The ID of the target/position/formation that must be targeted."
                            },
                            "type": {
                                "type": "integer",
                                "description": "The integer key of the type of support you want to call. Your options are:\n\t0, mortar and heavy gun barrage.\n\t1, aircraft bomb.\n\t2, orbital large ordenance drop bomb cluster strike.",
                            }
                        },
                        "required": [
                            "requester",
                            "target",
                            "type"
                        ],
                        "additionalProperties": False
                    },
                    "strict":True
                }
            },
            "getCharacterInfo":{
                "type": "function",
                "function":{
                    "name": "getCharacterInfo",
                    "description": "Use when a name is mentioned that is not present in your system prompt or convologs, or if a name is mentioned for which you have no ID. Particularly useful if your conversation partner asks if you know a certain person.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "The unknown name that was mentioned."
                            }
                        },
                        "required": [
                            "name"
                        ],
                        "additionalProperties": False
                    },
                    "strict":True
                }
            },
            "demandPossessionBack":{
                "type": "function",
                "function":{
                    "name": "demandPossessionBack",
                    "description": "Use when a character has stolen something from you, for example, money, posessions, etc.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "thief": {
                                "type": "integer",
                                "description": "The thief; Id of unit being asked to return money/posession."
                            },
                            "victim": {
                                "type": "integer",
                                "description": "Id of unit demanding their money/posession back."
                            },
                            "amount": {
                                "type": "number",
                                "description": "Amount of money the thief must return."
                            }
                        },
                        "required": [
                            "thief",
                            "victim",
                            "amount",
                        ],
                        "additionalProperties": False
                    },
                    "strict":True
                }
            },
            "loanMoney":{
                "type": "function",
                "function":{
                    "name": "loanMoney",
                    "description": "Loan money to the character you are speaking to, if you have enough.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "loaner": {
                                "type": "integer",
                                "description": "Id of unit being asked to loan money."
                            },
                            "requester": {
                                "type": "integer",
                                "description": "Id of unit asking you to loan them money."
                            },
                            "amount": {
                                "type": "number",
                                "description": "Amount of money the requester is asking for."
                            }
                        },
                        "required": [
                            "loaner",
                            "requester",
                            "amount"
                        ],
                        "additionalProperties": False
                    },
                    "strict":True
                }
            },
            "takeItem":{
                "type": "function",
                "function":{
                    "name": "takeItem",
                    "description": "Use if you want to take an item for which an 'ID' is supplied.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "taker": {
                                "type": "integer",
                                "description": "Id of unit taking an item."
                            },
                            "item": {
                                "type": "integer",
                                "description": "Id of item to take."
                            },
                            "amount": {
                                "type": "integer",
                                "description": "If more than one of an item is available, specify how many to take. Defaults to 1."
                            }
                        },
                        "required": [
                            "taker",
                            "item",
                            "amount"
                        ],
                        "additionalProperties": False
                    },
                    "strict":True
                }
            },
            "provideAmmo":{
                "type": "function",
                "function":{
                    "name": "provideAmmo",
                    "description": "Provide some ammo to the unit you are talking to.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "requester": {
                                "type": "integer",
                                "description": "Id of unit asking you for some ammo."
                            }
                        },
                        "required": [
                            "requester"
                        ],
                        "additionalProperties": False
                    },
                    "strict":True
                }
            },
            "talkTo":{
                "type": "function",
                "function":{
                    "name": "talkTo",
                    "description": "Call if you want to talk to, confront, or verbally interact with a unit whose ID is known. If the person you want to talk to is far away and requires you to move to them, it is not neccessary to call any move commands as this function will also handle that. Only call on third parties, never on the unit you are currently talking to.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "talker": {
                                "type": "integer",
                                "description": "Id of the unit that will initiate the conversation (you)."
                            },
                            "listener": {
                                "type": "integer",
                                "description": "Id of the unit you wish to talk to."
                            },
                            "openingLine": {
                                "type": "string",
                                "description": "The phrase you will say to the listener to start the conversation. This can be a question, statement, greeting, etc."
                            }
                        },
                        "required": [
                            "talker",
                            "listener",
                            "openingLine"
                        ],
                        "additionalProperties": False
                    },
                    "strict":True
                }
            },
            "follow":{
                "type": "function",
                "function":{
                    "name": "follow",
                    "description": "Follow the unit you are talking to.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "requester": {
                                "type": "integer",
                                "description": "Id of unit asking you to follow them."
                            },
                            "follower": {
                                "type": "integer",
                                "description": "The one who will follow."
                            }
                        },
                        "required": [
                            "requester",
                            "follower"
                        ],
                        "additionalProperties": False
                    },
                    "strict":True
                }
            },
            "startFight":{
                "type": "function",
                "function":{
                    "name": "startFight",
                    "description": "If a unit has insulted you, start a fight with them!",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "belligerent": {
                                "type": "integer",
                                "description": "Id of unit that has insulted you."
                            },
                            "offendedParty": {
                                "type": "integer",
                                "description": "Id of unit that has been insulted."
                            }
                        },
                        "required": [
                            "belligerent",
                            "offendedParty"
                        ],
                        "additionalProperties": False
                    },
                    "strict":True
                }
            },
            "leadTheWay":{
                "type": "function",
                "function":{
                    "name": "leadTheWay",
                    "description": "If a unit is asking for you to lead them to a destination you know by ID (character/position/etc), take them there.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "requester": {
                                "type": "integer",
                                "description": "Id of unit that is asking you to lead them."
                            },
                            "leader": {
                                "type": "integer",
                                "description": "Id of unit that wants you to show the way."
                            },
                            "destination": {
                                "type": "integer",
                                "description": "Id of the destination."
                            }
                        },
                        "required": [
                            "requester",
                            "leader",
                            "destination"
                        ],
                        "additionalProperties": False
                    },
                    "strict":True
                }
            },
            "moveToOrder":{
                "type": "function",
                "function":{
                    "name": "moveToOrder",
                    "description": "If a unit is asking you to move to a destination you know by ID (character/position/etc), move to that position.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "mover": {
                                "type": "integer",
                                "description": "Id of unit being asked to move somewhere."
                            },
                            "destination": {
                                "type": "integer",
                                "description": "Id of the destination."
                            }
                        },
                        "required": [
                            "mover",
                            "destination"
                        ],
                        "additionalProperties": False
                    },
                    "strict":True
                }
            }
        }

        self.functionsImpl = {
            "moveToOrder":self.functionBundle.moveToOrder,
            "loanMoney":self.functionBundle.loanMoney,
            "provideAmmo":self.functionBundle.provideAmmo,
            "follow":self.functionBundle.follow,
            "startFight":self.functionBundle.startFight,
            "leadTheWay":self.functionBundle.leadTheWay,
            "endConversation":self.functionBundle.endConversation,
            "takeItem":self.functionBundle.takeItem,
            "talkTo":self.functionBundle.talkTo,
            "getCharacterInfo":self.functionBundle.getCharacterInfo,
            "requestSupport":self.functionBundle.requestSupport
        }        
    
    def getCharTools(self,exclude=[]):
        if isinstance(exclude,str):
            exclude=[exclude]
        ret=[]
        for key, val in self.toolsCharacter.items():
            if not key in exclude:
                ret.append(val)
        return ret

if __name__=="__main__":
    inst=ArmaLlmFunctions("Bobbles")
    inst2=ArmaLlmFunctions("Sobbles")
    args={
        "name":"Asmongold",
        "nameList":[["Assman Susman",4],["Aberton Henkel",495],["Boris Mechano",4540]]
    }
    print([inst2.getCharacterInfo(args),inst.getCharacterInfo(args),inst.recursion["getCharacterInfo"]])