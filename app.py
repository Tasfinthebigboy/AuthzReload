#  #########################
#  #########################
#  #########################
#  -------------###########
#  -------------###########
#  -------------###########
#  -------------###########
#  #####################---  Made by Tasfinthebigboy (https://github.com/Tasfinthebigboy/AuthzReload/)
#  #####################---  Version number 3.2
#  #####################---  Free to use! This version will be continuously updated.
#  -------------###########
#  -------------###########
#  -------------###########
#  #########################
#  #########################
#  #########################

import discord, sys, os, json, asyncio, aiosqlite, aiohttp;from discord.ext import commands;from api import Token
sys.stdout.reconfigure(encoding='utf-8')
i=discord.Intents.all()
b=commands.Bot(command_prefix="m!", intents=i, help_command=None)
w={}
v='verification_data.json'
def l():
 if os.path.exists(v):
  with open(v, 'r') as f:return json.load(f)
 return {}
def s(d):
 with open(v, 'w') as f:json.dump(d, f, indent=4)
vd=l()
@b.event
async def o():
 print(f"{b.user} has connected to Discord!")
 try:
  await i_d()
  s=await b.tree.sync()
  print(f"Synced {len(s)} commands")
 except Exception as e:print(f"Error during command sync: {e}")
 if not vd:print("Verification data is empty or not loaded.");return
 asyncio.create_task(c())
 asyncio.create_task(u())
 print(f'{b.user} is ready and monitoring verification messages!')
async def c():
 for m,d in vd.items():
  g=b.get_guild(d['guild_id'])
  if g is None:print(f"Guild with ID {d['guild_id']} not found.");continue
  ch=g.get_channel(d['channel_id'])
  if ch is None:print(f"Channel with ID {d['channel_id']} not found in guild {g.name}.");continue
  try:
   m=await ch.fetch_message(int(m))
   for r in m.reactions:
    if str(r.emoji)=='✅':
     async for u in r.users():
      if u==b.user:
       await m.remove_reaction('✅', b.user);break
   await asyncio.sleep(3);await m.add_reaction('✅')
  except discord.NotFound:print(f"Message with ID {m} not found in channel {ch.name}.");continue
async def u():
 while True:
  await b.change_presence(activity=discord.Activity(type=discord.ActivityType.streaming, name=f"with {len(b.guilds)} servers", url="https://twitch.tv/discord"));await asyncio.sleep(10)
  t=sum(g.member_count for g in b.guilds)
  await b.change_presence(activity=discord.Activity(type=discord.ActivityType.streaming, name=f"with {t} members", url="https://twitch.tv/discord"));await asyncio.sleep(10)
  c=sum(len(g.channels) for g in b.guilds)
  await b.change_presence(activity=discord.Activity(type=discord.ActivityType.streaming, name=f"with {c} channels", url="https://twitch.tv/discord"));await asyncio.sleep(10)
@b.event
async def on_raw_reaction_add(p):
 if p.user_id==b.user.id:return
 m=str(p.message_id)
 if m in vd:
  if str(p.emoji.name)=='✅':
   g=b.get_guild(p.guild_id)
   r=g.get_role(vd[m]['role_id'])
   m=g.get_member(p.user_id)
   if r and m and r not in m.roles:
    try:
     await m.add_roles(r, reason="User  verified themselves.")
     try:await m.send(f"You have been verified in **{g.name}**!")
     except discord.Forbidden:pass
    except discord.Forbidden:print(f"Bot lacks permission to add the role {r.name} to {m.name}.");
    try:
        await m.send(f"Failed to verify you due to permission issues. Please contact an administrator.")
    except discord.Forbidden:pass
   elif r in m.roles:
    try:await m.send(f"You are already verified in **{g.name}**.")
    except discord.Forbidden:pass
   ch=b.get_channel(p.channel_id)
   m=await ch.fetch_message(p.message_id)
   try:await m.remove_reaction(p.emoji, m)
   except discord.Forbidden:pass
@b.tree.command(name="verify", description="Sets up a verification system")
@discord.app_commands.default_permissions(administrator=True)
@discord.app_commands.describe(role="Role to assign upon verification")
async def v(i:discord.Interaction, r:discord.Role):
 e=discord.Embed(title="Verification", description="React with ✅ to verify yourself and gain access to the server.", color=0x00ff00)
 await i.response.send_message(embed=e)
 m=await i.original_response()
 await m.add_reaction('✅')
 vd[str(m.id)]={'guild_id':i.guild_id,'channel_id':i.channel_id,'role_id':r.id}
 s(vd)
 await i.followup.send("Verification system set up successfully!", ephemeral=True)
@b.tree.command(name="kick", description="Kicks a user from the server")
@discord.app_commands.default_permissions(kick_members=True)
@discord.app_commands.describe(member="Member to kick", reason="Reason for the kick")
async def k(i:discord.Interaction, m:discord.Member, r:str=None):
 if m==i.user:await i.response.send_message("You can't kick yourself :no_entry:", ephemeral=True);return
 if m.top_role>=i.user.top_role:await i.response.send_message(f"You can't do that to the user :no_entry:", ephemeral=True);return
 await m.kick(reason=r)
 await i.response.send_message(f'User  {m} has been kicked for reason: {r}')
@b.tree.command(name="ban", description="Bans a user from the server")
@discord.app_commands.default_permissions(ban_members=True)
@discord.app_commands.describe(member="Member to ban", reason="Reason for the ban")
async def b(i:discord.Interaction, m:discord.Member, r:str=None):
 try:
  await m.ban(reason=r)
  await i.response.send_message(f'User  {m} has been banned for reason: {r}')
  if m==i.user:await i.response.send_message("You can't ban yourself :no_entry:", ephemeral=True);return
  if m.top_role>=i.user.top_role:await i.response.send_message(f"You can't do that to the user :no_entry:", ephemeral=True);return
  if commands.BotMissingPermissions:await i.response.send_message("Bot Missing Permission. Please contact a Admin :no_entry:", ephemeral=True);return
 except Exception as e:print(e);await i.response.send_message(f"You have caught an ultra rare error while trying to ban the member.")
@b.tree.command(name="unban", description="Unbans a user from the server")
@discord.app_commands.default_permissions(ban_members=True)
@discord.app_commands.describe(user="User  to unban")
async def ub(i:discord.Interaction, u:discord.User):
 async for b in i.guild.bans():
  bu=b.user
  if bu==u:
   await i.guild.unban(bu)
   await i.response.send_message(f'User  {u} has been unbanned.')
   return
 await i.response.send_message(f'User  {u} was not found in the banned list.')
@b.tree.command(name="mute", description="Mutes a user in the server")
@discord.app_commands.default_permissions(manage_roles=True)
@discord.app_commands.describe(member="Member to mute", reason="Reason for the mute")
async def m(i:discord.Interaction, m:discord.Member, r:str=None):
 if m==i.user:await i.response.send_message("You can't mute yourself :no_entry:", ephemeral=True);return
 if m.top_role>=i.user.top_role:await i.response.send_message(f"You can't do that to the user :no_entry:", ephemeral=True);return
 mr=discord.utils.get(i.guild.roles, name='Muted')
 if not mr:mr=await i.guild.create_role(name='Muted')
 for c in i.guild.channels:await c.set_permissions(mr, speak=False, send_messages=False, read_message_history=True, read_messages=True)
 await m.add_roles(mr, reason=r)
 e=discord.Embed(title="User  Muted", description=f"{m} has been muted.", color=0xff0000)
 e.add_field(name="Reason", value=r if r else "No reason provided", inline=False)
 e.set_footer(text=f"Muted by {i.user}", icon_url=i.user.avatar.url)
 await i.response.send_message(embed=e)
@b.tree.command(name="unmute", description="Unmutes a user in the server")
@discord.app_commands.default_permissions(manage_roles=True)
@discord.app_commands.describe(member="Member to unmute")
async def um(i:discord.Interaction, m:discord.Member):
 if m==i.user:await i.response.send_message("You can't unmute yourself :no_entry:", ephemeral=True);return
 mr=discord.utils.get(i.guild.roles, name='Muted')
 if not mr or mr not in m.roles:await i.response.send_message(f"{m} is not muted or the mute role doesn't exist.", ephemeral=True);return
 await m.remove_roles(mr)
 e=discord.Embed(title="User  Unmuted", description=f"{m} has been unmuted.", color=0x00ff00)
 e.set_footer(text=f"Unmuted by {i.user}", icon_url=i.user.avatar.url)
 await i.response.send_message(embed=e)
@b.tree.command(name="warn", description="Warns a user in the server")
@discord.app_commands.default_permissions(manage_messages=True)
@discord.app_commands.describe(member="Member to warn", reason="Reason for the warning")
async def w(i:discord.Interaction, m:discord.Member, r:str=None):
 if m.id not in w:w[m.id]=[]
 w[m.id].append(r)
 await i.response.send_message(f'User   {m} has been warned for: {r}')
@b.tree.command(name="warnings", description="Shows warnings of a user")
@discord.app_commands.default_permissions(manage_messages=True)
@discord.app_commands.describe(member="Member whose warnings to display")
async def wc(i:discord.Interaction, m:discord.Member):
 uw=w.get(m.id, [])
 if uw:await i.response.send_message(f'User   {m} has been warned for: {", ".join(uw)}')
 else:await i.response.send_message(f'User   {m} has no warnings.')
class HS(discord.ui.Select):
 def __init__(self):
  o=[discord.SelectOption(label="Admin Commands", description="Show admin commands"),discord.SelectOption(label="Mod Commands", description="Show mod commands"),discord.SelectOption(label="Member Commands", description="Show member commands")]
  super().__init__(placeholder="Choose command category...", options=o)
 async def callback(self, i:discord.Interaction):
  if self.values[0]=="Admin Commands":
   e=discord.Embed(title="Admin Commands", color=0xff0000)
   ac={"verify":"Sets up a verification system. Usage: /verify @Role","ban":"Bans a user from the server. Usage: /ban @User  [reason]","unban":"Unbans a user from the server. Usage: /unban User#1234","setup_automod":"Sets up automod for your guild. Usage: /setup_automod #alert-channel","setup_welcome":"Sets up the welcome channel. Usage: /setup_welcome #channel","setup_leave":"Sets up the leave channel. Usage: /setup_leave #channel","setup_autorole":"Gives the member a joining role. Usage: /setup_leave @role"}
   for cmd, desc in ac.items():e.add_field(name=cmd, value=desc, inline=False)
  elif self.values[0]=="Mod Commands":
   e=discord.Embed(title="Mod Commands", color=0x00ff00)
   mc={"kick":"Kicks a user from the server. Usage: /kick @User  [reason]","mute":"Mutes a user in the server. Usage: /mute @User  [reason]","unmute":"Unmutes a user in the server. Usage: /unmute @User ","warn":"Warns a user in the server. Usage: /warn @User  [reason]","purge":"Purges a user from the server. Usage: /purge [amount]","warnings":"Shows warnings of a user. Usage: /warnings @User "}
   for cmd, desc in mc.items():e.add_field(name=cmd, value=desc, inline=False)
  elif self.values[0]=="Member Commands":
   e=discord.Embed(title="Member Commands", color=0x0000ff)
   memc={"help":"Shows all commands usage. Usage: /help","customembed":"Make your custom embed. Usage: /customembed <title> <description>","ping":"Shows the bot's response time","avater":"Shows a user's avatar. Usage: /avater [user] [hide-reply]","serverinfo":"Shows the server information. Usage: /serverinfo"}
   for cmd, desc in memc.items():e.add_field(name=cmd, value=desc, inline=False)
  await i.response.edit_message(embed=e)
class HV(discord.ui.View):
 def __init__(self):
  super().__init__();self.add_item(HS())
@b.tree.command(name="help", description="Shows all commands usage")
async def help_command(i:discord.Interaction):
 e=discord.Embed(color=0x00ff00)
 e.set_author(name="Authz Bot Commands", icon_url=b.user.avatar)
 e.add_field(name="**Admin Commands**", value="Select Below")
 e.add_field(name="**Mod Commands**", value="Select Below")
 e.add_field(name="**Member Commands**", value="Select Below")
 e.set_footer(text="Authz | Made by @tasfinthebigboy")
 await i.response.send_message(embed=e, view=HV())
@b.tree.command(name="customembed", description="Create a custom embed")
@discord.app_commands.describe(title="Title of the embed", description="Description of the embed", color="Color of the embed (in hex, e.g., #e33235)", url="URL to hyperlink the title", thumbnail_url="URL of the thumbnail image", image_url="URL of the main image", footer_text="Text for the footer", footer_icon_url="URL of the footer icon", author_name="Name of the author", author_url="URL of the author", author_icon_url="URL of the author icon")
async def ce(i:discord.Interaction, t:str, d:str, c:str=None, u:str=None, th:str=None, im:str=None, ft:str=None, fi:str=None, an:str=None, au:str=None, ai:str=None):
 e=discord.Embed(title=t, description=d)
 if c:e.color=discord.Color(int(c.strip("#"), 16))
 if u:e.url=u
 if th:e.set_thumbnail(url=th)
 if im:e.set_image(url=im)
 if ft or fi:e.set_footer(text=ft, icon_url=fi)
 if an or ai or au:e.set_author(name=an, url=au, icon_url=ai)
 await i.response.send_message(embed=e)
@b.tree.command(name="purge", description="Deletes a specified number of messages from the channel")
@discord.app_commands.default_permissions(manage_messages=True)
@discord.app_commands.describe(amount="Number of messages to delete")
async def p(i:discord.Interaction, a:int):
 await i.response.defer(ephemeral=True)
 if a<=0:await i.followup.send("Please specify a positive number of messages to delete.", ephemeral=True);return
 d=await i.channel.purge(limit=a)
 await i.followup.send(f"Deleted {len(d)} messages.", ephemeral=True)
@b.tree.command(name="ping", description="Shows the bot ping/response time")
async def ping(i:discord.Interaction):
 e=discord.Embed(title="Authz Bot Ping", description=f"**Ping**: {round(b.latency * 1000)}ms", color=0x19a61b)
 e.set_footer(text=f"Requested by • {i.user.name}.")
 await i.response.send_message(embed=e)
async def gw(gid):
 async with aiosqlite.connect("join.db") as db:
  async with db.execute("SELECT welcome_channel_id FROM guild_settings WHERE guild_id = ?", (gid,)) as cursor:
   row=await cursor.fetchone()
   return row[0] if row else None
async def sw(gid, cid):
 async with aiosqlite.connect("join.db") as db:
  await db.execute("INSERT OR REPLACE INTO guild_settings (guild_id, welcome_channel_id) VALUES (?, ?)", (gid, cid))
  await db.commit()
async def gl(gid):
 async with aiosqlite.connect("leave.db") as db:
  async with db.execute("SELECT leave_channel_id FROM guild_settings WHERE guild_id = ?", (gid,)) as cursor:
   row=await cursor.fetchone()
   return row[0] if row else None
async def sl(gid, cid):
 async with aiosqlite.connect("leave.db") as db:
  await db.execute("INSERT OR REPLACE INTO guild_settings (guild_id, leave_channel_id) VALUES (?, ?)", (gid, cid))
  await db.commit()
async def gar(gid):
 async with aiosqlite.connect("autorole.db") as db:
  async with db.execute("SELECT role_id FROM guild_settings WHERE guild_id = ?", (gid,)) as cursor:
   row=await cursor.fetchone()
   return row[0] if row else None
async def sar(gid, rid):
 async with aiosqlite.connect("autorole.db") as db:
  await db.execute("INSERT OR REPLACE INTO guild_settings (guild_id, role_id) VALUES (?, ?)", (gid, rid))
  await db.commit()
@b.tree.command(name="setup_welcome", description="Sets up the welcome channel.")
@discord.app_commands.describe(channel="The channel where welcome messages will be sent.")
@discord.app_commands.default_permissions(administrator=True)
async def swc(i:discord.Interaction, c:discord.TextChannel):
 await i.response.defer()
 await sw(i.guild.id, c.id)
 await i.followup.send(embed=discord.Embed(title="Welcome Channel Set", description=f"The welcome channel has been set to {c.mention}.", color=discord.Color.green()))
@b.tree.command(name="setup_leave", description="Sets up the leave channel.")
@discord.app_commands.describe(channel="The channel where leave messages will be sent.")
@discord.app_commands.default_permissions(administrator=True)
async def slc(i:discord.Interaction, c:discord.TextChannel):
 await i.response.defer()
 await sl(i.guild.id, c.id)
 await i.followup.send(embed=discord.Embed(title="Leave Channel Set", description=f"The leave channel has been set to {c.mention}.", color=discord.Color.red()))
@b.tree.command(name="setup_autorole", description="Sets up the auto-role for new members.")
@discord.app_commands.describe(role="The role to assign to new members .")
@discord.app_commands.default_permissions(administrator=True)
async def sarc(i:discord.Interaction, r:discord.Role):
 await i.response.defer()
 await sar(i.guild.id, r.id)
 await i.followup.send(embed=discord.Embed(title="Auto-Role Set", description=f"The auto-role has been set to {r.mention}.", color=discord.Color.green()))
from PIL import Image, ImageDraw, ImageFont;from io import BytesIO;import requests
@b.event
async def on_member_join(m):
 try:
  gid=m.guild.id
  bg_url="https://cdn.pixabay.com/photo/2018/01/14/23/12/nature-3082832_1280.jpg"
  async with aiohttp.ClientSession() as s:
   async with s.get(bg_url) as bg_resp:
    bg=Image.open(BytesIO(await bg_resp.read())).convert("RGBA").resize((800, 450))
   av_url=m.avatar.url if m.avatar else m.default_avatar.url
   async with s.get(av_url) as av_resp:
    av=Image.open(BytesIO(await av_resp.read()))
  if getattr(av, "is_animated", False):av=av.copy().convert("RGBA").resize((150, 150))
  else:av=av.convert("RGBA").resize((150, 150))
  canvas=Image.new("RGBA", bg.size, "#2C2F33")
  canvas.paste(bg, (0, 0))
  draw=ImageDraw.Draw(canvas)
  avatar_pos=((canvas.width-150)//2, 100)
  canvas.paste(av, avatar_pos, av)
  font_path="DejaVuSans-Bold.ttf"
  font=ImageFont.truetype(font_path, 32)
  username=m.name
  text_bbox=draw.textbbox((0, 0), username, font=font)
  text_width=text_bbox[2]-text_bbox[0]
  text_height=text_bbox[3]-text_bbox[1]
  text_pos=((canvas.width-text_width)//2, avatar_pos[1]+170)
  draw.text(text_pos, username, font=font, fill="white")
  output_buffer=BytesIO()
  canvas.save(output_buffer, format="PNG")
  output_buffer.seek(0)
  welcome_channel_id=await gw(gid)
  if welcome_channel_id:
   try:
    ch=await b.fetch_channel(welcome_channel_id)
    if ch:
     file=discord.File(fp=output_buffer, filename="welcome.png")
     await ch.send(content=f"Hello {m.mention}, welcome to {m.guild.name}!", file=file)
   except discord.NotFound:print(f"Channel with ID {welcome_channel_id} not found.")
   except discord.Forbidden:print(f"Bot does not have permission to send messages in channel ID {welcome_channel_id}.")
  auto_role_id=await gar(gid)
  if auto_role_id:
   role=m.guild.get_role(auto_role_id)
   if role:await m.add_roles(role)
 except Exception as e:print(f"Error occurred while handling member join event: {e}")
@b.event
async def on_member_remove(m):
 gid=m.guild.id
 leave_channel_id=await gl(gid)
 if leave_channel_id:
  ch=b.get_channel(leave_channel_id)
  if ch:await ch.send(content=f"{m.name} has left the server.")
@swc.error
@slc.error
async def setup_error(i:discord.Interaction, e):
 if isinstance(e, discord.app_commands.MissingPermissions):await i.response.send_message("You don't have permission to use this command.")
 elif isinstance(e, discord.app_commands.BadArgument):await i.response.send_message("Please mention a valid text channel.")
async def i_d():
 async with aiosqlite.connect("join.db") as db:
  await db.execute("CREATE TABLE IF NOT EXISTS guild_settings (guild_id INTEGER PRIMARY KEY, welcome_channel_id INTEGER)")
  await db.commit()
 async with aiosqlite.connect("leave.db") as db:
  await db.execute("CREATE TABLE IF NOT EXISTS guild_settings (guild_id INTEGER PRIMARY KEY, leave_channel_id INTEGER)")
  await db.commit()
 async with aiosqlite.connect("autorole.db") as db:
  await db.execute("CREATE TABLE IF NOT EXISTS guild_settings (guild_id INTEGER PRIMARY KEY, role_id INTEGER)")
  await db.commit()
async def load_cogs():
 cogs=["cogs.counting", "cogs.avater", "cogs.automod", "cogs.serverinfo", "cogs.reactrole", "cogs.credits"]
 for cog in cogs:
  try:
   await b.load_extension(cog)
   print(f"Loaded {cog}")
  except Exception as e:print(f"Failed to load { cog}: {e}")
async def main(): 
 await load_cogs()
 await b.start(Token)
if __name__ == "__main__":
 try:
  asyncio.run(main())
  i_d()
 except Exception as e:print(f"Error running the bot: {e}")
