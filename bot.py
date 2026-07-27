import discord
from discord.ext import commands

# Configuración de los permisos obligatorios
intents = discord.Intents.default()
intents.message_content = True  
intents.members = True          

bot = commands.Bot(command_prefix="!", intents=intents)

# Variables globales en memoria para guardar las listas y el historial de bajas
ultima_lista = []
historial_todos_los_jugadores = set()  
jugadores_actuales = set()              

def limpiar_lineas(texto):
    """Convierte el bloque de texto en una lista limpia, ignorando adornos y casillas vacías."""
    lineas_limpias = []
    caracteres_ignorar = ["☆", "★", "─", "⦾", "🍧", "❤️", "💙", "🍨", "💚", "💛", "🍓", "✧", "💖", "⚡", "«", "»", "•", "·", "╰", "╭", "──"]
    
    for linea in texto.strip().split('\n'):
        linea = linea.strip()
        if not linea:
            continue
            
        if any(decoracion in linea.lower() for decoracion in ["horario", "premio", "coins", "organizador", "organizada", "arcana", "anotarse", "torneo"]):
            continue
            
        if (linea.endswith("⋮") or linea.endswith(":")) and len(linea) <= 8:
            continue
            
        if "⋮" in linea:
            partes = linea.split("⋮", 1)
            if len(partes) > 1 and partes[1].strip():
                linea = partes[1].strip()
            else:
                continue 

        elif ":" in linea and not any(h in linea for h in ["🟪", "⏰", "Ꮒ"]): 
            partes = linea.split(":", 1)
            if len(partes) > 1 and partes[1].strip():
                linea = partes[1].strip()
            else:
                continue

        linea = linea.replace("*", "")

        if any(adj in linea for adj in caracteres_ignorar) and len(linea) < 3:
            continue
            
        if linea:
            lineas_limpias.append(linea)
        
    return lineas_limpias

def analizar_cambios(anterior, actual):
    """Compara la lista anterior con la actual y encuentra diferencias."""
    set_anterior = set(anterior)
    set_actual = set(actual)
    
    vistos = set()
    duplicados = []
    for j in actual:
        if j in vistos and j not in duplicados:
            duplicados.append(j)
        vistos.add(j)
        
    nuevos = [j for j in actual if j not in set_anterior]
    eliminados = [j for j in anterior if j not in set_actual]
    
    mismos_elementos = set_anterior == set_actual
    orden_cambiado = mismos_elementos and (anterior != actual)
    
    return duplicados, nuevos, eliminados, orden_cambiado

@bot.event
async def on_ready():
    print(f"✅ Bot conectado exitosamente como {bot.user.name}")
    print("📋 Esperando listas en los canales de Discord...")

@bot.command(name="reiniciar")
async def reiniciar_lista(ctx):
    global ultima_lista, historial_todos_los_jugadores, jugadores_actuales
    ultima_lista = []  
    historial_todos_los_jugadores = set() 
    jugadores_actuales = set() 
    await ctx.send("🔄 **[SISTEMA]: El historial completo de listas y bajas acumuladas ha sido restablecido a cero.**")

@bot.command(name="bajas")
async def ver_bajas_historicas(ctx):
    global historial_todos_los_jugadores, jugadores_actuales
    
    bajas_totales = historial_todos_los_jugadores - jugadores_actuales
    
    reporte_bajas = ["📉 **HISTORIAL ACUMULADO DE BAJAS DEL DÍA** 📉\n"]
    reporte_bajas.append("Jugadores que estuvieron anotados hoy pero ya no figuran en la lista actual:\n")
    
    if bajas_totales:
        for b in sorted(list(bajas_totales)):
            reporte_bajas.append(f"• ❌ {b}")
    else:
        reporte_bajas.append("✨ ¡Ningún jugador ha abandonado o sido eliminado en lo que va del día!")
        
    texto_completo = "\n".join(reporte_bajas)
    if len(texto_completo) <= 1900:
        await ctx.send(texto_completo)
    else:
        mensaje_actual = ""
        for linea in reporte_bajas:
            if len(mensaje_actual) + len(linea) + 1 > 1900:
                await ctx.send(mensaje_actual)
                mensaje_actual = linea + "\n"
            else:
                mensaje_actual += linea + "\n"
        if mensaje_actual:
            await ctx.send(mensaje_actual)

@bot.event
async def on_message(message):
    global ultima_lista, historial_todos_los_jugadores, jugadores_actuales
    
    if message.author == bot.user:
        return

    # PRIORIDAD A LOS COMANDOS: Si empieza con "!", ejecuta el comando y detiene el análisis de listas
    if message.content.startswith("!"):
        await bot.process_commands(message)
        return

    if "\n" in message.content:
        bloques_texto = message.content.split("SIGUIENTE LISTA")
        bloques_listas = [b.strip() for b in bloques_texto if b.strip()]
        
        for i, bloque_individual in enumerate(bloques_listas, start=1):
            lineas_actuales = limpiar_lineas(bloque_individual)
            
            if len(lineas_actuales) >= 1:
                for jugador in lineas_actuales:
                    historial_todos_los_jugadores.add(jugador)
                
                jugadores_actuales = set(lineas_actuales)
                
                if not ultima_lista:
                    ultima_lista = lineas_actuales
                    vistos = set()
                    duplicados = list(set([j for j in lineas_actuales if j in vistos or vistos.add(j)]))
                    
                    msg_inicial = f"📥 **[SISTEMA]: Lista #{i} registrada como base inicial.**\n"
                    if duplicados:
                        msg_inicial += f"⚠️ **Alerta:** Duplicados internos: {', '.join(duplicados)}"
                    else:
                        msg_inicial += "✅ No hay duplicados internos en esta primera lista."
                        
                    await message.reply(msg_inicial)
                    continue

                duplicados, nuevos, eliminados, orden_cambiado = analizar_cambios(ultima_lista, lineas_actuales)
                
                reporte = [f"📊 **REPORTE AUTOMÁTICO DE CAMBIOS (Lista #{i})** 📊\n"]
                
                if duplicados:
                    reporte.append(f"👥 🔴 **Duplicados detectados:** {', '.join(duplicados)}")
                else:
                    reporte.append("👥 🟢 **Duplicados:** Ninguno.")
                    
                if nuevos:
                    reporte.append(f"➕ 🔵 **Nuevos (Aumentaron):** {', '.join(nuevos)}")
                else:
                    reporte.append("➕ **Nuevos:** Ninguno.")
                    
                if eliminados:
                    reporte.append(f"❌ 🟠 **Eliminados en esta transición:** {', '.join(eliminados)}")
                else:
                    reporte.append("❌ **Eliminados en esta transición:** Ninguno.")
                    
                if orden_cambiado:
                    reporte.append("\n🔄 ⚠️ **Aviso:** La lista tiene los mismos integrantes pero fue **REORDENADA**.")
                elif ultima_lista == lineas_actuales:
                    reporte.append("\n✅ **La lista es exactamente idéntica a la anterior.**")

                texto_completo = "\n".join(reporte)
                limite_mensaje = 1900  
                
                if len(texto_completo) <= limite_mensaje:
                    await message.reply(texto_completo)
                else:
                    mensaje_actual = ""
                    for linea_rep in reporte:
                        if len(mensaje_actual) + len(linea_rep) + 1 > limite_mensaje:
                            await message.reply(mensaje_actual)
                            mensaje_actual = linea_rep + "\n"
                        else:
                            mensaje_actual += linea_rep + "\n"
                    if mensaje_actual:
                        await message.reply(mensaje_actual)
                
                ultima_lista = lineas_actuales

# COLOCA TU TOKEN EN LAS COMILLAS (Recuerda cambiarlo en el portal de Discord por seguridad)
TOKEN_DE_TU_BOT = "MTUyMTkwMTcxNTM2Mjk0MzE1MQ.GKhn86.oeE4v2Ue4Vk9lxbwUVsjg00M6OrKi44eCrUwuk"
bot.run(TOKEN_DE_TU_BOT)
