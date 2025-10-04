import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Button, View
import asyncio
import re

MAX_FIELDS = 25
BUTTON_TIMEOUT = 900 

def is_valid_url(url: str) -> bool:
    return bool(re.match(r"^https?://\S+$", url))

class LiveEmbedBuilder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="sendembed", description="Create a live preview embed")
    @app_commands.describe(channel="Channel to send the embed to")
    @app_commands.default_permissions(manage_messages=True)
    async def sendembed(self, interaction: discord.Interaction, channel: discord.TextChannel):
        embed = discord.Embed(title="Embed Title", description="Embed Description", color=discord.Color.blue())

        class EmbedView(View):
            def __init__(self, bot, user, embed, channel):
                super().__init__(timeout=BUTTON_TIMEOUT)
                self.bot = bot
                self.user = user
                self.embed = embed
                self.channel = channel
                self.msg = None
                self.last_update = 0  
                self.interaction = None  

            async def ask_input(self, prompt):
                await self.interaction.followup.send(prompt, ephemeral=True)
                try:
                    msg = await self.bot.wait_for(
                        "message",
                        check=lambda m: m.author == self.user and m.channel == self.interaction.channel,
                        timeout=300
                    )
                    try:
                        await msg.delete()
                    except:
                        pass
                    return msg.content
                except asyncio.TimeoutError:
                    await self.interaction.followup.send("⏰ Time ran out!", ephemeral=True)
                    return None

            async def update_preview(self):
                now = asyncio.get_event_loop().time()
                if now - self.last_update < 0.5:  # 0.5 sec debounce
                    return
                self.last_update = now
                if self.msg:
                    try:
                        await self.msg.edit(embed=self.embed, view=self)
                    except discord.HTTPException:
                        pass

            async def interaction_check(self, interaction: discord.Interaction) -> bool:
                if interaction.user != self.user:
                    await interaction.response.send_message("❌ This is not your embed session.", ephemeral=True)
                    return False
                self.interaction = interaction
                return True

            async def on_timeout(self):
                for item in self.children:
                    item.disabled = True
                if self.msg:
                    try:
                        await self.msg.edit(view=self)
                    except:
                        pass

            # --- Buttons ---
            @discord.ui.button(label="Set Title", style=discord.ButtonStyle.primary)
            async def set_title(self, interaction: discord.Interaction, button: Button):
                await interaction.response.defer(ephemeral=True)
                result = await self.ask_input("Enter the embed title:")
                if result:
                    self.embed.title = result
                    await self.update_preview()
                    await self.interaction.followup.send("✅ Title updated.", ephemeral=True)

            @discord.ui.button(label="Set Description", style=discord.ButtonStyle.primary)
            async def set_description(self, interaction: discord.Interaction, button: Button):
                await interaction.response.defer(ephemeral=True)
                result = await self.ask_input("Enter the embed description:")
                if result:
                    self.embed.description = result
                    await self.update_preview()
                    await self.interaction.followup.send("✅ Description updated.", ephemeral=True)

            @discord.ui.button(label="Set Color", style=discord.ButtonStyle.secondary)
            async def set_color(self, interaction: discord.Interaction, button: Button):
                await interaction.response.defer(ephemeral=True)
                result = await self.ask_input("Enter HEX color code (e.g., #FF5733):")
                if result:
                    try:
                        self.embed.color = discord.Color(int(result.strip("#"), 16))
                        await self.update_preview()
                        await self.interaction.followup.send("✅ Color updated.", ephemeral=True)
                    except:
                        await self.interaction.followup.send("❌ Invalid color code.", ephemeral=True)

            @discord.ui.button(label="Set Footer", style=discord.ButtonStyle.secondary)
            async def set_footer(self, interaction: discord.Interaction, button: Button):
                await interaction.response.defer(ephemeral=True)
                text = await self.ask_input("Enter footer text:")
                if text is not None:
                    self.embed.set_footer(text=text)
                    await self.update_preview()
                    await self.interaction.followup.send("✅ Footer updated.", ephemeral=True)

            @discord.ui.button(label="Set Author", style=discord.ButtonStyle.secondary)
            async def set_author(self, interaction: discord.Interaction, button: Button):
                await interaction.response.defer(ephemeral=True)
                name = await self.ask_input("Enter author name:")
                if name:
                    icon_url = await self.ask_input("Enter author icon URL (optional):")
                    if icon_url and not is_valid_url(icon_url):
                        icon_url = None
                    self.embed.set_author(name=name, icon_url=icon_url)
                    await self.update_preview()
                    await self.interaction.followup.send("✅ Author updated.", ephemeral=True)

            @discord.ui.button(label="Set Thumbnail", style=discord.ButtonStyle.secondary)
            async def set_thumbnail(self, interaction: discord.Interaction, button: Button):
                await interaction.response.defer(ephemeral=True)
                url = await self.ask_input("Enter thumbnail URL:")
                if url and is_valid_url(url):
                    self.embed.set_thumbnail(url=url)
                    await self.update_preview()
                    await self.interaction.followup.send("✅ Thumbnail updated.", ephemeral=True)
                else:
                    await self.interaction.followup.send("❌ Invalid URL.", ephemeral=True)

            @discord.ui.button(label="Set Image", style=discord.ButtonStyle.secondary)
            async def set_image(self, interaction: discord.Interaction, button: Button):
                await interaction.response.defer(ephemeral=True)
                url = await self.ask_input("Enter image URL:")
                if url and is_valid_url(url):
                    self.embed.set_image(url=url)
                    await self.update_preview()
                    await self.interaction.followup.send("✅ Image updated.", ephemeral=True)
                else:
                    await self.interaction.followup.send("❌ Invalid URL.", ephemeral=True)

            @discord.ui.button(label="Add Field", style=discord.ButtonStyle.primary)
            async def add_field(self, interaction: discord.Interaction, button: Button):
                await interaction.response.defer(ephemeral=True)
                if len(self.embed.fields) >= MAX_FIELDS:
                    await self.interaction.followup.send("❌ Max 25 fields reached.", ephemeral=True)
                    return
                name = await self.ask_input("Enter field name:")
                if not name: return
                value = await self.ask_input("Enter field value:")
                if not value: return
                inline_resp = await self.ask_input("Inline? (yes/no):")
                inline = inline_resp.lower() in ("yes", "y") if inline_resp else False
                self.embed.add_field(name=name, value=value, inline=inline)
                await self.update_preview()
                await self.interaction.followup.send("✅ Field added.", ephemeral=True)

            @discord.ui.button(label="Remove Last Field", style=discord.ButtonStyle.danger)
            async def remove_field(self, interaction: discord.Interaction, button: Button):
                await interaction.response.defer(ephemeral=True)
                if self.embed.fields:
                    self.embed.remove_field(-1)
                    await self.update_preview()
                    await self.interaction.followup.send("✅ Last field removed.", ephemeral=True)
                else:
                    await self.interaction.followup.send("❌ No fields to remove.", ephemeral=True)

            @discord.ui.button(label="Save & Exit", style=discord.ButtonStyle.success)
            async def save_exit(self, interaction: discord.Interaction, button: Button):
                await interaction.response.defer(ephemeral=True)
                await self.interaction.followup.send("✅ Embed sent!", ephemeral=True)
                for item in self.children:
                    item.disabled = True
                if self.msg:
                    await self.msg.edit(view=self)
                await self.channel.send(embed=self.embed)
                self.stop()

            @discord.ui.button(label="Cancel & Exit", style=discord.ButtonStyle.danger)
            async def cancel_exit(self, interaction: discord.Interaction, button: Button):
                await interaction.response.defer(ephemeral=True)
                await self.interaction.followup.send("❌ Embed creation cancelled.", ephemeral=True)
                for item in self.children:
                    item.disabled = True
                if self.msg:
                    await self.msg.edit(view=self)
                self.stop()

        view = EmbedView(bot=self.bot, user=interaction.user, embed=embed, channel=channel)
        await interaction.response.send_message(embed=embed, view=view)
        view.msg = await interaction.original_response()
        view.interaction = interaction


async def setup(bot):
    await bot.add_cog(LiveEmbedBuilder(bot))