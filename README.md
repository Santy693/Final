# Final
'Este es mi proyecto final: un bot de Discord que permite buscar y reproducir música de YouTube directamente en un canal de voz.
El bot cumple con las funciones básicas de cualquier bot de música, incluyendo:

Sistema de queue (cola de canciones)
Comando para reproducir canciones por nombre o link
Comando para pausar, reanudar y saltar canciones
Comando para parar la música y desconectar al bot del canal de voz
El bot utiliza yt-dlp para buscar y extraer el audio de YouTube, y aprovecha los comandos slash de Discord para una experiencia más cómoda.'

'¿Cómo funciona este bot?

El bot está desarrollado en Python usando la librería discord.py (v2+) y utiliza yt-dlp para buscar y extraer el audio de canciones de YouTube.
A continuación, se explica el flujo principal y la lógica del código:

Carga de configuración y arranque

El bot lee el token de Discord desde un archivo .env usando python-dotenv.
Se configuran los permisos (intents) necesarios para operar en servidores de Discord.
Comandos principales

Todos los comandos son slash commands (/play, /skip, /pause, /resume, /stop), lo que permite una integración moderna y cómoda en Discord.
El comando /play permite buscar una canción por nombre o link de YouTube. Si el bot no está en un canal de voz, se conecta automáticamente al canal del usuario.
Cuando se ejecuta /play, el bot usa yt-dlp para buscar la canción y obtiene la URL directa del audio.
Sistema de cola (queue)

Cada servidor tiene su propia cola de canciones, implementada con un diccionario de deque.
Si hay una canción sonando, las nuevas se agregan a la cola. Si no hay nada sonando, el bot empieza a reproducir inmediatamente.
Reproducción y control

El bot usa FFmpeg para reproducir el audio en el canal de voz.
Cuando termina una canción, automáticamente reproduce la siguiente de la cola (si hay).
El bot no se desconecta solo: queda esperando nuevas canciones hasta que se use el comando /stop.

Comandos de control

/skip: Salta la canción actual y reproduce la siguiente de la cola.
/pause y /resume: Pausan y reanudan la reproducción.
/stop: Limpia la cola, detiene la música y desconecta al bot del canal de voz.
Sincronización y eventos

Al iniciar, el bot sincroniza los comandos slash con el servidor.
El evento on_ready avisa cuando el bot está listo para usarse.'
