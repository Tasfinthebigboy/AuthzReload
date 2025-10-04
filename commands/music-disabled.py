import asyncio
import functools
import itertools
import math
import random
import os
import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
from async_timeout import timeout


class VoiceError(Exception):
    pass


class YTDLError(Exception):
    pass


class YTDLSource(discord.PCMVolumeTransformer):
    YTDL_OPTIONS = {
        # General
        'format': 'bestaudio/best',
        'quiet': True,
        'noplaylist': True,
        'extract_flat': False,
        'force_generic_extractor': False,
    
        # Authentication
        'cookiefile': os.path.join(os.path.dirname(__file__), 'cookies.txt'),
    
        # Networking
        'socket_timeout': 30,
        'retries': 10,
        'fragment_retries': 10,
        'skip_unavailable_fragments': True,
    
        # Video / Audio Handling
        'ignoreerrors': 'only_download',
        'no_warnings': True,
        'prefer_insecure': False,  # use HTTPS
        'nocheckcertificate': True,
    
        # Output (not writing to disk, just memory for discord.FFmpegPCMAudio)
        'outtmpl': '%(id)s.%(ext)s',
    
        # Extraction tweaks
        'geo_bypass': True,
        'geo_bypass_country': 'IN',
        'source_address': '0.0.0.0',
    
        # Post-processing
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    FFMPEG_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn',
    }

    ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

    def __init__(self, interaction: discord.Interaction, source: discord.FFmpegPCMAudio, *, data: dict, volume: float = 0.5):
        super().__init__(source, volume)

        self.requester = interaction.user
        self.channel = interaction.channel
        self.data = data

        self.uploader = data.get('uploader')
        self.uploader_url = data.get('uploader_url')
        date = data.get('upload_date')
        self.upload_date = date[6:8] + '.' + date[4:6] + '.' + date[0:4] if date else None
        self.title = data.get('title')
        self.thumbnail = data.get('thumbnail')
        self.description = data.get('description')
        self.duration = self.parse_duration(int(data.get('duration'))) if data.get('duration') else None
        self.tags = data.get('tags')
        self.url = data.get('webpage_url')
        self.views = data.get('view_count')
        self.likes = data.get('like_count')
        self.dislikes = data.get('dislike_count')
        self.stream_url = data.get('url')

    def __str__(self):
        return '**{0.title}** by **{0.uploader}**'.format(self)

    @classmethod
    async def create_source(cls, interaction: discord.Interaction, search: str, *, loop: asyncio.BaseEventLoop = None):
        loop = loop or asyncio.get_event_loop()
        
        # Check if search is a URL starting with http or https
        if search.startswith(('http://', 'https://')):
            # It's a URL, process it directly
            partial = functools.partial(cls.ytdl.extract_info, search, download=False)
            processed_info = await loop.run_in_executor(None, partial)
        else:
            # It's a search query, use ytsearch
            extract_url = f"ytsearch:{search}"
            partial = functools.partial(cls.ytdl.extract_info, extract_url, download=False, process=False)
            data = await loop.run_in_executor(None, partial)
            
            if data is None or 'entries' not in data or not data['entries']:
                raise YTDLError(f"Couldn't find anything that matches `{search}`")
            
            # Get the first valid entry
            process_info = None
            for entry in data['entries']:
                if entry:
                    process_info = entry
                    break
                
            if process_info is None:
                raise YTDLError(f"Couldn't find anything that matches `{search}`")
            
            # Now process the specific video URL
            webpage_url = process_info.get('webpage_url') or process_info.get('url')
            if not webpage_url:
                raise YTDLError(f"Couldn't extract URL from search result")
            
            partial = functools.partial(cls.ytdl.extract_info, webpage_url, download=False)
            processed_info = await loop.run_in_executor(None, partial)
    
        if processed_info is None:
            raise YTDLError(f"Couldn't fetch the audio source")
    
        if 'entries' not in processed_info:
            info = processed_info
        else:
            info = None
            while info is None:
                try:
                    info = processed_info['entries'].pop(0)
                except IndexError:
                    raise YTDLError(f"Couldn't retrieve any matches")
    
        return cls(interaction, discord.FFmpegPCMAudio(info['url'], **cls.FFMPEG_OPTIONS), data=info)
    
    @staticmethod
    def parse_duration(duration: int):
        minutes, seconds = divmod(duration, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)

        duration_list = []
        if days > 0:
            duration_list.append(f'{days} days')
        if hours > 0:
            duration_list.append(f'{hours} hours')
        if minutes > 0:
            duration_list.append(f'{minutes} minutes')
        if seconds > 0:
            duration_list.append(f'{seconds} seconds')

        return ', '.join(duration_list)


class Song:
    __slots__ = ('source', 'requester')

    def __init__(self, source: YTDLSource):
        self.source = source
        self.requester = source.requester

    def create_embed(self):
        embed = (discord.Embed(title='Now playing',
                               description=f'```css\n{self.source.title}\n```',
                               color=16202876)
                 .add_field(name='Duration', value=self.source.duration)
                 .add_field(name='Requested by', value=self.requester.mention)
                 .add_field(name='Uploader', value=f'[{self.source.uploader}]({self.source.uploader_url})')
                 .set_thumbnail(url=self.source.thumbnail))
        return embed


class SongQueue(asyncio.Queue):
    def __getitem__(self, item):
        if isinstance(item, slice):
            return list(itertools.islice(self._queue, item.start, item.stop, item.step))
        else:
            return self._queue[item]

    def __iter__(self):
        return self._queue.__iter__()

    def __len__(self):
        return self.qsize()

    def clear(self):
        self._queue.clear()

    def shuffle(self):
        random.shuffle(self._queue)

    def remove(self, index: int):
        del self._queue[index]


class VoiceState:
    def __init__(self, bot: commands.Bot, interaction: discord.Interaction):
        self.bot = bot
        self._interaction = interaction

        self.current = None
        self.voice = None
        self.next = asyncio.Event()
        self.songs = SongQueue()

        self._loop = False
        self._volume = 1
        self.skip_votes = set()

        self.audio_player = bot.loop.create_task(self.audio_player_task())

    def __del__(self):
        self.audio_player.cancel()

    @property
    def loop(self):
        return self._loop

    @loop.setter
    def loop(self, value: bool):
        self._loop = value

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value: float):
        self._volume = value
        if self.current:
            self.current.source.volume = value
        if self.voice and self.voice.source:
            self.voice.source.volume = value

    @property
    def is_playing(self):
        return self.voice and self.current

    async def audio_player_task(self):
        while True:
            self.next.clear()

            if not self.loop:
                try:
                    async with timeout(604800):  # 1 week
                        self.current = await self.songs.get()
                except asyncio.TimeoutError:
                    self.bot.loop.create_task(self.stop())
                    return

            self.current.source.volume = self._volume
            self.voice.play(self.current.source, after=self.play_next_song)
            await self.current.source.channel.send(embed=self.current.create_embed())
            await self.next.wait()

    def play_next_song(self, error=None):
        if error:
            raise VoiceError(str(error))
        self.next.set()

    def skip(self):
        self.skip_votes.clear()
        if self.is_playing:
            self.voice.stop()

    async def stop(self):
        self.songs.clear()
        if self.voice:
            await self.voice.disconnect()
            self.voice = None


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.voice_states = {}

    def get_voice_state(self, interaction: discord.Interaction):
        state = self.voice_states.get(interaction.guild.id)
        if not state:
            state = VoiceState(self.bot, interaction)
            self.voice_states[interaction.guild.id] = state
        return state

    def cog_unload(self):
        for state in self.voice_states.values():
            self.bot.loop.create_task(state.stop())

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        await interaction.response.send_message(f'An error occurred: {error}', ephemeral=True)

    async def ensure_voice_state(self, interaction: discord.Interaction):
        if not interaction.user.voice or not interaction.user.voice.channel:
            raise app_commands.AppCommandError('You are not connected to any voice channel.')
        
        voice_client = interaction.guild.voice_client
        if voice_client and voice_client.channel != interaction.user.voice.channel:
            raise app_commands.AppCommandError('Bot is already in a different voice channel.')
        
        return True

    # --- Voice Commands ---
    @app_commands.command(name='join', description='Joins your voice channel')
    async def join(self, interaction: discord.Interaction):
        """Joins a voice channel."""
        await self.ensure_voice_state(interaction)
        
        destination = interaction.user.voice.channel
        voice_state = self.get_voice_state(interaction)
        
        if voice_state.voice:
            await voice_state.voice.move_to(destination)
            await interaction.response.send_message(f'Moved to {destination.name}')
        else:
            voice_state.voice = await destination.connect()
            await interaction.response.send_message(f'Joined {destination.name}')

    @app_commands.command(name='summon', description='Summons the bot to a voice channel')
    @app_commands.default_permissions(manage_guild=True)
    async def summon(self, interaction: discord.Interaction, channel: discord.VoiceChannel = None):
        """Summons the bot to a voice channel."""
        if not channel and not interaction.user.voice:
            raise app_commands.AppCommandError('You are neither connected to a voice channel nor specified a channel to join.')
        
        destination = channel or interaction.user.voice.channel
        voice_state = self.get_voice_state(interaction)
        
        if voice_state.voice:
            await voice_state.voice.move_to(destination)
            await interaction.response.send_message(f'Moved to {destination.name}')
        else:
            voice_state.voice = await destination.connect()
            await interaction.response.send_message(f'Joined {destination.name}')

    @app_commands.command(name='leave', description='Clears the queue and leaves the voice channel')
    async def leave(self, interaction: discord.Interaction):
        """Clears the queue and leaves the voice channel."""
        voice_state = self.get_voice_state(interaction)
        
        if not voice_state.voice:
            await interaction.response.send_message('Not connected to any voice channel.')
            return
        
        await voice_state.stop()
        del self.voice_states[interaction.guild.id]
        await interaction.response.send_message('Left the voice channel.')

    @app_commands.command(name='volume', description='Sets the volume of the player (0-100)')
    @app_commands.describe(volume='Volume level between 0 and 100')
    async def volume(self, interaction: discord.Interaction, volume: app_commands.Range[int, 0, 100]):
        """Sets the volume of the player."""
        voice_state = self.get_voice_state(interaction)
        
        if not voice_state.is_playing:
            await interaction.response.send_message('Nothing being played at the moment.', ephemeral=True)
            return

        voice_state.volume = volume / 100
        await interaction.response.send_message(f'Volume set to {volume}%')

    # --- Music Controls ---
    @app_commands.command(name='now', description='Shows the currently playing song')
    async def now(self, interaction: discord.Interaction):
        """Shows the currently playing song."""
        voice_state = self.get_voice_state(interaction)
        
        if not voice_state.current:
            await interaction.response.send_message('Nothing is currently playing.', ephemeral=True)
            return
        
        await interaction.response.send_message(embed=voice_state.current.create_embed())

    @app_commands.command(name='pause', description='Pauses the current song')
    async def pause(self, interaction: discord.Interaction):
        """Pauses the current song."""
        voice_state = self.get_voice_state(interaction)
        
        if voice_state.is_playing and voice_state.voice.is_playing():
            voice_state.voice.pause()
            await interaction.response.send_message('⏸️ Paused')
        else:
            await interaction.response.send_message('Nothing is playing to pause.', ephemeral=True)

    @app_commands.command(name='resume', description='Resumes the current song')
    async def resume(self, interaction: discord.Interaction):
        """Resumes the current song."""
        voice_state = self.get_voice_state(interaction)
        
        if voice_state.is_playing and voice_state.voice.is_paused():
            voice_state.voice.resume()
            await interaction.response.send_message('▶️ Resumed')
        else:
            await interaction.response.send_message('Nothing is paused to resume.', ephemeral=True)

    @app_commands.command(name='stop', description='Stops playback and clears the queue')
    async def stop(self, interaction: discord.Interaction):
        """Stops playback and clears the queue."""
        voice_state = self.get_voice_state(interaction)
        
        voice_state.songs.clear()
        if voice_state.is_playing:
            voice_state.voice.stop()
        await interaction.response.send_message('⏹ Stopped')

    @app_commands.command(name='skip', description='Skips the current song')
    async def skip(self, interaction: discord.Interaction):
        """Skips the current song."""
        voice_state = self.get_voice_state(interaction)
        
        if not voice_state.is_playing:
            await interaction.response.send_message('Not playing any music right now...', ephemeral=True)
            return
        
        voter = interaction.user
        if voter == voice_state.current.requester:
            voice_state.skip()
            await interaction.response.send_message('⏭ Skipped by requester')
        elif voter.id not in voice_state.skip_votes:
            voice_state.skip_votes.add(voter.id)
            total_votes = len(voice_state.skip_votes)
            if total_votes >= 3:
                voice_state.skip()
                await interaction.response.send_message('⏭ Skipped by vote')
            else:
                await interaction.response.send_message(f'Skip vote added, currently at **{total_votes}/3**')
        else:
            await interaction.response.send_message('You have already voted to skip this song.', ephemeral=True)

    @app_commands.command(name='queue', description='Shows the current queue')
    @app_commands.describe(page='Page number to view')
    async def queue(self, interaction: discord.Interaction, page: int = 1):
        """Shows the current queue."""
        voice_state = self.get_voice_state(interaction)
        
        if len(voice_state.songs) == 0:
            await interaction.response.send_message('Empty queue.', ephemeral=True)
            return
        
        items_per_page = 10
        pages = math.ceil(len(voice_state.songs) / items_per_page)
        page = max(1, min(page, pages))
        
        start = (page - 1) * items_per_page
        end = start + items_per_page
        queue = ''
        
        for i, song in enumerate(voice_state.songs[start:end], start=start):
            queue += f'`{i+1}.` [**{song.source.title}**]({song.source.url})\n'
        
        embed = discord.Embed(description=f'**{len(voice_state.songs)} tracks:**\n\n{queue}')
        embed.set_footer(text=f'Viewing page {page}/{pages}')
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='shuffle', description='Shuffles the queue')
    async def shuffle(self, interaction: discord.Interaction):
        """Shuffles the queue."""
        voice_state = self.get_voice_state(interaction)
        
        if len(voice_state.songs) == 0:
            await interaction.response.send_message('Empty queue.', ephemeral=True)
            return
        
        voice_state.songs.shuffle()
        await interaction.response.send_message('✅ Queue shuffled')

    @app_commands.command(name='remove', description='Removes a song from the queue')
    @app_commands.describe(index='Position of the song to remove')
    async def remove(self, interaction: discord.Interaction, index: int):
        """Removes a song from the queue."""
        voice_state = self.get_voice_state(interaction)
        
        if len(voice_state.songs) == 0:
            await interaction.response.send_message('Empty queue.', ephemeral=True)
            return
        
        if index < 1 or index > len(voice_state.songs):
            await interaction.response.send_message('Invalid position.', ephemeral=True)
            return
        
        voice_state.songs.remove(index - 1)
        await interaction.response.send_message(f'✅ Removed song at position {index}')

    @app_commands.command(name='loop', description='Toggles looping of the current song')
    async def loop(self, interaction: discord.Interaction):
        """Toggles looping of the current song."""
        voice_state = self.get_voice_state(interaction)
        
        if not voice_state.is_playing:
            await interaction.response.send_message('Nothing being played at the moment.', ephemeral=True)
            return
        
        voice_state.loop = not voice_state.loop
        status = "enabled" if voice_state.loop else "disabled"
        await interaction.response.send_message(f'✅ Loop {status}')

    @app_commands.command(name='play', description='Plays a song from YouTube')
    @app_commands.describe(search='YouTube URL or search query')
    async def play(self, interaction: discord.Interaction, search: str):
        """Plays a song from YouTube."""
        await self.ensure_voice_state(interaction)
        
        voice_state = self.get_voice_state(interaction)
        if not voice_state.voice:
            destination = interaction.user.voice.channel
            voice_state.voice = await destination.connect()
        
        await interaction.response.defer()
        
        try:
            source = await YTDLSource.create_source(interaction, search, loop=self.bot.loop)
        except YTDLError as e:
            await interaction.followup.send(f'An error occurred while processing this request, We only support youtube url for songs. Error: {e}')
        else:
            song = Song(source)
            await voice_state.songs.put(song)
            await interaction.followup.send(f'Enqueued {str(source)}')


async def setup(bot):
    await bot.add_cog(Music(bot))
