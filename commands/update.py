import discord
from discord.ext import commands
from discord import app_commands

class VersionCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.version = "v4.1"
        self.updates = [
            {
                "version":"v4.1",
                "date": "2025-09-22",
                "changes": [
                    "Updated Utils Commands (/serverinfo, /roleinfo, /channelinfo)",
                    "Added Embed Builder (/sendembed #channel)"
                    "Bug Fixes and Improvements."
                ]
            },
            {
                "version":"v4.0",
                "date": "2025-09-16",
                "changes": [
                    "AI Automod System Added.",
                    "AI Chat Added with image, pdf and file readable function (you just have to add attachment on replying to the bot's message)",
                    "Temp disabled music system. Due to yt_dlp cookie issue",
                    "Bug Fixes and Improvements."
                ]
            },            
            {
                "version":"v4.0-prerelease1",
                "date": "2025-08-27",
                "changes": [
                    "Redesigned Help Command.",
                    "Bug Fixes and Improvements."
                ]
            },
            {
                "version": "v4.0-beta3",
                "date": "2025-08-20",
                "changes": [
                    "Coverted Music Cog to slash commands (!play -> /play, !join -> /join and more!)",
                    "Change /update to /version for more accurate command name."
                ]
            },
                        {
                "version": "v4.0-beta2",
                "date": "2025-08-17",
                "changes": [
                    "Bug Fixes...",
                    "Added Music Cog in prefix commands (eg. !join, !play, !volume, etc)"
                ]
            },
            {
                "version": "v4.0-beta1",
                "date": "2025-08-10",
                "changes": [
                    "Redesigned Bot commands and functions",
                    "Added support for multiple blocked words using commas.",
                    "Improved error messages for every commands.",
                    "Improved the bot's response and embeds.",
                    "Better Uptime for the bot and Focused on Moderation and Utils",
                    "* Removed Welcome and Leave System",
                    "Added Fun commands for members"
                ]
            },
            {
                "version": "v3.1/2",
                "date": "2024-08-30 / 2024-10-08",
                "changes": [
                    "Added warning system with punishments.",
                    "Fixed slash command permissions.",
                    "Fixed Automod"
                ]
            },
            {
                "version": "v3.0.1",
                "date": "2024-08-29",
                "changes": [
                    "Added AutoMod System.",
                    "Added Welcome and Leave System"
                ]
            },
            {
                "version": "v3.0.1-beta",
                "date": "2024-08-25",
                "changes": [
                    "Added AutoMod System for the first time."
                ]
            },
            {
                "version": "v3.0",
                "date": "2024-05-28",
                "changes": [
                    "Remake of the bot for the third time.",
                    "Improved help command with buttons.",
                    "Better Function and Fixed Moderation Commands.",
                    "Bug Patches and Better Responses for commands."
                ]
            }
        ]

    @app_commands.command(name="version", description="Shows the bot's update history and current version")
    async def update(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title=f"Bot Updates — Current Version {self.version}",
            description="Here's what's new and what's changed over time:",
            color=discord.Color.blue()
        )

        for update in self.updates:
            changes_formatted = "\n".join([f"• {change}" for change in update["changes"]])
            embed.add_field(
                name=f"{update['version']} — {update['date']}",
                value=changes_formatted,
                inline=False
            )

        embed.set_footer(text="Made with ❤️ for the community")
        await interaction.response.send_message(embed=embed, ephemeral=False)


async def setup(bot):
    await bot.add_cog(VersionCommand(bot))
