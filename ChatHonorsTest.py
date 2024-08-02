import random
import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, timedelta, timezone

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

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    print("Bot is online.")
    await bot.tree.sync()  # Sync application commands
    print("Application commands synced.")
    check_most_reacted_message.start()

@bot.event
async def on_guild_join(guild):
    print(f"Joined new guild: {guild.name}")
    try:
        await ensure_awards_channel(guild)
    except discord.Forbidden:
        print(f"Failed to create or access the awards channel in {guild.name}. The bot might not have the necessary permissions.")

async def ensure_awards_channel(guild):
    # Check if the awards channel exists
    channel = discord.utils.get(guild.text_channels, name='awards')
    
    if not channel:
        # Create the awards channel if it does not exist
        try:
            channel = await guild.create_text_channel('awards')
            print(f"Created 'awards' channel in {guild.name}")
        except discord.Forbidden:
            print(f"Cannot create 'awards' channel in {guild.name}. Missing permissions.")
            return
    else:
        print(f"Found 'awards' channel in {guild.name}")
    
    # Store the awards channel ID
    bot.awards_channels[guild.id] = channel.id

@bot.event
async def on_member_join(member):
    # Ensure awards channel exists when a new member joins
    if member.guild.id not in bot.awards_channels:
        await ensure_awards_channel(member.guild)

@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return
    message = reaction.message
    print(f"Reaction added: {reaction.emoji} by {user} on message: {message.id}")
    if message.id not in message_reactions:
        message_reactions[message.id] = {"message": message, "reaction_count": 0}
    message_reactions[message.id]["reaction_count"] += 1

def get_random_congratulatory_phrase() -> str:
    phrases = [
        "👏 **Well done!** 👏",
        "🌟 **Fantastic job!** 🌟",
        "🎉 **Awesome achievement! You’re a star!** 🎉",
        "🚀 **Amazing work!** 🚀",
        "🎊 **Keep making us proud!** 🎊",
        "✨ **Great job!** ✨",
        "💪 **You’re on fire!** 💪",
        "🎖 **Outstanding!** 🎖️",
        "🏆 **You’ve nailed it! Here’s to many more successes!** 🏆",
        "🌈 **Superb achievement!** 🌈",
        "🔥 **You’re unstoppable! Congratulations on your amazing achievement!** 🔥",
        "🌟 **Brilliant work!** 🌟",
        "🎯 **Your achievement is remarkable!** 🎯",
        "💫 **Exceptional job! You’re a true superstar!** 💫",
        "🥳 **You’ve outdone yourself! Keep up the great work!** 🥳"
    ]
    return random.choice(phrases)

def create_congratulatory_message(award_title: str, author: str, condition: str, additional_info: str) -> str:
    return f"""
🏅 **{award_title} Award!** 🏅

🎉 **Congratulations {author}!** 🎉

You’ve won the *{award_title}* award for {condition}! 🌟

{additional_info}

{get_random_congratulatory_phrase()}
"""

@tasks.loop(hours=8)
async def check_most_reacted_message():
    print("Checking for most reacted message...")
    one_week_ago = datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(weeks=1)
    top_message = None
    top_reaction_count = 0                      

    for message_id, data in message_reactions.items():
        message_created = data["message"].created_at
        print(f"Message ID: {message_id}, Created At: {message_created}, Reactions: {data['reaction_count']}")
        
        # Ensure message_created is timezone-aware
        if message_created.tzinfo is None:
            message_created = message_created.replace(tzinfo=timezone.utc)

        if message_created > one_week_ago and data["reaction_count"] > top_reaction_count:
            top_reaction_count = data["reaction_count"]
            top_message = data["message"]

    for guild in bot.guilds:
        channel_id = bot.awards_channels.get(guild.id)
        if channel_id:
            channel = guild.get_channel(channel_id)
            if channel:
                if top_message:
                    try:
                        title = "Emoji Magnet"
                        condition = "recieving the most amount of reactions on your message"

                        additional_info = (f"""📈 Reactions: {top_reaction_count} 📈
💬 Message: “{top_message.content}” 💬""")
                        congrats = create_congratulatory_message(title, top_message.author.mention, condition, additional_info)
                        
                        await channel.send(congrats)
                    except discord.Forbidden:
                        print(f"Cannot send message to 'awards' channel in {guild.name}. Missing permissions.")
                else:
                    try:
                        await channel.send("No top message found this week.")
                    except discord.Forbidden:
                        print(f"Cannot send message to 'awards' channel in {guild.name}. Missing permissions.")
            else:
                print(f"'awards' channel not found in {guild.name}.")
                await ensure_awards_channel(guild)
                channel_id = bot.awards_channels.get(guild.id)
                channel = guild.get_channel(channel_id)
                if channel:
                    try:
                        await channel.send("📢 Manually triggered award announcement!")
                    except discord.Forbidden:
                        print(f"Cannot send message to 'awards' channel in {guild.name}. Missing permissions.")
        else:
            print(f"'awards' channel not set up for {guild.name}.")
            await ensure_awards_channel(guild)
            channel_id = bot.awards_channels.get(guild.id)
            channel = guild.get_channel(channel_id)
            if channel:
                try:
                    await channel.send("📢 Manually triggered award announcement!")
                except discord.Forbidden:
                    print(f"Cannot send message to 'awards' channel in {guild.name}. Missing permissions.")

    message_reactions.clear()

@bot.tree.command(name="doaward", description="Trigger the award announcement")
async def doaward(interaction: discord.Interaction):
    if interaction.guild is None:
        await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
        return

    try:
        guild = interaction.guild
        member = guild.get_member(interaction.user.id)
        if member is None:
            member = await guild.fetch_member(interaction.user.id)
    except discord.NotFound:
        await interaction.response.send_message("Could not fetch member information. Please make sure the bot has the 'MEMBER' intent enabled and try again.", ephemeral=True)
        return
    except discord.Forbidden:
        await interaction.response.send_message("I don't have permission to fetch member information.", ephemeral=True)
        return
    except discord.HTTPException:
        await interaction.response.send_message("An error occurred while fetching member information.", ephemeral=True)
        return

    if not member.guild_permissions.administrator:
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return

    channel_id = bot.awards_channels.get(interaction.guild.id)
    if not channel_id:
        await ensure_awards_channel(interaction.guild)
        channel_id = bot.awards_channels.get(interaction.guild.id)
    
    if channel_id:
        channel = interaction.guild.get_channel(channel_id)
        if channel:
            try:
                await channel.send("📢 Manually triggered award announcement!")
                one_week_ago = datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(weeks=1)
                top_message = None
                top_reaction_count = 0

                for message_id, data in message_reactions.items():
                    message_created = data["message"].created_at
                    if message_created.tzinfo is None:
                        message_created = message_created.replace(tzinfo=timezone.utc)

                    if message_created > one_week_ago and data["reaction_count"] > top_reaction_count:
                        top_reaction_count = data["reaction_count"]
                        top_message = data["message"]

                if top_message:
                    await channel.send(f"🎉 Congratulations {top_message.author.mention} for having the most reacted message this week with {top_reaction_count} reactions! The message was: {top_message.content}")
                else:
                    await channel.send("No top message found this week.")
            except discord.Forbidden:
                await interaction.response.send_message("I don't have permission to send messages in the awards channel.", ephemeral=True)
        else:
            await interaction.response.send_message("The awards channel does not exist. Please try again later.", ephemeral=True)
    else:
        await interaction.response.send_message("Could not find or create the awards channel.", ephemeral=True)

    await interaction.response.send_message("Award announcement triggered successfully!")

# Load the bot token from token.txt
with open('token.txt', 'r') as file:
    token = file.read().strip()

bot.run(token)
