#WARNING: Giveaway Function is Beta. Use it on our own risk, May break the Function 



import discord
from discord.ext import commands, tasks
from discord import app_commands
import aiosqlite
import asyncio
import random
from datetime import datetime, timedelta
import time
import re

DATABASE = "giveaways.db"

def parse_duration_seconds(duration: str) -> int:
    """Parse duration string into seconds with improved error handling."""
    pattern = re.compile(r"(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?")
    match = pattern.fullmatch(duration.lower().replace(" ", ""))
    if not match:
        raise ValueError("Invalid duration format. Use format like 1d2h30m15s, 90m, 2h, 45s, etc.")

    days, hours, minutes, seconds = match.groups()
    total_seconds = 0
    if days:
        total_seconds += int(days) * 24 * 60 * 60
    if hours:
        total_seconds += int(hours) * 60 * 60
    if minutes:
        total_seconds += int(minutes) * 60
    if seconds:
        total_seconds += int(seconds)
    if total_seconds == 0:
        raise ValueError("Duration must be greater than 0 seconds.")
    return total_seconds

class GiveawayView(discord.ui.View):
    """Persistent view for entering giveaways."""
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Enter", style=discord.ButtonStyle.blurple, emoji="🎉", custom_id="giveaway_enter")
    async def enter(self, interaction: discord.Interaction, button: discord.ui.Button):
        async with aiosqlite.connect(DATABASE) as db:
            cursor = await db.execute("SELECT participants, winners_count FROM giveaways WHERE message_id = ?", (interaction.message.id,))
            row = await cursor.fetchone()
            
            if not row:
                await interaction.response.send_message("This giveaway is no longer active.", ephemeral=True)
                return
                
            participants, winners_count = row
            participants_list = participants.split(",") if participants and participants != "" else []
            
            if str(interaction.user.id) in participants_list:
                await interaction.response.send_message("You have already entered this giveaway!", ephemeral=True)
                return
            
            participants_list.append(str(interaction.user.id))
            await db.execute("UPDATE giveaways SET participants = ? WHERE message_id = ?", 
                           (",".join(participants_list), interaction.message.id))
            await db.commit()
            
            await interaction.response.send_message(
                f"🎉 You've successfully entered the giveaway! Good luck!", 
                ephemeral=True
            )

class ConfirmView(discord.ui.View):
    """Confirmation view for giveaway creation."""
    def __init__(self, original_interaction: discord.Interaction, channel: discord.TextChannel, 
                 prize: str, duration: str, winners: int):
        super().__init__(timeout=60)
        self.original_interaction = original_interaction
        self.channel = channel
        self.prize = prize
        self.duration = duration
        self.winners = winners

    async def on_timeout(self):
        try:
            await self.original_interaction.edit_original_response(
                content="Giveaway creation timed out.", view=None
            )
        except:
            pass

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        
        try:
            duration_seconds = parse_duration_seconds(self.duration)
        except ValueError as e:
            await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)
            return

        ends_at = datetime.now() + timedelta(seconds=duration_seconds)
        unix_end_time = int(ends_at.timestamp())

        # Create giveaway embed
        giveaway_embed = discord.Embed(
            title="🎉 **GIVEAWAY** 🎉",
            description=f"**Prize:** {self.prize}",
            color=discord.Color.gold(),
            timestamp=ends_at
        )
        giveaway_embed.add_field(
            name="Details", 
            value=f"**Winners:** {self.winners}\n**Ends:** <t:{unix_end_time}:R>",
            inline=True
        )
        giveaway_embed.add_field(
            name="Host", 
            value=self.original_interaction.user.mention,
            inline=True
        )
        giveaway_embed.set_footer(text=f"Ends at • <t:{unix_end_time}:F>")

        try:
            # Send giveaway message
            msg = await self.channel.send(embed=giveaway_embed, view=GiveawayView())
            
            # Store in database
            async with aiosqlite.connect(DATABASE) as db:
                await db.execute(
                    """INSERT INTO giveaways 
                    (message_id, channel_id, guild_id, prize, ends_at, winners_count, participants) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (msg.id, self.channel.id, self.original_interaction.guild.id, 
                     self.prize, ends_at.isoformat(), self.winners, "")
                )
                await db.commit()
            
            await interaction.followup.send(
                f"✅ Giveaway started successfully in {self.channel.mention}!", 
                ephemeral=True
            )
            
        except discord.Forbidden:
            await interaction.followup.send(
                "❌ I don't have permission to send messages in that channel.", 
                ephemeral=True
            )
        except Exception as e:
            await interaction.followup.send(
                f"❌ An error occurred while starting the giveaway: {str(e)}", 
                ephemeral=True
            )

        # Disable the confirmation buttons
        for item in self.children:
            item.disabled = True
        await self.original_interaction.edit_original_response(view=self)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await interaction.followup.send("Giveaway creation cancelled.", ephemeral=True)
        
        # Disable the confirmation buttons
        for item in self.children:
            item.disabled = True
        await self.original_interaction.edit_original_response(view=self)

class GiveawayCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_lock = asyncio.Lock()

    async def cog_load(self):
        """Initialize database and start background tasks."""
        async with aiosqlite.connect(DATABASE) as db:
            await db.execute("""
            CREATE TABLE IF NOT EXISTS giveaways (
                message_id INTEGER PRIMARY KEY,
                channel_id INTEGER,
                guild_id INTEGER,
                prize TEXT,
                ends_at TEXT,
                winners_count INTEGER,
                participants TEXT
            )
            """)
            await db.commit()
        
        # Register persistent view
        self.bot.add_view(GiveawayView())
        self.check_giveaways.start()

    def cog_unload(self):
        """Cleanup when cog is unloaded."""
        self.check_giveaways.cancel()

    @tasks.loop(seconds=30)
    async def check_giveaways(self):
        """Check for ended giveaways every 30 seconds."""
        async with self.db_lock:
            async with aiosqlite.connect(DATABASE) as db:
                cursor = await db.execute("SELECT * FROM giveaways")
                giveaways = await cursor.fetchall()
                
                for giveaway in giveaways:
                    message_id, channel_id, guild_id, prize, ends_at, winners_count, participants = giveaway
                    end_time = datetime.fromisoformat(ends_at)
                    
                    if datetime.now() >= end_time:
                        channel = self.bot.get_channel(channel_id)
                        if not channel:
                            continue
                            
                        try:
                            # Try to fetch the original message
                            message = await channel.fetch_message(message_id)
                            
                            # Disable the enter button
                            disabled_view = GiveawayView()
                            for item in disabled_view.children:
                                item.disabled = True
                            await message.edit(view=disabled_view)
                            
                        except discord.NotFound:
                            pass  # Message was deleted
                        except discord.Forbidden:
                            pass  # No permissions to edit message
                        
                        # Select winners
                        participants_list = participants.split(",") if participants and participants != "" else []
                        winners_embed = discord.Embed(
                            title="🎉 **GIVEAWAY ENDED** 🎉",
                            description=f"**Prize:** {prize}",
                            color=discord.Color.green()
                        )
                        
                        if participants_list and len(participants_list) >= winners_count:
                            winners = random.sample(participants_list, min(int(winners_count), len(participants_list)))
                            winner_mentions = ", ".join(f"<@{w}>" for w in winners)
                            winners_embed.add_field(
                                name=f"Winner{'s' if len(winners) > 1 else ''}", 
                                value=winner_mentions, 
                                inline=False
                            )
                            winners_embed.set_footer(text=f"Congratulations! {len(participants_list)} people participated.")
                        else:
                            winners_embed.add_field(
                                name="Result", 
                                value="Not enough participants to determine winners.", 
                                inline=False
                            )
                            winners_embed.set_footer(text="No winners were selected.")
                        
                        await channel.send(embed=winners_embed)
                        
                        # Remove from database
                        await db.execute("DELETE FROM giveaways WHERE message_id = ?", (message_id,))
                
                await db.commit()

    @check_giveaways.before_loop
    async def before_check_giveaways(self):
        """Wait until bot is ready before starting the loop."""
        await self.bot.wait_until_ready()

    giveaway_group = app_commands.Group(name="giveaway", description="Manage giveaways")

    @giveaway_group.command(name="create", description="Create a new giveaway")
    @app_commands.describe(
        channel="Channel to host the giveaway",
        prize="Prize of the giveaway",
        duration="Duration (1d2h30m15s, 45m, 2h, 30s)",
        winners="Number of winners",
    )
    async def create(self, interaction: discord.Interaction, channel: discord.TextChannel, 
                    prize: str, duration: str, winners: int):
        """Create a new giveaway with confirmation."""
        if winners < 1:
            await interaction.response.send_message("❌ Number of winners must be at least 1.", ephemeral=True)
            return
        
        try:
            duration_seconds = parse_duration_seconds(duration)
        except ValueError as e:
            await interaction.response.send_message(f"❌ {e}", ephemeral=True)
            return

        # Preview embed
        preview_embed = discord.Embed(
            title="🎉 **GIVEAWAY PREVIEW** 🎉",
            description=f"**Prize:** {prize}",
            color=discord.Color.blue()
        )
        preview_embed.add_field(name="Channel", value=channel.mention, inline=True)
        preview_embed.add_field(name="Duration", value=duration, inline=True)
        preview_embed.add_field(name="Winners", value=winners, inline=True)
        preview_embed.set_footer(text="Please confirm to start the giveaway")

        view = ConfirmView(interaction, channel, prize, duration, winners)
        await interaction.response.send_message(embed=preview_embed, view=view, ephemeral=True)

    @giveaway_group.command(name="list", description="List active giveaways in this server")
    async def list_giveaways(self, interaction: discord.Interaction):
        """List all active giveaways in the server."""
        async with aiosqlite.connect(DATABASE) as db:
            cursor = await db.execute(
                "SELECT prize, ends_at, winners_count FROM giveaways WHERE guild_id = ?", 
                (interaction.guild.id,)
            )
            rows = await cursor.fetchall()
            
            if not rows:
                await interaction.response.send_message("No active giveaways in this server.", ephemeral=True)
                return
            
            embed = discord.Embed(
                title=f"Active Giveaways in {interaction.guild.name}",
                color=discord.Color.blue()
            )
            
            for prize, ends_at, winners_count in rows:
                unix_end_time = int(datetime.fromisoformat(ends_at).timestamp())
                embed.add_field(
                    name=prize,
                    value=f"Ends: <t:{unix_end_time}:R> | Winners: {winners_count}",
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @giveaway_group.command(name="end", description="End a giveaway early")
    @app_commands.describe(message_id="The message ID of the giveaway to end")
    async def end(self, interaction: discord.Interaction, message_id: str):
        """End a giveaway early by message ID."""
        try:
            message_id_int = int(message_id)
        except ValueError:
            await interaction.response.send_message("❌ Please provide a valid message ID.", ephemeral=True)
            return
        
        async with aiosqlite.connect(DATABASE) as db:
            cursor = await db.execute(
                "SELECT channel_id, prize, participants, winners_count FROM giveaways WHERE message_id = ? AND guild_id = ?",
                (message_id_int, interaction.guild.id)
            )
            row = await cursor.fetchone()
            
            if not row:
                await interaction.response.send_message("❌ Giveaway not found.", ephemeral=True)
                return
                
            channel_id, prize, participants, winners_count = row
            channel = self.bot.get_channel(channel_id)
            
            if not channel:
                await interaction.response.send_message("❌ Channel not found.", ephemeral=True)
                return
            
            # End the giveaway by setting its end time to now
            await db.execute(
                "UPDATE giveaways SET ends_at = ? WHERE message_id = ?",
                (datetime.now().isoformat(), message_id_int)
            )
            await db.commit()
            
            await interaction.response.send_message(
                f"✅ Giveaway for **{prize}** will be ended shortly.", 
                ephemeral=True
            )

    @giveaway_group.command(name="reroll", description="Reroll winners for a completed giveaway")
    @app_commands.describe(message_id="The message ID of the giveaway to reroll")
    async def reroll(self, interaction: discord.Interaction, message_id: str):
        """Reroll winners for a completed giveaway."""
        try:
            message_id_int = int(message_id)
        except ValueError:
            await interaction.response.send_message("❌ Please provide a valid message ID.", ephemeral=True)
            return
        
        async with aiosqlite.connect(DATABASE) as db:
            cursor = await db.execute(
                "SELECT channel_id, prize, participants, winners_count FROM giveaways WHERE message_id = ?",
                (message_id_int,)
            )
            row = await cursor.fetchone()
            
            if row:
                await interaction.response.send_message(
                    "❌ This giveaway is still active. Use `/giveaway end` first.", 
                    ephemeral=True
                )
                return
            
        # For completed giveaways, you would need to store completed giveaways in another table
        # This is a placeholder for the reroll functionality
        await interaction.response.send_message(
            "❌ Reroll functionality for completed giveaways is not yet implemented.", 
            ephemeral=True
        )

async def setup(bot):
    """Setup function for loading the cog."""
    await bot.add_cog(GiveawayCog(bot))