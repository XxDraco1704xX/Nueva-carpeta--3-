# ecoalertbot.py
import discord
from discord.ext import commands, tasks
import aiohttp
from datetime import datetime
import os
import random
import asyncio
import unittest
from unittest.mock import Mock, patch, AsyncMock
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import time
from functools import wraps
import logging


class Config:
    # ✅ Debug: evitar exponer tokens directamente
    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
    OPENWEATHER_API = os.getenv("OPENWEATHER_API")
    NEWS_API = os.getenv("NEWS_API")
    GUARDIAN_API = os.getenv("GUARDIAN_API")
    IUCN_API = os.getenv("IUCN_API")
    ALERT_CHANNEL_ID = int(os.getenv("ALERT_CHANNEL_ID", "0"))  
    # evita AttributeError


class Climate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_key = Config.OPENWEATHER_API
        self.scheduler = AsyncIOScheduler()
        self.co2_levels_cache = None

    async def on_ready(self):
        print("Bot listo, iniciando scheduler")
        # ✅ Debug: asegurarse de que el loop esté activo
        if not self.extreme_weather_check.is_running():
            self.extreme_weather_check.start()
        if not self.scheduler.running:
            self.scheduler.start()

    def cog_unload(self):
        self.extreme_weather_check.cancel()

    @tasks.loop(hours=1)
    async def extreme_weather_check(self):
        """Verifica eventos climáticos extremos cada hora"""
        tracked_cities = ['Bogota', 'Mexico City', 'Buenos Aires',
                          'Madrid', 'Lima']
        alerts = []

        for city in tracked_cities:
            data = await self.get_weather_data(city)
            if data:
                temp = data['main']['temp']
                if temp > 38:
                    alerts.append(f"🔥 *{city}*: Ola de calor extrema ({temp}°C)")
                elif temp < -15:
                    alerts.append(f"❄️ **{city}**: Frío extremo ({temp}°C)")

                if 'weather' in data:
                    for weather in data['weather']:
                        if 200 <= weather['id'] < 300:
                            alerts.append(
                                f"⛈️ **{city}**:Tormenta eléctrica severa")
                        elif 500 <= weather['id'] < 600 and weather['id'] >= 502:
                            alerts.append(f"🌧️ **{city}**: Lluvia intensa")

        # ✅ Debug: validar canal
        if alerts and Config.ALERT_CHANNEL_ID:
            channel = self.bot.get_channel(Config.ALERT_CHANNEL_ID)
            if channel:
                embed = discord.Embed(
                    title="⚠️ Alertas Climáticas Extremas",
                    description="\n".join(alerts),
                    color=discord.Color.red(),
                    timestamp=datetime.utcnow()
                )
                await channel.send(embed=embed)

    async def get_weather_data(self, city):
        """Obtiene datos del clima para una ciudad"""
        async with aiohttp.ClientSession() as session:
            url = "https://api.openweathermap.org/data/2.5/weather"
            params = {
                'q': city,
                'appid': self.api_key,
                'units': 'metric',
                'lang': 'es'
            }
            try:
                async with session.get(url, params=params) as resp:
                    if resp.status == 200:
                        return await resp.json()
            except Exception as e:
                print(f"Error getting weather for {city}: {e}")
        return None

    @commands.command(name='co2')
    async def co2_levels(self, ctx):
        """Muestra los niveles actuales de CO2 atmosférico"""
        current_co2 = 421.5
        pre_industrial = 280
        increase = ((current_co2 - pre_industrial) / pre_industrial) * 100

        embed = discord.Embed(
            title="🏭 Niveles de CO₂ Atmosférico",
            color=discord.Color.orange()
        )
        embed.add_field(name="Nivel Actual", value=f"**{current_co2} ppm**", inline=True)
        embed.add_field(name="Nivel Pre-industrial", value=f"{pre_industrial} ppm", inline=True)
        embed.add_field(name="Incremento", value=f"+{increase:.1f}%", inline=True)

        bar_length = 20
        filled = int((current_co2 / 450) * bar_length)
        bar = "🟥" * filled + "⬜" * (bar_length - filled)
        embed.add_field(
            name="Visualización",
            value=f"{bar}\n280 ppm ────────── 450 ppm",
            inline=False
        )
        embed.add_field(
            name="⚠️ Impacto",
            value="Niveles superiores a 350 ppm se consideran peligrosos para el clima estable",
            inline=False
        )
        embed.set_footer(text="Fuente: NASA Climate Change "
                         "| Última actualización: Hoy")
        await ctx.send(embed=embed)


class EcoScheduler:
    def __init__(self, bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler()
        self.setup_jobs()

    def setup_jobs(self):
        self.scheduler.add_job(self.daily_eco_tip, 'cron',
                               hour=9, minute=0, id='daily_tip')
        self.scheduler.add_job(self.weekly_climate_summary, 
                               'cron', day_of_week='mon',
                               hour=10, minute=0, id='weekly_summary')
        self.scheduler.add_job(self.check_extreme_events, 
                               'interval', hours=3, id='extreme_events')

    def start(self):
        self.scheduler.start()

    def stop(self):
        self.scheduler.shutdown()

    async def daily_eco_tip(self):
        tips = [
            {"title": "💡 Ahorra Energía", "tip": "Apaga las luces al salir", "impact": "Ahorra 0.04 kWh"},
            {"title": "🚿 Conserva Agua", "tip": "Ducha de 5 min ahorra 95 litros", "impact": "Ahorra 95 litros"},
            {"title": "🚴 Transporte Verde", "tip": "Usa bicicleta", "impact": "Evita 150g CO₂/km"}
        ]
        tip = random.choice(tips)
        for guild in self.bot.guilds:
            channel = discord.utils.get(guild.text_channels, name='eco-tips') or \
                      discord.utils.get(guild.text_channels, name='general')
            if channel:
                embed = discord.Embed(
                    title=f"🌱 Eco-Tip del Día: {tip['title']}",
                    description=tip['tip'],
                    color=discord.Color.green()
                )
                embed.add_field(name="Impacto", value=tip['impact'], inline=False)
                message = await channel.send(embed=embed)
                await message.add_reaction('✅')

    async def check_extreme_events(self):
        pass  # placeholder


# ✅ Debug: usar IsolatedAsyncioTestCase para async tests
class TestClimate(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.bot = Mock()
        self.cog = Climate(self.bot)

    @patch('aiohttp.ClientSession.get')
    async def test_get_weather_data(self, mock_get):
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            'main': {'temp': 20, 'humidity': 65},
            'weather': [{'id': 800, 'description': 'clear sky'}],
            'name': 'Bogota',
            'sys': {'country': 'CO'}
        })
        mock_get.return_value.__aenter__.return_value = mock_response
        result = await self.cog.get_weather_data('Bogota')
        self.assertIsNotNone(result)
        self.assertEqual(result['main']['temp'], 20)


logger = logging.getLogger(__name__)


def performance_monitor(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        if end_time - start_time > 2:
            logger.warning(f"{func.__name__} tardó {end_time - start_time:.2f} segundos")
        return result
    return wrapper


class Cache:
    def __init__(self, ttl=300):
        self.cache = {}
        self.ttl = ttl

    async def get(self, key):
        if key in self.cache:
            data, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return data
            else:
                del self.cache[key]
        return None

    async def set(self, key, value):
        self.cache[key] = (value, time.time())

    def clear(self):
        self.cache.clear()


class RateLimiter:
    def __init__(self, calls=10, period=60):
        self.calls = calls
        self.period = period
        self.call_times = []

    async def check(self):
        now = time.time()
        self.call_times = [t for t in self.call_times if now - t < self.period]
        if len(self.call_times) >= self.calls:
            sleep_time = self.period - (now - self.call_times[0])
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
                return await self.check()
        self.call_times.append(now)
        return True


if __name__ == "__main__":
    unittest.main()
