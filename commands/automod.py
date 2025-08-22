import discord
import aiosqlite
import re
import aiohttp
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta

INVITE_REGEX = r"(?:https?:\/\/)?(?:www\.)?(?:discord\.gg|discordapp\.com\/invite)\/[^\s]+"
CAPS_THRESHOLD = 0.8
CARL_TIMESTAMP = "%Y-%m-%d %H:%M:%S (UTC)"

class AutomodGroup(app_commands.Group):
    def __init__(self, cog):
        super().__init__(name="automod", description="Manage automod settings")
        self.cog = cog


    @app_commands.command(name="setlog")
    @app_commands.describe(channel="Select the log channel")
    async def setlog(self, interaction: discord.Interaction, channel: discord.TextChannel):
        async with aiosqlite.connect(self.cog.db_path) as db:
            await db.execute("""
                INSERT INTO automod_config (guild_id, log_channel)
                VALUES (?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET log_channel = excluded.log_channel
            """, (str(interaction.guild.id), str(channel.id)))
            await db.commit()
        await interaction.response.send_message(f"Set log channel to {channel.mention}", ephemeral=True)

    @app_commands.command(name="toggle")
    @app_commands.describe(setting="invites or caps", value="Enable or disable it")
    @app_commands.choices(setting=[
        app_commands.Choice(name="invites", value="invites"),
        app_commands.Choice(name="caps", value="caps")
    ])
    async def toggle(self, interaction: discord.Interaction, setting: app_commands.Choice[str], value: bool):
        column = {"invites": "filter_invites", "caps": "filter_caps"}.get(setting.value)
        if not column:
            return await interaction.response.send_message("Invalid setting.", ephemeral=True)

        async with aiosqlite.connect(self.cog.db_path) as db:
            await db.execute(f"""
                INSERT INTO automod_config (guild_id, {column})
                VALUES (?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET {column} = excluded.{column}
            """, (str(interaction.guild.id), int(value)))
            await db.commit()
        await interaction.response.send_message(f"Set `{setting.value}` filter to `{value}`.", ephemeral=True)

    @app_commands.command(name="mode")
    @app_commands.describe(enabled="Enable or disable the entire automod system")
    async def mode(self, interaction: discord.Interaction, enabled: bool):
        async with aiosqlite.connect(self.cog.db_path) as db:
            await db.execute("""
                INSERT INTO automod_config (guild_id, enabled)
                VALUES (?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET enabled = excluded.enabled
            """, (str(interaction.guild.id), int(enabled)))
            await db.commit()
        await interaction.response.send_message(f"Automod is now {'enabled' if enabled else 'disabled'}.", ephemeral=True)

    @app_commands.command(name="ignore")
    async def ignore(self, interaction: discord.Interaction,
                     user: discord.User = None,
                     channel: discord.TextChannel = None,
                     role: discord.Role = None):
        if not any([user, channel, role]):
            return await interaction.response.send_message("Please provide at least one option.", ephemeral=True)

        async with aiosqlite.connect(self.cog.db_path) as db:
            await db.execute("INSERT INTO ignored (guild_id, user_id, channel_id, role_id) VALUES (?, ?, ?, ?)",
                             (str(interaction.guild.id),
                              str(user.id) if user else None,
                              str(channel.id) if channel else None,
                              str(role.id) if role else None))
            await db.commit()
        await interaction.response.send_message("Added to ignore list.", ephemeral=True)

    @app_commands.command(name="unignore")
    async def unignore(self, interaction: discord.Interaction,
                       user: discord.User = None,
                       channel: discord.TextChannel = None,
                       role: discord.Role = None):
        if not any([user, channel, role]):
            return await interaction.response.send_message("Please provide at least one option.", ephemeral=True)

        async with aiosqlite.connect(self.cog.db_path) as db:
            await db.execute("""
                DELETE FROM ignored WHERE guild_id = ? AND user_id IS ? AND channel_id IS ? AND role_id IS ?
            """, (str(interaction.guild.id),
                  str(user.id) if user else None,
                  str(channel.id) if channel else None,
                  str(role.id) if role else None))
            await db.commit()
        await interaction.response.send_message("Removed from ignore list.", ephemeral=True)

    @app_commands.command(name="blockwords", description="Sets up Prohibit offensive language automod rules for the server")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(channel="Channel to send alert messages to")
    @app_commands.describe(badword="Comma-separated list of words that will be blocked (e.g., word1,word2,word3)")
    async def setup_automod_command(self, interaction: discord.Interaction, channel: discord.TextChannel, badword: str):
        # Split and clean up bad words
        badwords_list = [w.strip() for w in badword.split(",") if w.strip()]
        
        if not badwords_list:
            await interaction.response.send_message("Please provide at least one valid word to block.", ephemeral=True)
            return

        headers = {
            "Authorization": f"Bot {self.bot.http.token}",
            "Content-Type": "application/json"
        }
        auto_mod_rule = {
            "name": "Prohibit offensive language | Az Authz",
            "event_type": 1,  
            "trigger_type": 1,  
            "trigger_metadata": {
                "keyword_filter": badwords_list,
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
                if resp.status in [200, 201, 204]:
                    await interaction.response.send_message(
                        f"✅ Automod rule created for {interaction.guild.name}.\nAlert channel: {channel.mention}\nBlocked words: `{', '.join(badwords_list)}`",
                        ephemeral=True
                    )
                else:
                    error_text = await resp.text()
                    await interaction.response.send_message(
                        f"❌ Error creating automod rule: {resp.status} - {error_text}",
                        ephemeral=True
                    )

class Automod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "automod.db"
        self.invite_pattern = re.compile(INVITE_REGEX)

    async def cog_load(self):
        await self.init_db()
        self.bot.tree.add_command(AutomodGroup(self))

    async def init_db(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS automod_config (
                    guild_id TEXT PRIMARY KEY,
                    log_channel TEXT,
                    filter_invites INTEGER DEFAULT 1,
                    filter_caps INTEGER DEFAULT 1,
                    enabled INTEGER DEFAULT 1
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS warnings (
                    guild_id TEXT,
                    user_id TEXT,
                    reason TEXT,
                    moderator TEXT,
                    timestamp TEXT
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS ignored (
                    guild_id TEXT,
                    user_id TEXT,
                    channel_id TEXT,
                    role_id TEXT
                )
            """)
            await db.commit()

    async def get_config(self, guild_id):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT * FROM automod_config WHERE guild_id = ?", (str(guild_id),)) as cursor:
                return await cursor.fetchone()

    async def is_ignored(self, message):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT * FROM ignored WHERE guild_id = ?", (str(message.guild.id),)) as cursor:
                rows = await cursor.fetchall()
                for row in rows:
                    if (
                        (row[1] and str(message.author.id) == row[1]) or
                        (row[2] and str(message.channel.id) == row[2]) or
                        (row[3] and any(str(role.id) == row[3] for role in message.author.roles))
                    ):
                        return True
        return False

    async def add_warning(self, guild, user, reason, moderator):
        timestamp = datetime.utcnow().strftime(CARL_TIMESTAMP)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("INSERT INTO warnings VALUES (?, ?, ?, ?, ?)",
                             (str(guild.id), str(user.id), reason, moderator, timestamp))
            await db.commit()

        count = await self.get_warn_count(guild.id, user.id)
        try:
            await user.send(f"You were warned in **{guild.name}** for: `{reason}`. Total warnings: {count}")
        except:
            pass

        if count == 3:
            until = discord.utils.utcnow() + timedelta(days=7)
            await user.timeout(until, reason="Reached 3 warnings (Automod)")
        elif count == 5:
            await guild.ban(user, reason="Reached 5 warnings (Automod)")
            await self.clear_warnings(guild.id, user.id)

    async def get_warn_count(self, guild_id, user_id):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*) FROM warnings WHERE guild_id = ? AND user_id = ?", (str(guild_id), str(user_id))) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else 0

    async def clear_warnings(self, guild_id, user_id):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM warnings WHERE guild_id = ? AND user_id = ?", (guild_id, user_id))
            await db.commit()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return

        config = await self.get_config(message.guild.id)
        if not config or config[4] == 0:
            return

        if await self.is_ignored(message):
            return

        if config[2] and self.invite_pattern.search(message.content):
            await message.delete()
            await message.channel.send(f"{message.author.mention}, invite links are not allowed.", delete_after=5)
            await self.add_warning(message.guild, message.author, "Posting invite link", "Automod")

        if config[3]:
            content = message.content
            if len(content) >= 10:
                cap_ratio = sum(1 for c in content if c.isupper()) / len(content)
                if cap_ratio >= CAPS_THRESHOLD:
                    await message.delete()
                    await message.channel.send(f"{message.author.mention}, please avoid excessive caps.", delete_after=5)
                    await self.add_warning(message.guild, message.author, "Excessive caps", "Automod")

async def setup(bot):
    await bot.add_cog(Automod(bot))