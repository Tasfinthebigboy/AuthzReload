import discord
from discord.ext import commands
from discord import app_commands

class Utils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="serverinfo", description="Shows information about the server.")
    async def serverinfo(self, interaction: discord.Interaction):
        guild = interaction.guild
        owner = guild.owner.mention if guild.owner else "Unknown"

        created_at = discord.utils.format_dt(guild.created_at, style="F")
        created_ago = discord.utils.format_dt(guild.created_at, style="R")

        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)

        boost_level = guild.premium_tier
        boost_count = guild.premium_subscription_count
        afk_timeout = guild.afk_timeout

        description = guild.description or "No description set for this server."

        embed = discord.Embed(
            title=f"{guild.name}",
            description=f"📢 Server Information\n{description}",
            color=discord.Color.teal(),
        )
        embed.set_thumbnail(url=guild.icon.url if guild.icon else discord.Embed.Empty)

        embed.add_field(
            name="📝 General Info",
            value=(
                f"**Name:** {guild.name}\n"
                f"**Server ID:** {guild.id}\n"
                f"**Owner:** {owner}\n"
                f"**Created:** {created_ago} • {created_at}"
            ),
            inline=False,
        )

        embed.add_field(
            name="👥 Members & Roles",
            value=(
                f"**Members:** {guild.member_count}\n"
                f"**Roles:** {len(guild.roles)}\n"
                f"**Verification Level:** {guild.verification_level}"
            ),
            inline=True,
        )

        embed.add_field(
            name="💎 Boost Status",
            value=(
                f"**Level:** {boost_level}\n"
                f"**Boosts:** {boost_count}\n"
                f"**AFK Timeout:** {afk_timeout} sec"
            ),
            inline=True,
        )

        embed.add_field(
            name="📂 Channels",
            value=(
                f"**Text:** {text_channels}\n"
                f"**Voice:** {voice_channels}\n"
                f"**Categories:** {categories}"
            ),
            inline=False,
        )

        embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="roleinfo", description="Shows information about a role.")
    async def roleinfo(self, interaction: discord.Interaction, role: discord.Role):
        permissions = [perm[0].replace("_", " ").title() for perm in role.permissions if perm[1]]
        perms_text = ", ".join(permissions) if permissions else "No permissions"

        embed = discord.Embed(
            title=f"Role info {role.mention}",
            color=role.color
        )
        embed.add_field(name="Role ID", value=role.id, inline=False)
        embed.add_field(name="Hoisted", value=role.hoist, inline=True)
        embed.add_field(name="Position from bottom", value=role.position, inline=True)
        embed.add_field(name="Mentionable", value=role.mentionable, inline=True)
        embed.add_field(name="Permissions", value=perms_text, inline=False)

        embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="userinfo", description="Shows information about a user.")
    async def userinfo(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user

        created_at = discord.utils.format_dt(member.created_at, style="F")
        created_ago = discord.utils.format_dt(member.created_at, style="R")

        joined_at = discord.utils.format_dt(member.joined_at, style="F") if member.joined_at else "Unknown"
        joined_ago = discord.utils.format_dt(member.joined_at, style="R") if member.joined_at else "Unknown"

        roles = [role.mention for role in member.roles if role != interaction.guild.default_role]
        top_role = member.top_role.mention if member.top_role else "None"

        embed = discord.Embed(
            title=f"🔍 User Info: {member.display_name}",
            description=f"Details about {member.mention}",
            color=discord.Color.blurple()
        )
        embed.set_thumbnail(url=member.display_avatar.url)

        embed.add_field(
            name="📋 Basic Info",
            value=(
                f"**ID:** {member.id}\n"
                f"**Username:** {member.name}\n"
                f"**Display Name:** {member.display_name}\n"
                f"**Bot:** {member.bot}"
            ),
            inline=False,
        )

        embed.add_field(
            name="📅 Timestamps",
            value=(
                f"**Joined:** {joined_ago} • {joined_at}\n"
                f"**Created:** {created_ago} • {created_at}"
            ),
            inline=False,
        )

        if member.premium_since:
            boosted_at = discord.utils.format_dt(member.premium_since, style="F")
            boosted_ago = discord.utils.format_dt(member.premium_since, style="R")
            embed.add_field(name="✨ Boosting", value=f"{boosted_ago} • {boosted_at}", inline=False)
        else:
            embed.add_field(name="✨ Boosting", value=f"None", inline=False)

        embed.add_field(
            name=f"📌 Roles [{len(roles)}]",
            value=" ".join(roles) if roles else "No roles",
            inline=False,
        )
        embed.add_field(name="🏆 Top Role", value=top_role, inline=False)

        embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.display_avatar.url)
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
