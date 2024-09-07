import discord
import aiohttp
from discord.ext import commands
from discord import app_commands

class SetupAutoMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="setup_automod", description="Sets up the automod rules for the server")
    @discord.app_commands.default_permissions(administrator=True)
    @discord.app_commands.describe(channel="Channel to send alert messages to")
    @discord.app_commands.describe(badword="Word that will be blocked")
    async def setup_automod_command(self, interaction: discord.Interaction, channel: discord.TextChannel, badword: str = None):
        headers = {
            "Authorization": f"Bot {self.bot.http.token}",
            "Content-Type": "application/json"
        }
        if badword is not None:
            auto_mod_rule = {
                "name": "Prohibit offensive language",
                "event_type": 1,  
                "trigger_type": 1,  
                "trigger_metadata": {
                    "keyword_filter": [f"{badword}"],
                },
                "actions": [
                    {
                        "type": 1,  
                    },
                    {
                        "type": 2,  
                        "metadata": {
                            "channel_id": channel.id
                        }
                    }
                ],
                "enabled": True  
            }
        else:
            auto_mod_rule = {
                "name": "Prohibit offensive language",
                "event_type": 1,  
                "trigger_type": 1,  
                "trigger_metadata": {
                    "keyword_filter": [f"Fuck", "Bitch"],
                },
                "actions": [
                    {
                        "type": 1,  
                    },
                    {
                        "type": 2,  
                        "metadata": {
                            "channel_id": channel.id
                        }
                    }
                ],
                "enabled": True  
            }
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://discord.com/api/v10/guilds/{interaction.guild.id}/auto-moderation/rules",
                headers=headers
            ) as resp:
                existing_rules = await resp.json()
                keyword_rules = [rule for rule in existing_rules if rule['trigger_type'] == 1]
                if len(keyword_rules) >= 6:
                    await interaction.response.send_message("The server has reached the maximum number of keyword-based automod rules.", ephemeral=True)
                    return

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"https://discord.com/api/v10/guilds/{interaction.guild.id}/auto-moderation/rules",
                headers=headers,
                json=auto_mod_rule
            ) as resp:
                if resp.status in [200,201,204]:
                    await interaction.response.send_message(f"Automod rule created for {interaction.guild.name}. alert channel is {channel.mention}", ephemeral=True)
                else:
                    error_text = await resp.text()
                    await interaction.response.send_message(f"Error creating automod rule: {resp.status} - {error_text}", ephemeral=True)


async def setup(bot):
    await bot.add_cog(SetupAutoMod(bot))