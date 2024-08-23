import discord
from discord.ext import commands
import aiohttp
import traceback
from discord.ui import *
from api import Token
import sys

sys.stdout.reconfigure(encoding='utf-8')

intents = discord.Intents.default()
# intents.members = True  # Enable guild members intent
# intents.messages = True  # Enable message content intent # i don't intents i guess
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

warnings = {}

@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(f"Error during command sync: {e}")
                
@bot.tree.command(name="setup_automod", description="Sets up the automod rules for the server")
@discord.app_commands.default_permissions(administrator=True)
@discord.app_commands.describe(channel="Channel to send alert messages to")
async def setup_automod_command(interaction: discord.Interaction, channel: discord.TextChannel):
    headers = {
        "Authorization": f"Bot {bot.http.token}",
        "Content-Type": "application/json"
    }

    auto_mod_rule = {
        "name": "Prohibit offensive language",
        "event_type": 1,  # MESSAGE_SEND
        "trigger_type": 1,  # KEYWORD
        "trigger_metadata": {
            "keyword_filter": ["bad word 1", "bad word 2"]
        },
        "actions": [
            {
                "type": 1,  # BLOCK_MESSAGE
            },
            {
                "type": 2,  # SEND_ALERT_MESSAGE
                "metadata": {
                    "channel_id": channel.id
                }
            }
        ],
        "enabled": True  # Enable the rule
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://discord.com/api/v10/guilds/{interaction.guild.id}/auto-moderation/rules",
            headers=headers
        ) as resp:
            existing_rules = await resp.json()
            keyword_rules = [rule for rule in existing_rules if rule['trigger_type'] == 1]
            if len(keyword_rules) >= 6:
                await interaction.response.send_message("The server has reached the maximum number of keyword-based automod rules.", ephemeral=True)
                return

    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"https://discord.com/api/v10/guilds/{interaction.guild.id}/auto-moderation/rules",
            headers=headers,
            json=auto_mod_rule
        ) as resp:
            if resp.status == 201:
                await interaction.response.send_message(f"Automod rule created for {interaction.guild.name} in {channel.mention}")
            else:
                error_text = await resp.text()
                await interaction.response.send_message(f"Error creating automod rule: {resp.status} - {error_text}", ephemeral=True)

# Slash command for verification
@bot.tree.command(name="verify", description="Sets up a verification system")
@discord.app_commands.default_permissions(administrator=True)
@discord.app_commands.describe(role="Role to assign upon verification")
async def verify(interaction: discord.Interaction, role: discord.Role):
    embed = discord.Embed(
        title="Verification",
        description="Click the button below to verify yourself and gain access to the server.",
        color=0x00ff00
    )

    class VerifyButton(discord.ui.Button):
        def __init__(self):
            super().__init__(label='Verify', style=discord.ButtonStyle.green)

        async def callback(self, interaction: discord.Interaction):
            if role not in interaction.user.roles:
                await interaction.user.add_roles(role)
                await interaction.response.send_message('You have been verified!', ephemeral=True)
            else:
                await interaction.response.send_message('You are already verified.', ephemeral=True)

    view = discord.ui.View()
    view.add_item(VerifyButton())

    await interaction.response.send_message(embed=embed, view=view)

# Slash command for kick
@bot.tree.command(name="kick", description="Kicks a user from the server")
@discord.app_commands.default_permissions(kick_members=True)
@discord.app_commands.describe(member="Member to kick", reason="Reason for the kick")
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = None):
    if member == interaction.user:
        await interaction.response.send_message("You can't kick yourself :no_entry:", ephemeral=True)
        return

    if member.top_role >= interaction.user.top_role:
        await interaction.response.send_message(f"You can't do that to the user :no_entry:", ephemeral=True)
        return

    await member.kick(reason=reason)
    await interaction.response.send_message(f'User {member} has been kicked for reason: {reason}')

# Slash command for ban
@bot.tree.command(name="ban", description="Bans a user from the server")
@discord.app_commands.default_permissions(ban_members=True)
@discord.app_commands.describe(member="Member to ban", reason="Reason for the ban")
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = None):
    if member == interaction.user:
        await interaction.response.send_message("You can't ban yourself :no_entry:", ephemeral=True)
        return

    if member.top_role >= interaction.user.top_role:
        await interaction.response.send_message(f"You can't do that to the user :no_entry:", ephemeral=True)
        return

    await member.ban(reason=reason)
    await interaction.response.send_message(f'User {member} has been banned for reason: {reason}')


# Slash command for unban
@bot.tree.command(name="unban", description="Unbans a user from the server")
@discord.app_commands.default_permissions(ban_members=True)
@discord.app_commands.describe(user="User to unban")
async def unban(interaction: discord.Interaction, user: discord.User):
    banned_users = await interaction.guild.bans()
    for ban_entry in banned_users:
        banned_user = ban_entry.user
        if banned_user == user:
            await interaction.guild.unban(banned_user)
            await interaction.response.send_message(f'User {user} has been unbanned.')
            return
    await interaction.response.send_message(f'User {user} was not found in the banned list.')

# Slash command for mute
@bot.tree.command(name="mute", description="Mutes a user in the server")
@discord.app_commands.default_permissions(manage_roles=True)
@discord.app_commands.describe(member="Member to mute", reason="Reason for the mute")
async def mute(interaction: discord.Interaction, member: discord.Member, reason: str = None):
    if member == interaction.user:
        await interaction.response.send_message("You can't mute yourself :no_entry:", ephemeral=True)
        return

    if member.top_role >= interaction.user.top_role:
        await interaction.response.send_message(f"You can't do that to the user :no_entry:", ephemeral=True)
        return

    mute_role = discord.utils.get(interaction.guild.roles, name='Muted')
    if not mute_role:
        mute_role = await interaction.guild.create_role(name='Muted')

        for channel in interaction.guild.channels:
            await channel.set_permissions(mute_role, speak=False, send_messages=False, read_message_history=True, read_messages=True)

    await member.add_roles(mute_role, reason=reason)

    embed = discord.Embed(
        title="User Muted",
        description=f"{member} has been muted.",
        color=0xff0000
    )
    embed.add_field(name="Reason", value=reason if reason else "No reason provided", inline=False)
    embed.set_footer(text=f"Muted by {interaction.user}", icon_url=interaction.user.avatar.url)

    await interaction.response.send_message(embed=embed)

# Slash command for unmute
@bot.tree.command(name="unmute", description="Unmutes a user in the server")
@discord.app_commands.default_permissions(manage_roles=True)
@discord.app_commands.describe(member="Member to unmute")
async def unmute(interaction: discord.Interaction, member: discord.Member):
    if member == interaction.user:
        await interaction.response.send_message("You can't unmute yourself :no_entry:", ephemeral=True)
        return

    mute_role = discord.utils.get(interaction.guild.roles, name='Muted')
    if not mute_role or mute_role not in member.roles:
        await interaction.response.send_message(f"{member} is not muted or the mute role doesn't exist.", ephemeral=True)
        return

    await member.remove_roles(mute_role)

    embed = discord.Embed(
        title="User Unmuted",
        description=f"{member} has been unmuted.",
        color=0x00ff00
    )
    embed.set_footer(text=f"Unmuted by {interaction.user}", icon_url=interaction.user.avatar.url)

    await interaction.response.send_message(embed=embed)

# Slash command for warn
@bot.tree.command(name="warn", description="Warns a user in the server")
@discord.app_commands.default_permissions(manage_messages=True)
@discord.app_commands.describe(member="Member to warn", reason="Reason for the warning")
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str = None):
    if member.id not in warnings:
        warnings[member.id] = []

    warnings[member.id].append(reason)
    await interaction.response.send_message(f'User {member} has been warned for: {reason}')

# Slash command for checking warnings
@bot.tree.command(name="warnings", description="Shows warnings of a user")
@discord.app_commands.default_permissions(manage_messages=True)
@discord.app_commands.describe(member="Member whose warnings to display")
async def warnings_command(interaction: discord.Interaction, member: discord.Member):
    user_warnings = warnings.get(member.id, [])
    if user_warnings:
        await interaction.response.send_message(f'User {member} has been warned for: {", ".join(user_warnings)}')
    else:
        await interaction.response.send_message(f'User {member} has no warnings.')

# Slash command for help
class HelpSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Admin Commands", description="Show admin commands"),
            discord.SelectOption(label="Mod Commands", description="Show mod commands"),
            discord.SelectOption(label="Member Commands", description="Show member commands")
        ]
        super().__init__(placeholder="Choose command category...", options=options)

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "Admin Commands":
            embed = discord.Embed(title="Admin Commands", color=0xff0000)
            admin_commands = {
                "verify": "Sets up a verification system. Usage: /verify @Role",
                "ban": "Bans a user from the server. Usage: /ban @User [reason]",
                "unban": "Unbans a user from the server. Usage: /unban User#1234"
            }
            for cmd, desc in admin_commands.items():
                embed.add_field(name=cmd, value=desc, inline=False)
        elif self.values[0] == "Mod Commands":
            embed = discord.Embed(title="Mod Commands", color=0x00ff00)
            mod_commands = {
                "kick": "Kicks a user from the server. Usage: /kick @User [reason]",
                "mute": "Mutes a user in the server. Usage: /mute @User [reason]",
                "unmute": "Unmutes a user in the server. Usage: /unmute @User",
                "warn": "Warns a user in the server. Usage: /warn @User [reason]",
                "warnings": "Shows warnings of a user. Usage: /warnings @User"
            }
            for cmd, desc in mod_commands.items():
                embed.add_field(name=cmd, value=desc, inline=False)
        elif self.values[0] == "Member Commands":
            embed = discord.Embed(title="Member Commands", color=0x0000ff)
            member_commands = {
                "help": "Shows all commands usage. Usage: /help",
                "customembed": "Make your custom oneline embed. Usage: /customembed <title> <description>"
            }
            for cmd, desc in member_commands.items():
                embed.add_field(name=cmd, value=desc, inline=False)

        await interaction.response.edit_message(embed=embed)

class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(HelpSelect())

@bot.tree.command(name="help", description="Shows all commands usage")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(color=0x00ff00)
    embed.set_author(name="Authz Reloaded Commands", icon_url=bot.user.avatar)
    embed.add_field(name="**Admin Commands**", value="Select Below")
    embed.add_field(name="**Mod Commands**", value="Select Below")
    embed.add_field(name="**Member Commands**", value="Select Below (Not Complete)")
    await interaction.response.send_message(embed=embed, view=HelpView())

# Slash command for custom embed
@bot.tree.command(name="customembed", description="Create a custom embed")
@discord.app_commands.describe(title="Title of the embed", description="Description of the embed")
async def customembed(interaction: discord.Interaction, title: str, description: str):
    embed = discord.Embed(title=title, description=description, color=0xe33235)
    await interaction.response.send_message(embed=embed)

# Slash command for purge/clear
@bot.tree.command(name="purge", description="Deletes a specified number of messages from the channel")
@discord.app_commands.default_permissions(manage_messages=True)
@discord.app_commands.describe(amount="Number of messages to delete")
async def purge(interaction: discord.Interaction, amount: int):
    if amount <= 0:
        await interaction.response.send_message("Please specify a positive number of messages to delete.", ephemeral=True)
        return

    deleted = await interaction.channel.purge(limit=amount)

    embed = discord.Embed(
        title="Messages Purged",
        description=f"Deleted {len(deleted)} messages from {interaction.channel.mention}",
        color=0xff0000
    )
    embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.avatar.url)

    await interaction.response.send_message(embed=embed, ephemeral=True)

# Alias for purge command
@bot.tree.command(name="clear", description="Alias for the purge command")
@discord.app_commands.default_permissions(manage_messages=True)
@discord.app_commands.describe(amount="Number of messages to delete")
async def clear(interaction: discord.Interaction, amount: int):
    await purge(interaction, amount)

# Run the bot
if __name__ == "__main__":
    try:
        bot.run(Token)
    except Exception as e:
        print(f"Error running the bot: {e}")
