# config.py
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
    DISCORD_TOKEN = os.getenv('MTMzMTc3NTU5NDA1MjA2MzI1Mw.G2QTNi. '
                              'NCip95XamvEF3eFoJ-rqI45PBPsaciME02C_w4')
    OPENWEATHER_API = os.getenv('6a11835592e85adfd592774625dd42b3')
    NEWS_API = os.getenv('4d2605812cc14d36bcae70bbecb4dce9')
    GUARDIAN_API = os.getenv('97de0942-b3e9-4aa0-af95-fb4177c4c6e1')
    IUCN_API = os.getenv('gyPq6yNuT4DxPWjG1QGUKSGtmww3wPauucnd')


class Climate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_key = Config.OPENWEATHER_API
        self.scheduler = AsyncIOScheduler()
        self.co2_levels_cache = None

    async def on_ready(self):
       
       print("Bot listo, iniciando scheduler")
      
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
                # Verificar condiciones extremas
                temp = data['main']['temp']
                if temp > 38:
                    alerts.append(
                                 f"🔥 *{city}*: Ola de calor extrema ({temp}°C)"
                                 )
                elif temp < -15:
                    alerts.append(f"❄️ **{city}**: Frío extremo ({temp}°C)")
                
                # Verificar tormentas
                if 'weather' in data:
                    for weather in data['weather']:
                        if weather['id'] in range(200, 300):  # Tormentas
                            alerts.append(
                                f"⛈️ **{city}**:Tormenta eléctrica severa")
                        elif weather['id'] in range(500, 600):  
                            # Lluvia intensa
                            if weather['id'] >= 502:
                                alerts.append(f"🌧️ **{city}**: Lluvia intensa")
        
        # Enviar alertas si hay alguna
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
        # Simular datos de CO2 (en producción, usar API real de NASA)
        current_co2 = 421.5  # ppm actual aproximado
        pre_industrial = 280  # ppm pre-industrial
        increase = ((current_co2 - pre_industrial) / pre_industrial) * 100
        embed = discord.Embed(
            title="🏭 Niveles de CO₂ Atmosférico",
            color=discord.Color.orange()
        )
        embed.add_field(
            name="Nivel Actual",
            value=f"**{current_co2} ppm**",
            inline=True
        )
        embed.add_field(
            name="Nivel Pre-industrial",
            value=f"{pre_industrial} ppm",
            inline=True
        )
        embed.add_field(
            name="Incremento",
            value=f"+{increase:.1f}%",
            inline=True
        )
    # Agregar gráfico visual con barras
        bar_length = 20
        filled = int((current_co2 / 450) * bar_length)  
        # 450 ppm como máximo visual
        bar = "🟥" * filled + "⬜" * (bar_length - filled)
        embed.add_field(
            name="Visualización",
            value=f"{bar}\n280 ppm ────────── 450 ppm",
            inline=False
        )
        embed.add_field(
            name="⚠️ Impacto",
            value="Niveles superiores a 350 ppm se consideran peligrosos para "
                  "el clima estable",
            inline=False
        )
        embed.set_footer(text="Fuente: NASA Climate Change "
                         "| Última actualización: Hoy")
        await ctx.send(embed=embed)




























































# Fase 4: Sistema de Notificaciones (Día 11-12)

# utils/scheduler.py


class EcoScheduler:

    def __init__(self, bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler()
        self.setup_jobs()
    
    def setup_jobs(self):
        """Configura todas las tareas programadas"""
        # Tip diario a las 9 AM
        self.scheduler.add_job(
            self.daily_eco_tip,
            'cron',
            hour=9,
            minute=0,
            id='daily_tip'
        )
        
        # Resumen semanal los lunes
        self.scheduler.add_job(
            self.weekly_climate_summary,
            'cron',
            day_of_week='mon',
            hour=10,
            minute=0,
            id='weekly_summary'
        )
        
        # Verificación de eventos extremos cada 3 horas
        self.scheduler.add_job(
            self.check_extreme_events,
            'interval',
            hours=3,
            id='extreme_events'
        )
    
    def start(self):
        """Inicia el scheduler"""
        self.scheduler.start()
    
    def stop(self):
        """Detiene el scheduler"""
        self.scheduler.shutdown()
    
    async def daily_eco_tip(self):
        """Envía el tip ecológico del día"""
        tips = [
            {
                "title": "💡 Ahorra Energía",
                "tip": "Apaga las luces al salir de una habitación",
                "impact": "Ahorra 0.04 kWh por hora"
            },
            {
                "title": "🚿 Conserva Agua",
                "tip": 
                "Una ducha de 5 minutos usa 95 litros menos que un baño",
                "impact": "Ahorra hasta 95 litros de agua"
            },
            {
                "title": "🚴 Transporte Verde",
                "tip": "Usa la bicicleta para trayectos cortos",
                "impact": "Evita 150g de CO₂ por kilómetro"
            }
        ]
        
        tip = random.choice(tips)
        
        for guild in self.bot.guilds:
            # Buscar canal general o eco-tips
            channel = discord.utils.get(
                guild.text_channels,
                name='eco-tips'
            ) or discord.utils.get(
                guild.text_channels,
                name='general'
            )
            
            if channel:
                embed = discord.Embed(
                    title=f"🌱 Eco-Tip del Día: {tip['title']}",
                    description=tip['tip'],
                    color=discord.Color.green()
                )
                embed.add_field(name="Impacto", value=tip['impact'],
                                inline=False)
                embed.set_footer(text="Reacciona con ✅ si completaste este tip"
                                 "hoy")
                
                message = await channel.send(embed=embed)
                await message.add_reaction('✅')
    
    async def check_extreme_events(self):
        """Verifica eventos climáticos extremos globalmente"""
        # Aquí iría la integración con APIs de alertas climáticas
        # Por ejemplo: NOAA, servicio meteorológico nacional, etc.
# Fase 5: Testing y Optimización (Día 13-14)
# 5.1 Suite de Tests

# tests/test_climate.py


class TestClimate(unittest.TestCase):
    def setUp(self):
        self.bot = Mock()
        self.cog = Climate(self.bot)

    @patch('aiohttp.ClientSession.get')
    async def test_get_weather_data(self, mock_get):
        """Test obtención de datos del clima"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            'main': {'temp': 20, 'humidity': 65},
            'weather': [{'description': 'clear sky'}],
            'name': 'Bogota',
            'sys': {'country': 'CO'}
        })
        
        mock_get.return_value.__aenter__.return_value = mock_response
        
        result = await self.cog.get_weather_data('Bogota')
        self.assertIsNotNone(result)
        self.assertEqual(result['main']['temp'], 20)
    
    def test_temperature_color(self):
        """Test colores según temperatura"""
        self.assertEqual(
            self.cog.get_temp_color(-5),
            discord.Color.blue()
        )
        self.assertEqual(
            self.cog.get_temp_color(20),
            discord.Color.green()
        )
        self.assertEqual(
            self.cog.get_temp_color(40),
            discord.Color.red()
        )
# Create cogs directory if it doesn't exist
    os.makedirs('cogs', exist_ok=True)
# Create __init__.py in cogs directory
    with open(os.path.join('cogs', '__init__.py'), 'a'):
        pass
# climate.py


class TestClimateCommands(unittest.TestCase):
    def setUp(self):
        self.bot = Mock()
        self.cog = Climate(self.bot)


@patch('aiohttp.ClientSession.get')
async def test_get_weather_data(self, mock_get):
    # Test obtención de datos del clima
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={
            'main': {'temp': 20, 'humidity': 65},
            'weather': [{'description': 'clear sky'}],
            'name': 'Bogota',
            'sys': {'country': 'CO'}
        })
        
    mock_get.return_value.__aenter__.return_value = mock_response
    result = await self.cog.get_weather_data('Bogota')
    self.assertIsNotNone(result)
    self.assertEqual(result['main']['temp'], 20)


def test_temperature_color(self):  # Test colores según temperatura

    self.assertEqual(
     self.cog.get_temp_color(-5),
     discord.Color.blue()
        )
    self.assertEqual(
        self.cog.get_temp_color(20),
        discord.Color.green()
        )
    self.assertEqual(
        self.cog.get_temp_color(40),
        discord.Color.red()
        )


if __name__ == '__main__':
    unittest.main()

logger = logging.getLogger(__name__)


def performance_monitor(func):
    """Decorador para monitorear performance"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        if execution_time > 2:  # Alerta si toma más de 2 segundos
            logger.warning(
                f"{func.__name__} took {execution_time:.2f} seconds"
            )
        return result
    return wrapper
# Implementar caché simple


class Cache:
    # Sistema de caché simple para reducir llamadas a API"""
    def __init__(self, ttl=300):  # 5 minutos por defecto
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

# Implementar rate limiting


class RateLimiter:
    def __init__(self, calls=10, period=60):
        self.calls = calls
        self.period = period
        self.call_times = []

    async def check(self):
        now = time.time()
        # Limpiar llamadas antiguas
        self.call_times = [
            t for t in self.call_times 
            if now - t < self.period
        ]        
        if len(self.call_times) >= self.calls:
            sleep_time = self.period - (now - self.call_times[0])
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
                return await self.check()         
        self.call_times.append(now)
        return True