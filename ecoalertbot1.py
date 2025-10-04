import os
import discord
import aiohttp
import asyncio
import random
from discord.ext import commands, tasks

# ==================
# CONFIG
# ==================
import os
import random
import aiohttp
import discord
from discord.ext import commands

class Config:
    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
    OPENWEATHER_API = os.getenv("OPENWEATHER_API")
    NEWS_API = os.getenv("NEWS_API")
    GUARDIAN_API = os.getenv("GUARDIAN_API")
    IUCN_API = os.getenv("IUCN_API")

    ALERT_CHANNEL_ID = int(os.getenv("ALERT_CHANNEL_ID", "0"))


class Climate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # =========
    # HELPERS
    # =========
    async def fetch_json(self, url, params=None, headers=None):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers) as resp:
                    if resp.status == 200:
                        return await resp.json()
        except Exception as e:
            print(f"Error al hacer request: {e}")
        return None

    # =========
    # COMANDOS
    # =========

    @commands.hybrid_command(name="clima")
    async def clima(self, ctx, ciudad: str):
        """Obtiene el clima real de OpenWeather"""
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {"q": ciudad, "appid": Config.OPENWEATHER_API, "units": "metric", "lang": "es"}
        data = await self.fetch_json(url, params=params)

        if not data:
            return await ctx.send(f"❌ No pude obtener datos de {ciudad}")

        temp = data["main"]["temp"]
        desc = data["weather"][0]["description"].capitalize()
        humedad = data["main"]["humidity"]
        await ctx.send(f"🌡️ Clima en {ciudad}: {temp}°C, {desc}, Humedad {humedad}%")

    @commands.hybrid_command(name="alertas")
    async def alertas(self, ctx):
        """Muestra artículos recientes de The Guardian sobre clima"""
        url = "https://content.guardianapis.com/search"
        params = {"q": "climate OR weather", "api-key": Config.GUARDIAN_API, "page-size": 3}
        data = await self.fetch_json(url, params=params)

        if not data:
            return await ctx.send("❌ No pude obtener artículos de The Guardian")

        results = data.get("response", {}).get("results", [])
        if not results:
            return await ctx.send("🌍 No hay alertas recientes encontradas")

        msg = "⚠️ **Últimas alertas sobre el clima (The Guardian):**\n"
        for art in results:
            msg += f"• [{art['webTitle']}]({art['webUrl']})\n"
        await ctx.send(msg)

    @commands.hybrid_command(name="aire")
    async def aire(self, ctx, ciudad: str):
        """Obtiene la calidad del aire desde OpenWeather"""
        # primero geocodificar ciudad
        geo_url = "http://api.openweathermap.org/geo/1.0/direct"
        geo_params = {"q": ciudad, "limit": 1, "appid": Config.OPENWEATHER_API}
        geo_data = await self.fetch_json(geo_url, params=geo_params)

        if not geo_data:
            return await ctx.send(f"❌ No pude localizar {ciudad}")

        lat, lon = geo_data[0]["lat"], geo_data[0]["lon"]
        air_url = "http://api.openweathermap.org/data/2.5/air_pollution"
        air_params = {"lat": lat, "lon": lon, "appid": Config.OPENWEATHER_API}
        air_data = await self.fetch_json(air_url, params=air_params)

        if not air_data:
            return await ctx.send("❌ No pude obtener calidad del aire")

        aqi = air_data["list"][0]["main"]["aqi"]
        niveles = {1: "Bueno", 2: "Aceptable", 3: "Moderado", 4: "Malo", 5: "Muy dañino"}
        await ctx.send(f"💨 Calidad del aire en {ciudad}: {niveles.get(aqi, 'Desconocido')}")

    @commands.hybrid_command(name="randomclima")
    async def randomclima(self, ctx):
        """Envía un artículo aleatorio sobre clima usando NewsAPI"""
        url = "https://newsapi.org/v2/everything"
        params = {"q": "climate OR weather", "language": "es", "apiKey": Config.NEWS_API, "pageSize": 20}
        data = await self.fetch_json(url, params=params)

        if not data:
            return await ctx.send("❌ No pude obtener datos de noticias")

        articles = data.get("articles", [])
        if not articles:
            return await ctx.send("🌍 No hay artículos sobre clima en este momento")

        art = random.choice(articles)
        await ctx.send(f"📰 **{art['title']}**\n{art['url']}")

    @commands.hybrid_command(name="helpclima")
    async def helpclima(self, ctx):
        """Muestra los comandos disponibles"""
        msg = (
            "📖 **Comandos disponibles (con datos reales):**\n"
            "• `/clima [ciudad]` → Clima actual con OpenWeather\n"
            "• `/alertas` → Últimos artículos sobre clima de The Guardian\n"
            "• `/aire [ciudad]` → Calidad del aire actual (OpenWeather)\n"
            "• `/randomclima` → Artículo aleatorio sobre clima (NewsAPI)\n"
            "• `/helpclima` → Esta ayuda"
        )
        await ctx.send(msg)

    # ============
    # LOOP ALERTAS
    # ============
    @tasks.loop(minutes=30)
    async def check_alerts(self):
        if not Config.ALERT_CHANNEL_ID:
            return
        channel = self.bot.get_channel(Config.ALERT_CHANNEL_ID)
        if not channel:
            return
        for city in Config.CITIES:
            data = await self.get_weather(city)
            if data:
                weather = data['weather'][0]
                wid = weather.get('id')
                if wid and 200 <= wid < 300:
                    await channel.send(f"⛈️ Tormenta detectada en {city}!")
                elif wid and 500 <= wid < 600 and wid >= 502:
                    await channel.send(f"🌧️ Lluvia intensa en {city}!")

# ==================
# SETUP DEL BOT
# ==================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot listo: {bot.user}")

async def setup():
    await bot.add_cog(Climate(bot))

async def main():
    async with bot:
        await setup()
        await bot.start(Config.DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())

