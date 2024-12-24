import discord
import aiohttp
from discord.ext import commands

class MemeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="meme", description="Get a random meme from Reddit")
    async def meme(self, interaction: discord.Interaction):
        await interaction.response.defer()

        try:
            timeout = aiohttp.ClientTimeout(total=15)  # Set a 15-second timeout
            async with aiohttp.ClientSession(timeout=timeout) as session:
                url = "https://www.reddit.com/r/memes/random.json?limit=1"  # Fetch a random post
                async with session.get(url) as response:
                    if response.status == 200:
                        meme_data = await response.json()

                        if meme_data and isinstance(meme_data, list) and len(meme_data) > 0:
                            # Extract the random meme from the list
                            random_meme = meme_data[0]['data']['children'][0]['data']

                            meme_title = random_meme.get('title', 'No Title')
                            meme_url = random_meme.get('url', '')
                            meme_subreddit = random_meme.get('subreddit_name_prefixed', '')
                            meme_permalink = f"https://reddit.com{random_meme.get('permalink', '')}"

                            embed = discord.Embed(title=meme_title, url=meme_permalink, color=discord.Color.blue())
                            embed.set_footer(text=f"From {meme_subreddit}")

                            # Check if the URL points to an image or video
                            if meme_url.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                                embed.set_image(url=meme_url)
                                await interaction.followup.send(embed=embed)
                            elif "v.redd.it" in meme_url or meme_url.endswith('.mp4'):
                                await interaction.followup.send(content=meme_url)
                            else:
                                await interaction.followup.send("Unsupported media format.")
                        else:
                            await interaction.followup.send("No memes found.")
                    else:
                        await interaction.followup.send(f"Failed to fetch meme. Status code: {response.status}")
        except Exception as e:
            await interaction.followup.send(f"An ultra rare error occurred")
            print(e)

async def setup(bot: commands.Bot):
    await bot.add_cog(MemeCog(bot))
