## Plan: Add Website Auth Support

Enable agents to access authenticated pages by threading optional credentials from config/CLI/Slack into browser sessions and performing login before scraping.

### Observations from http://localhost:3001/auth

**Authentication System:**
- Single-Page Application (SPA) with client-side routing
- Uses React/Vite development server (localhost:3001)
- Authentication state persists in browser storage (localStorage/sessionStorage)
- Authenticated users automatically redirect from `/auth` → `/customer-center`
- No traditional form-based login page visible in authenticated state
- Session management appears token-based (stored client-side)

**Required Login Information:**
- Username field (observed: "admin")
- Password field (not visible in current session)
- Login form likely has input selectors that need identification
- May use HTTP POST to authentication endpoint

**Implementation Approach:**
Since manual recording wasn't possible (already authenticated), the implementation should support:
1. **Generic form-based auth** with configurable selectors
2. **Playwright context persistence** to maintain session across page visits
3. **Auth state detection** (check if already logged in before attempting login)

### Implementation Steps

#### 1. Config Schema Enhancement
**Files:** `core/config_loader.py`, `examples/config.example.yaml`

Add per-target auth configuration:
```yaml
targets:
  - url: "http://localhost:3001/customer-center"
    auth:
      type: "form"  # or "basic" for HTTP Basic Auth
      username: "admin"
      password: "password123"
      login_url: "http://localhost:3001/auth"  # optional, defaults to url
      selectors:  # for form-based auth
        username_field: "input[name='username']"  # CSS selector
        password_field: "input[name='password']"
        submit_button: "button[type='submit']"
      wait_after_login: 2000  # ms to wait after login
```

#### 2. Browser Session Enhancement
**File:** `utils/browser_utils.py`

Add authentication capabilities to `BrowserSession`:
- Accept auth credentials in `__init__`
- New method: `authenticate(auth_config)` 
  - Check if already authenticated (detect redirect or specific element)
  - If not authenticated, navigate to login page
  - Fill username/password fields using selectors
  - Click submit button
  - Wait for navigation/success indicator
- Support both HTTP Basic Auth and form-based auth
- Maintain Playwright context for session persistence

#### 3. Agent Updates
**Files:** `agents/spell_checker_agent.py`, `agents/visual_qa_agent.py`

- Accept `auth` parameter in agent execution
- Call `browser.authenticate(auth)` before `get_page_text()` or screenshots
- Handle authentication failures gracefully

#### 4. Orchestrator Changes
**File:** `core/orchestrator.py`

- Extract `auth` from target configuration
- Pass auth credentials to agent execution context
- Log authentication attempts (without exposing passwords)

#### 5. CLI Support  
**File:** `main.py`

- Add command-line flags: `--username`, `--password`, `--auth-type`
- Override config-based auth if provided via CLI
- Document in help text

#### 6. Slack Integration (Optional)
**Files:** `integrations/slack_bot.py`, `integrations/conversation_manager.py`

- Add conversation flow to collect credentials when needed
- Store credentials securely in conversation state (temporary)
- Clear credentials after validation run completes

### Security Considerations

1. **Never log passwords** - sanitize all log output
2. **Config file encryption** - consider encrypting auth section in config.yaml
3. **Environment variables** - support `${ENV_VAR}` syntax for passwords
4. **Credential rotation** - document best practices
5. **Session cleanup** - clear browser contexts after use

### Testing Strategy

1. Test with `http://localhost:3001/auth` as reference
2. Create mock authenticated endpoints for testing
3. Test both HTTP Basic and form-based auth
4. Verify session persistence across multiple page visits
5. Test auth failure scenarios

### Fallback/Alternative Approaches

If form automation fails:
- **Option A:** Manual cookie injection (if cookies are known)
- **Option B:** Playwright persistent context (save authenticated session)
- **Option C:** API token authentication (if backend supports it)
