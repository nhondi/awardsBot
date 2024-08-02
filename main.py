# main.py
import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta, timezone
from config import TOKEN
from commands import setup_commands
from utils import ensure_awards_channel, ensure_awards_channel_and_permissions, create_congratulatory_message

# Define intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True
intents.reactions = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Store messages with their reactions count
message_reactions = {}

# Dictionary to store awards channel IDs
bot.awards_channels = {}

async def send_message_to_awards_channel(guild, message_content):
    await ensure_awards_channel_and_permissions(guild, bot)
    channel_id = bot.awards_channels.get(guild.id)
    if channel_id:
        channel = guild.get_channel(channel_id)
        if channel:
            try:
                await channel.send(message_content)
            except discord.Forbidden:
                print(f"Cannot send message to 'awards' channel in {guild.name}. Missing permissions.")
        else:
            print(f"'awards' channel not found in {guild.name}.")
            await ensure_awards_channel_and_permissions(guild, bot)
            channel_id = bot.awards_channels.get(guild.id)
            channel = guild.get_channel(channel_id)
            if channel:
                try:
                    await channel.send(message_content)
                except discord.Forbidden:
                    print(f"Cannot send message to 'awards' channel in {guild.name}. Missing permissions.")
    else:
        print(f"'awards' channel not set up for {guild.name}.")
        await ensure_awards_channel_and_permissions(guild, bot)
        channel_id = bot.awards_channels.get(guild.id)
        channel = guild.get_channel(channel_id)
        if channel:
            try:
                await channel.send(message_content)
            except discord.Forbidden:
                print(f"Cannot send message to 'awards' channel in {guild.name}. Missing permissions.")

async def send_update_message():
    # Choose a channel to send the update message
    for guild in bot.guilds:
        await send_message_to_awards_channel(guild, f"The bot '{bot.user.name}' has been updated!")

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    print("Bot is online.")
    await bot.tree.sync()  # Sync application commands
    print("Application commands synced.")
    await send_update_message()  # Send the update message when bot starts
    check_most_reacted_message.start()

@bot.event
async def on_guild_join(guild):
    print(f"Joined new guild: {guild.name}")
    await ensure_awards_channel_and_permissions(guild, bot)

@bot.event
async def on_member_join(member):
    # Ensure awards channel exists when a new member joins
    if member.guild.id not in bot.awards_channels:
        await ensure_awards_channel_and_permissions(member.guild, bot)

@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return
    message = reaction.message
    print(f"Reaction added: {reaction.emoji} by {user} on message: {message.id}")
    if message.id not in message_reactions:
        message_reactions[message.id] = {"message": message, "reaction_count": 0}
    message_reactions[message.id]["reaction_count"] += 1

@tasks.loop(seconds = 15)
async def check_most_reacted_message():
    print("Checking for most reacted message...")
    one_week_ago = datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(weeks=1)
    top_message = None
    top_reaction_count = 0                      

    for message_id, data in message_reactions.items():
        message_created = data["message"].created_at
        print(f"Message ID: {message_id}, Created At: {message_created}, Reactions: {data['reaction_count']}")
        
        if message_created.tzinfo is None:
            message_created = message_created.replace(tzinfo=timezone.utc)

        if message_created > one_week_ago and data["reaction_count"] > top_reaction_count:
            top_reaction_count = data["reaction_count"]
            top_message = data["message"]

    for guild in bot.guilds:
        if top_message:
            title = "Emoji Magnet"
            condition = "receiving the most amount of reactions on your message"
            additional_info = (f"""{top_message.content}
                                📈 Reactions: {top_reaction_count} 📈""")
            congrats = create_congratulatory_message(title, top_message.author.mention, condition, additional_info)
            await send_message_to_awards_channel(guild, congrats)
        else:
            await send_message_to_awards_channel(guild, "No top message found this week.")
            
    message_reactions.clear()

setup_commands(bot)

# Run the bot
if TOKEN:
    bot.run(TOKEN)
else:
    print("Bot token not found. Please ensure the token.txt file exists and contains a valid token.")
