import discord
from discord.ext import commands
from discord import app_commands


class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        # Dropdown menu
        options = [
            discord.SelectOption(label="Moderation", description="Ban, kick, mute, warn, etc.", emoji="🔨"),
            discord.SelectOption(label="Utility", description="Useful server tools", emoji="🛠️"),
            discord.SelectOption(label="Automod", description="Automod setup & management", emoji="🤖"),
            discord.SelectOption(label="Fun & Entertainment", description="Games & fun stuff", emoji="🎉"),
            discord.SelectOption(label="General & Bot", description="General & AI features", emoji="📌"),
        ]
        self.add_item(HelpDropdown(options))

        # Buttons
        self.add_item(discord.ui.Button(
            label="Join our Support Server",
            url="https://discord.gg/t96vesj5Sx"
        ))
        self.add_item(discord.ui.Button(
            label="Visit Our Website",
            url="https://authz.bot.nu"
        ))


class HelpDropdown(discord.ui.Select):
    def __init__(self, options):
        super().__init__(placeholder="Choose a command category...", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        header = "```Use the select menu to explore the various categories AZ Authz offers```"

        if self.values[0] == "Moderation":
            desc = (
                f"{header}\n\n"
                "**🔨 Moderation Commands**\n"
                "`/ban` • Ban a member from the server\n"
                "`/kick` • Kick a member from the server\n"
                "`/unban` • Remove a ban from a user\n"
                "`/purge` • Bulk delete messages\n"
                "`/mute` • Temporarily mute a member\n"
                "`/unmute` • Remove a member's mute\n"
                "`/lock` • Lock a channel\n"
                "`/unlock` • Unlock a channel\n"
                "`/warn` • Issue a warning to a user\n"
                "`/warnings` • View a user's warnings\n"
                "`/delwarns` • Clear warnings for a user"
            )
            embed = discord.Embed(description=desc, color=discord.Color.red())

        elif self.values[0] == "Utility":
            desc = (
                f"{header}\n\n"
                "**🛠️ Utility Commands**\n"
                "`/ping` • Check the bot’s response time\n"
                "`/serverinfo` • View server information\n"
                "`/userinfo` • View user information\n"
                "`/roleinfo` • View details of a role\n"
                "`/channelinfo` • View details of a channel\n"
                "`/avatar` • Get a user’s avatar\n"
                "`/version` • Check the bot version\n"
                "`/createinvite` • Generate an invite link"
            )
            embed = discord.Embed(description=desc, color=discord.Color.green())

        elif self.values[0] == "Automod":
            desc = (
                f"{header}\n\n"
                "**🤖 Automod Commands**\n"
                "`/automod toggle` • Enable or disable automod\n"
                "`/automod setlog` • Set a channel for automod logs\n"
                "`/automod mode` • Change automod mode\n"
                "`/automod ignore` • Ignore a channel, role, or user\n"
                "`/automod unignore` • Remove an ignored target\n"
                "`/automod blockwords` • Manage blocked words\n"
                "`/automod setlogs` • Configure automod logging"
            )
            embed = discord.Embed(description=desc, color=discord.Color.orange())

        elif self.values[0] == "Fun & Entertainment":
            desc = (
                f"{header}\n\n"
                "**🎉 Fun & Entertainment Commands**\n"
                "`/8ball` • Ask the magic 8-ball\n"
                "`/meme` • Get a random meme\n"
                "`/coinflip` • Flip a coin\n"
                "`/roll` • Roll a dice\n"
                "`/rate` • Get a random rating\n"
                "`/joke` • Hear a random joke\n"
                "`/roast` • Get roasted by the bot"
            )
            embed = discord.Embed(description=desc, color=discord.Color.purple())

        elif self.values[0] == "General & Bot":
            desc = (
                f"{header}\n\n"
                "**📌 General & Bot Commands**\n"
                "`/say` • Make the bot say something\n"
                "`/help` • Show the help menu\n"
                "`/createinvite` • Create an invite link\n"
                "`/ai ask` • Ask the AI a question\n"
                "`/ai allowchannel` • Allow AI in a channel\n"
                "`/ai removechannel` • Remove AI from a channel\n"
                "`/sendembed` • Create a custom embed"
            )
            embed = discord.Embed(description=desc, color=discord.Color.blurple())

        await interaction.response.edit_message(embed=embed, view=self.view)



class HelpCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Don't know what to do? Get started by looking at the commands")
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="AZ Authz | Help",
            description="```Use the select menu to explore AZ Authz```\n**Links**\nWebsite: https://authz.bot.nu/\nSupport Server: https://authz.bot.nu/discord/\nBot Invite: https://authz.bot.nu/invite/.",
            color=discord.Color.blurple()
        )
        await interaction.response.send_message(embed=embed, view=HelpView())


async def setup(bot):
    await bot.add_cog(HelpCommand(bot))
