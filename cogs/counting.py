import re
import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite

# Auto-moderation regex patterns
prohibited_words_pattern = re.compile(
    r'\b(bad|words)\b', re.IGNORECASE
)
profanity_pattern = re.compile(
    r'\b(bad|words)\b', re.IGNORECASE
)
link_pattern = re.compile(r'http[s]?://\S+', re.IGNORECASE)
caps_lock_pattern = re.compile(r'[A-Z]{2,}', re.IGNORECASE)
mention_pattern = re.compile(r'<@!?\d+>', re.IGNORECASE)

spam_count = 5
max_caps_percentage = 70
max_mentions = 5

async def check_permissions(member):
    """Check if the member has Manage Server permission."""
    return member.guild_permissions.manage_guild

class Counting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        # Initialize the database
        async with aiosqlite.connect("counting.db") as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS counts (
                    guild_id INTEGER PRIMARY KEY,
                    channel_id INTEGER NOT NULL,
                    current_number INTEGER NOT NULL DEFAULT 0,
                    last_counter_id INTEGER
                )
                """
            )
            await db.commit()

    async def automoderation(self, message):
        """Automod checks for the message content"""
        if await check_permissions(message.author):
            return False  # Skip automod if the user has manage guild permissions

        if prohibited_words_pattern.search(message.content):
            await message.delete()
            await message.author.send("⚠️ Your message contained a prohibited word and was deleted.")
            return True

        if profanity_pattern.search(message.content):
            await message.delete()
            await message.author.send("⚠️ Your message contained profanity and was deleted.")
            return True

        if link_pattern.search(message.content):
            await message.delete()
            await message.author.send("⚠️ Your message contained an unapproved link and was deleted.")
            return True

        caps_percentage = (sum(1 for c in message.content if c.isupper()) / len(message.content)) * 100
        if caps_percentage > max_caps_percentage:
            await message.delete()
            await message.author.send("⚠️ Your message contained too many uppercase letters and was deleted.")
            return True

        mentions = len(mention_pattern.findall(message.content))
        if mentions > max_mentions:
            await message.delete()
            await message.author.send("⚠️ Your message contained too many mentions and was deleted.")
            return True

        return False  # No automod actions were taken

    @app_commands.command(name="count", description="Set the counting channel")
    @app_commands.describe(channel="The channel where counting will take place")
    async def set_count_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = interaction.guild_id
        channel_id = channel.id

        async with aiosqlite.connect("counting.db") as db:
            await db.execute(
                """
                INSERT OR REPLACE INTO counts (guild_id, channel_id, current_number, last_counter_id)
                VALUES (?, ?, 0, NULL)
                """,
                (guild_id, channel_id),
            )
            await db.commit()

        embed = discord.Embed(
            title="Counting Channel Set",
            description=f"The counting channel has been set to {channel.mention}.",
            color=discord.Color.green(),
        )
        await interaction.response.send_message(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        # Run automod first
        automod_action_taken = await self.automoderation(message)
        if automod_action_taken:
            return  # Automod action was taken, don't continue to counting logic

        # Counting logic
        guild_id = message.guild.id
        channel_id = message.channel.id

        async with aiosqlite.connect("counting.db") as db:
            # Get the counting channel and current number
            cursor = await db.execute(
                "SELECT channel_id, current_number, last_counter_id FROM counts WHERE guild_id = ?",
                (guild_id,)
            )
            result = await cursor.fetchone()

            if result is None or result[0] != channel_id:
                return  # No channel set or wrong channel

            current_number = result[1]
            last_counter_id = result[2]

            try:
                number = int(message.content)
            except ValueError:
                await message.delete()
                return  # Invalid number

            if number == current_number + 1:
                if message.author.id == last_counter_id:
                    await message.delete()
                    error_embed = discord.Embed(
                        title="Error",
                        description="You cannot send two numbers in a row. The count starts at 2 again.",
                        color=discord.Color.red(),
                    )
                    await message.channel.send(embed=error_embed, delete_after=5)
                else:
                    current_number += 1
                    await db.execute(
                        "UPDATE counts SET current_number = ?, last_counter_id = ? WHERE guild_id = ?",
                        (current_number, message.author.id, guild_id),
                    )
                    await db.commit()
                    await message.add_reaction("✅")
            else:
                await message.delete()
                error_embed = discord.Embed(
                    title="Error",
                    description=f"Number {number} sent by {message.author.mention} has been deleted. The next number is: {current_number + 1}.",
                    color=discord.Color.red(),
                )
                await message.channel.send(embed=error_embed, delete_after=5)

        # Process other bot commands
        await self.bot.process_commands(message)

# Setup function for the cog
async def setup(bot):
    await bot.add_cog(Counting(bot))
