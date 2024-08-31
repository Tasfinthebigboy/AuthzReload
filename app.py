import discord
from discord.ext import commands
import aiohttp
from discord.ui import *
from api import Token
import aiosqlite
import sys
import re
import os
import json
import asyncio

sys.stdout.reconfigure(encoding='utf-8')

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

warnings = {}

VERIFICATION_DATA_FILE = 'verification_data.json'

def load_verification_data():
    if os.path.exists(VERIFICATION_DATA_FILE):
        with open(VERIFICATION_DATA_FILE, 'r') as f:
            return json.load(f)
    else:
        return {}

def save_verification_data(data):
    with open(VERIFICATION_DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

verification_data = load_verification_data()

@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")
    try:
        await initialize_databases()
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(f"Error during command sync: {e}")

    for message_id, data in verification_data.items():
        guild = bot.get_guild(data['guild_id'])
        channel = guild.get_channel(data['channel_id'])
        try:
            message = await channel.fetch_message(int(message_id))
            
            for reaction in message.reactions:
                if str(reaction.emoji) == '✅':
                    async for user in reaction.users():
                        if user == bot.user:
                            await message.remove_reaction('✅', bot.user)
                            break
            
            await asyncio.sleep(3)
            await message.add_reaction('✅')

        except discord.NotFound:
            print(f"Message with ID {message_id} not found.")
            continue

    print(f'{bot.user} is ready and monitoring verification messages!')
    while True:
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Slash commands"))
        await asyncio.sleep(10)

        total_members = sum(guild.member_count for guild in bot.guilds)
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"{total_members} members"))
        await asyncio.sleep(10)

@bot.event
async def on_raw_reaction_add(payload):
    # Check if the reaction was added by the bot itself
    if payload.user_id == bot.user.id:
        return

    message_id = str(payload.message_id)
    if message_id in verification_data:
        if str(payload.emoji.name) == '✅':
            guild = bot.get_guild(payload.guild_id)
            role = guild.get_role(verification_data[message_id]['role_id'])
            member = guild.get_member(payload.user_id)

            if role and member and role not in member.roles:
                try:
                    await member.add_roles(role, reason="User verified themselves.")
                    try:
                        await member.send(f"You have been verified in **{guild.name}**!")
                    except discord.Forbidden:
                        pass
                except discord.Forbidden:
                    print(f"Bot lacks permission to add the role {role.name} to {member.name}.")
                    try:
                        await member.send(f"Failed to verify you due to permission issues. Please contact an administrator.")
                    except discord.Forbidden:
                        pass

            elif role in member.roles:
                try:
                    await member.send(f"You are already verified in **{guild.name}**.")
                except discord.Forbidden:
                    pass

            channel = bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            try:
                await message.remove_reaction(payload.emoji, member)
            except discord.Forbidden:
                pass

                
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
        "event_type": 1,  
        "trigger_type": 1,  
        "trigger_metadata": {
            "keyword_filter": ["bad word 1", "bad word 2"]
        },
        "actions": [
            {
                "type": 1,  
            },
            {
                "type": 2,  
                "metadata": {
                    "channel_id": channel.id
                }
            }
        ],
        "enabled": True  
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
            if resp.status in [200,201,204]:
                await interaction.response.send_message(f"Automod rule created for {interaction.guild.name}. alert channel is {channel.mention}", ephemeral=True)
            else:
                error_text = await resp.text()
                await interaction.response.send_message(f"Error creating automod rule: {resp.status} - {error_text}", ephemeral=True)

# @bot.command(name="globalinfo", help="Displays global information including total member count, channel count, and server count across all servers.")
# async def globalinfo(ctx):
#     total_members = sum(guild.member_count for guild in bot.guilds)
#     total_channels = sum(len(guild.channels) for guild in bot.guilds)
#     total_servers = len(bot.guilds)
# 
#     embed = discord.Embed(title="Global Bot Information", color=0x00ff00)
#     embed.add_field(name="Total Member Count", value=total_members, inline=False)
#     embed.add_field(name="Total Channel Count", value=total_channels, inline=False)
#     embed.add_field(name="Total Server Count", value=total_servers, inline=False)
#
#     await ctx.send(embed=embed)


@bot.tree.command(name="verify", description="Sets up a verification system")
@discord.app_commands.default_permissions(administrator=True)
@discord.app_commands.describe(role="Role to assign upon verification")
async def verify(interaction: discord.Interaction, role: discord.Role):
    embed = discord.Embed(
        title="Verification",
        description="React with ✅ to verify yourself and gain access to the server.",
        color=0x00ff00
    )

    await interaction.response.send_message(embed=embed)
    message = await interaction.original_response()

    await message.add_reaction('✅')

    verification_data[str(message.id)] = {
        'guild_id': interaction.guild_id,
        'channel_id': interaction.channel_id,
        'role_id': role.id
    }
    save_verification_data(verification_data)

    await interaction.followup.send("Verification system set up successfully!", ephemeral=True)

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

@bot.tree.command(name="ban", description="Bans a user from the server")
@discord.app_commands.default_permissions(ban_members=True)
@discord.app_commands.describe(member="Member to ban", reason="Reason for the ban")
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = None):
    try:
        await member.ban(reason=reason)
        await interaction.response.send_message(f'User {member} has been banned for reason: {reason}')
        if member == interaction.user:
            await interaction.response.send_message("You can't ban yourself :no_entry:", ephemeral=True)
            return

        if member.top_role >= interaction.user.top_role:
            await interaction.response.send_message(f"You can't do that to the user :no_entry:", ephemeral=True)
            return

        if commands.BotMissingPermissions:
            await interaction.response.send_message("Bot Missing Permission. Please contact a Admin :no_entry:", ephemeral=True)
            return
    except Exception as e:
        print(e)
        await interaction.response.send_message(f"You have caught an ultra rare error while trying to ban the member.")    



@bot.tree.command(name="unban", description="Unbans a user from the server")
@discord.app_commands.default_permissions(ban_members=True)
@discord.app_commands.describe(user="User to unban")
async def unban(interaction: discord.Interaction, user: discord.User):
    async for ban_entry in interaction.guild.bans():
        banned_user = ban_entry.user
        if banned_user == user:
            await interaction.guild.unban(banned_user)
            await interaction.response.send_message(f'User {user} has been unbanned.')
            return
    await interaction.response.send_message(f'User {user} was not found in the banned list.')

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

@bot.tree.command(name="warn", description="Warns a user in the server")
@discord.app_commands.default_permissions(manage_messages=True)
@discord.app_commands.describe(member="Member to warn", reason="Reason for the warning")
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str = None):
    if member.id not in warnings:
        warnings[member.id] = []

    warnings[member.id].append(reason)
    await interaction.response.send_message(f'User {member} has been warned for: {reason}')

@bot.tree.command(name="warnings", description="Shows warnings of a user")
@discord.app_commands.default_permissions(manage_messages=True)
@discord.app_commands.describe(member="Member whose warnings to display")
async def warnings_command(interaction: discord.Interaction, member: discord.Member):
    user_warnings = warnings.get(member.id, [])
    if user_warnings:
        await interaction.response.send_message(f'User {member} has been warned for: {", ".join(user_warnings)}')
    else:
        await interaction.response.send_message(f'User {member} has no warnings.')

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
                "unban": "Unbans a user from the server. Usage: /unban User#1234",
                "setup_automod": "Sets up automod for your guild. Usage: /setup_automod #alert-channel",
                "setup_welcome": "Sets up the welcome channel. Usage: /setup_welcome #channel",
                "setup_leave": "Sets up the leave channel. Usage: /setup_leave #channel"
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
                "purge": "Purges a user from the server. Usage: /purge [amount]",
                "warnings": "Shows warnings of a user. Usage: /warnings @User"
            }
            for cmd, desc in mod_commands.items():
                embed.add_field(name=cmd, value=desc, inline=False)
        elif self.values[0] == "Member Commands":
            embed = discord.Embed(title="Member Commands", color=0x0000ff)
            member_commands = {
                "help": "Shows all commands usage. Usage: /help",
                "customembed": "Make your custom oneline embed. Usage: /customembed <title> <description>",
                "ping": "Shows the bot's response time"
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
    embed.add_field(name="**Member Commands**", value="Select Below")
    await interaction.response.send_message(embed=embed, view=HelpView())

@bot.tree.command(name="customembed", description="Create a custom embed")
@discord.app_commands.describe(title="Title of the embed", description="Description of the embed")
async def customembed(interaction: discord.Interaction, title: str, description: str):
    embed = discord.Embed(title=title, description=description, color=0xe33235)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="purge", description="Deletes a specified number of messages from the channel")
@discord.app_commands.default_permissions(manage_messages=True)
@discord.app_commands.describe(amount="Number of messages to delete")
async def purge(interaction: discord.Interaction, amount: int):
    await interaction.response.defer(ephemeral=True)
    if amount <= 0:
        await interaction.followup.send("Please specify a positive number of messages to delete.", ephemeral=True)
        return

    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"Deleted {len(deleted)} messages.", ephemeral=True)

@bot.tree.command(name="ping", description="Shows the bot ping/response time")
async def ping(interaction: discord.Interaction):
    embed = discord.Embed(title="Authz Bot Ping", description=f"**Ping**: {round(bot.latency * 1000)}ms", color=0x19a61b)
    embed.set_footer(text=f"Requested by • {interaction.user.name}.")
    await interaction.response.send_message(embed=embed)
    
async def get_welcome_channel(guild_id):
    async with aiosqlite.connect("join.db") as db:
        async with db.execute("SELECT welcome_channel_id FROM guild_settings WHERE guild_id = ?", (guild_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

async def set_welcome_channel(guild_id, channel_id):
    async with aiosqlite.connect("join.db") as db:
        await db.execute("INSERT OR REPLACE INTO guild_settings (guild_id, welcome_channel_id) VALUES (?, ?)", (guild_id, channel_id))
        await db.commit()

async def get_leave_channel(guild_id):
    async with aiosqlite.connect("leave.db") as db:
        async with db.execute("SELECT leave_channel_id FROM guild_settings WHERE guild_id = ?", (guild_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

async def set_leave_channel(guild_id, channel_id):
    async with aiosqlite.connect("leave.db") as db:
        await db.execute("INSERT OR REPLACE INTO guild_settings (guild_id, leave_channel_id) VALUES (?, ?)", (guild_id, channel_id))
        await db.commit()

async def get_auto_role(guild_id):
    async with aiosqlite.connect("autorole.db") as db:
        async with db.execute("SELECT role_id FROM guild_settings WHERE guild_id = ?", (guild_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

async def set_auto_role(guild_id, role_id):
    async with aiosqlite.connect("autorole.db") as db:
        await db.execute("INSERT OR REPLACE INTO guild_settings (guild_id, role_id) VALUES (?, ?)", (guild_id, role_id))
        await db.commit()


@bot.tree.command(name="setup_welcome", description="Sets up the welcome channel.")
@discord.app_commands.describe(channel="The channel where welcome messages will be sent.")
@discord.app_commands.default_permissions(administrator=True)
async def setup_welcome(interaction: discord.Interaction, channel: discord.TextChannel):
    await interaction.response.defer()
    await set_welcome_channel(interaction.guild.id, channel.id)
    await interaction.followup.send(embed=discord.Embed(
        title="Welcome Channel Set",
        description=f"The welcome channel has been set to {channel.mention}.",
        color=discord.Color.green()
    ))

@bot.tree.command(name="setup_leave", description="Sets up the leave channel.")
@discord.app_commands.describe(channel="The channel where leave messages will be sent.")
@discord.app_commands.default_permissions(administrator=True)
async def setup_leave(interaction: discord.Interaction, channel: discord.TextChannel):
    await interaction.response.defer()
    await set_leave_channel(interaction.guild.id, channel.id)
    await interaction.followup.send(embed=discord.Embed(
        title="Leave Channel Set",
        description=f"The leave channel has been set to {channel.mention}.",
        color=discord.Color.red()
    ))

@bot.tree.command(name="setup_autorole", description="Sets up the auto-role for new members.")
@discord.app_commands.describe(role="The role to assign to new members.")
@discord.app_commands.default_permissions(administrator=True)
async def setup_autorole(interaction: discord.Interaction, role: discord.Role):
    await interaction.response.defer()
    await set_auto_role(interaction.guild.id, role.id)
    await interaction.followup.send(embed=discord.Embed(
        title="Auto-Role Set",
        description=f"The auto-role has been set to {role.mention}.",
        color=discord.Color.green()
    ))

@bot.event
async def on_member_join(member):
    try:
        guild_id = member.guild.id
        auto_role_id = await get_auto_role(guild_id)
        if auto_role_id:
            role = member.guild.get_role(auto_role_id)
            if role:
                await member.add_roles(role)
                # Send a welcome message with the role (optional)
                welcome_channel_id = await get_welcome_channel(guild_id)
                if welcome_channel_id:
                    channel = bot.get_channel(welcome_channel_id)
                    if channel:
                        embed = discord.Embed(
                            title="🎉 Welcome to the Server!",
                            description=f"Hello {member.mention}, we're thrilled to have you at {member.guild.name}",
                            color=discord.Color.blue()
                        )
                        embed.set_thumbnail(url=member.avatar.url)
                        embed.add_field(name="Member Count", value=f"{member.guild.member_count}", inline=True)
                        embed.set_footer(text="Enjoy your stay!")
                        await channel.send(embed=embed)
    except Exception as e:
        print(f"Error occurred while handling member join event: {e}")

@bot.event
async def on_member_remove(member):
    guild_id = member.guild.id
    leave_channel_id = await get_leave_channel(guild_id)
    if leave_channel_id:
        channel = bot.get_channel(leave_channel_id)
        if channel:
            embed = discord.Embed(
                title="😢 Goodbye!",
                description=f"{member.name} has left the server.",
                color=discord.Color.orange()
            )
            embed.set_thumbnail(url=member.avatar.url)
            embed.add_field(name="We hope to see you again!", value="Goodbye!", inline=True)
            embed.set_footer(text="We'll miss you!")
            await channel.send(embed=embed)

@setup_welcome.error
@setup_leave.error
async def setup_error(interaction: discord.Interaction, error):
    if isinstance(error, discord.app_commands.MissingPermissions):
        await interaction.response.send_message("You don't have permission to use this command.")
    elif isinstance(error, discord.app_commands.BadArgument):
        await interaction.response.send_message("Please mention a valid text channel.")

async def initialize_databases():
    async with aiosqlite.connect("join.db") as db:
        await db.execute("CREATE TABLE IF NOT EXISTS guild_settings (guild_id INTEGER PRIMARY KEY, welcome_channel_id INTEGER)")
        await db.commit()
    
    async with aiosqlite.connect("leave.db") as db:
        await db.execute("CREATE TABLE IF NOT EXISTS guild_settings (guild_id INTEGER PRIMARY KEY, leave_channel_id INTEGER)")
        await db.commit()
    
    async with aiosqlite.connect("autorole.db") as db:
        await db.execute("CREATE TABLE IF NOT EXISTS guild_settings (guild_id INTEGER PRIMARY KEY, role_id INTEGER)")
        await db.commit()

prohibited_words_pattern = re.compile(
    r'\b(shit|piss|fuck|cunt|cocksucker|motherfucker|tits)\b', re.IGNORECASE
)
profanity_pattern = re.compile(
    r'\b(bitch|asshole|dick|slut|nigger|whore|fag|faggot|cocks|cum)\b', re.IGNORECASE
)
link_pattern = re.compile(r'http[s]?://\S+', re.IGNORECASE)
caps_lock_pattern = re.compile(r'[A-Z]{2,}', re.IGNORECASE)
mention_pattern = re.compile(r'<@!?\d+>', re.IGNORECASE)

spam_count = 5
max_caps_percentage = 70
max_mentions = 5

async def check_permissions(member):
    return member.guild_permissions.manage_guild

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if await check_permissions(message.author):
        return

    if prohibited_words_pattern.search(message.content):
        await message.delete()
        await message.author.send("⚠️ Your message contained a prohibited word and was deleted.")
        return

    if profanity_pattern.search(message.content):
        await message.delete()
        await message.author.send("⚠️ Your message contained profanity and was deleted.")
        return

    if link_pattern.search(message.content):
        await message.delete()
        await message.author.send("⚠️ Your message contained an unapproved link and was deleted.")
        return

    caps_percentage = (sum(1 for c in message.content if c.isupper()) / len(message.content)) * 100
    if caps_percentage > max_caps_percentage:
        await message.delete()
        await message.author.send("⚠️ Your message contained too many uppercase letters and was deleted.")
        return

    mentions = len(mention_pattern.findall(message.content))
    if mentions > max_mentions:
        await message.delete()
        await message.author.send("⚠️ Your message contained too many mentions and was deleted.")
        return

    await bot.process_commands(message)
 
async def main():   
    await bot.start(Token)

if __name__ == "__main__":
    try:
        asyncio.run(main())
        initialize_databases()
    except Exception as e:
        print(f"Error running the bot: {e}")
