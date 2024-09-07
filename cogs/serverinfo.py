import discord
from discord.ext import commands
from discord import app_commands

class ServerInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="serverinfo", description="Displays information about the server.")
    async def server_info(self, interaction: discord.Interaction):
        await interaction.response.defer()
        guild = interaction.guild
        embed = discord.Embed(title=f"[ {guild.name} ] Server Information", color=discord.Color.blue())
        embed.add_field(name="🆔 Server ID:", value=guild.id, inline=True)
        embed.add_field(name="👑 Owner:", value=guild.owner.mention, inline=True)
        embed.add_field(name="📅 Created:", value=f"{(discord.utils.snowflake_time(guild.id)).strftime('%Y-%m-%d')}", inline=True)
        embed.add_field(name="📊 Channels:", value=f"Text: {len(guild.text_channels)}, Voice: {len(guild.voice_channels)}", inline=True)
        embed.add_field(name="👥 Members:", value=guild.member_count, inline=True)
        embed.add_field(name="🎭 Roles:", value=len(guild.roles), inline=True)

        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ServerInfo(bot))