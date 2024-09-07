import discord
from discord import app_commands
from discord.ext import commands

class AvatarView(discord.ui.View):
    def __init__(self, target: discord.User):
        super().__init__(timeout=60)  # View timeout after 60 seconds
        self.target = target

    async def on_timeout(self):
        # Disable all buttons when the view times out
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True
        # Update the message to reflect the disabled state of the buttons
        if self.message:
            await self.message.edit(view=self)

    @discord.ui.button(label="Avatar", style=discord.ButtonStyle.primary)
    async def avatar_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        avatar_url = self.target.display_avatar.url
        embed = discord.Embed(title=f"{self.target}'s Avatar", color=discord.Color.blurple())
        embed.set_image(url=avatar_url)
        embed.set_footer(text=f"ID: {self.target.id}")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Banner", style=discord.ButtonStyle.secondary)
    async def banner_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Fetch the user to ensure we get the banner data
        target = await interaction.client.fetch_user(self.target.id)

        if target.banner:
            banner_url = target.banner.url
            embed = discord.Embed(title=f"{target}'s Banner", color=discord.Color.blurple())
            embed.set_image(url=banner_url)
            embed.set_footer(text=f"ID: {target.id}")
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message("This user has no banner set.", ephemeral=True)

class Avatar(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="avatar", description="Display a user's avatar or banner")
    @app_commands.describe(target="The user whose avatar or banner you want to display", hide_reply="Hide the bot's reply")
    async def avatar(self, interaction: discord.Interaction, target: discord.User = None, hide_reply: bool = False):
        target = target or interaction.user  # Default to the command user if no target is provided
        view = AvatarView(target=target)
        
        avatar_url = target.display_avatar.url
        embed = discord.Embed(title=f"{target}'s Avatar", color=discord.Color.blurple())
        embed.set_image(url=avatar_url)
        embed.set_footer(text=f"ID: {target.id}")

        # Send the message with buttons and an embed
        message = await interaction.response.send_message(embed=embed, view=view, ephemeral=hide_reply)
        view.message = message  # Save the message object to update it later

async def setup(bot):
    await bot.add_cog(Avatar(bot))
