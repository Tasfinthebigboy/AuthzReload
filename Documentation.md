# AZ Authz Bot Documentation

Welcome to **AZ Authz**, a versatile Discord bot that brings moderation, fun, utilities, and custom plugin capabilities to your server. This guide will help you understand how to use the bot effectively, including our powerful **Plugins** feature.

---

## ⚡ Easy to Use

Using AZ Authz is straightforward. All commands are **slash commands**, so you can execute them simply by typing:

```
/command_name
```

For example:

* `/ban @user` – Ban a member from your server
* `/ping` – Check the bot’s response time
* `/meme` – Get a random meme

Just start typing `/` and select the desired command from the Discord suggestions.

---

## 📂 Command Categories

### Moderation

* `/ban` • Ban a member from the server
* `/kick` • Kick a member from the server
* `/mute` • Temporarily mute a member
* `/unmute` • Remove a member's mute
* `/warn` • Issue a warning
* `/warnings` • View warnings
* `/delwarns` • Remove warnings
* `/lock` • Lock a channel
* `/unlock` • Unlock a channel

### Utility

* `/ping` • Check bot latency
* `/serverinfo` • View server info
* `/userinfo` • View user info
* `/roleinfo` • View role details
* `/channelinfo` • View channel details
* `/avatar` • Get a user’s avatar
* `/version` • Check bot version

### Automod

* `/automod toggle` • Enable/disable automod
* `/automod setlog` • Set a log channel
* `/automod mode` • Change automod mode
* `/automod ignore` • Ignore channels, roles, or users
* `/automod unignore` • Remove ignored targets
* `/automod blockwords` • Manage blocked words

### Fun & Entertainment

* `/8ball` • Ask the magic 8-ball
* `/meme` • Get a random meme
* `/coinflip` • Flip a coin
* `/roll` • Roll a dice
* `/rate` • Get a random rating
* `/joke` • Hear a joke
* `/roast` • Get roasted by the bot

### General & Bot

* `/say` • Make the bot say something
* `/help` • Show the help menu
* `/createinvite` • Generate a server invite link
* `/ai ask` • Ask the AI a question
* `/ai allowchannel` • Allow AI in a channel
* `/ai removechannel` • Remove AI from a channel
* `/sendembed` • Create a custom embed

### Plugins

The **Plugins** system allows you to create custom commands and automated actions in your server.

* `/uploadplugin name:<plugin_name> file:<.json file> force:<True/False>` – Upload a plugin
* `/pluginlist` – List all installed plugins
* `/removeplugin name:<plugin_name>` – Remove a plugin

#### Example Plugin

```json
{
  "command_name": "hello",
  "description": "Say hello to the world or greet a user",
  "response": {
    "type": "immediate",
    "content": "👋 Hello {target_user.mention or user.mention}! Welcome to {guild.name}!",
    "ephemeral": false,
    "embed": {
      "title": "Greetings!",
      "description": "This is a friendly hello message from the bot.",
      "color": "#00FF00",
      "footer": "Have a great day!",
      "thumbnail": "https://i.imgur.com/4M34hi2.png"
    },
    "sendafter": [
      {
        "content": "💡 Tip: Use `/hello @user` to greet someone specifically!"
      }
    ]
  },
  "action_rules": {
    "action": "none",
    "trigger": null
  }
}

```

* `command_name` – The slash command to execute your plugin
* `description` – Short description for the command
* `response.content` – Message content using placeholders
* `sendafter` – Optional follow-up messages
* `action_rules` – Automated actions like `ban`, `mute`, `warn`
* `conditions` – Limit which roles, channels, or users can trigger the plugin
* `api_endpoint` – Optional API request to include `{api_response}`

#### Placeholders

* `{user.name}` – Command user’s name
* `{user.mention}` – Mention the user
* `{guild.name}` – Server name
* `{guild.member_count}` – Total members
* `{target_user.name}` – Target user (for actions)
* `{time}` – Current UTC time

#### Tips

* Start simple with message-based plugins
* Use `sendafter` for extra fun messages or facts
* Test plugins on a small channel or role before general use
* Combine `action_rules` and `conditions` to automate moderation

---

AZ Authz is designed to be **intuitive for everyone**, while giving power users full control to customize their server experience.
