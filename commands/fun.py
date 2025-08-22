import discord
from discord.ext import commands
from discord import app_commands
import random
import aiohttp

class FunCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.jokes = [
            "Why don't skeletons fight each other? They don't have the guts.",
            "I'm reading a book on anti-gravity. It's impossible to put down!",
            "Why did the scarecrow win an award? Because he was outstanding in his field!",
            "I told my wife she was drawing her eyebrows too high. She looked surprised.",
            "Did you hear about the cheese factory that exploded? There was nothing left but de-brie.",
            "I would tell you a construction joke, but I'm still working on it.",
            "Why don’t scientists trust atoms? Because they make up everything.",
            "I asked the librarian if the library had books on paranoia. She whispered, 'They're right behind you.'",
            "What do you call fake spaghetti? An impasta.",
            "Why did the bicycle fall over? Because it was two-tired!",
            "I’m on a seafood diet. I see food and I eat it.",
            "Why don’t programmers like nature? Too many bugs.",
            "Why do cows have hooves instead of feet? Because they lactose.",
            "Why did the math book look sad? Because it had too many problems.",
            "What do you call a fish wearing a bowtie? Sofishticated.",
            "Why can’t your nose be 12 inches long? Because then it would be a foot.",
            "Why did the coffee file a police report? It got mugged.",
            "What do you call a snowman with a six-pack? An abdominal snowman.",
            "How do you organize a space party? You planet.",
            "Why don't eggs tell jokes? They'd crack each other up.",
            "What do you call cheese that isn't yours? Nacho cheese.",
            "Why did the tomato turn red? Because it saw the salad dressing!",
            "How does a penguin build its house? Igloos it together.",
            "Why did the golfer bring two pairs of pants? In case he got a hole in one.",
            "What do you call an alligator in a vest? An investigator.",
            "Why don’t oysters share their pearls? Because they’re shellfish.",
            "Why did the cookie go to the hospital? Because he felt crummy.",
            "Why did the computer go to the doctor? It had a virus.",
            "What do you call a bear with no teeth? A gummy bear.",
            "Why did the calendar go on a diet? It had too many dates.",
            "Why don’t skeletons ever go trick or treating? Because they have no body to go with.",
            "Why did the scarecrow become a successful neurosurgeon? Because he was outstanding in his field.",
            "Why don’t some couples go to the gym? Because some relationships don’t work out.",
            "What do you call a sleeping bull? A bulldozer.",
            "Why did the music teacher go to jail? Because she got caught with too many sharp objects.",
            "Why was the math lecture so long? The professor kept going off on a tangent.",
            "Why was the broom late? It swept in.",
            "Why don’t ants get sick? Because they have tiny ant-bodies.",
            "What do you call a dinosaur with an extensive vocabulary? A thesaurus.",
            "Why don’t you ever see elephants hiding in trees? Because they’re so good at it.",
            "Why did the jellybean go to school? Because it wanted to be a smartie.",
            "What do you call a pig that knows karate? A pork chop.",
            "Why was the belt arrested? For holding up a pair of pants.",
            "Why are ghosts bad liars? Because you can see right through them.",
            "Why do chicken coops only have two doors? Because if they had four, they’d be chicken sedans.",
            "What did the grape say when it got crushed? Nothing, it just let out a little wine.",
            "Why was the computer cold? It left its Windows open.",
            "Why can’t you trust stairs? Because they’re always up to something.",
            "Why was the stadium so cool? It was filled with fans.",
            "Why did the cow jump over the moon? Because the farmer had cold hands.",
            "Why did the banana go to the doctor? Because it wasn’t peeling well.",
            "What’s orange and sounds like a parrot? A carrot.",
            "Why did the chicken cross the playground? To get to the other slide.",
            "What do you get when you cross a snowman and a vampire? Frostbite.",
            "What do you call a pile of cats? A meowtain.",
            "Why did the skeleton go to the party alone? Because he had no body to go with.",
            "Why did the coffee break up with the sugar? Because it found her too sweet.",
            "How do you catch a squirrel? Climb a tree and act like a nut.",
            "Why don’t elephants use computers? Because they’re afraid of the mouse.",
            "Why did the orange stop rolling down the hill? It ran out of juice.",
            "Why did the fish blush? Because it saw the ocean’s bottom.",
            "What did one wall say to the other? I’ll meet you at the corner.",
            "Why do bees have sticky hair? Because they use honeycombs.",
            "Why was the tomato blushing? Because it saw the salad dressing.",
            "Why do ducks have feathers? To cover their butt quacks.",
            "What do you call a lazy kangaroo? A pouch potato.",
            "Why did the scarecrow win an award? Because he was outstanding in his field!",
            "Why do seagulls fly over the sea? Because if they flew over the bay, they’d be bagels.",
            "What do you call a bear caught in the rain? A drizzly bear.",
            "Why did the cookie go to the doctor? Because it felt crummy.",
            "Why did the bicycle fall over? Because it was two tired.",
            "What do you call a snowman with a six-pack? An abdominal snowman.",
            "How do you make a tissue dance? Put a little boogie in it.",
            "Why don’t scientists trust atoms? Because they make up everything.",
            "What’s brown and sticky? A stick.",
            "What do you call an elephant that doesn’t matter? An irrelephant.",
            "Why don’t some fish play piano? Because you can’t tuna fish.",
            "Why did the golfer bring two pairs of pants? In case he got a hole in one.",
            "Why did the man put his money in the freezer? Because he wanted cold hard cash.",
            "What do you call fake noodles? An impasta.",
            "Why did the mushroom go to the party alone? Because he’s a fungi.",
            "Why don’t you ever see elephants hiding in trees? Because they’re so good at it.",
            "Why did the coffee file a police report? It got mugged.",
            "What did the janitor say when he jumped out of the closet? Supplies!",
            "Why was the math book sad? Because it had too many problems.",
            "What did the ocean say to the beach? Nothing, it just waved.",
            "Why was the computer cold? It left its Windows open.",
            "Why did the chicken cross the road? To get to the other side.",
            "What do you call cheese that isn’t yours? Nacho cheese.",
            "Why did the hipster burn his mouth? Because he drank his coffee before it was cool.",
            "How do you organize a space party? You planet.",
            "Why did the scarecrow get promoted? Because he was outstanding in his field.",
            "What do you call a factory that makes okay products? A satisfactory.",
            "Why don’t skeletons fight each other? They don’t have the guts.",
            "Why do cows wear bells? Because their horns don’t work.",
            "What do you call a fish without eyes? Fsh.",
            "Why was the broom late? It swept in.",
            "Why was the stadium so cool? Because it had lots of fans.",
            "What do you call a dinosaur with an extensive vocabulary? A thesaurus.",
            "What’s a skeleton’s least favorite room? The living room.",
            "Why do chicken coops only have two doors? Because if they had four, they’d be chicken sedans.",
            "Why did the elephant paint its toenails red? So it could hide in cherry trees.",
            "Why did the hipster drown? He went ice skating before it was cool.",
            "Why did the scarecrow win an award? Because he was outstanding in his field.",
            "What do you call a boomerang that doesn’t come back? A stick.",
            "Why did the tomato turn red? Because it saw the salad dressing!",
            "How do you make holy water? You boil the hell out of it.",
            "What do you call a lazy kangaroo? A pouch potato.",
            "Why don’t ants get sick? Because they have tiny ant-bodies.",
            "Why did the coffee go to school? Because it wanted to be a little latte.",
            "What do you call a pile of cats? A meowtain.",
            "Why don’t oysters donate to charity? Because they are shellfish.",
            "Why was the math book sad? Because it had too many problems.",
            "What do you call a fish wearing a bowtie? Sofishticated.",
            "Why do bees have sticky hair? Because they use honeycombs.",
            "Why was the belt arrested? Because it held up a pair of pants.",
            "What did one wall say to the other? I’ll meet you at the corner.",
            "Why do ducks have feathers? To cover their butt quacks.",
            "Why don’t you ever see elephants hiding in trees? Because they’re so good at it.",
            "Why did the bicycle fall over? Because it was two tired.",
            "What do you call fake spaghetti? An impasta.",
            "Why don’t some couples go to the gym? Because some relationships don’t work out.",
            "Why did the golfer bring two pairs of pants? In case he got a hole in one.",
            "How do you catch a squirrel? Climb a tree and act like a nut.",
            "Why don’t scientists trust atoms? Because they make up everything.",
            "Why don’t ants get sick? Because they have tiny ant-bodies.",
            "What do you call a dinosaur with an extensive vocabulary? A thesaurus.",
            "Why did the cookie go to the doctor? Because it felt crummy.",
            "Why was the computer cold? It left its Windows open.",
            "Why don’t oysters share their pearls? Because they’re shellfish.",
            "Why did the scarecrow become a successful neurosurgeon? Because he was outstanding in his field.",
            "Why don’t you ever see elephants hiding in trees? Because they’re so good at it.",
            "Why did the coffee file a police report? It got mugged.",
            "Why did the calendar go on a diet? It had too many dates.",
            "Why did the banana go to the doctor? Because it wasn’t peeling well.",
            "Why did the man put his money in the freezer? Because he wanted cold hard cash.",
            "Why do cows have hooves instead of feet? Because they lactose.",
            "Why did the tomato turn red? Because it saw the salad dressing!",
            "What do you call a fish without eyes? Fsh.",
            "Why don’t skeletons ever go trick or treating? Because they have no body to go with.",
            "Why did the cookie go to the hospital? Because he felt crummy.",
            "Why did the computer go to the doctor? It had a virus.",
            "Why don’t programmers like nature? Too many bugs.",
            "Why did the music teacher go to jail? Because she got caught with too many sharp objects.",
            "Why was the stadium so cool? It was filled with fans.",
            "What’s orange and sounds like a parrot? A carrot.",
            "Why did the chicken cross the playground? To get to the other slide.",
            "What do you get when you cross a snowman and a vampire? Frostbite.",
            "Why did the fish blush? Because it saw the ocean’s bottom.",
            "What do you call a sleeping bull? A bulldozer.",
            "What do you call a bear caught in the rain? A drizzly bear.",
            "Why was the broom late? It swept in.",
            "What do you call an elephant that doesn’t matter? An irrelephant.",
            "What do you call a lazy kangaroo? A pouch potato.",
            "Why did the mushroom go to the party alone? Because he’s a fungi.",
            "Why did the jellybean go to school? Because it wanted to be a smartie.",
            "Why was the math lecture so long? The professor kept going off on a tangent.",
            "Why don’t ants get sick? Because they have tiny ant-bodies.",
            "Why did the chicken cross the road? To get to the other side.",
            "Why don’t some fish play piano? Because you can’t tuna fish.",
            "Why did the orange stop rolling down the hill? It ran out of juice.",
            "Why did the cow jump over the moon? Because the farmer had cold hands.",
            "Why don’t you trust stairs? Because they’re always up to something.",
            "Why did the coffee break up with the sugar? Because it found her too sweet.",
            "Why did the scarecrow get promoted? Because he was outstanding in his field.",
            "What do you call a factory that makes okay products? A satisfactory.",
            "What’s a skeleton’s least favorite room? The living room.",
            "What did the ocean say to the beach? Nothing, it just waved.",
            "Why was the computer cold? It left its Windows open.",
            "Why don’t skeletons fight each other? They don’t have the guts.",
            "Why do cows wear bells? Because their horns don’t work.",
            "Why was the belt arrested? For holding up a pair of pants.",
            "Why did the chicken cross the road? To get to the other side.",
            "What do you call cheese that isn’t yours? Nacho cheese.",
            "Why did the man put his money in the freezer? Because he wanted cold hard cash.",
            "What do you call fake noodles? An impasta.",
            "How do you organize a space party? You planet.",
            "Why don’t you ever see elephants hiding in trees? Because they’re so good at it.",
            "Why did the coffee file a police report? It got mugged.",
            "What did the janitor say when he jumped out of the closet? Supplies!",
            "Why was the math book sad? Because it had too many problems.",
            "Why did the bicycle fall over? Because it was two tired.",
            "What do you call a snowman with a six-pack? An abdominal snowman.",
            "How do you make a tissue dance? Put a little boogie in it.",
            "Why was the stadium so cool? Because it had lots of fans.",
            "Why do bees have sticky hair? Because they use honeycombs.",
            "Why was the tomato blushing? Because it saw the salad dressing.",
            "Why did the cookie go to the doctor? Because it felt crummy.",
            "Why did the coffee go to school? Because it wanted to be a little latte.",
            "Why did the chicken cross the playground? To get to the other slide.",
            "What do you call a sleeping bull? A bulldozer.",
            "What do you call a bear caught in the rain? A drizzly bear.",
            "Why was the broom late? It swept in.",
            "Why was the computer cold? It left its Windows open.",
            "Why don’t scientists trust atoms? Because they make up everything.",
            "Why don’t you trust stairs? Because they’re always up to something.",
            "Why did the cow jump over the moon? Because the farmer had cold hands.",
            "Why did the orange stop rolling down the hill? It ran out of juice.",
            "What’s brown and sticky? A stick.",
            "Why do chicken coops only have two doors? Because if they had four, they’d be chicken sedans.",
            "Why did the tomato turn red? Because it saw the salad dressing!",
            "What do you call a pile of cats? A meowtain.",
            "Why don’t oysters share their pearls? Because they’re shellfish.",
            "Why was the math book sad? Because it had too many problems.",
            "What do you call a fish wearing a bowtie? Sofishticated.",
            "Why did the mushroom go to the party alone? Because he’s a fungi.",
            "What do you call a boomerang that doesn’t come back? A stick.",
            "Why did the chicken cross the road? To get to the other side.",
            "Why did the golfer bring two pairs of pants? In case he got a hole in one.",
            "How do you catch a squirrel? Climb a tree and act like a nut.",
            "Why don’t programmers like nature? Too many bugs.",
            "Why don’t ants get sick? Because they have tiny ant-bodies.",
            "What do you call a dinosaur with an extensive vocabulary? A thesaurus.",
            "Why did the cookie go to the hospital? Because he felt crummy.",
            "Why was the computer cold? It left its Windows open.",
            "Why don’t oysters share their pearls? Because they’re shellfish.",
            "Why did the scarecrow become a successful neurosurgeon? Because he was outstanding in his field.",
            "Why don’t you ever see elephants hiding in trees? Because they’re so good at it.",
            "Why did the coffee file a police report? It got mugged.",
            "Why did the calendar go on a diet? It had too many dates.",
            "Why did the banana go to the doctor? Because it wasn’t peeling well.",
            "Why did the man put his money in the freezer? Because he wanted cold hard cash."
        ]

        self.roasts = [
            "You're like a cloud. When you disappear, it's a beautiful day.",
            "You're as sharp as a marble.",
            "You bring everyone so much joy… when you leave the room.",
            "You're the reason the gene pool needs a lifeguard.",
            "You're as useless as the 'ueue' in 'queue'.",
            "You have something on your chin… no, the third one down.",
            "You're as bright as a black hole, and twice as dense.",
            "Your secrets are always safe with me. I never even listen when you tell me them.",
            "You have something on your chin… no, the third one down.",
            "You're like a software update — whenever I see you, I think, 'Not now.'",
            "You're the human version of a participation trophy.",
            "If you were any slower, you'd be going backward.",
            "You're as confusing as a Rubik’s cube in the dark.",
            "You're proof that even evolution takes a break sometimes.",
            "You're like a puzzle with half the pieces missing.",
            "You're like a slinky — not really good for anything, but you bring a smile when pushed down the stairs.",
            "Your brain's got so many windows, but none of them open.",
            "You're about as useful as a screen door on a submarine.",
            "You have something on your chin… no, the third one down.",
            "You're like a WiFi signal in the basement — weak and hard to connect with.",
            "You're the reason we have instructions on shampoo bottles.",
            "You're the human version of a typo.",
            "Your brain is like the Bermuda Triangle — information goes in and never comes out.",
            "You're as interesting as watching paint dry.",
            "You're like a software bug — annoying but sometimes hilarious.",
            "You're the human embodiment of a migraine.",
            "You put the ‘pro’ in procrastinate.",
            "You're as organized as a tornado in a trailer park.",
            "You have the charm of a damp rag.",
            "You're like a broken pencil — pointless.",
            "You're about as bright as a burnt-out light bulb.",
            "You bring everyone so much joy… when you leave the room.",
            "You're as sharp as a marble.",
            "You're as useless as a chocolate teapot.",
            "You're like a GPS that keeps recalculating because you never get it right.",
            "You have all the personality of a soggy sandwich.",
            "You're as subtle as a clown at a funeral.",
            "You bring everyone so much joy… when you leave the room.",
            "You're like a software update — whenever I see you, I think, 'Not now.'",
            "You're the human version of a participation trophy.",
            "If you were any slower, you'd be going backward.",
            "You're as confusing as a Rubik’s cube in the dark.",
            "You're proof that even evolution takes a break sometimes.",
            "You're like a puzzle with half the pieces missing.",
            "You're like a slinky — not really good for anything, but you bring a smile when pushed down the stairs.",
            "Your brain's got so many windows, but none of them open.",
            "You're about as useful as a screen door on a submarine.",
            "You're like a WiFi signal in the basement — weak and hard to connect with.",
            "You're the reason we have instructions on shampoo bottles.",
            "You're the human version of a typo.",
            "Your brain is like the Bermuda Triangle — information goes in and never comes out.",
            "You're as interesting as watching paint dry.",
            "You're like a software bug — annoying but sometimes hilarious.",
            "You're the human embodiment of a migraine.",
            "You put the ‘pro’ in procrastinate.",
            "You're as organized as a tornado in a trailer park.",
            "You have the charm of a damp rag.",
            "You're like a broken pencil — pointless.",
            "You're about as bright as a burnt-out light bulb.",
            "You're the reason the gene pool needs a lifeguard.",
            "Your secrets are always safe with me. I never even listen when you tell me them.",
            "You're as useful as a screen door on a submarine.",
            "You have something on your chin… no, the third one down.",
            "You're like a cloud. When you disappear, it's a beautiful day.",
            "You're the human equivalent of a participation ribbon.",
            "You're as sharp as a bowling ball.",
            "You're as bright as a black hole, and twice as dense.",
            "Your brain is like a web browser with 1,000 tabs open... and none of them responding.",
            "You're as funny as a funeral.",
            "You bring everyone so much joy… when you leave the room.",
            "You're about as intimidating as a kitten with a paper crown.",
            "You have the personality of a damp sponge.",
            "You're like a broken escalator — never quite moving up.",
            "You're the human equivalent of a typo.",
            "Your jokes are like dad jokes on steroids — painfully good.",
            "You're about as useful as a chocolate fireguard.",
            "You have all the wit of a damp rag.",
            "You're as bright as a black hole.",
            "You're like a screen door on a submarine — not very effective.",
            "Your brain is like a factory that makes mistakes.",
            "You're as sharp as a marble.",
            "You're like a cloud — when you disappear, it’s a beautiful day.",
            "You bring everyone so much joy… when you leave the room.",
            "You're about as useful as a waterproof towel.",
            "You’re like a slinky — fun to watch but not very practical.",
            "You’re the human equivalent of a participation ribbon.",
            "Your secrets are safe with me. I never listen when you tell me them.",
            "You're like a WiFi signal in a basement — weak and unreliable.",
            "You put the ‘pro’ in procrastinate.",
            "You’re as organized as a tornado in a trailer park.",
            "Your brain’s got more windows than a skyscraper, but none of them open.",
            "You’re like a software update — nobody wants you but eventually, we have to deal with you.",
            "You're the human embodiment of a migraine."
        ]

        self.magic_8ball_answers = [
            "It is certain.", "It is decidedly so.", "Without a doubt.",
            "Yes – definitely.", "You may rely on it.", "As I see it, yes.",
            "Most likely.", "Outlook good.", "Yes.", "Signs point to yes.",
            "Reply hazy, try again.", "Ask again later.", "Better not tell you now.",
            "Cannot predict now.", "Concentrate and ask again.", "Don't count on it.",
            "My reply is no.", "My sources say no.", "Outlook not so good.",
            "Very doubtful."
        ]

    @app_commands.command(name="8ball", description="Ask the Magic 8-ball a question")
    @app_commands.describe(question="Your question")
    async def eight_ball(self, interaction: discord.Interaction, question: str):
        answer = random.choice(self.magic_8ball_answers)
        embed = discord.Embed(title="🎱 Magic 8-Ball", color=discord.Color.blue())
        embed.add_field(name="Question", value=question, inline=False)
        embed.add_field(name="Answer", value=answer, inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="meme", description="Get a random SFW meme from Reddit")
    async def meme(self, interaction: discord.Interaction):
        await interaction.response.defer()
        url = "https://www.reddit.com/r/memes/top/.json?limit=50&t=day"
        headers = {"User-Agent": "DiscordBot"}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status != 200:
                    await interaction.followup.send("Failed to fetch memes.")
                    return
                data = await resp.json()
                posts = data["data"]["children"]
                memes = [post["data"] for post in posts if not post["data"]["over_18"] and post["data"]["post_hint"] == "image"]
                if not memes:
                    await interaction.followup.send("No memes found :(")
                    return
                meme = random.choice(memes)
                embed = discord.Embed(title=meme["title"], url="https://reddit.com"+meme["permalink"], color=discord.Color.random())
                embed.set_image(url=meme["url"])
                embed.set_footer(text=f"👍 {meme['ups']} | 💬 {meme['num_comments']}")
                await interaction.followup.send(embed=embed)

    @app_commands.command(name="coinflip", description="Flip a coin")
    async def coinflip(self, interaction: discord.Interaction):
        result = random.choice(["Heads", "Tails"])
        await interaction.response.send_message(f"🪙 The coin landed on **{result}**!")

    @app_commands.command(name="roll", description="Roll a dice with specified sides")
    @app_commands.describe(sides="Number of sides (default 6)")
    async def roll(self, interaction: discord.Interaction, sides: int = 6):
        if sides < 2:
            await interaction.response.send_message("Dice must have at least 2 sides.")
            return
        result = random.randint(1, sides)
        await interaction.response.send_message(f"🎲 You rolled a **{result}** on a {sides}-sided dice!")

    @app_commands.command(name="rate", description="Rate something out of 10")
    @app_commands.describe(thing="What to rate")
    async def rate(self, interaction: discord.Interaction, thing: str):
        rating = random.randint(0, 10)
        await interaction.response.send_message(f"I rate **{thing}** a **{rating}/10**!")

    @app_commands.command(name="joke", description="Tell a random dad joke")
    async def joke(self, interaction: discord.Interaction):
        joke = random.choice(self.jokes)
        await interaction.response.send_message(f"😂 {joke}")

    @app_commands.command(name="roast", description="Send a friendly roast to a user")
    @app_commands.describe(user="User to roast")
    async def roast(self, interaction: discord.Interaction, user: discord.Member):
        roast_line = random.choice(self.roasts)
        await interaction.response.send_message(f"{user.mention}, {roast_line}")

async def setup(bot: commands.Bot):
    await bot.add_cog(FunCog(bot))
