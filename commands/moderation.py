import discord
import aiosqlite
from datetime import datetime, timedelta
from discord.ext import commands
from discord import app_commands

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ban", description="Bans member from the guild.") 
    @app_commands.default_permissions(ban_members=True)
    @app_commands.describe(member="Member to ban", reason="Reason for the ban")
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = None):
        try:
            embed1 = discord.Embed(
                title=None,
                description=f"<:success:1402197013147291748> {member.name} was banned for {reason}",
                color=discord.Color.green()
            )
            embed2 = discord.Embed(
                title=None,
                description=f"<:success:1402197013147291748> {member.name} was banned without reason provided",
                color=discord.Color.green()
            )
            embed3 = discord.Embed(
                title=None,
                description=f"<:fail:1402197051894403103> You can't ban yourself",
                color=discord.Color.red()
            )
            embed4 = discord.Embed(
                title=None,
                description=f"<:fail:1402197051894403103> You can't do that to the user",
                color=discord.Color.red()
            )
            embed5 = discord.Embed(
                title=None,
                description=f"<:fail:1402197051894403103> Bot Missing Permission. Please contact a Admin",
                color=discord.Color.red()
            )
            await member.ban(reason=reason)
            await interaction.response.send_message(embed=embed1)

            if reason == None:
                await member.ban(reason=None)
                await interaction.response.send_message(embed=embed2)
                return
            
            if member == interaction.user:
                await interaction.response.send_message(embed=embed3, ephemeral=True)
                return

            if member.top_role >= interaction.user.top_role:
                await interaction.response.send_message(embed=embed4, ephemeral=True)
                return

            if commands.BotMissingPermissions:
                await interaction.response.send_message(embed=embed5, ephemeral=True)
                return
        except Exception as e:
            print(e)
            await interaction.response.send_message(f"You have caught an ultra rare error while trying to ban the member.")    

    @app_commands.command(name="kick", description="kicks a member from the guild.")
    @app_commands.default_permissions(kick_members=True)
    @app_commands.describe(member="Member to kick", reason="Reason for the kick")
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = None):
        try:
            embed1 = discord.Embed(
                title=None,
                description=f"<:success:1402197013147291748> {member.name} was kicked for {reason}",
                color=discord.Color.green()
            )
            embed2 = discord.Embed(
                title=None,
                description=f"<:success:1402197013147291748> {member.name} was kicked without reason provided",
                color=discord.Color.green()
            )
            embed3 = discord.Embed(
                title=None,
                description=f"<:fail:1402197051894403103> You can't kick yourself",
                color=discord.Color.red()
            )
            embed4 = discord.Embed(
                title=None,
                description=f"<:fail:1402197051894403103> You can't do that to the user",
                color=discord.Color.red()
            )
            if reason == None:
                await member.kick(reason=None)
                await interaction.response.send_message(embed=embed2)

            if member == interaction.user:
                await interaction.response.send_message(embed=embed3, ephemeral=True)
                return

            if member.top_role >= interaction.user.top_role:
                await interaction.response.send_message(embed=embed4, ephemeral=True)
                return

            await member.kick(reason=reason)
            await interaction.response.send_message(embed=embed1)
        except Exception as e:
            print(e)
            await interaction.response.send_message(f"You have caught an ultra rare error while trying to kick the member.")  

    @app_commands.command(name="unban", description="Unbans a user from the server")
    @app_commands.default_permissions(ban_members=True)
    @app_commands.describe(user="User to unban")
    async def unban(self, interaction: discord.Interaction, user: discord.User):
        embed = discord.Embed(
            title=None,
            description=f"<:success:1402197013147291748> User {user} was unbanned.",
            color=discord.Color.green()
        )
        async for ban_entry in interaction.guild.bans():
            banned_user = ban_entry.user
            if banned_user == user:
                await interaction.guild.unban(banned_user)
                await interaction.response.send_message(embed=embed)
                return
        await interaction.response.send_message(f'User {user} was not found in the banned list.')

    @app_commands.command(name="purge", description="Deletes a specified number of messages from the channel")
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.describe(amount="Number of messages to delete")
    async def purge(self, interaction: discord.Interaction, amount: int):
        await interaction.response.defer(ephemeral=True)
        if amount <= 0:
            await interaction.followup.send("Please specify a positive number of messages to delete.", ephemeral=True)
            return

        deleted = await interaction.channel.purge(limit=amount)
        await interaction.followup.send(f"Deleted {len(deleted)} messages.", ephemeral=True)

    @app_commands.command(name="lock", description="Locks a channel")
    async def lock_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await interaction.response.defer()
        overwrite = channel.overwrites_for(interaction.guild.default_role)
        overwrite.send_message = False
        await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
        await interaction.followup.send(embed=discord.Embed(
            title="Channel Locked",
            description=f"The channel {channel.mention} has been locked for messages.",
            color=discord.Color.red()
        ))

    @app_commands.command(name="unlock", description="Locks a channel")
    async def lock_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await interaction.response.defer()
        overwrite = channel.overwrites_for(interaction.guild.default_role)
        overwrite.send_message = True
        await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
        await interaction.followup.send(embed=discord.Embed(
            title="Channel Unlocked",
            description=f"The channel {channel.mention} has been unlocked.",
            color=discord.Color.green()
        ))

    async def ensure_table(self):
        async with aiosqlite.connect("warnings.db") as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS warnings (
                    user_id INTEGER,
                    guild_id INTEGER,
                    reason TEXT,
                    timestamp TEXT
                )
            """)
            await db.commit()

    @commands.Cog.listener()
    async def on_ready(self):
        await self.ensure_table()

    @app_commands.command(name="warn", description="Warn a user and DM them.")
    async def warn(self, interaction: discord.Interaction, user: discord.Member, reason: str):
        if user.bot:
            return await interaction.response.send_message("You can't warn a bot.", ephemeral=True)

        await self.ensure_table()

        async with aiosqlite.connect("warnings.db") as db:
            await db.execute(
                "INSERT INTO warnings (user_id, guild_id, reason, timestamp) VALUES (?, ?, ?, ?)",
                (user.id, interaction.guild.id, reason, datetime.utcnow().isoformat())
            )
            await db.commit()

            async with db.execute(
                "SELECT COUNT(*) FROM warnings WHERE user_id = ? AND guild_id = ?",
                (user.id, interaction.guild.id)
            ) as cursor:
                result = await cursor.fetchone()
                warn_count = result[0]

        try:
            embed = discord.Embed(
                title=f"You've been warned in {interaction.guild.name}",
                description=f"**Reason:** {reason}",
                color=discord.Color.orange()
            )
            embed.add_field(name="Total Warnings", value=f"{warn_count}/5", inline=False)
            embed.set_footer(text="Please follow the server rules.")
            await user.send(embed=embed)
        except:
            pass

        await interaction.response.send_message(f"{user.mention} has been warned. (Total: {warn_count}/5)")

        if warn_count == 3:
            await user.timeout(duration=604800, reason="3 warnings reached")  # 7 days in seconds
            await interaction.followup.send(f"{user.mention} has been timed out for 7 days due to 3 warnings.")
        elif warn_count >= 5:
            try:
                await user.ban(reason="5 warnings reached")
                await interaction.followup.send(f"{user.mention} has been banned for 7 days due to 5 warnings.")
            except:
                await interaction.followup.send(f"Failed to ban {user.mention}. Check bot permissions.")
            self.bot.loop.create_task(self.unban_and_reset(user.id, interaction.guild.id))

    async def unban_and_reset(self, user_id: int, guild_id: int):
        await discord.utils.sleep_until(datetime.utcnow() + timedelta(days=7))

        guild = self.bot.get_guild(guild_id)
        if guild is None:
            return

        try:
            await guild.unban(discord.Object(id=user_id), reason="Temporary 7-day ban expired.")
        except:
            pass

        async with aiosqlite.connect("warnings.db") as db:
            await db.execute(
                "DELETE FROM warnings WHERE user_id = ? AND guild_id = ?",
                (user_id, guild_id)
            )
            await db.commit()

    @app_commands.command(name="warnings", description="Check a user's warnings.")
    async def warnings(self, interaction: discord.Interaction, user: discord.Member):
        await self.ensure_table()

        async with aiosqlite.connect("warnings.db") as db:
            async with db.execute(
                "SELECT reason, timestamp FROM warnings WHERE user_id = ? AND guild_id = ?",
                (user.id, interaction.guild.id)
            ) as cursor:
                rows = await cursor.fetchall()

        if not rows:
            return await interaction.response.send_message(f"{user.mention} has no warnings.", ephemeral=True)

        embed = discord.Embed(
            title=f"{user} - Warning Log",
            color=discord.Color.red()
        )
        for i, (reason, timestamp) in enumerate(rows, start=1):
            time_fmt = datetime.fromisoformat(timestamp).strftime('%Y-%m-%d %H:%M')
            embed.add_field(name=f"#{i} at {time_fmt}", value=reason, inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="delwarns", description="Clear all warnings for a user.")
    async def delwarns(self, interaction: discord.Interaction, user: discord.Member):
        await self.ensure_table()

        async with aiosqlite.connect("warnings.db") as db:
            await db.execute(
                "DELETE FROM warnings WHERE user_id = ? AND guild_id = ?",
                (user.id, interaction.guild.id)
            )
            await db.commit()

        await interaction.response.send_message(f"All warnings cleared for {user.mention}.")

    @app_commands.command(name="mute", description="Mute (timeout) a member for a certain duration.")
    @app_commands.describe(
        member="The member to mute",
        duration="Duration of timeout in minutes",
        reason="Reason for mute (optional)"
    )
    async def mute(self, interaction: discord.Interaction, member: discord.Member, duration: int, reason: str = None):
        if member == interaction.user:
            return await interaction.response.send_message("You can't mute yourself.", ephemeral=True)
        if member.guild_permissions.administrator:
            return await interaction.response.send_message("You can't mute an administrator.", ephemeral=True)

        try:
            await member.timeout(timedelta(minutes=duration), reason=reason)

            if reason:
                embed = discord.Embed(
                    description=f"<:success:1402197013147291748> {member.name} was muted for {duration} minutes for {reason}",
                    color=discord.Color.green()
                )
            else:
                embed = discord.Embed(
                    description=f"<:success:1402197013147291748> {member.name} was muted for {duration} minutes without reason provided",
                    color=discord.Color.green()
                )

            await interaction.response.send_message(embed=embed)

        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to mute that user.", ephemeral=True)

    @app_commands.command(name="unmute", description="Remove timeout from a member.")
    @app_commands.describe(
        member="The member to unmute",
    )
    async def unmute(self, interaction: discord.Interaction, member: discord.Member):
        if member.timed_out_until is None:
            return await interaction.response.send_message(f"{member.mention} is not muted.", ephemeral=True)

        try:
            await member.timeout(None)
            embed = discord.Embed(
                description=f"<:success:1402197013147291748> {member.name} was unmuted without reason provided",
                color=discord.Color.green()
            )

            await interaction.response.send_message(embed=embed)

        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to unmute that user.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Moderation(bot))