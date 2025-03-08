# REMINDER: NEED TO CONVERT TIME ZONES 

import discord
import json
import os
import dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime

dotenv.load_dotenv()

# Initialize bot    
intents = discord.Intents.default()
intents.message_content = True  # Enable reading message content
client = discord.Client(intents=intents)
scheduler = AsyncIOScheduler()

# Load scheduled messages from JSON
def load_messages():
    try:
        with open("schedule.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

scheduled_messages = load_messages()

# Function to send scheduled messages
async def send_scheduled_message(channel_id, message):
    channel = client.get_channel(channel_id)
    if channel:
        await channel.send(message)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    
    for timestamp, message in scheduled_messages.items():
        dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M")
        scheduler.add_job(send_scheduled_message, "date", run_date=dt, args=[1327304088513286268, message])

    scheduler.start()

@client.event
async def on_message(message):

    content = message.content

    print(f"message received: {content}")
    if message.author == client.user:
        return
    
    if content.startswith("!schedule"):
        parts = content.split(" ", 3)
        if len(parts) < 4:
            await message.channel.send("Invalid Message. Usage: !schedule YYYY-MM-DD HH:MM Message")
            return
        
        date_time = parts[1] + " " + parts[2]
        msg = parts[3]
        scheduled_messages[date_time] = msg
        
        with open("schedule.json", "w") as f:
            json.dump(scheduled_messages, f, indent=4)

        dt = datetime.strptime(date_time, "%Y-%m-%d %H:%M")
        scheduler.add_job(send_scheduled_message, "date", run_date=dt, args=[message.channel.id, msg])

        await message.channel.send(f"✅ Scheduled message for {date_time}: {msg}")

client.run(os.getenv('DISCORD_BOT_TOKEN'))
