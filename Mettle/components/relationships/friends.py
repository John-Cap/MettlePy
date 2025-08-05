import copy
import os
import random
from collections import defaultdict

from ...config.LLM.topics import FlavourTextSeeds
from ...shared.Networks.networks import SocialNetwork

FRIENDSHIP_ENGINE=None

def pingPythia():
    return "Hello from Mettle.friends!"

def getFriendshipEngineInst():
    global FRIENDSHIP_ENGINE
    return FRIENDSHIP_ENGINE

class SocialEntity:
    def __init__(self, id, name):
        self.name = name
        self.id = id
        self.likes = set()
        self.dislikes = set()
        self.friend_points = defaultdict(int)
        self.closest_friends = []
        
    def get_friends(self):
        return self.friend_points.keys()
    
    def getLikes(self):
        return list(self.likes)
        
class FriendshipEngine:
    def __init__(self):
        self.topics = FlavourTextSeeds().toDictTopics()
        self.entities = {}  # name -> SocialEntity
        self.socialNetwork = SocialNetwork()
        
    @staticmethod
    def inst():
        global FRIENDSHIP_ENGINE
        FRIENDSHIP_ENGINE=None
        FRIENDSHIP_ENGINE=FriendshipEngine()
        return True
        
    @staticmethod
    def deInst():
        global FRIENDSHIP_ENGINE
        FRIENDSHIP_ENGINE=None
        return False
    
    def getEntityLikes(self,entity):
        ent=self.getEntity(entity)
        if not ent:
            return []
        return [self.topics[l] for l in ((ent).getLikes())]
    
    def getConnectionChain(self,entity1,entity2):
        return self.socialNetwork.getConnectionChain(entity1,entity2)
        
    def initializeEntities(self,entities,numLikes=7):
        # if not isinstance(entities,list):
        #     entities=[entities]
        for x in entities:
            self.addEntity(x[0],x[1])
            self.assign_random_likes(x[0],numLikes)
    
    def initializeEntity(self,entity,name,numLikes=7):
        self.addEntity(entity,name)
        self.assign_random_likes(entity,numLikes)
    
    def connectSocially(self,entity1,entity2,friendPoints=0,lastPos=[]):
        self.socialNetwork.addEntityConnection(entity1=entity1,entity2=entity2,friendPoints=friendPoints,lastPos=lastPos)
                        
    def allNamesAndIds(self):
        return [[entity.name, key] for key, entity in self.entities.items()]
    
    def allEntities(self):
        return list(self.entities.keys())
    
    def generateRandomFriendsAll(self,entities=None,numPasses=5):
        if not entities:
            entities=list(self.entities.keys())
        _i=0
        while _i < numPasses:
            _choices=[]
            _allGuysTemp=[]
            for x in entities:
                _choices=[guy for guy in _allGuysTemp if guy != x]
                if len(_choices) == 0:
                    _choices=[guy for guy in entities if guy != x]
                    
                _thisGuy=random.choice(_choices)
                _allGuysTemp=[guy for guy in _allGuysTemp if guy != _thisGuy]
                
                if (len(_allGuysTemp)) == 0:
                    _allGuysTemp=copy.deepcopy(entities)

                self.updateFriendPoints(x,_thisGuy)
                
                print(f"{_i}. {x} and {_thisGuy} have {len(self.shared_interests(x,_thisGuy))} shareInterests!")
            _i+=1
        

    def addEntity(self, id, name):
        if id not in self.entities:
            self.entities[id] = SocialEntity(id,name)

    def getEntity(self, id):
        if not id in self.entities:
            return None
        return self.entities[id]

    def get_falvourText(self,index):
        return self.topics[index]
    
    def getFriends(self,name):
        ent=self.getEntity(name)
        if not ent:
            return []
        friends=list(self.getEntity(name).friend_points.keys())
        if not friends:
            return []
        return friends

    def assign_random_likes(self, name, count=3):
        entity=self.getEntity(name)
        if not entity:
            return []
        topic_indices = list(self.topics.keys())
        chosen = random.sample(topic_indices, min(count, len(topic_indices)))
        entity.likes.update(chosen)
        return chosen

    def shared_interests(self, name1, name2):
        e1 = self.getEntity(name1)
        e2 = self.getEntity(name2)
        if (not e1) or (not e2):
            return []
        return e1.likes.intersection(e2.likes)

    def updateFriendPoints(self, name1, name2):
        e1, e2 = self.getEntity(name1), self.getEntity(name2)
        if (not e1) or (not e2):
            return []
        shared = self.shared_interests(name1, name2)
        if shared:
            num=len(shared)
            e1.friend_points[name2] += num
            e2.friend_points[name1] += num
            self.socialNetwork.updateConnection(name1,name2,e1.friend_points[name2])
            
            ret=[]
            # Topic propagation
            topic1 = random.choice(list(e1.likes))
            topic2 = random.choice(list(e2.likes))
            if not topic1 in e2.likes:
                ret.append(topic1)
                e2.likes.add(topic1)
            if not topic2 in e1.likes:
                ret.append(topic2)
                e1.likes.add(topic2)
            return ret
        else:
            return []
        
    def updateFriendPointsPairs(self, friendPairs):
        ret=[]
        for x in friendPairs:
            name1=x[0]
            name2=x[1]
            e1, e2 = self.getEntity(name1), self.getEntity(name2)
            if (not e1) or (not e2):
                continue
            shared = self.shared_interests(name1, name2)
            if shared:
                num=len(shared)
                e1.friend_points[name2] += num
                e2.friend_points[name1] += num
                self.socialNetwork.updateConnection(name1,name2,e1.friend_points[name2])
                # Topic propagation
                topic1 = random.choice(list(e1.likes))
                topic2 = random.choice(list(e2.likes))
                if not topic1 in e2.likes:
                    ret.append([name2,[name1,topic1]])
                    e2.likes.add(topic1)
                if not topic2 in e1.likes:
                    ret.append([name1,[name2,topic2]])
                    e1.likes.add(topic2)
        return ret
    
    def bestFriend(self, name):
        entity = self.getEntity(name)
        if not entity:
            return ""
        if not entity.friend_points:
            return ""
        return max(entity.friend_points, key=lambda k: entity.friend_points[k])

    def mutualBestFriend(self, name):
        bf = self.bestFriend(name)
        if not bf:
            return None
        return name if self.bestFriend(bf) == name else None

    def updateFriendsByProximity(self, name, nearby_entities):
        """Simulates proximity interactions by updating friend points with nearest friends"""
        for other in nearby_entities:
            if other != name:
                self.updateFriendPoints(name, other)

if __name__ == "__main__":

    FriendshipEngine.inst()
    
    _i=0
    _guys=[]
    while _i < 100:
        _guys.append([_i,f"bob_{_i}"])
        _i+=1

    FRIENDSHIP_ENGINE.initializeEntities(_guys)

    _j=0
    _numOf=2
    _friendPairs=[]
    _i=0
    
    _mainReport=[]
    
    while _i < 10:
        _guysTemp=copy.deepcopy(_guys)
        _subReport=[]
        while len(_guysTemp) != 0:
            _mainGuy=random.choice(_guysTemp)
            _guysTemp.remove(_mainGuy)
            _theseFriends=[]
            while _numOf > _j and len(_guysTemp) != 0:
                _thisGuy=random.choice(_guysTemp)
                _theseFriends.append(_thisGuy)
                _guysTemp.remove(_thisGuy)
                
                _j+=1
                
            for x in _theseFriends:
                _friendPairs.append([_mainGuy,x])
                
            _j=0

        FRIENDSHIP_ENGINE.updateFriendPointsPairs(_friendPairs)
        
        _subReport.append("\n")

        for x in FRIENDSHIP_ENGINE.allEntities():
            _ret=f"{x} has friends: {FRIENDSHIP_ENGINE.getFriends(x)}"
            _subReport.append(_ret)
            print(_ret)
        _subReport.append("\n////////////////////////////////////////////////////////////\n//////////////////////////////////////////////////")
        print("\n////////////////////////////////////////////////////////////\n//////////////////////////////////////////////////")
        _mainReport.append(_subReport)
        _i+=1
        
    # print(FRIENDSHIP_ENGINE.getEntityLikes(random.choice(FRIENDSHIP_ENGINE.allEntities())))
    print(FRIENDSHIP_ENGINE.allEntities())
    _doIt=False
    _all=copy.deepcopy(((FRIENDSHIP_ENGINE.allEntities())))
    one, two = random.sample(_all, 2)
    while not _doIt:
        one, two = random.sample(_all, 2)
        _doIt=FRIENDSHIP_ENGINE.socialNetwork.sociallyConnected(one,two)
    print(FRIENDSHIP_ENGINE.socialNetwork.getSocialConnections(one))
    print(FRIENDSHIP_ENGINE.socialNetwork.getSocialConnections(two))
    print(FRIENDSHIP_ENGINE.socialNetwork.getNumberOfJumps(one,two))
    print(FRIENDSHIP_ENGINE.allNamesAndIds())