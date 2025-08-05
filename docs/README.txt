Arma 3 LLM Agents Python Extension

-Overview
This extension augments the Arma 3 simulation environment with large language model (LLM) agents that possess advanced cognitive and social capabilities. Built as a modular Python backend around the Pythia mod, the system enables in-game entities to speak, think, remember, interact socially, and utilize tools. It includes fully extensible memory, conversation, economic, and relationship models, as well as native text-to-speech (TTS) voice integration.

-Features
Conversational LLM Agents:
NPCs powered by OpenAI models, capable of nuanced spoken interaction, memory recall, and context-driven tool use.

-Memory & Experience:
Each agent retains conversation summaries and overheard dialogue, influencing future behavior and dialogue.

-Friends & Social Networks:
The 'Friends' component maintains a persistent, weighted network of social connections and relationship states.

-Game Economy Integration:
The 'Economy' component manages in-game currency, transactions, and economic decisions.

-Tool Use:
Agents use game-specific "tool" functions (API) for tasks such as lending money, demanding possessions, requesting support, and more.

-TTS Voice Output:
ElevenLabs-generated .ogg speech files are converted for Arma 3 playback, enabling fully voiced LLM agents.

-Network Abstractions:
Reusable graph/network logic underpins memory, social, and spatial data.

-Directory Structure
root
│   config.cpp
├───addons
│       this_pbo.pbo
└───Mettle
    │   $PYTHIA$
    │   arma_entrypoint.py
    │   __init__.py
    ├───audio
    │   └───temp_files/speech/buffered_to_save
    ├───components
    │   ├───Brehn
    │   │   │   chat_bot.py
    │   │   │   __init__.py
    │   │   └───voice
    │   │           tts.py
    │   ├───economy
    │   │       economy.py
    │   └───relationships
    │           friends.py
    ├───config
    │   └───LLM
    │       │   environmental_descriptions.py
    │       │   function_register.py
    │       │   topics.py
    │       └───personalities
    │               personalities.txt
    ├───debug
    │   │   logging.py
    │   └───chat_logging
    │           log_def.txt
    └───shared
        └───Networks
                networks.py
Key Components
1. LLM Agent Framework
    chat_bot.py and associated logic define agent cognition and conversation, leveraging OpenAI APIs.

    Personality Generation: Agents are seeded with unique personalities, either from predefined templates (personalities.txt) or via LLM inference.

    Contextual Reasoning:
    Agents construct a comprehensive system prompt from:

    Environment descriptions

    Recent experiences and conversations

    Current social and economic state

    Relationship context (ranks, friends, etc.)

    Action Toolset:
    The function call system enables agents to interact with the world (e.g., move, loan money, start fights, trade items) using game-appropriate actions, always referring to in-game entity IDs.

2. Social Network / Friends System
    friends.py and networks.py manage an Erdos/Social network graph of relationships, including connection strengths, last seen, and position data.

    Supports queries such as social distance (degrees of separation), mutual friends, and updating connection state.

3. Economy System
    economy.py manages agent wallets, transactions, loans, and economic behavior.

    Integrated with LLM tool functions for lending, borrowing, and demanding repayments.

4. Text-to-Speech Pipeline
    tts.py invokes ElevenLabs for speech synthesis, storing .ogg files in the temp directory.

    These files are post-processed to standard Arma-compatible .ogg format.

    The path to the final audio file is returned to Arma for in-game playback via playSound3D.

5. Function Registry / Tool Use
    function_register.py:
    Encapsulates the tool function API for agents, exposing operations like:

    loanMoney

    demandPossessionBack

    startFight

    talkTo

    moveToOrder

    ...and more

    Functions are referenced via unique IDs for each entity, ensuring robust mapping between LLM and game state.

6. Networking and Data Sharing
networks.py:
Shared base classes for Erdos (general graphs), spatial, and social networks.

Used to underpin both economic transactions and social/relationship modeling.

Workflow Summary
Agent receives in-game event or dialogue request.

Agent constructs full context prompt (environment, relationships, personality, recent memory).

LLM is called via OpenAI API to generate a reply, possibly with tool/function recommendations.

If tool calls are recommended, the Python backend executes them and can recurse with updated context.

If audio output is needed, the response is passed to ElevenLabs TTS, file is converted, and its path is returned for Arma playback.

Dependencies
Python 3.8+

OpenAI Python API

networkx (for graph/network logic)

matplotlib (for visualization)

Pythia mod (Arma 3 Workshop)

ElevenLabs API access (for speech synthesis)

Configuration & Usage
Install the required Python dependencies.

Provide valid API keys for OpenAI and ElevenLabs in arma_entrypoint.py or via environment variables.

Install the Pythia mod in your Arma 3 instance.

Copy or symlink the this_pbo.pbo file into your Arma 3 addons directory as per Pythia's requirements.

Launch Arma 3 with the Pythia mod and this extension enabled.

Configure LLM personalities and functions in the config/LLM/ directory as desired.

Extending & Customization
Custom Personalities:
Add or modify entries in personalities.txt.

Custom Tool Functions:
Extend function_register.py and register new actions for the LLM.

Relationship & Economy Logic:
Modify or subclass components in relationships/ and economy/ directories.

TTS Output:
Adjust tts.py for alternate TTS backends if desired.

Example Initialization
python
Copy
Edit
from Mettle.components.Brehn.chat_bot import Character, ConversationManager

# Instantiate conversation manager
ConversationManager.inst()

# Example of handling an Arma event payload:
CONVERSATION_MANAGER.handleSayTo(arma_data)
Credits
Pythia Mod: For the core Arma <-> Python bridge and mod framework.

OpenAI, ElevenLabs: For LLM and TTS APIs.

Contributors: See project source for code authorship.

License
This project is provided under the MIT License.
Please refer to LICENSE for details.

For further information, bug reports, or contributions, please contact the maintainer or submit issues via the project repository.