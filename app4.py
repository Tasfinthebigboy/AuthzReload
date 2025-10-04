import discord, sys, asyncio
from discord.ext import commands, tasks
from api import Token

#-------------UTF-8-------------#

sys.stdout.reconfigure(encoding='utf-8')

#--------------BOT--------------#

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

#------------UPINFO-------------#
status_index = 0

@tasks.loop(seconds=10)
async def rotate_streaming_status():
    global status_index

    members = sum(g.member_count for g in bot.guilds)
    channels = sum(len(g.channels) for g in bot.guilds)
    servers = len(bot.guilds)

    status_list = [
        f"With {members} members",
        f"With {channels} channels",
        f"With {servers} servers"
    ]

    activity = discord.Streaming(
        name=status_list[status_index],
        url="https://twitch.tv/discord"
    )
    await bot.change_presence(activity=activity)
    status_index = (status_index + 1) % len(status_list)

@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")
    rotate_streaming_status.start()
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(f"Error during command sync: {e}")


#------------COMMANDS-----------#

# class HelpButton(discord.ui.View):
#     def __init__(self):
#         super().__init__(timeout=None)
# 
#     @discord.ui.button(label="Help", style=discord.ButtonStyle.primary, emoji="❓")
#     async def help_button(self, interaction: discord.Interaction, button: discord.ui.Button):
#         await interaction.response.send_message(
#             "You can use `/help` to see all available commands!",
#             ephemeral=True
#         )
# 
# @bot.event
# async def on_command_error(ctx, error):
#     if isinstance(error, commands.CommandNotFound):
#         embed = discord.Embed(
#             title="👋 Hello There!",
#             description=(
#                 "It looks like you tried to use a prefix command, but I prefer **slash commands** for better experience.\n\n"
#                 "Try using `/help` to see all available commands.\n"
#                 "Or click the Help button below!"
#             ),
#             color=discord.Color.teal()
#         )
#         embed.set_thumbnail(url=bot.user.display_avatar.url)
#         embed.set_footer(text="Thanks for being here! 💙")
# 
#         view = HelpButton()
#         await ctx.send(embed=embed, view=view)
#     else:
#         raise error
# 
#--------------COGS-------------#
async def load_cogs():
    cogs = ["commands.ping", "commands.moderation", "commands.utils", "commands.avater", "commands.help", "commands.automod", "commands.fun", "commands.embedbuilder", "commands.genai", "commands.uptime"]
    print(f"Loaded {len(cogs)} cog(s)")
    for cog in cogs:
        
        try:
            await bot.load_extension(cog)
            
            print(f"Loaded {cog}")
        except Exception as e:
            print(f"Failed to load {cog}: {e}")

#--------------MAIN-------------#

async def main(): 
    await load_cogs()
    await bot.start(token=Token)      

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Error running the bot: {e}")
    except KeyboardInterrupt:
        print("Shutting down the bot")
