# REMINDER: NEED TO CONVERT TIME ZONES 

import discord
import json
import os
import dotenv
import gspread
import pytz
from google.oauth2.service_account import Credentials
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
from flask import Flask

# Define Vancouver timezone that automatically adjusts for DST
vancouver_tz = pytz.timezone('America/Vancouver')

dotenv.load_dotenv()

# Initialize bot    
intents = discord.Intents.default()
intents.message_content = True  # Enable reading message content
intents.guilds = True  # Enable server/guild related events
intents.guild_messages = True  # Enable message events in servers
intents.guild_scheduled_events = True  # Enable scheduled events
client = discord.Client(intents=intents)

# Initialize scheduler with Vancouver timezone
scheduler = AsyncIOScheduler(timezone=vancouver_tz)

app = Flask(__name__)

@app.route('/')
def index():
    return "Discord Bot is running!"

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

            try:
                # Parse the time in Vancouver timezone with automatic DST handling
                naive_dt = datetime.strptime(f"{date} {time}", "%m/%d/%Y %H:%M")
                scheduled_time = vancouver_tz.localize(naive_dt)
                current_time = datetime.now(vancouver_tz)
                
                print(f"⏰ Scheduled time: {scheduled_time}, Current time: {current_time}")
                
                if status == "": 
                    if current_time > scheduled_time:
                        print(f"📝 Message is overdue {date} {time} - {message}")
                        # Don't send overdue messages, just mark them
                        sheet.update_cell(i+1, 5, "overdue")
                    else: 
                        print(f"📝 Found new message to schedule: {date} {time} - {message}")
                        # Schedule the message and let the scheduler handle it
                        await add_scheduled_message(date, time, message, channel)
                        sheet.update_cell(i+1, 5, "scheduled")
                # Remove this part - let the scheduler handle scheduled messages
                # elif status == "scheduled" and current_time > scheduled_time:
                #     print(f"📝 Scheduled message is due: {date} {time} - {message}")
                #     sheet.update_cell(i+1, 5, "overdue")
            except Exception as e:
                print(f"❌ Error processing row {i+1}: {e}")

    except Exception as e:
        print(f"❌ Error checking Google Sheets: {e}")

# # Load scheduled messages from JSON
# def load_messages():
#     try:
#         with open("schedule.json", "r") as f:
#             return json.load(f)
#     except FileNotFoundError:
#         return {}

# scheduled_messages = load_messages()

# Function to send scheduled messages
async def send_scheduled_message(channel_id, message, date=None, time=None):  # Add date and time parameters
    try:
        print(f"📢 Attempting to send message: '{message}' to channel {channel_id}")
        # Convert channel_id to integer if it's a string
        channel_id = int(channel_id)
        print(f"🔍 Looking for channel with ID: {channel_id}")
        print(f"🌐 Bot is in {len(client.guilds)} servers")
        
        # Debug: List all available channels
        for guild in client.guilds:
            print(f"📋 Server: {guild.name}")
            for channel in guild.channels:
                print(f"  - Channel: {channel.name} (ID: {channel.id})")
        
        channel = client.get_channel(channel_id)
        
        if channel is None:
            print(f"❌ Could not find channel with ID: {channel_id}")
            return
            
        print(f"✅ Found channel: {channel.name}")
        await channel.send(message)
        print(f"✅ WOAH Successfully sent message to channel {channel_id} at {date} {time}")

        # Update the sheet status to "sent"
        try:
            sheet = setup_sheets()
            if sheet:
                data = sheet.get_all_values()
                # Skip header row and search for the message
                for i in range(1, len(data)):
                    row = data[i]
                    # Match all available criteria
                    matches_criteria = (
                        row[2] == message and  # Message content matches
                        row[3] == str(channel_id) and  # Channel ID matches
                        (date is None or row[0] == date) and  # Date matches if provided
                        (time is None or row[1] == time) and  # Time matches if provided
                        row[4] in ["scheduled", ""]  # Status is either empty or scheduled
                    )
                    
                    if matches_criteria:
                        print(f"📝 Found message in sheet at row {i+1}, updating status to sent")
                        sheet.update_cell(i+1, 5, "sent")
                        break
        except Exception as e:
            print(f"❌ Error updating sheet status: {e}")

    except ValueError as e:
        print(f"❌ Invalid channel ID format: {channel_id}. Error: {e}")
    except Exception as e:
        print(f"❌ Error sending message: {e}")
        import traceback
        print(f"Stack trace: {traceback.format_exc()}")

@client.event
async def on_ready():
    print(f"🤖 Bot is connected as {client.user.name}")
    print(f"🔗 Bot ID: {client.user.id}")
    print(f"🌐 Connected to {len(client.guilds)} servers")
    
    # here are the current scheduled messages
    # Run once on startup
    await check_sheets_updates()

    print("⏰ Setting up scheduler to check every 60 minutes...")
    scheduler.add_job(check_sheets_updates, "interval", minutes=60)

    if not scheduler.running:
        scheduler.start()
        print("⏰ Scheduler started successfully")
        # Print all scheduled jobs
        jobs = scheduler.get_jobs()
        print(f"📅 Current scheduled jobs: {len(jobs)}")
        for job in jobs:
            print(f"  - Job ID: {job.id}, Next run: {job.next_run_time}")

# # one option to quick add messages via discord commands 
# @client.event
# async def on_message(message):

#     content = message.content

#     print(f"message received: {content}")
#     if message.author == client.user:
#         return
    
#     if content.startswith("!schedule"):
#         parts = content.split(" ", 3)
#         if len(parts) < 4:
#             await message.channel.send("Invalid Message. Usage: !schedule YYYY-MM-DD HH:MM Message")
#             return
        
#         date_time = parts[1] + " " + parts[2]
#         msg = parts[3]
#         scheduled_messages[date_time] = msg
        
#         with open("schedule.json", "w") as f:
#             json.dump(scheduled_messages, f, indent=4)

#         dt = datetime.strptime(date_time, "%Y-%m-%d %H:%M")
#         scheduler.add_job(send_scheduled_message, "date", run_date=dt, args=[1327304088513286268, msg])

#         await message.channel.send(f"✅ Scheduled message for {date_time}: {msg}")

@client.event 
async def add_scheduled_message(date, time, message, channel_id):
    try:
        # Convert to datetime and schedule with proper timezone
        naive_dt = datetime.strptime(f"{date} {time}", "%m/%d/%Y %H:%M")
        dt = vancouver_tz.localize(naive_dt)
        
        scheduler.add_job(
            send_scheduled_message, 
            "date", 
            run_date=dt, 
            args=[channel_id, message, date, time],
            id=f"msg_{date}_{time}_{message[:10]}"
        )
        
        print(f"✅ Added new scheduled message for {dt}: {message}")
        return True
    except Exception as e:
        print(f"❌ Error adding scheduled message: {e}")
        return False



if __name__ == "__main__":
    import multiprocessing
    import signal
    import sys
    
    # Handle graceful shutdown
    def signal_handler(sig, frame):
        print("Shutting down the bot...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Set the start method for multiprocessing
    multiprocessing.set_start_method('fork')
    
    def run_flask():
        try:
            port = int(os.environ.get("PORT", 8080))
            print(f"🌐 Starting Flask server on port {port}...")
            app.run(host="0.0.0.0", port=port, debug=False)
        except Exception as e:
            print(f"❌ Flask server error: {e}")
            sys.exit(1)

    def run_discord():
        try:
            token = os.getenv("DISCORD_BOT_TOKEN")
            if not token:
                print("❌ DISCORD_BOT_TOKEN not found in environment variables")
                sys.exit(1)
            print("🤖 Starting Discord bot...")
            client.run(token)
        except Exception as e:
            print(f"❌ Discord bot error: {e}")
            sys.exit(1)

    # Start both processes
    flask_process = multiprocessing.Process(target=run_flask)
    discord_process = multiprocessing.Process(target=run_discord)
    
    flask_process.start()
    discord_process.start()
    
    # Wait for processes to complete
    flask_process.join()
    discord_process.join()
