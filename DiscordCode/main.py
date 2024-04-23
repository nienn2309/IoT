import discord 
from discord.ext import commands, tasks
import mysql.connector
import asyncio
import statistics
import json
import paho.mqtt.client as mqtt
import requests

urlbach = 'https://demo.thingsboard.io:443/api/plugins/telemetry/DEVICE/761e0660-f1c3-11ee-b557-29d7e1f72fb2/SHARED_SCOPE'
urlnguyen = 'https://demo.thingsboard.io:443/api/plugins/telemetry/DEVICE/056c1540-f193-11ee-81e8-7942c9f23c0f/SHARED_SCOPE'

access_token = 'eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJuZ3V5ZW5ob2FuZ25ndXllbjI3MkBnbWFpbC5jb20iLCJ1c2VySWQiOiIwNDk3MmU4MC1mMTkyLTExZWUtODFlOC03OTQyYzlmMjNjMGYiLCJzY29wZXMiOlsiVEVOQU5UX0FETUlOIl0sInNlc3Npb25JZCI6ImVlMWM3NjM5LWU3MzMtNGZlMS04NDY5LTEwOTcwYTcwZGI2ZiIsImlzcyI6InRoaW5nc2JvYXJkLmlvIiwiaWF0IjoxNzEyMTMyMzQyLCJleHAiOjE3MTM5MzIzNDIsImZpcnN0TmFtZSI6Ik5ndXllbiIsImxhc3ROYW1lIjoibk5ndXllbiIsImVuYWJsZWQiOnRydWUsInByaXZhY3lQb2xpY3lBY2NlcHRlZCI6dHJ1ZSwiaXNQdWJsaWMiOmZhbHNlLCJ0ZW5hbnRJZCI6IjAyZjRmMDMwLWYxOTItMTFlZS04MWU4LTc5NDJjOWYyM2MwZiIsImN1c3RvbWVySWQiOiIxMzgxNDAwMC0xZGQyLTExYjItODA4MC04MDgwODA4MDgwODAifQ.Biz1gKuwtCbsWXr-TvEeXQdUUYEBAyzgsb5pAPqdmwrZoNRSqXB7TYJKJwkGOeHNesPzjEfy7ptL-diq5Rnyvg'

headers={'Content-Type':'application/json', 'x-authorization': 'Bearer {}'.format(access_token)}

data_channel_lastest_data = None
data_channel_warning = None

db_config = {
    'host': 'localhost',
    'user': 'nguyen',
    'password': '123321',
    'database': 'data_sensor'
}

client = commands.Bot(command_prefix="!", intents=discord.Intents.all())

def execute_query(query):
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        connection.commit()
        return result
    except Exception as e:
        print("Error executing query:", e)
        return None
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

warning_sent = False 

async def insert_saved_data():
    print("yeah")
    while True:
        try:
            query = "INSERT INTO saved_data (water_level, temperature, humidity, state, moisture, lights) SELECT water_level, temperature, humidity, state, moisture, lights FROM sensor_data ORDER BY id DESC LIMIT 1;"
            execute_query(query)
            await asyncio.sleep(5)
        except Exception as e:
            print("Error occurred during insertion:", e)

async def check_water_consumption():
    global warning_sent
    
    try:
        query = "SELECT water_level FROM (SELECT * FROM saved_data ORDER BY id DESC LIMIT 30) AS sub_query ORDER BY id ASC;"
        result = execute_query(query)
        if result:
            water_levels = [row[0] for row in result]
            average_water_consumption = statistics.mean(water_levels)
            if average_water_consumption != 0:
                percentage_changes = [((water_level - average_water_consumption) / average_water_consumption) * 100 for water_level in water_levels]
            else:
                percentage_changes = []

            if not warning_sent:
                for percentage_change in percentage_changes:
                    if percentage_change <= -40 or percentage_change >= 50:
                        message = "Warning: Signs of drought detected. Water consumption is significantly lower than average." if percentage_change <= -40 else "Warning: Signs of excessive water consumption detected. Risk of depleting water sources."
                        await send_warning(message)
                        break
        else:
            print("No data available to calculate water consumption.")
    except Exception as e:
        print("Error occurred during water consumption check:", e)

async def check_soil_moisture():
    try:
        while True:
            query = "SELECT moisture FROM sensor_data ORDER BY id DESC LIMIT 1;"
            result = execute_query(query)
            
            if result:
                moisture = result[0][0]
                if moisture > 1000:
                    await send_warning("Warning: Soil moisture is low.")
                    requests.post(urlnguyen, headers=headers, json= {'method': 'setState', 'params': 'turnon2'})
                elif moisture < 300:
                    await send_warning("Warning: Soil is excessively moist.")
                    requests.post(urlnguyen, headers=headers, json= {'method': 'setState', 'params': 'turnon1'})
            else:
                print("No soil moisture data available.")
            await asyncio.sleep(60)
    except Exception as e:
        print("Error occurred during soil moisture check:", e)

async def check_light_sensor():
    try:
        while True:
            query = "SELECT lights FROM sensor_data ORDER BY id DESC LIMIT 1;"
            result = execute_query(query)
            
            if result:
                lights = result[0][0]
                if lights < 100:
                    await send_warning("Warning: Low light intensity detected. Turn the lamp off")
                    requests.post(urlbach, headers=headers, json= {'method': 'setState', 'params': 'turn2'})
                elif lights > 600:
                    await send_warning("Warning: High light intensity detected. Turn the lamp on")
                    requests.post(urlbach, headers=headers, json= {'method': 'setState', 'params': 'turn1'})
            else:
                print("No light sensor data available.")
            await asyncio.sleep(60)
    except Exception as e:
        print("Error occurred during light sensor check:", e)

async def check_humidity_sensor():
    try:
        while True:
            query = "SELECT humidity FROM sensor_data ORDER BY id DESC LIMIT 1;"
            result = execute_query(query)
            
            if result:
                humidity = result[0][0]
                if humidity < 30:
                    await send_warning("Warning: Low humidity detected. The ventilation system turn on")
                    requests.post(urlbach, headers=headers, json= {'method': 'setState', 'params': 'turn3'})
                elif humidity > 80:
                    await send_warning("Warning: Low humidity detected. The ventilation system turn off")
                    requests.post(urlbach, headers=headers, json= {'method': 'setState', 'params': 'turn4'})
            else:
                print("No humidity sensor data available.")
            await asyncio.sleep(60)
    except Exception as e:
        print("Error occurred during humidity sensor check:", e)
            
async def send_warning(message):
    if data_channel_warning is not None:
        embed = discord.Embed(title="Warning", description=message, color=discord.Color.red())
        embed.set_footer(text="Bot Warning System")
        await data_channel_warning.send(embed=embed)
    else:
        print("No channel has been set yet. Use the '!set_channel_warning' command to set a channel.")

@tasks.loop(seconds=10)
async def update_sensor_data(channel):
    global sensor_embed

    query = "SELECT * FROM sensor_data ORDER BY id DESC LIMIT 1;"
    result = execute_query(query)
    if result:
        row = result[0]
        sensor_embed = discord.Embed(title="Latest Sensor Data", color=discord.Color.green())
        sensor_embed.add_field(name="Water Level", value=row[1], inline=True)
        sensor_embed.add_field(name="Temperature", value=row[2], inline=True)
        if row[4] == 2:
            sensor_embed.add_field(name="Watering Frequency", value="Twice a day", inline=True)
        elif row[4] == 1:
            sensor_embed.add_field(name="Watering Frequency", value="Once a day", inline=True)
        sensor_embed.add_field(name="Humidity", value=row[3], inline=True)
        sensor_embed.add_field(name="Light", value=row[5], inline=True)
        sensor_embed.add_field(name="Moisture", value=row[6], inline=True)
        if row[7] == 1:
            sensor_embed.add_field(name="Lamp", value="On", inline=True)
        elif row[7] == 0:
            sensor_embed.add_field(name="Lamp", value="Off", inline=True)
        if row[8] == 1:
            sensor_embed.add_field(name="Ventilation system", value="On", inline=True)
        elif row[8] == 0:
            sensor_embed.add_field(name="Ventilation system", value="Off", inline=True)
        sensor_embed.set_footer(text="Bot Sensor Data Update")

        try:
            message = await channel.fetch_message(channel.last_message_id)
            await message.edit(embed=sensor_embed)
        except (discord.NotFound, discord.HTTPException):
            await channel.send(embed=sensor_embed)
    else:
        await channel.send("Failed to retrieve latest sensor data from the database.")

@client.event    
async def on_ready():
    print("The bot is now ready for use!")
    print("-----------------------------")
    if data_channel_warning is None:
        print("No channel has been set yet. Use the '!set_channel_warning' and '!set_channel_lastest_data' command to set a channel.")

@client.command()    
async def hello(ctx):
    await ctx.send("Hello")

@client.command()    
async def goodbye(ctx):
    await ctx.send("Goodbye")

@client.command()
async def set_channel_lastest_data(ctx, channel: discord.TextChannel):
    global data_channel_lastest_data
    if isinstance(channel, discord.TextChannel):
        data_channel_lastest_data = channel
        await ctx.send(f"Sensor data now be sent to {channel.mention}.")
        
        update_sensor_data.start(data_channel_lastest_data)
    else:
        await ctx.send("Invalid channel provided. Please mention a valid text channel.")

@client.command()
async def set_channel_warning(ctx, channel: discord.TextChannel):
    global data_channel_warning
    if isinstance(channel, discord.TextChannel):
        data_channel_warning = channel
        await ctx.send(f"Warnings now be sent to {channel.mention}.")
        
        client.loop.create_task(check_soil_moisture())
        client.loop.create_task(insert_saved_data())
        client.loop.create_task(check_water_consumption())
        client.loop.create_task(check_light_sensor())
        client.loop.create_task(check_humidity_sensor())
    else:
        await ctx.send("Invalid channel provided. Please mention a valid text channel.")

@client.command()
async def query_data(ctx, column: str):
    try:
        query = f"SELECT {column} FROM sensor_data;"
        result = execute_query(query)
        
        if result:
            embed = discord.Embed(title=f"Query Results for '{column}'", color=discord.Color.green())
            values = ', '.join([str(row[0]) for row in result])
            embed.add_field(name=column, value=values, inline=False)
            await ctx.send(embed=embed)
        else:
            await ctx.send("No data found in the specified column.")
    except Exception as e:
        await ctx.send(f"An error occurred while querying the data: {e}")

@client.command()
async def query_saved_data(ctx, column: str):
    try:
        query = f"SELECT {column} FROM (SELECT * FROM saved_data ORDER BY id DESC LIMIT 30) AS sub_query;"
        result = execute_query(query)
        
        if result:
            embed = discord.Embed(title=f"Query Results for column '{column}'", color=discord.Color.green())
            values = ', '.join([str(row[0]) for row in result])
            embed.add_field(name=column, value=values, inline=False)
            await ctx.send(embed=embed)
        else:
            await ctx.send("No data found in the specified column.")
    except Exception as e:
        await ctx.send(f"An error occurred while querying the data: {e}")

client.run('MTIyNDM5MzY2MDM1MTc3NDgyMQ.G9VJoE.d4fMzgSpPWNxdiJ9vHWwqemesZvudm3fOaWcbg')