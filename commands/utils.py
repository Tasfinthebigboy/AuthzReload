import discord
from discord.ext import commands
from discord import app_commands

class Utils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="userinfo", description="Show info about a user.")
    async def userinfo(self, interaction: discord.Interaction, user: discord.Member = None):
        user = user or interaction.user
        embed = discord.Embed(
            title=f"User Info - {user}",
            color=user.color if hasattr(user, 'color') else discord.Color.blue()
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="🆔 ID", value=user.id, inline=False)
        embed.add_field(name="🗓️ Joined", value=user.joined_at.strftime("%Y-%m-%d %H:%M"), inline=False)
        embed.add_field(name="📅 Created", value=user.created_at.strftime("%Y-%m-%d %H:%M"), inline=False)
        embed.add_field(name="🎭 Roles", value=', '.join(r.mention for r in user.roles[1:]) or "None", inline=False)
        embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="roleinfo", description="Show details about a role.")
    async def roleinfo(self, interaction: discord.Interaction, role: discord.Role):
        embed = discord.Embed(title=f"Role Info - {role.name}", color=role.color)
        embed.add_field(name="🆔 ID", value=role.id, inline=False)
        embed.add_field(name="📅 Created", value=role.created_at.strftime("%Y-%m-%d %H:%M"), inline=False)
        embed.add_field(name="👥 Members", value=len(role.members), inline=False)
        embed.add_field(name="💬 Mentionable", value=role.mentionable, inline=False)
        embed.add_field(name="📌 Position", value=role.position, inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="serverinfo", description="Get information about the server.")
    async def serverinfo(self, interaction: discord.Interaction):
        guild = interaction.guild
        embed = discord.Embed(title=f"Server Info - {guild.name}", color=discord.Color.green())
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        embed.add_field(name="🆔 ID", value=guild.id, inline=True)
        embed.add_field(name="👑 Owner", value=guild.owner, inline=True)
        embed.add_field(name="👥 Members", value=guild.member_count, inline=True)
        embed.add_field(name="📅 Created", value=guild.created_at.strftime("%Y-%m-%d %H:%M"), inline=True)
        embed.add_field(name="💬 Channels", value=len(guild.channels), inline=True)
        embed.add_field(name="🗂️ Roles", value=len(guild.roles), inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="channelinfo", description="Get information about a channel.")
    async def channelinfo(self, interaction: discord.Interaction, channel: discord.abc.GuildChannel = None):
        channel = channel or interaction.channel
        embed = discord.Embed(title=f"Channel Info - {channel.name}", color=discord.Color.teal())
        embed.add_field(name="🆔 ID", value=channel.id, inline=False)
        embed.add_field(name="📚 Type", value=type(channel).__name__, inline=False)
        embed.add_field(name="📅 Created", value=channel.created_at.strftime("%Y-%m-%d %H:%M"), inline=False)
        embed.add_field(name="📂 Category", value=channel.category.name if channel.category else "None", inline=False)
        if isinstance(channel, discord.TextChannel):
            embed.add_field(name="🔐 NSFW", value=channel.is_nsfw(), inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="say", description="Make the bot say something.")
    async def say(self, interaction: discord.Interaction, message: str):
        await interaction.response.send_message("✅ Sent.", ephemeral=True)
        await interaction.channel.send(f"*'{message}' said by {interaction.user.name}*")

    @app_commands.command(name="createinvite", description="Create a plain invite link to this server")
    async def create_invite(self, interaction: discord.Interaction):
        await interaction.response.defer()

        try:
        
            invite = await interaction.channel.create_invite(
                max_age=604800,
                max_uses=5,
                unique=True,
                reason=f"Requested by {interaction.user}"
            )
        except discord.Forbidden:
            return await interaction.followup.send("❌ I don't have permission to create invites.", ephemeral=True)
        except Exception as e:
            return await interaction.followup.send(f"❌ Failed to create invite: {e}", ephemeral=True)

        await interaction.followup.send(f"Here is your invite link:\n{invite.url}\n")
async def setup(bot):
    await bot.add_cog(Utils(bot))
