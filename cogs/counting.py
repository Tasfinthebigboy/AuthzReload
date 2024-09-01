import discord
from discord import app_commands
from discord.ext import commands
import aiosqlite

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

    @app_commands.command(name="count", description="Set the counting channel")
    @app_commands.describe(channel="The channel where counting will take place")
    async def set_count_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = interaction.guild_id
        channel_id = channel.id

        async with aiosqlite.connect("counting.db") as db:
            await db.execute(
                "INSERT OR REPLACE INTO counts (guild_id, channel_id) VALUES (?, ?)",
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

        guild_id = message.guild.id
        channel_id = message.channel.id

        async with aiosqlite.connect("counting.db") as db:
            # Get the counting channel and current number
            cursor = await db.execute(
                "SELECT channel_id, current_number, last_counter_id FROM counts WHERE guild_id = ?",
                (guild_id,),
            )
            result = await cursor.fetchone()
            
            if result is None or result[0] != channel_id:
                return
            
            current_number = result[1]
            last_counter_id = result[2]

            try:
                number = int(message.content)
            except ValueError:
                await message.delete()
                return

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

async def setup(bot):
    await bot.add_cog(Counting(bot))
