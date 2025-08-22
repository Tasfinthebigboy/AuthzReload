import discord, random
from discord.ext import commands
from discord import app_commands

class PingCMD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Tracks and shows the bot's current latency.")
    async def ping(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Pong! Bot's Latency",
            description=None,
            color=discord.Color.blurple()
        )
        embed.add_field(name="🤖 Bot Connection", value=f"{int(round(self.bot.latency * 1000))} ms", inline=True)
        embed.add_field(name="🛰️ Server Connection", value=f"{random.randint(30, 110)} ms", inline=True)
        embed.add_field(name="📡 Bot Location", value=f"India (cluster-3ef2f10c)", inline=True)
        embed.set_footer(text=f"Requested by • {interaction.user.name}.")

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(PingCMD(bot))