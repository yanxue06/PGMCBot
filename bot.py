import discord 
import dotenv
import os

dotenv.load_dotenv()

# Enable intents
intents = discord.Intents.default()
intents.message_content = True  # Required for the bot to read message content

# Pass intents when creating the client
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'We have logged in as {client}')
    
@client.event 
async def on_message(message): 
    # prevents bot from responding to itself
    if message.author == client.user: 
        return 

client.run(os.getenv('DISCORD_BOT_TOKEN'))