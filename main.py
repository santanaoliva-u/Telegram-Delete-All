import asyncio
from telethon import TelegramClient
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
import json
import os

# ---------------------- CONFIGURACIÓN ----------------------
console = Console()

# Ruta del archivo donde se guardarán las sesiones
SESSIONS_FILE = "sessions.json"

# Crear archivo de sesiones si no existe
if not os.path.exists(SESSIONS_FILE):
    with open(SESSIONS_FILE, "w") as f:
        json.dump([], f)

def load_sessions():
    """Carga las sesiones guardadas desde el archivo JSON"""
    with open(SESSIONS_FILE, "r") as f:
        return json.load(f)

def save_sessions(sessions):
    """Guarda las sesiones en el archivo JSON"""
    with open(SESSIONS_FILE, "w") as f:
        json.dump(sessions, f)

async def add_new_session():
    """Función para agregar nuevas sesiones"""
    console.print(Panel("[bold yellow]📱 Agregar una nueva sesión de Telegram[/bold yellow]", expand=False))
    
    # Instrucciones de registro en caso de que no se tenga API ID y Hash
    console.print(Markdown("""
    ### Si aún no tienes un API ID y API Hash:
    1. Visita [my.telegram.org](https://my.telegram.org/auth).
    2. Inicia sesión con tu número de teléfono.
    3. Crea una nueva aplicación para obtener tu API ID y API Hash.
    """))
    
    phone = Prompt.ask("[green]Introduce tu número de teléfono (+52xxxxxxxxxxx):[/green]")
    api_id = Prompt.ask("[green]Introduce tu API ID (Consulta en [my.telegram.org](https://my.telegram.org/auth)):[/green]")
    api_hash = Prompt.ask("[green]Introduce tu API Hash (Consulta en [my.telegram.org](https://my.telegram.org/auth)):[/green]")
    session_name = phone.replace("+", "plus")  # Formato único para la sesión
    
    sessions = load_sessions()
    sessions.append({
        "name": session_name,
        "phone": phone,
        "api_id": api_id,
        "api_hash": api_hash
    })
    
    save_sessions(sessions)
    console.print(f"[bold green]✅ Sesión para {phone} agregada correctamente![/bold green]")

async def manage_session(session_name):
    """Función para manejar la sesión de Telegram seleccionada"""
    sessions = load_sessions()
    session_info = next((s for s in sessions if s["name"] == session_name), None)
    api_id = session_info["api_id"]
    api_hash = session_info["api_hash"]
    
    # Iniciar cliente con la sesión seleccionada
    async with TelegramClient(session_name, api_id, api_hash) as client:
        await client.start()  # Necesario para que se autentique y esté listo para usar
        dialogs = await client.get_dialogs()

        # Menú interactivo con opciones numeradas y detalladas
        console.print(Panel("[bold cyan]🔹 Menú de Opciones 🔹", expand=False))
        console.print("[1] 🗑 Eliminar chats o canales seleccionados")
        console.print("[2] 👥 Salir de grupos seleccionados")
        console.print("[3] 🧹 Eliminar todos los chats, grupos y canales")
        console.print("[4] 📩 Enviar un mensaje a un grupo")
        console.print("[5] 🗂 Ver detalles de tus chats actuales")
        console.print("[6] 📝 Actualizar API ID y API Hash")
        console.print("[7] 💬 Ver estadísticas de tus interacciones")
        console.print("[8] 🚪 Salir de la sesión")

        option = Prompt.ask("[green]Selecciona una opción:", choices=["1", "2", "3", "4", "5", "6", "7", "8"], default="8")

        if option == "1":
            await delete_chats_or_channels(client, dialogs)
        elif option == "2":
            await leave_groups(client, dialogs)
        elif option == "3":
            await delete_all(client, dialogs)
        elif option == "4":
            await send_message_to_group(client)
        elif option == "5":
            await show_current_chats(client, dialogs)
        elif option == "6":
            await update_api_credentials(session_name)
        elif option == "7":
            await view_interaction_statistics(client)
        elif option == "8":
            console.print("[bold yellow]👋 Saliendo de la sesión. ¡Hasta pronto![/bold yellow]")
            return

async def delete_chats_or_channels(client, dialogs):
    """Función para eliminar chats o canales seleccionados"""
    console.print("\n[bold red]🗑 Eliminar chats o canales seleccionados[/bold red]")
    for dialog in dialogs:
        try:
            if dialog.is_user:
                action = Prompt.ask(f"[cyan]Eliminar chat con {dialog.name}? [y/n]", choices=["y", "n"])
                if action == "y":
                    await client.delete_dialog(dialog.id)
                    console.print(f"[bold green]✅ Chat con {dialog.name} eliminado.[/bold green]")
            elif dialog.is_channel:
                action = Prompt.ask(f"[cyan]Eliminar canal {dialog.name}? [y/n]", choices=["y", "n"])
                if action == "y":
                    await client.delete_dialog(dialog.id)
                    console.print(f"[bold green]✅ Canal {dialog.name} eliminado.[/bold green]")
        except Exception as e:
            console.print(f"[bold red]⚠️ Error al eliminar {dialog.name}: {e}[/bold red]")

async def leave_groups(client, dialogs):
    """Función para salir de grupos seleccionados"""
    console.print("\n[bold yellow]👥 Salir de grupos seleccionados[/bold yellow]")
    for dialog in dialogs:
        try:
            if dialog.is_group and not dialog.is_user:
                action = Prompt.ask(f"[cyan]Salir del grupo {dialog.name}? [y/n]", choices=["y", "n"])
                if action == "y":
                    await client.leave_group(dialog.id)
                    console.print(f"[bold green]✅ Saliste del grupo {dialog.name}.[/bold green]")
        except Exception as e:
            console.print(f"[bold red]⚠️ Error al salir del grupo {dialog.name}: {e}[/bold red]")

async def delete_all(client, dialogs):
    """Función para eliminar todos los chats, grupos y canales"""
    console.print("\n[bold red]🗑 Eliminando todos los chats, grupos y canales...[/bold red]")
    for dialog in dialogs:
        try:
            if dialog.is_user or dialog.is_channel or dialog.is_group:
                await client.delete_dialog(dialog.id)
                console.print(f"[bold green]✅ Eliminado {dialog.name}[/bold green]")
        except Exception as e:
            console.print(f"[bold red]⚠️ Error al eliminar {dialog.name}: {e}[/bold red]")

async def send_message_to_group(client):
    """Función para enviar un mensaje a un grupo seleccionado"""
    group_name = Prompt.ask("[green]Introduce el nombre del grupo al que deseas enviar un mensaje:[/green]")
    message = Prompt.ask("[green]Escribe el mensaje que deseas enviar:[/green]")
    
    try:
        group = await client.get_entity(group_name)
        await client.send_message(group, message)
        console.print(f"[bold green]✅ Mensaje enviado correctamente al grupo {group_name}[/bold green]")
    except Exception as e:
        console.print(f"[bold red]⚠️ Error al enviar mensaje: {e}[/bold red]")

async def show_current_chats(client, dialogs):
    """Función para ver los detalles de los chats actuales"""
    console.print("\n[bold cyan]📝 Detalles de tus chats actuales:[/bold cyan]")
    for dialog in dialogs:
        if dialog.is_user:
            console.print(f"[bold blue]💬 Chat con: {dialog.name}[/bold blue]")
        elif dialog.is_group:
            console.print(f"[bold green]👥 Grupo: {dialog.name}[/bold green]")
        elif dialog.is_channel:
            console.print(f"[bold magenta]📡 Canal: {dialog.name}[/bold magenta]")

async def update_api_credentials(session_name):
    """Función para actualizar API ID y API Hash"""
    console.print("[bold yellow]🔑 Actualizar tus credenciales de Telegram[/bold yellow]")
    new_api_id = Prompt.ask("[green]Introduce el nuevo API ID:[/green]")
    new_api_hash = Prompt.ask("[green]Introduce el nuevo API Hash:[/green]")
    
    sessions = load_sessions()
    session_info = next((s for s in sessions if s["name"] == session_name), None)
    session_info["api_id"] = new_api_id
    session_info["api_hash"] = new_api_hash
    
    save_sessions(sessions)
    console.print(f"[bold green]✅ Las credenciales de {session_name} han sido actualizadas correctamente![/bold green]")

async def view_interaction_statistics(client):
    """Función para ver estadísticas de interacciones"""
    dialogs = await client.get_dialogs()
    total_messages = sum([dialog.unread_count for dialog in dialogs])
    
    console.print("\n[bold cyan]📊 Estadísticas de interacciones[/bold cyan]")
    console.print(f"Total de mensajes no leídos: {total_messages}")
    console.print(f"Total de chats: {len(dialogs)}")

async def main_menu():
    """Menú principal para gestionar sesiones múltiples"""
    sessions = load_sessions()

    if not sessions:
        console.print("[bold red]⚠️ No tienes sesiones guardadas. Añade una nueva sesión.[/bold red]")
        await add_new_session()

    while True:
        # Mostrar sesiones disponibles
        console.print(Panel("[bold cyan]🔹 Menú de Sesiones 🔹", expand=False))
        for idx, session in enumerate(sessions, 1):
            console.print(f"{idx}. {session['phone']}")

        # Seleccionar sesión
        session_choice = Prompt.ask("[green]Selecciona el número de sesión:", choices=[str(i) for i in range(1, len(sessions) + 1)], default="1")
        session_name = sessions[int(session_choice) - 1]["name"]

        # Manejar sesión seleccionada
        await manage_session(session_name)

        # Preguntar si continuar o salir
        continue_choice = Prompt.ask("[green]¿Deseas continuar con otra sesión o salir? [s/n]", choices=["s", "n"], default="n")
        if continue_choice == "n":
            console.print("[bold yellow]👋 ¡Hasta luego![/bold yellow]")
            break

if __name__ == "__main__":
    asyncio.run(main_menu())

