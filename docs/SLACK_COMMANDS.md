# Slack Bot Quick Reference

## Getting Started

### Direct Message
```
help
```

### Channel Mention
```
@Agent Validator Bot help
```

## Available Commands

### Help & Information

| Command | Description | Example |
|---------|-------------|---------|
| `help` | Show help message | `@bot help` |
| `list agents` | List available agents | `list agents` |

### Running Agents

#### Spell Checker

**With URL:**
```
check spelling on https://example.com
run spell checker on https://example.com
validate https://example.com for grammar
```

**Without URL (interactive):**
```
run spell checker
check spelling
```
_Bot will ask for URL_

#### Visual QA

**With URL:**
```
run visual qa on https://example.com
check https://example.com for visual issues
validate ui for https://example.com
```

**Without URL (interactive):**
```
run visual qa
check for visual issues
```
_Bot will ask for URL_

## Natural Language Examples

The bot understands natural language! Try:

- "Can you check spelling on https://myblog.com?"
- "I need to validate https://mysite.com for grammar errors"
- "Please run visual QA on https://example.com"
- "Check this page for UI problems: https://example.com"
- "What agents do you have?"
- "How can I use you?"

## Response Format

### Spell Checker Report
```
✍️ Spell Checker Report

URL: https://example.com

Found 2 issue(s):

1. `teh` → `the`
   Context: This is teh main page...

2. `recieve` → `receive`
   Context: You will recieve updates...
```

### Visual QA Report
```
👁️ Visual QA Report

URL: https://example.com

Found 2 visual issue(s):

🔴 1. Button text is cut off on mobile viewport
   Element: `.submit-button`

🟡 2. Image aspect ratio distorted
   Element: `.hero-image`
```

### No Issues Found
```
✅ No spelling or grammar issues found!
```

## Severity Indicators (Visual QA)

- 🔴 High severity
- 🟡 Medium severity
- 🟢 Low severity

## Tips

1. **Always include http:// or https://** in URLs
   - ✅ `https://example.com`
   - ❌ `example.com`

2. **Use @mention in channels**, direct message in DMs
   - Channel: `@Agent Validator Bot check spelling on https://example.com`
   - DM: `check spelling on https://example.com`

3. **Conversations timeout after 30 minutes** (configurable)
   - If stuck, just start a new request

4. **Case insensitive** - commands work in any case
   - `HELP`, `help`, `HeLp` all work

5. **Multiple ways to say the same thing**
   - "check spelling" = "run spell checker" = "validate grammar"
   - "visual qa" = "visual check" = "ui validation" = "layout check"

## Troubleshooting

### "I couldn't find a valid URL"
Make sure your URL starts with `http://` or `https://`

### "Unknown agent"
Use `list agents` to see available agents

### No response from bot
1. Make sure bot is invited to the channel (`/invite @Agent Validator Bot`)
2. Check if bot is running (ask your admin)
3. Try in a direct message

### "An unexpected error occurred"
The validation might have failed. Common reasons:
- Website is down or unreachable
- Website blocks bots/automation
- Network timeout

Contact your admin if issues persist.

## Admin Commands

_Coming soon: Admin features for configuration and monitoring_
