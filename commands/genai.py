import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import aiosqlite
import os
from google import genai
from google.genai import types
from io import BytesIO
from api import GenAI_ChatBot_Token
import pathlib
import httpx
import PyPDF2
import time
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler("bot_messages.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

TEACHING_FILE = "teaching.txt"

MEMORY_DIR = "memory"
ALLOWED_CHANNELS_DB = "allowed_channels.db"
INLINE_SIZE_LIMIT = 20 * 1024 * 1024  # 20 MB

CACHE_DIR = "temp_uploads"
CACHE_DB = "attachment_cache.db"
CACHE_EXPIRY = 24 * 3600  # 1 day

os.makedirs(CACHE_DIR, exist_ok=True)

class AI(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.gemini_client = genai.Client(api_key=GenAI_ChatBot_Token)
        os.makedirs(MEMORY_DIR, exist_ok=True)

    async def cog_load(self):
        async with aiosqlite.connect(ALLOWED_CHANNELS_DB) as db:
            await db.execute(
                "CREATE TABLE IF NOT EXISTS allowed_channels (channel_id INTEGER PRIMARY KEY)"
            )
            await db.commit()

        await self.init_cache_db()    

    async def init_cache_db(self):
        async with aiosqlite.connect(CACHE_DB) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    message_id INTEGER PRIMARY KEY,
                    file_path TEXT,
                    timestamp REAL
                )
            """)
            await db.commit()

    def load_teaching(self) -> str:
            """Load teaching.txt content once per prompt."""
            if os.path.exists(TEACHING_FILE):
                try:
                    with open(TEACHING_FILE, "r", encoding="utf-8") as f:
                        return f.read().strip()
                except Exception as e:
                    logging.error(f"Error reading {TEACHING_FILE}: {e}")
            return "You're a helpful AI, your work is to help people." 

    def is_memory_full(self, user_id: int, limit_kb: int = 10) -> bool:
        """Check if a user's memory exceeds the given size in KB."""
        path = os.path.join(MEMORY_DIR, f"{user_id}.txt")
        if os.path.exists(path):
            size_kb = os.path.getsize(path) / 30720  #30 KB
            return size_kb > limit_kb
        return False


    async def cache_cleanup_task(self):
        """Periodically delete expired cached files."""
        while True:
            try:
                now = time.time()
                async with aiosqlite.connect(CACHE_DB) as db:
                    async with db.execute("SELECT message_id, file_path, timestamp FROM cache") as cursor:
                        rows = await cursor.fetchall()
                        for message_id, file_path, ts in rows:
                            if now - ts > CACHE_EXPIRY:
                                if os.path.exists(file_path):
                                    os.remove(file_path)
                                await db.execute("DELETE FROM cache WHERE message_id=?", (message_id,))
                    await db.commit()
            except Exception as e:
                logging.error(f"Cache cleanup error: {e}")

            await asyncio.sleep(3600)    

    def load_user_memory(self, user_id: int) -> str:
        path = os.path.join(MEMORY_DIR, f"{user_id}.txt")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        return ""

    def save_user_memory(self, user_id: int, user_msg: str, ai_msg: str):
        path = os.path.join(MEMORY_DIR, f"{user_id}.txt")
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"User: {user_msg}\nAI: {ai_msg}\n")

    async def is_allowed_channel(self, channel_id: int) -> bool:
        async with aiosqlite.connect(ALLOWED_CHANNELS_DB) as db:
            async with db.execute("SELECT channel_id FROM allowed_channels") as cursor:
                channels = await cursor.fetchall()
                return (channel_id,) in channels

    async def get_ai_response(self, prompt: str, user_id: int, attachments=None) -> str:
        """Get AI response from Gemini, including code execution results if available."""
        try:
            teaching_content = self.load_teaching()
            history = self.load_user_memory(user_id)
            full_prompt = f"Guidelines / Teaching:\n{teaching_content}\n"
            if history:
                full_prompt += f"Conversation so far:\n{history}\n"
            full_prompt += f"User: {prompt}\nAI:"

            attachments = attachments or []

            contents = []
            contents.extend(attachments)
            contents.append(full_prompt)

            grounding_tool = types.Tool(google_search=types.GoogleSearch())
            code_tool = types.Tool(code_execution=types.ToolCodeExecution())
            config = types.GenerateContentConfig(
                tools=[grounding_tool, code_tool],
                thinking_config=types.ThinkingConfig(thinking_budget=1024)
            )

            for attempt in range(3):
                try:
                    response = await asyncio.to_thread(
                        self.gemini_client.models.generate_content,
                        model="gemini-2.5-flash",
                        contents=contents,
                        config=config
                    )
                    break
                except Exception as e:
                    if attempt < 2:
                        await asyncio.sleep(2)
                    else:
                        raise

            ai_text_parts = []
            if hasattr(response, "candidates"):
                for part in response.candidates[0].content.parts:
                    if getattr(part, "text", None):
                        ai_text_parts.append(part.text)
                    if getattr(part, "executable_code", None):
                        code_block = f"```py\n{part.executable_code.code}\n```"
                        ai_text_parts.append(code_block)
                    if getattr(part, "code_execution_result", None):
                        result_block = f"```py\n# Execution result:\n{part.code_execution_result.output}\n```"
                        ai_text_parts.append(result_block)

            ai_text = "\n".join(ai_text_parts).strip() or str(response)

            self.save_user_memory(user_id, prompt, ai_text)
            return ai_text

        except Exception as e:
            return f"❌ Error: {e}"

    async def send_long_response(self, send_func, content: str, block_size: int = 1900):
        lines = content.strip().splitlines()
        blocks = []
        current = ""
        for line in lines:
            if len(current) + len(line) + 1 < block_size:
                current += line + "\n"
            else:
                blocks.append(current)
                current = line + "\n"
        if current:
            blocks.append(current)

        for idx, block in enumerate(blocks, 1):
            footer = f"\n\n-# **Block {idx} of {len(blocks)}**"
            await send_func(block.strip() + footer)
            await asyncio.sleep(1)

    ai_group = app_commands.Group(name="ai", description="AI commands")

    async def prepare_file_for_gemini(self, file_or_url):
        if isinstance(file_or_url, str):
            if file_or_url.startswith(("http://", "https://")):
                async with httpx.AsyncClient() as session:
                    resp = await session.get(file_or_url)
                    resp.raise_for_status()
                    file_bytes = resp.content
                filename = file_or_url.split("/")[-1].split("?")[0]
            else:
                with open(file_or_url, "rb") as f:
                    file_bytes = f.read()
                filename = os.path.basename(file_or_url)
        else:
            file_bytes = await file_or_url.read()
            filename = file_or_url.filename
    
        size = len(file_bytes)
        fname_lower = filename.lower()
    
        if fname_lower.endswith((".png", ".jpg", ".jpeg", ".webp", ".heic", ".heif")):
            ext = fname_lower.split(".")[-1]
            mime_type = f"image/{ext if ext != 'jpg' else 'jpeg'}"
            if size < INLINE_SIZE_LIMIT:
                return types.Part.from_bytes(data=file_bytes, mime_type=mime_type)
            else:
                return self.gemini_client.files.upload(
                    file=BytesIO(file_bytes),
                    config=dict(mime_type=mime_type)
                )
    
        elif fname_lower.endswith(".pdf"):
            if size < INLINE_SIZE_LIMIT:
                return types.Part.from_bytes(data=file_bytes, mime_type="application/pdf")
            else:
                return self.gemini_client.files.upload(
                    file=BytesIO(file_bytes),
                    config=dict(mime_type="application/pdf")
                )
            
        else:
            try:
                text_content = file_bytes.decode("utf-8", errors="ignore")
                if text_content.strip():
                    return text_content
            except Exception:
                pass
            
        return None

    @ai_group.command(name="ask", description="Ask something to the AI")
    async def ask(self, interaction: discord.Interaction, question: str):
        if await self.is_allowed_channel(interaction.channel_id):
            await interaction.response.defer()
            response = await self.get_ai_response(question, interaction.user.id)
            await self.send_long_response(interaction.followup.send, response)
        else:
            await interaction.response.send_message(
                "❌ This channel is not allowed.", ephemeral=True
            )

    @ai_group.command(name="allowchannel", description="Allow this channel to use AI")
    @app_commands.default_permissions(manage_guild=True)
    async def allowchannel(self, interaction: discord.Interaction):
        async with aiosqlite.connect(ALLOWED_CHANNELS_DB) as db:
            await db.execute(
                "INSERT OR IGNORE INTO allowed_channels VALUES (?)", (interaction.channel_id,)
            )
            await db.commit()
        await interaction.response.send_message("✅ This channel can now use AI.")

    @ai_group.command(name="removechannel", description="Disallow this channel from AI")
    @app_commands.default_permissions(manage_guild=True)
    async def removechannel(self, interaction: discord.Interaction):
        async with aiosqlite.connect(ALLOWED_CHANNELS_DB) as db:
            await db.execute(
                "DELETE FROM allowed_channels WHERE channel_id=?", (interaction.channel_id,)
            )
            await db.commit()
        await interaction.response.send_message("❌ This channel is no longer allowed.")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if not await self.is_allowed_channel(message.channel.id):
            return

        attachments = []
        extra_text = []

        if message.content.lower() == "clear memory":
            mem_path = os.path.join(MEMORY_DIR, f"{message.author.id}.txt")
            if os.path.exists(mem_path):
                os.remove(mem_path)
            await message.channel.send("🧹 Your memory has been cleared.")
            content = "Hi"
        else:
            content = message.content.strip()

        # --- Context prioritization ---
        prompt_history = ""

        is_reply_to_bot = (
            message.reference
            and message.reference.resolved
            and message.reference.resolved.author == self.bot.user
        )

        is_mention_to_bot = self.bot.user in message.mentions

        if not (is_reply_to_bot or is_mention_to_bot):
            return

        if is_reply_to_bot:
            replied_msg = message.reference.resolved
            if replied_msg and replied_msg.content:
                prompt_history += f"Previous bot message:\n{replied_msg.content}\n"

            async with aiosqlite.connect(CACHE_DB) as db:
                async with db.execute(
                    "SELECT file_path, timestamp FROM cache WHERE message_id=?", (replied_msg.id,)
                ) as cursor:
                    rows = await cursor.fetchall()
                    for file_path, ts in rows:
                        if time.time() - ts < CACHE_EXPIRY and os.path.exists(file_path):
                            result = await self.prepare_file_for_gemini(file_path)
                            if isinstance(result, types.Part):
                                attachments.append(result)

        if self.is_memory_full(message.author.id):
            await message.channel.send("⚠️ Your memory is full! Please clear it using 'clear memory'.")
            user_memory = "" 
        else:
            user_memory = self.load_user_memory(message.author.id)
            if user_memory:
                prompt_history += f"User memory:\n{user_memory}\n"

        for attach in message.attachments:
            file_ext = pathlib.Path(attach.filename).suffix
            temp_file_path = os.path.join(CACHE_DIR, f"{attach.id}{file_ext}")
            await attach.save(temp_file_path)

            async with aiosqlite.connect(CACHE_DB) as db:
                await db.execute(
                    "INSERT OR REPLACE INTO cache (message_id, file_path, timestamp) VALUES (?, ?, ?)",
                    (message.id, temp_file_path, time.time())
                )
                await db.commit()

            result = await self.prepare_file_for_gemini(temp_file_path)
            if isinstance(result, types.Part):
                attachments.append(result)
            elif isinstance(result, str):
                extra_text.append(result)

        if extra_text:
            content += "\n" + "\n".join(extra_text)

        if content or attachments:
            async with message.channel.typing():
                final_prompt = content + "\n" + prompt_history
                response = await self.get_ai_response(
                    final_prompt,
                    message.author.id,
                    attachments=attachments
                )
                await self.send_long_response(message.channel.send, response)

async def setup(bot: commands.Bot):
    await bot.add_cog(AI(bot))
