# Website Authentication Support

The agent-validator now supports testing websites that require authentication. This document explains how to configure and use authentication in your validation workflows.

## Overview

Authentication support allows agents to:
- Log in to websites before performing validation
- Test authenticated pages and user interfaces
- Validate content behind login walls

Two authentication methods are supported:
1. **Form-based authentication** - For standard login forms
2. **HTTP Basic authentication** - For basic auth protected sites

## Configuration

### Form-Based Authentication

Form-based authentication fills out a login form and submits it before navigating to target pages.

#### YAML Configuration

```yaml
targets:
  - url: "https://example.com/dashboard"
    agents:
      - spell_checker
      - visual_qa
    auth:
      type: form
      username: "${AUTH_USERNAME}"  # Use environment variable
      password: "${AUTH_PASSWORD}"  # Use environment variable
      selectors:
        username: 'input[name="username"]'    # CSS selector for username field
        password: 'input[name="password"]'    # CSS selector for password field
        submit: 'button[type="submit"]'       # CSS selector for submit button
```

#### CLI Usage

```bash
# Using environment variables for credentials (recommended)
export AUTH_USERNAME="your_username"
export AUTH_PASSWORD="your_password"

python main.py \
  --url https://example.com/dashboard \
  --auth-type form \
  --username '${AUTH_USERNAME}' \
  --password '${AUTH_PASSWORD}' \
  --username-selector 'input[name="username"]' \
  --password-selector 'input[name="password"]' \
  --submit-selector 'button[type="submit"]'

# Or directly with credentials (not recommended for production)
python main.py \
  --url https://example.com/dashboard \
  --auth-type form \
  --username "my_user" \
  --password "my_pass" \
  --username-selector 'input[name="username"]' \
  --password-selector 'input[name="password"]' \
  --submit-selector 'button[type="submit"]'
```

### HTTP Basic Authentication

HTTP Basic authentication sends credentials via HTTP headers.

#### YAML Configuration

```yaml
targets:
  - url: "https://api.example.com/protected"
    agents:
      - spell_checker
    auth:
      type: basic
      username: "admin"
      password: "${API_KEY}"  # Use environment variable
```

#### CLI Usage

```bash
export API_KEY="your_api_key"

python main.py \
  --url https://api.example.com/protected \
  --auth-type basic \
  --username "admin" \
  --password '${API_KEY}'
```

## Environment Variables

For security, it's recommended to use environment variables for passwords and API keys.

### Format

Use the format `${VARIABLE_NAME}` in your configuration:

```yaml
auth:
  username: "${MY_USERNAME}"
  password: "${MY_PASSWORD}"
```

### Setting Environment Variables

**Linux/macOS:**
```bash
export MY_USERNAME="user@example.com"
export MY_PASSWORD="secret123"
```

**Windows (PowerShell):**
```powershell
$env:MY_USERNAME = "user@example.com"
$env:MY_PASSWORD = "secret123"
```

**Using .env file:**

Create a `.env` file in your project root:
```
MY_USERNAME=user@example.com
MY_PASSWORD=secret123
```

The agent-validator automatically loads `.env` files.

## Finding CSS Selectors

To configure form-based authentication, you need CSS selectors for the login form fields.

### Using Browser DevTools

1. Open the login page in your browser
2. Right-click on the username field → Inspect
3. In DevTools, right-click the highlighted element → Copy → Copy selector
4. Repeat for password field and submit button

### Common Selector Patterns

```yaml
# By name attribute
username: 'input[name="username"]'
password: 'input[name="password"]'
submit: 'button[type="submit"]'

# By ID
username: '#username'
password: '#password'
submit: '#login-button'

# By class
username: '.username-input'
password: '.password-input'
submit: '.login-submit'

# By placeholder
username: 'input[placeholder="Username"]'
password: 'input[placeholder="Password"]'

# Complex selectors
username: 'form#login input[type="email"]'
password: 'div.login-form input[type="password"]'
submit: 'form button.primary'
```

## Authentication Flow

### Form Authentication

1. Browser navigates to the target URL
2. System detects form authentication is configured
3. Fills username field using configured selector
4. Fills password field using configured selector
5. Clicks submit button using configured selector
6. Waits for navigation to complete
7. Continues with validation

### Basic Authentication

1. Browser context is created with HTTP credentials
2. All requests include HTTP Basic auth headers
3. Browser navigates to target URL
4. Continues with validation

## Examples

### Example 1: Testing Authenticated Dashboard

```yaml
# config.yaml
agents:
  spell_checker:
    enabled: true
  visual_qa:
    enabled: true

targets:
  - url: "http://localhost:3001/customer-center"
    agents:
      - spell_checker
      - visual_qa
    auth:
      type: form
      username: "${APP_USERNAME}"
      password: "${APP_PASSWORD}"
      selectors:
        username: 'input[name="username"]'
        password: 'input[name="password"]'
        submit: 'button[type="submit"]'
```

```bash
# Set credentials
export APP_USERNAME="demo@example.com"
export APP_PASSWORD="demo123"

# Run validation
pipenv run python main.py --config config.yaml
```

### Example 2: API Documentation Site with Basic Auth

```yaml
targets:
  - url: "https://docs.internal.company.com"
    agents:
      - spell_checker
    auth:
      type: basic
      username: "docs-user"
      password: "${DOCS_PASSWORD}"
```

### Example 3: CLI with Form Auth

```bash
export LOGIN_USER="user@test.com"
export LOGIN_PASS="testpass123"

pipenv run python main.py \
  --url https://app.example.com/reports \
  --agents visual_qa \
  --auth-type form \
  --username '${LOGIN_USER}' \
  --password '${LOGIN_PASS}' \
  --username-selector '#email' \
  --password-selector '#password' \
  --submit-selector 'button.login'
```

## Troubleshooting

### Authentication Fails

**Issue:** Login doesn't work, gets stuck or times out

**Solutions:**
1. Verify CSS selectors are correct using browser DevTools
2. Check that the login form is not in an iframe
3. Ensure the page doesn't require CAPTCHA or 2FA
4. Try increasing wait times in browser_utils.py
5. Check console logs for JavaScript errors

### Environment Variables Not Resolved

**Issue:** Seeing `${VAR_NAME}` instead of actual value

**Solutions:**
1. Verify environment variable is set: `echo $VAR_NAME`
2. Check variable name matches exactly (case-sensitive)
3. Ensure `.env` file is in project root
4. Restart terminal/shell after setting variables

### Session Not Persisting

**Issue:** Each agent run requires re-authentication

**Expected Behavior:** This is normal - each agent run creates a fresh browser session for isolation and reliability. Authentication happens automatically on each run.

### Selectors Don't Match

**Issue:** Elements not found with configured selectors

**Solutions:**
1. Check if page uses dynamic IDs/classes
2. Try more specific selectors
3. Wait for page to fully load before form appears
4. Check if element is hidden or in shadow DOM

## Security Best Practices

1. **Always use environment variables** for passwords and API keys
2. **Never commit credentials** to version control
3. **Add `.env` to `.gitignore`**
4. **Use different credentials** for testing vs production
5. **Rotate credentials regularly**
6. **Limit account permissions** to minimum required
7. **Use read-only accounts** when possible

## Limitations

- CAPTCHA and 2FA are not supported
- OAuth/SAML flows are not supported
- Session-based auth with cookies only persists within a single agent run
- iframes and shadow DOM require special handling
- JavaScript-heavy SPAs may require custom wait logic

## Next Steps

- See [examples/config.example.yaml](../examples/config.example.yaml) for more configuration examples
- Check [QUICKSTART.md](QUICKSTART.md) for getting started guide
- Review [ARCHITECTURE.md](ARCHITECTURE.md) for implementation details
