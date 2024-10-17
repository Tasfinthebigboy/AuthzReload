import discord
from discord.ext import commands

class Credits(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="credits", description="Show credits of the bot creators.")
    async def credits(self, interaction: discord.Interaction):
        banner = discord.Embed(title=None, description=None)
        banner.set_image(url="https://cdn.discordapp.com/attachments/1279120256018808963/1296456237910724628/Untitled_design.png?ex=67125a76&is=671108f6&hm=846332a714af38a202f84ffe0160568c3e7d3904799e613049031f54b711adb3&")

        credit = discord.Embed(title=None, description=None)
        credit.set_image(url="https://cdn.discordapp.com/attachments/1279120256018808963/1296459714955313152/Developer.png?ex=67125db3&is=67110c33&hm=dc0597a2e180db30af093b21516cbb17ada5355484df2a8a32571fe8110f95e8&")
        await interaction.response.send_message(embed=(banner, credit))

async def setup(bot):
    await bot.add_cog(Credits(bot))
