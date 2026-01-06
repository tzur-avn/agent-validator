# Slack Integration Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Slack Workspace                         │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Channel    │  │   Channel    │  │  Direct      │          │
│  │   #general   │  │   #testing   │  │  Message     │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                  │                  │                   │
│         └──────────────────┴──────────────────┘                  │
│                            │                                      │
└────────────────────────────┼──────────────────────────────────────┘
                             │
                             │ Socket Mode (WebSocket)
                             │
┌────────────────────────────▼──────────────────────────────────────┐
│                      Agent Validator Bot                          │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                      slack_app.py                           │ │
│  │  - Main entry point                                         │ │
│  │  - Configuration loading                                    │ │
│  │  - Logging setup                                            │ │
│  └──────────────────────────┬──────────────────────────────────┘ │
│                             │                                     │
│  ┌──────────────────────────▼──────────────────────────────────┐ │
│  │                    SlackBot                                 │ │
│  │  ┌──────────────────────────────────────────────────────┐  │ │
│  │  │  Message Handler                                      │  │ │
│  │  │  - Parse incoming messages                            │  │ │
│  │  │  - Extract user intent                                │  │ │
│  │  │  - Route to appropriate handler                       │  │ │
│  │  └──────────────────┬────────────────────────────────────┘  │ │
│  └─────────────────────┼────────────────────────────────────────┘ │
│                        │                                          │
│         ┌──────────────┼──────────────┐                          │
│         │              │              │                           │
│         ▼              ▼              ▼                           │
│  ┌────────────┐ ┌────────────┐ ┌──────────────┐                 │
│  │Conversation│ │Orchestrator│ │   Formatter  │                 │
│  │  Manager   │ │            │ │              │                 │
│  └────────────┘ └──────┬─────┘ └──────────────┘                 │
│                        │                                          │
│                        │                                          │
└────────────────────────┼──────────────────────────────────────────┘
                         │
                         │ Run Agent
                         │
┌────────────────────────▼──────────────────────────────────────────┐
│                      Agent Layer                                  │
│                                                                    │
│  ┌──────────────────┐              ┌──────────────────┐          │
│  │ SpellChecker     │              │   VisualQA       │          │
│  │ Agent            │              │   Agent          │          │
│  │                  │              │                  │          │
│  │ - Extract text   │              │ - Take screenshots│         │
│  │ - Analyze with   │              │ - Analyze with   │          │
│  │   Gemini AI      │              │   Gemini Vision  │          │
│  │ - Return errors  │              │ - Return issues  │          │
│  └────────┬─────────┘              └────────┬─────────┘          │
│           │                                 │                     │
└───────────┼─────────────────────────────────┼─────────────────────┘
            │                                 │
            │                                 │
┌───────────▼─────────────────────────────────▼─────────────────────┐
│                    External Services                              │
│                                                                    │
│  ┌──────────────────┐              ┌──────────────────┐          │
│  │  Google Gemini   │              │   Playwright     │          │
│  │  AI API          │              │   Browser        │          │
│  │                  │              │                  │          │
│  │  - Text analysis │              │  - Page rendering│          │
│  │  - Vision analysis│             │  - Screenshots   │          │
│  └──────────────────┘              └──────────────────┘          │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

## Message Flow

### User Request Flow

```
1. User sends message
   │
   ├─→ Slack API receives message
   │
   ├─→ Socket Mode forwards to bot
   │
   ├─→ SlackBot.handle_message()
   │
   ├─→ Parse intent & extract URL
   │
   ├─→ Check ConversationManager for active session
   │
   ├─→ If URL missing:
   │   ├─→ Start conversation
   │   └─→ Ask user for URL
   │
   └─→ If URL present:
       ├─→ Call Orchestrator.run_agent()
       │
       ├─→ Agent executes validation
       │
       ├─→ Return results
       │
       ├─→ SlackFormatter.format_result()
       │
       └─→ Send formatted report to user
```

### Conversation State Flow

```
┌─────────────────────────────────────┐
│  User: "run spell checker"          │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  ConversationManager:                │
│  - Create session                    │
│  - Set agent: spell_checker          │
│  - Set step: url                     │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  Bot: "Please provide URL"           │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  User: "https://example.com"         │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  ConversationManager:                │
│  - Update session with URL           │
│  - Mark ready to execute             │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  Execute agent & return report       │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  ConversationManager:                │
│  - End conversation                  │
└─────────────────────────────────────┘
```

## Component Details

### SlackBot
- **Purpose**: Main bot controller
- **Responsibilities**:
  - Message routing
  - Intent parsing
  - Command handling
  - Agent orchestration
  - Error handling
- **Key Methods**:
  - `_handle_message()` - Process incoming messages
  - `_parse_intent()` - Understand user intent
  - `_run_agent()` - Execute validation
  - `_show_help()` - Display help

### ConversationManager
- **Purpose**: Manage conversation state
- **Responsibilities**:
  - Session creation/management
  - State persistence
  - Timeout handling
  - Data storage
- **Key Methods**:
  - `start_conversation()` - Begin new session
  - `get_conversation()` - Retrieve session
  - `update_conversation()` - Store data
  - `end_conversation()` - Clean up

### SlackFormatter
- **Purpose**: Format responses for Slack
- **Responsibilities**:
  - Block Kit message creation
  - Agent-specific formatting
  - Error/success messages
  - Rich text formatting
- **Key Methods**:
  - `format_agent_result()` - Main formatter
  - `_format_spell_checker_result()` - Spell reports
  - `_format_visual_qa_result()` - Visual reports
  - `format_error()` - Error messages

### Orchestrator
- **Purpose**: Coordinate agent execution
- **Responsibilities**:
  - Agent registry
  - Agent creation
  - Execution management
  - Result aggregation
- **Key Methods**:
  - `run_agent()` - Execute single agent
  - `create_agent()` - Instantiate agent
  - `register_agent()` - Add custom agent

## Data Flow

```
Input Message
    ↓
Intent Recognition
    ↓
Parameter Extraction (URL, etc.)
    ↓
Conversation State Check
    ↓
[If missing params]
    ↓
Multi-turn Conversation
    ↓
[All params collected]
    ↓
Agent Execution
    ↓
Result Processing
    ↓
Format for Slack
    ↓
Send Response
```

## Security Layers

```
┌─────────────────────────────────┐
│  Environment Variables          │
│  - SLACK_BOT_TOKEN              │
│  - SLACK_APP_TOKEN              │
│  - GOOGLE_API_KEY               │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│  Input Validation               │
│  - URL validation               │
│  - Message sanitization         │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│  Slack API Authentication       │
│  - Token verification           │
│  - Socket Mode connection       │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│  Error Handling                 │
│  - No sensitive data in errors  │
│  - Graceful failure             │
└─────────────────────────────────┘
```

## Scalability Considerations

### Current Architecture
- Single bot instance
- In-memory conversation storage
- Synchronous message processing

### Future Enhancements
- Multiple bot instances (load balancing)
- Redis for conversation state (distributed)
- Queue-based agent execution (async)
- Database for conversation history
- Caching layer for repeated URLs
- Rate limiting per user

## Integration Points

```
┌────────────────────────────────────┐
│  Existing System                   │
│  - Orchestrator                    │
│  - Agents (Spell, Visual)          │
│  - Config System                   │
│  - Reporters                       │
└──────────────┬─────────────────────┘
               │
               │ No Changes Required
               │
┌──────────────▼─────────────────────┐
│  Slack Integration (New)           │
│  - SlackBot                        │
│  - ConversationManager             │
│  - SlackFormatter                  │
└────────────────────────────────────┘
```

The integration is designed to be non-invasive and works alongside existing functionality.
