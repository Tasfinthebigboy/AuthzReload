import discord
from discord.ext import commands
from discord import app_commands
import json, aiosqlite, re, aiohttp, asyncio, os, random, time

PLUGINS_FOLDER = "plugins"

class Plugins(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        os.makedirs(PLUGINS_FOLDER, exist_ok=True)
        self.db = await aiosqlite.connect("plugins.db")
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS plugins (
                guild_id INTEGER,
                name TEXT,
                path TEXT,
                data TEXT,
                PRIMARY KEY(guild_id, name)
            )
        """)
        await self.db.commit()
        async with self.db.execute("SELECT guild_id, data FROM plugins") as cursor:
            async for guild_id, data in cursor:
                plugin = json.loads(data)
                self._register_command(plugin, guild_id)

    async def _save_plugin(self, guild_id: int, name: str, data: dict):
        guild_folder = os.path.join(PLUGINS_FOLDER, str(guild_id))
        os.makedirs(guild_folder, exist_ok=True)
        path = os.path.join(guild_folder, f"{name}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        await self.db.execute(
            "REPLACE INTO plugins VALUES (?, ?, ?, ?)",
            (guild_id, name, path, json.dumps(data))
        )
        await self.db.commit()

    async def _delete_plugin(self, guild_id: int, name: str):
        async with self.db.execute(
            "SELECT path FROM plugins WHERE guild_id=? AND name=?",
            (guild_id, name)
        ) as cursor:
            row = await cursor.fetchone()
            if row and os.path.exists(row[0]):
                os.remove(row[0])
        await self.db.execute(
            "DELETE FROM plugins WHERE guild_id=? AND name=?",
            (guild_id, name)
        )
        await self.db.commit()

    async def _get_plugins(self, guild_id: int):
        async with self.db.execute(
            "SELECT name, data FROM plugins WHERE guild_id=?",
            (guild_id,)
        ) as cursor:
            rows = await cursor.fetchall()
        result = {}
        for name, data in rows:
            result[name] = json.loads(data)
        return result

    # ------------------------ PLACEHOLDERS ------------------------
    def _apply_placeholders(self, text, ctx, target_user=None, reason=None, duration=None):
        if not text: return ""
        replacements = {
            "{user.mention}": ctx.user.mention if isinstance(ctx, discord.Interaction) else ctx.author.mention,
            "{user.name}": ctx.user.name if isinstance(ctx, discord.Interaction) else ctx.author.name,
            "{user.id}": str(ctx.user.id if isinstance(ctx, discord.Interaction) else ctx.author.id),
            "{target_user.mention}": target_user.mention if target_user else "",
            "{target_user.name}": target_user.name if target_user else "",
            "{target_user.id}": str(target_user.id) if target_user else "",
            "{guild.name}": ctx.guild.name if ctx.guild else "DMs",
            "{guild.id}": str(ctx.guild.id if ctx.guild else 0),
            "{guild.member_count}": str(ctx.guild.member_count if ctx.guild else 0),
            "{channel.name}": getattr(ctx.channel, "name", "DM"),
            "{channel.id}": str(getattr(ctx.channel, "id", 0)),
            "{reason}": reason or "No reason provided",
            "{duration}": duration or "perma",
            "{time}": discord.utils.format_dt(discord.utils.utcnow())
        }

        # New random placeholders
        replacements["{random_number}"] = str(random.randint(0, 100))
        if "{random_choice:" in text:
            pattern = r"\{random_choice:([^\}]+)\}"
            matches = re.findall(pattern, text)
            for match in matches:
                options = match.split(",")
                text = text.replace(f"{{random_choice:{match}}}", random.choice(options))

        for k,v in replacements.items(): text = text.replace(k,v)
        return text

    # ------------------------ DURATION PARSER ------------------------
    def _parse_duration(self, duration: str):
        units = {"s":1, "m":60, "h":3600, "d":86400, "w":604800}
        try: return int(duration[:-1]) * units[duration[-1]]
        except: return 0

    async def _temporary_unban(self, guild, user, seconds):
        await asyncio.sleep(seconds)
        try: await guild.unban(user)
        except: pass

    async def _temporary_unmute(self, guild, user, seconds, mute_role_id):
        await asyncio.sleep(seconds)
        role = guild.get_role(mute_role_id)
        if role:
            try: await user.remove_roles(role)
            except: pass

    # ------------------------ EMBED MAKER ------------------------
    def _make_embed(self, embed_data, ctx):
        if not embed_data: return None
        color = embed_data.get("color", 0x3498db)
        if isinstance(color,str): color=int(color.replace("#","0x"),16)
        embed = discord.Embed(
            title=self._apply_placeholders(embed_data.get("title",""), ctx),
            description=self._apply_placeholders(embed_data.get("description",""), ctx),
            color=color
        )
        for f in embed_data.get("fields", []):
            embed.add_field(
                name=self._apply_placeholders(f.get("name",""),ctx),
                value=self._apply_placeholders(f.get("value",""),ctx),
                inline=f.get("inline", False)
            )
        if "footer" in embed_data: embed.set_footer(text=self._apply_placeholders(embed_data["footer"],ctx))
        if "thumbnail" in embed_data: embed.set_thumbnail(url=self._apply_placeholders(embed_data["thumbnail"],ctx))
        if "image" in embed_data: embed.set_image(url=self._apply_placeholders(embed_data["image"],ctx))
        return embed

    # ------------------------ PLUGIN EXECUTION ------------------------
    async def _execute_plugin(self, ctx, plugin, target_user=None, reason=None, duration=None):
        resp = plugin.get("response", {})

        # Random/Sequential support
        if "content" in resp and isinstance(resp["content"], list):
            resp["content"] = random.choice(resp["content"])

        # API endpoint support
        if plugin.get("api_endpoint"):
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(plugin["api_endpoint"]) as r:
                        data = await r.json()
                        resp["content"] = resp.get("content","").replace("{api_response}",str(data))
                except: resp["content"] = "⚠️ API request failed."

        content = self._apply_placeholders(resp.get("content",""),ctx,target_user,reason,duration)
        embed = self._make_embed(resp.get("embed",{}), ctx)
        ephemeral = resp.get("ephemeral",False)

        # Cooldown support
        cooldown = plugin.get("cooldown",0)
        last_used = getattr(self,"_plugin_last_used",{})
        key = (ctx.guild.id if ctx.guild else 0, plugin.get("command_name"))
        now = time.time()
        if cooldown>0 and key in last_used and now-last_used[key]<cooldown:
            if isinstance(ctx, discord.Interaction):
                return await ctx.response.send_message("⏱️ This command is on cooldown.", ephemeral=True)
            else:
                return await ctx.channel.send("⏱️ This command is on cooldown.")
        last_used[key]=now
        self._plugin_last_used = last_used

        # Send main message
        if isinstance(ctx, discord.Interaction):
            if resp.get("type")=="defer":
                await ctx.response.defer(ephemeral=ephemeral)
                if content or embed: await ctx.followup.send(content=content or None, embed=embed, ephemeral=ephemeral)
            else:
                await ctx.response.send_message(content=content or None, embed=embed, ephemeral=ephemeral)
        else:
            await ctx.channel.send(content=content or None, embed=embed)

        # Followup messages (random selection supported)
        for follow in resp.get("sendafter",[]):
            f_content = follow.get("content","")
            if isinstance(f_content,list): f_content=random.choice(f_content)
            f_content = self._apply_placeholders(f_content, ctx, target_user, reason, duration)
            if isinstance(ctx,discord.Interaction): await ctx.followup.send(f_content,ephemeral=ephemeral)
            else: await ctx.channel.send(f_content)

        # Actions (moderation / points / polls / games)
        rules = plugin.get("action_rules",{})
        action = rules.get("action")
        action_duration = duration or rules.get("duration","perma")

        if target_user:
            try:
                if action=="ban":
                    await ctx.guild.ban(target_user,reason=reason)
                    if action_duration!="perma":
                        self.bot.loop.create_task(self._temporary_unban(ctx.guild,target_user,self._parse_duration(action_duration)))
                elif action=="unban":
                    await ctx.guild.unban(target_user)
                elif action=="kick":
                    await ctx.guild.kick(target_user,reason=reason)
                elif action=="mute":
                    role_id = rules.get("role_id")
                    role = ctx.guild.get_role(role_id)
                    if role:
                        await target_user.add_roles(role,reason=reason)
                        if action_duration!="perma":
                            self.bot.loop.create_task(self._temporary_unmute(ctx.guild,target_user,self._parse_duration(action_duration),role_id))
                elif action=="unmute":
                    role_id = rules.get("role_id")
                    role = ctx.guild.get_role(role_id)
                    if role:
                        await target_user.remove_roles(role,reason=reason)
                elif action=="give_points" and rules.get("points"):
                    key = f"points_{target_user.id}"
                    if not hasattr(self,"_plugin_points"): self._plugin_points={}
                    self._plugin_points[key] = self._plugin_points.get(key,0)+rules["points"]
                elif action=="poll" and rules.get("options") and ctx.channel:
                    msg = await ctx.channel.send(f"📊 {rules.get('question','Vote!')}")
                    for emoji in rules["options"]:
                        await msg.add_reaction(emoji)
            except Exception as e:
                print(f"[Plugin Error] {e}")

    # ------------------------ COMMAND REGISTRATION ------------------------
    def _register_command(self, plugin, guild_id: int):
        rules = plugin.get("action_rules", {})
        action = rules.get("action")
        needs_target = action in ["ban", "kick", "mute", "unmute", "unban"]

        if needs_target:
            async def plugin_command(
                inter: discord.Interaction,
                target_user: discord.Member,
                reason: str | None = None,
                duration: str = "perma"
            ):
                await self._execute_plugin(inter, plugin, target_user, reason, duration)
        else:
            async def plugin_command(inter: discord.Interaction):
                await self._execute_plugin(inter, plugin)

        cmd = app_commands.Command(
            name=plugin["command_name"],
            description=plugin["description"],
            callback=plugin_command
        )

        try:
            old_cmd = self.bot.tree.get_command(plugin["command_name"], guild=discord.Object(id=guild_id))
            if old_cmd:
                self.bot.tree.remove_command(plugin["command_name"], guild=discord.Object(id=guild_id))
        except:
            pass

        self.bot.tree.add_command(cmd, guild=discord.Object(id=guild_id))


    # ------------------------ UPLOAD / LIST / REMOVE ------------------------
    @app_commands.command(name="uploadplugin", description="Upload a JSON plugin file")
    @app_commands.describe(force="Overwrite existing plugin if it exists")
    async def uploadplugin(self, interaction: discord.Interaction, name: str, file: discord.Attachment, force: bool = False):
        await interaction.response.defer()
        if not file.filename.endswith(".json"):
            return await interaction.followup.send("❌ Must be a .json file", ephemeral=True)
        try:
            data = json.loads(await file.read())
        except Exception as e:
            return await interaction.followup.send(f"❌ Invalid JSON: {e}", ephemeral=True)

        plugins = await self._get_plugins(interaction.guild_id)
        if name in plugins and not force:
            return await interaction.followup.send(
                f"❌ Plugin `{name}` already exists. Use `force=True` to overwrite.", ephemeral=True
            )
        for p_name, p_data in plugins.items():
            if p_data.get("command_name") == data.get("command_name") and (p_name != name or not force):
                return await interaction.followup.send(
                    f"❌ Command name `{data['command_name']}` is already used by plugin `{p_name}`.", ephemeral=True
                )

        await self._save_plugin(interaction.guild_id, name, data)
        self._register_command(data, interaction.guild_id)
        await self.bot.tree.sync(guild=discord.Object(id=interaction.guild_id))
        await interaction.followup.send(f"✅ Plugin `{name}` uploaded successfully.", ephemeral=True)

    @app_commands.command(name="pluginlist", description="List all plugins in this guild")
    async def pluginlist(self, interaction: discord.Interaction):
        plugins = await self._get_plugins(interaction.guild_id)
        if not plugins: return await interaction.response.send_message("No plugins installed.", ephemeral=True)
        await interaction.response.send_message("📂 Installed plugins:\n" + "\n".join(f"- {n}" for n in plugins.keys()))

    @app_commands.command(name="removeplugin", description="Remove a plugin by name")
    async def removeplugin(self, interaction: discord.Interaction, name:str):
        plugins = await self._get_plugins(interaction.guild_id)
        if name not in plugins: return await interaction.response.send_message("❌ Plugin not found.", ephemeral=True)
        await self._delete_plugin(interaction.guild_id,name)
        try:
            cmd = self.bot.tree.get_command(plugins[name]["command_name"], guild=discord.Object(id=interaction.guild_id))
            if cmd:
                self.bot.tree.remove_command(cmd.name, guild=discord.Object(id=interaction.guild_id))
            await self.bot.tree.sync(guild=discord.Object(id=interaction.guild_id))
        except: pass
        await interaction.response.send_message(f"🗑️ Plugin `{name}` removed.")

    # ------------------------ EVENTS ------------------------
    @commands.Cog.listener()
    async def on_ready(self):
        if not hasattr(self.bot, "_plugins_synced"):
            await self.bot.tree.sync()
            self.bot._plugins_synced = True
            print("✅ Plugins commands synced!")
    
    @commands.Cog.listener()
    async def on_message(self,message:discord.Message):
        if message.author.bot or not message.guild: return
        plugins = await self._get_plugins(message.guild.id)
        for plugin in plugins.values():
            rules = plugin.get("action_rules")
            if not rules: continue
            trigger=rules.get("trigger")
            pattern=rules.get("pattern","")
            action=rules.get("action")
            warn_message=rules.get("warn_message")
            duration=rules.get("duration")

            conditions = plugin.get("conditions",{})
            if conditions:
                if any(role.id in conditions.get("excluded_roles",[]) for role in message.author.roles): continue
                if conditions.get("required_roles") and not any(role.id in conditions.get("required_roles") for role in message.author.roles): continue
                if conditions.get("channels") and message.channel.id not in conditions.get("channels"): continue
                if conditions.get("guilds") and message.guild.id not in conditions.get("guilds"): continue

            triggered=False
            if trigger=="message_contains" and pattern in message.content: triggered=True
            elif trigger=="regex" and pattern and re.search(pattern,message.content): triggered=True
            elif trigger=="caps" and len(message.content)>5 and sum(1 for c in message.content if c.isupper())/len(message.content)>0.7: triggered=True
            elif trigger=="mention_limit" and len(message.mentions)>int(pattern): triggered=True

            if triggered:
                if action=="delete":
                    try: await message.delete()
                    except: pass
                elif action=="warn" and warn_message:
                    await message.channel.send(self._apply_placeholders(warn_message,message))
                elif action=="assign_role" and rules.get("role_id"):
                    role = message.guild.get_role(rules["role_id"])
                    if role:
                        try: await message.author.add_roles(role)
                        except: pass

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        plugins = await self._get_plugins(member.guild.id)
        for plugin in plugins.values():
            rules = plugin.get("action_rules", {})
            trigger = rules.get("trigger")
            if trigger != "member_join":
                continue

            channel_id = rules.get("channel_id")
            channel = member.guild.get_channel(channel_id) if channel_id else None
            content = plugin["response"].get("content", "")
            embed_data = plugin["response"].get("embed")

            msg_content = self._apply_placeholders(content, member)

            if channel:
                embed = self._make_embed(embed_data, member)
                await channel.send(content=msg_content, embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        plugins = await self._get_plugins(member.guild.id)
        for plugin in plugins.values():
            rules = plugin.get("action_rules", {})
            trigger = rules.get("trigger")
            if trigger != "member_leave":
                continue

            channel_id = rules.get("channel_id")
            channel = member.guild.get_channel(channel_id) if channel_id else None
            content = plugin["response"].get("content", "")
            embed_data = plugin["response"].get("embed")

            msg_content = self._apply_placeholders(content, member)

            if channel:
                embed = self._make_embed(embed_data, member)
                await channel.send(content=msg_content, embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Plugins(bot))
