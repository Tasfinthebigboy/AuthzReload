import discord
from discord.ext import commands
from discord import app_commands

class ButtonList(discord.ui.View):
    def __init__(self):
        super().__init__()

        self.add_item(discord.ui.Button(
            label="Join our Support Server",
            url="https://discord.gg/t96vesj5Sx"
        )) 

        self.add_item(discord.ui.Button(
            label="Visit Our Website",
            url="https://authz.bot.nu"
        ))            

class HelpCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Don't know what to do? Get started by looking at the commands")
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="AZ Authz | Help",
            description="All commands of the bot has been shown down below.",
            color=discord.Color.blurple()
        )
        embed.add_field(name="Moderation Commands", value="`/ban`,`/kick`,`/purge`,`/mute`,`/unmute`,`/lock`,`/unlock`,`/warn`,`/warnings`,`/delwarns`", inline=False)
        embed.add_field(name="Utils Commands", value="`/serverinfo`,`/avater`,`/channelinfo`,`/userinfo`,`and more`", inline=False)
        embed.add_field(name="Automod Commands", value="`/automod toggle`, `/automod setlog`, `/automod mode`, `and more`", inline=False)
        embed.add_field(name="Fun and Others", value="`/say`, `/help`, `/create_invite`", inline=False)

        await interaction.response.send_message(embed=embed, view=ButtonList())    


async def setup(bot):
    await bot.add_cog(HelpCommand(bot))     
        