import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import yt_dlp
from collections import deque
import asyncio

# Carga las variables de entorno del archivo .env (acá está el token del bot)
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Diccionario para guardar la cola de canciones por servidor
SONG_QUEUES = {}

# ID del servidor donde se van a registrar los comandos (cambialo por el tuyo si hace falta)
GUILD_ID = 693182998647930990

# Función para buscar canciones en YouTube usando yt_dlp de forma asíncrona
async def search_ytdlp_async(query, ydl_opts):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: _extract(query, ydl_opts))

# Función interna para extraer info de YouTube (la usa la de arriba)
def _extract(query, ydl_opts):
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(query, download=False)

# Configura los intents del bot (acá le decís qué eventos puede ver)
intents = discord.Intents.default()
intents.message_content = True

# Vuelve a cargar el token por si acaso (no es necesario dos veces, pero no molesta)
load_dotenv()
token = os.getenv('DISCORD_TOKEN')

# Crea la instancia del bot con el prefijo "!" y los intents configurados
bot = commands.Bot(command_prefix="!", intents=intents)

# Diccionario para saber si el bot está reproduciendo algo en cada servidor
is_playing = {}

# Comando para reproducir una canción o agregarla a la cola
@bot.tree.command(name="play", description="Reproduce o agrega una canción.")
@app_commands.describe(song_query="Consulta de búsqueda")
async def play(interaction: discord.Interaction, song_query: str):
    await interaction.response.defer()
    
    # Chequea si el usuario está en un canal de voz
    voice_channel = interaction.user.voice.channel
    if voice_channel is None:
        await interaction.followup.send("No estas en un canal de voz. Por favor, unite a uno antes de usar este comando.")
        return
    
    # Busca si el bot ya está conectado a un canal de voz en el server
    voice_client = interaction.guild.voice_client
    if voice_client is None:
        voice_client = await voice_channel.connect()
    elif voice_channel != voice_client.channel:
        await voice_client.move_to(voice_channel)
        
    # Opciones para yt_dlp, así baja solo el audio y no el video
    ydl_options = {
        "format": "bestaudio[abr<=96]/bestaudio",
        "noplaylist": True,
        "youtube_include_dash_manifest": False,
        "youtube_include_hls_manifest": False,
    }
    
    # Busca la canción en YouTube
    query = "ytsearch1: " + song_query
    results = await search_ytdlp_async(query, ydl_options)
    tracks = results.get("entries", [])
    
    # Si no encontró nada, avisa y sale
    if not tracks:
        await interaction.followup.send("No se encontró nada.")
        return
    
    # Saca la info de la primera canción que encontró
    first_track = tracks[0]
    audio_url = first_track["url"]
    title = first_track.get("title", "Sin título")
    
    guild_id = str(interaction.guild.id)
    if SONG_QUEUES.get(guild_id) is None:
        SONG_QUEUES[guild_id] = deque()
    if is_playing.get(guild_id) is None:
        is_playing[guild_id] = False

    # Agrega la canción a la cola del server
    SONG_QUEUES[guild_id].append((audio_url, title))

    # Si no está reproduciendo nada, arranca la reproducción
    if not voice_client.is_playing() and not voice_client.is_paused() and not is_playing[guild_id]:
        await play_next_song(voice_client, guild_id, interaction.channel)
        await interaction.followup.send(f"Ahora está sonando: **{title}**")
    else:
        # Si ya está sonando algo, solo avisa que se agregó a la cola
        await interaction.followup.send(f"Añadido a la queue: **{title}**")
        
# Comando para saltar la canción actual
@bot.tree.command(name="skip", description="Salta la canción actual.")
async def skip(interaction: discord.Interaction):
    # Si hay algo sonando o en pausa, lo para (y arranca la siguiente si hay)
    if interaction.guild.voice_client and (interaction.guild.voice_client.is_playing() or interaction.guild.voice_client.is_paused()):
        interaction.guild.voice_client.stop()
        await interaction.response.send_message("Canción saltada.")
    else:
        await interaction.response.send_message("No hay ninguna canción para saltar.")
        
# Comando para pausar la canción
@bot.tree.command(name="pause", description="Pausa la canción actual.")
async def pause(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client

    if voice_client is None:
        return await interaction.response.send_message("No estoy en un canal de voz.")
    
    if not voice_client.is_playing():
        return await interaction.response.send_message("No hay ninguna canción reproduciéndose.")
    
    voice_client.pause()
    await interaction.response.send_message("Canción pausada.")
    
# Comando para reanudar la canción
@bot.tree.command(name="resume", description="Reanuda la canción actual.")
async def resume(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client

    # Chequea si el bot está en un canal de voz
    if voice_client is None:
        return await interaction.response.send_message("No estoy en un canal de voz.")

    # Chequea si hay una canción en pausa
    if not voice_client.is_paused():
        return await interaction.response.send_message("No estoy en pausa en este momento.")

    # Reanuda la reproducción
    voice_client.resume()
    await interaction.response.send_message("Canción reanudada!")
    
# Comando para parar todo y desconectar el bot del canal de voz
@bot.tree.command(name="stop", description="Pausa la canción actual.")
async def stop(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client

    # Chequea si el bot está conectado
    if not voice_client or not voice_client.is_connected():
        return await interaction.response.send_message("No estoy conectado a ningún canal de voz.")

    # Limpia la cola de canciones
    guild_id_str = str(interaction.guild_id)
    if guild_id_str in SONG_QUEUES:
        SONG_QUEUES[guild_id_str].clear()

    # Si hay algo sonando o en pausa, lo para
    if voice_client.is_playing() or voice_client.is_paused():
        voice_client.stop()

    # Desconecta el bot del canal de voz
    await voice_client.disconnect()

    await interaction.response.send_message("Se detuvo la reproducción y se desconectó.")

# Evento que se ejecuta cuando el bot está listo
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"{bot.user} Está listo!")

# Función que se encarga de reproducir la siguiente canción de la cola
async def play_next_song(voice_client, guild_id, channel):
    global is_playing
    is_playing[guild_id] = True

    while True:
        if not SONG_QUEUES[guild_id]:
            is_playing[guild_id] = False
            # Espera hasta 60 segundos, chequeando cada 2 segundos si agregan algo
            for _ in range(30):
                await asyncio.sleep(2)
                if SONG_QUEUES[guild_id]:
                    is_playing[guild_id] = True
                    break
            else:
                # Si después de esperar sigue vacía la cola, desconectate y salí
                await voice_client.disconnect()
                return
            # Si se agregó algo, seguí el bucle y reproducí
            continue

        audio_url, title = SONG_QUEUES[guild_id].popleft()
        ffmpeg_options = {
            "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            "options": "-vn -c:a libopus -b:a 96k",
        }
        source = discord.FFmpegOpusAudio(audio_url, **ffmpeg_options, executable="E:\\Escritorio XD\\ffmpeg-7.1.1-essentials_build\\bin\\ffmpeg.exe") # Ruta de acceso de ffmpeg

        # Usamos un future para esperar a que termine la canción antes de seguir el bucle
        done = asyncio.Event()

        def after_play(error):
            if error:
                print(f"Error al reproducir {title}: {error}")
            done.set()

        voice_client.play(source, after=after_play)
        await channel.send(f"Ahora está sonando: **{title}**")
        await done.wait()

if __name__ == "__main__":
    bot.run(TOKEN)
