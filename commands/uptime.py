import discord
from discord.ext import commands
from discord import app_commands
import datetime

BOT_VERSION = "4.2"
LIBRARY = "discord.py"

class Uptime(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.start_time = datetime.datetime.now()

    @app_commands.command(name="uptime", description="Shows bot info and uptime.")
    async def uptime(self, interaction: discord.Interaction):
        now = datetime.datetime.utcnow()
        delta = now - self.start_time

        days, remainder = divmod(int(delta.total_seconds()), 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"

        latency = round(self.bot.latency * 1000)  # in ms

        embed = discord.Embed(
            title="ℹ️ Bot Information",
            description=(
                f"**📌 Version:** {BOT_VERSION}\n"
                f"**📚 Library:** {LIBRARY}\n"
                f"**⏱️ Uptime:** {uptime_str}\n"
                f"**🏓 Ping:** {latency} ms"
            ),
            color=discord.Color.green()
        )

        embed.set_footer(
            text=f"Requested by {interaction.user}",
            icon_url=interaction.user.display_avatar.url
        )

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Uptime(bot))
