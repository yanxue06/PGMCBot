# REMINDER: NEED TO CONVERT TIME ZONES 

import discord
import json
import os
import dotenv
import gspread
from google.oauth2.service_account import Credentials
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime

dotenv.load_dotenv()

# Initialize bot    
intents = discord.Intents.default()
intents.message_content = True  # Enable reading message content
client = discord.Client(intents=intents)
scheduler = AsyncIOScheduler()

# Google Sheets setup
def setup_sheets():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_file("google-key.json", scopes=scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key("1qoG8XBBKPJiAA-2r0XHNc_RfktJI1S4n3qwDtRWS1uI").sheet1
        return sheet
    except Exception as e:
        print(f"❌ Error setting up Google Sheets: {e}")
        return None

# Function to check for updates in Google Sheets
async def check_sheets_updates():
    print("🔍 Checking Google Sheets for updates...")
    try:
        sheet = setup_sheets()
        if not sheet:
            return
            
        data = sheet.get_all_values()
        
        # Skip header row
        for i in range(1, len(data)):
            row = data[i]
            
            date = row[0]
            time = row[1]
            message = row[2]
            channel = row[3] 
            status = row[4]

            if status == "": 
                if datetime.now() > datetime.strptime(f"{date} {time}", "%m-%d-%Y %H:%M"):
                    print(f"📝 Found new message to send: {date} {time} - {message}")
                    sheet.update_cell(i+1, 5, "sent") 
                else: 
                    # that was a new row that was added
                    # need to add the message to the scheduled messages
                    print(f"📝 Found new message to schedule: {date} {time} - {message}")
                    await add_scheduled_message(date, time, message, channel)
                    sheet.update_cell(i+1, 5, "scheduled")
            else:
                print(f"📝 Message already sent: {date} {time} - {message}")

    except Exception as e:
        print(f"❌ Error checking Google Sheets: {e}")

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

    print(f"📢 Attempting to send message: '{message}' to channel {channel_id}")
    channel = client.get_channel(channel_id)
    if channel:
        await channel.send(message)

@client.event
async def on_ready():
    # here are the current scheduled messages
    # Run once on startup
    await check_sheets_updates()

    scheduler.add_job(check_sheets_updates, "interval", minutes=5)

    if not scheduler.running:
        scheduler.start()


# one option to quick add messages via discord commands 
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
        scheduler.add_job(send_scheduled_message, "date", run_date=dt, args=[1327304088513286268, msg])

        await message.channel.send(f"✅ Scheduled message for {date_time}: {msg}")

@client.event 
async def add_scheduled_message(date, time, message, channel_id):
    try:
        # Check if already scheduled
        uid = (date, time, message, channel_id)
        if uid in scheduled_messages:
            print(f"⚠️ Message already scheduled: {date} - {time} - {message}")
            return False
        
        # Convert to datetime and schedule
        dt = datetime.strptime(f"{date} {time}", "%m-%d-%Y %H:%M")
        scheduler.add_job(
            send_scheduled_message, 
            "date", 
            run_date=dt, 
            args=[channel_id, message],
            id=f"msg_{date}_{time}_{message[:10]}"
        )
        
        print(f"✅ Added new scheduled message for {dt}: {message}")
        return True
    except Exception as e:
        print(f"❌ Error adding scheduled message: {e}")
        return False



# run the bot
client.run(os.getenv('DISCORD_BOT_TOKEN'))
