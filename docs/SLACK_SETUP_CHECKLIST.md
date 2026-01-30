# Slack Integration Setup Checklist

Use this checklist to ensure your Slack integration is properly configured.

## Prerequisites

- [ ] Python 3.13+ installed
- [ ] pipenv installed (`pip install pipenv`)
- [ ] Slack workspace where you can install apps
- [ ] Google Gemini API key

## Slack App Setup

- [ ] Created Slack app at https://api.slack.com/apps
- [ ] Enabled Socket Mode
- [ ] Generated App-Level Token (xapp-...)
- [ ] Configured OAuth scopes:
  - [ ] `app_mentions:read`
  - [ ] `chat:write`
  - [ ] `channels:history`
  - [ ] `groups:history`
  - [ ] `im:history`
  - [ ] `mpim:history`
  - [ ] `channels:read`
  - [ ] `groups:read`
  - [ ] `im:read`
  - [ ] `mpim:read`
- [ ] Enabled Event Subscriptions:
  - [ ] `app_mention`
  - [ ] `message.channels`
  - [ ] `message.groups`
  - [ ] `message.im`
  - [ ] `message.mpim`
- [ ] Installed app to workspace
- [ ] Copied Bot User OAuth Token (xoxb-...)

## Local Setup

- [ ] Cloned/have the agent-validator repository
- [ ] Created `.env` file (from `.env.example`)
- [ ] Set `SLACK_BOT_TOKEN` in `.env`
- [ ] Set `SLACK_APP_TOKEN` in `.env`
- [ ] Set `GOOGLE_API_KEY` in `.env`
- [ ] Ran `pipenv install`
- [ ] Ran `pipenv run install-playwright`
- [ ] Verified config.yaml exists

## Testing

- [ ] Ran `python examples/slack_integration_example.py` successfully
- [ ] Ran `pipenv run test tests/test_slack_integration.py` successfully
- [ ] Started bot with `pipenv run slack-bot -v`
- [ ] Saw "⚡️ Bolt app is running!" message

## Slack Testing

- [ ] Invited bot to a test channel (`/invite @Agent Validator Bot`)
- [ ] Bot appears in channel member list
- [ ] Sent `@Agent Validator Bot help` in channel
- [ ] Received help response from bot
- [ ] Sent DM to bot with `help`
- [ ] Received help response in DM

## Validation Tests

- [ ] Tested spell checker:
  ```
  @Agent Validator Bot check spelling on https://example.com
  ```
- [ ] Received spell checker report
- [ ] Tested visual QA:
  ```
  @Agent Validator Bot run visual qa on https://example.com
  ```
- [ ] Received visual QA report
- [ ] Tested interactive mode:
  ```
  @Agent Validator Bot run spell checker
  ```
- [ ] Bot asked for URL
- [ ] Provided URL
- [ ] Received validation report

## Troubleshooting

If something doesn't work, check:

- [ ] Bot process is running (check terminal)
- [ ] No errors in bot logs
- [ ] Tokens are correct in `.env`
- [ ] Slack app has correct permissions
- [ ] Socket Mode is enabled
- [ ] Bot is invited to the channel
- [ ] Internet connection is stable

## Production Deployment (Optional)

- [ ] Set up process manager (systemd, supervisor, pm2)
- [ ] Configured logging to file
- [ ] Set up monitoring/alerts
- [ ] Secured tokens (use secrets manager)
- [ ] Set up auto-restart on failure
- [ ] Tested failover scenarios
- [ ] Documented deployment process
- [ ] Set up backup bot instance (optional)

## Documentation Review

- [ ] Read [SLACK_INTEGRATION.md](SLACK_INTEGRATION.md)
- [ ] Read [SLACK_COMMANDS.md](SLACK_COMMANDS.md)
- [ ] Read [SLACK_IMPLEMENTATION_SUMMARY.md](SLACK_IMPLEMENTATION_SUMMARY.md)
- [ ] Bookmarked Slack API docs: https://api.slack.com/docs

## Quick Start Script

Alternatively, run the automated setup:

```bash
./scripts/setup_slack.sh
```

This will:
- Check for dependencies
- Install Playwright browsers
- Verify environment variables
- Run setup verification
- Guide you through any missing steps

## Support

If you encounter issues:

1. Check logs with `pipenv run slack-bot -v`
2. Review error messages
3. Consult documentation in `docs/`
4. Check Slack app event logs at https://api.slack.com/apps
5. Verify tokens are valid and not expired

## Success Criteria

✅ You're ready when:
- Bot responds to messages in Slack
- Agents run successfully and return reports
- No errors in bot logs
- Users can interact naturally with the bot

---

**Last Updated:** January 6, 2026  
**Version:** 1.0.0
