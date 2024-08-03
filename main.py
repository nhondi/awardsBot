# main.py

import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta, timezone
from config import TOKEN
from utils import ensure_awards_channel, ensure_awards_channel_and_permissions, create_congratulatory_message
from shared import message_reactions, message_lengths, awards_channels, message_counts, edit_counts
import asyncio

# Define intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True
intents.reactions = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Define the interval for task loops
TASK_INTERVAL = 15  # in seconds
AWARD_DISPLAY_DELAY = 2  # delay between displaying awards in seconds

async def send_message_to_awards_channel(guild, message_content):
    await ensure_awards_channel_and_permissions(guild, bot)
    channel_id = awards_channels.get(guild.id)
    if channel_id:
        channel = guild.get_channel(channel_id)
        if channel:
            try:
                await channel.send(message_content)
            except discord.Forbidden:
                print(f"Cannot send message to 'awards' channel in {guild.name}. Missing permissions.")
            except discord.HTTPException as e:
                print(f"Failed to send message to 'awards' channel in {guild.name}. HTTPException: {e}")
        else:
            print(f"'awards' channel not found in {guild.name}.")
            await ensure_awards_channel_and_permissions(guild, bot)
            channel_id = awards_channels.get(guild.id)
            channel = guild.get_channel(channel_id)
            if channel:
                try:
                    await channel.send(message_content)
                except discord.Forbidden:
                    print(f"Cannot send message to 'awards' channel in {guild.name}. Missing permissions.")
                except discord.HTTPException as e:
                    print(f"Failed to send message to 'awards' channel in {guild.name}. HTTPException: {e}")
    else:
        print(f"'awards' channel not set up for {guild.name}.")
        await ensure_awards_channel_and_permissions(guild, bot)
        channel_id = awards_channels.get(guild.id)
        channel = guild.get_channel(channel_id)
        if channel:
            try:
                await channel.send(message_content)
            except discord.Forbidden:
                print(f"Cannot send message to 'awards' channel in {guild.name}. Missing permissions.")
            except discord.HTTPException as e:
                print(f"Failed to send message to 'awards' channel in {guild.name}. HTTPException: {e}")

async def send_update_message():
    for guild in bot.guilds:
        await send_message_to_awards_channel(guild, f"The bot '{bot.user.name}' has been updated!")

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    print("Bot is online.")
    await bot.tree.sync()  # Sync application commands
    print("Application commands synced.")
    await send_update_message()  # Send the update message when bot starts
    check_awards.start()

@bot.event
async def on_guild_join(guild):
    print(f"Joined new guild: {guild.name}")
    await ensure_awards_channel_and_permissions(guild, bot)

@bot.event
async def on_member_join(member):
    if member.guild.id not in awards_channels:
        await ensure_awards_channel_and_permissions(member.guild, bot)
        
@bot.event
async def on_message(message):
    # Skip messages from bots
    if message.author.bot:
        return

    guild_id = message.guild.id if message.guild else None
    awards_channel_id = awards_channels.get(guild_id)
    
    # Track messages in all channels except the awards channel
    if guild_id and message.channel.id != awards_channel_id:
        if message.id not in message_lengths:
            message_lengths[message.id] = {"message": message, "length": len(message.content)}

        # Track message count for "Fluent in Yapanese" award
        if message.author.id not in message_counts:
            message_counts[message.author.id] = 0
        message_counts[message.author.id] += 1
        print(f"User {message.author.id} has sent {message_counts[message.author.id]} messages.")

    await bot.process_commands(message)  # Ensure commands are still processed

@bot.event
async def on_message_edit(before, after):
    if before.author.bot:
        return

    guild_id = before.guild.id if before.guild else None
    if guild_id and before.id != awards_channels.get(guild_id):
        if before.author.id not in edit_counts:
            edit_counts[before.author.id] = 0
        edit_counts[before.author.id] += 1
        print(f"User {before.author.id} has edited a message. Total edits: {edit_counts[before.author.id]}")

@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return
    message = reaction.message
    print(f"Reaction added: {reaction.emoji} by {user} on message: {message.id}")
    if message.id not in message_reactions:
        message_reactions[message.id] = {"message": message, "reaction_count": 0}
    message_reactions[message.id]["reaction_count"] += 1

@tasks.loop(seconds=TASK_INTERVAL)
async def check_awards():
    print("Checking for awards...")
    one_week_ago = datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(weeks=1)
    
    top_message = None
    top_reaction_count = 0
    
    longest_message = None
    max_length = 0
    
    most_messages_user = None
    most_messages_count = 0
    
    most_edits_user = None
    most_edits_count = 0

    # Check messages for both criteria
    for message_id, data in message_reactions.items():
        message_created = data["message"].created_at
        print(f"Message ID: {message_id}, Created At: {message_created}, Reactions: {data['reaction_count']}")
        
        if message_created.tzinfo is None:
            message_created = message_created.replace(tzinfo=timezone.utc)

        if message_created > one_week_ago:
            if data["reaction_count"] > top_reaction_count:
                top_reaction_count = data["reaction_count"]
                top_message = data["message"]

    for message_id, data in message_lengths.items():
        message_created = data["message"].created_at
        print(f"Message ID: {message_id}, Created At: {message_created}, Length: {data['length']}")
        
        if message_created.tzinfo is None:
            message_created = message_created.replace(tzinfo=timezone.utc)

        if message_created > one_week_ago and data["length"] > max_length:
            max_length = data["length"]
            longest_message = data["message"]

    # Determine the user with the most messages for "Fluent in Yapanese" award
    for user_id, count in message_counts.items():
        print(f"User {user_id} has sent {count} messages.")
        if count > most_messages_count:
            most_messages_count = count
            most_messages_user = user_id

    # Determine the user with the most edits for "Autocorrect Victim" award
    for user_id, count in edit_counts.items():
        print(f"User {user_id} has edited messages {count} times.")
        if count > most_edits_count:
            most_edits_count = count
            most_edits_user = user_id

    # Notify guilds about the awards
    for guild in bot.guilds:
        # Emoji Magnet Award
        if top_message:
            title = "Emoji Magnet"
            condition = "receiving the most reactions on your message"
            additional_info = f"""{top_message.content} 📈 Reactions: {top_reaction_count}"""
            congrats = create_congratulatory_message(title, top_message.author.mention, condition, additional_info)
            await send_message_to_awards_channel(guild, congrats)
            await asyncio.sleep(AWARD_DISPLAY_DELAY)
        else:
            await send_message_to_awards_channel(guild, "No top message found this week.")
            await asyncio.sleep(AWARD_DISPLAY_DELAY)

        # Waffle Maker Award
        if longest_message:
            title = "Waffle Maker"
            condition = "sending the longest message"
            additional_info = f"""{longest_message.content} 📏 Length: {max_length} characters"""
            congrats = create_congratulatory_message(title, longest_message.author.mention, condition, additional_info)
            await send_message_to_awards_channel(guild, congrats)
            await asyncio.sleep(AWARD_DISPLAY_DELAY)
        else:
            await send_message_to_awards_channel(guild, "No message found with the longest length this week.")
            await asyncio.sleep(AWARD_DISPLAY_DELAY)

        # Fluent in Yapanese Award
        if most_messages_user:
            member = guild.get_member(most_messages_user)
            if member:
                title = "Fluent in Yapanese"
                condition = "sending the most messages"
                additional_info = f"Messages sent: {most_messages_count}"
                congrats = create_congratulatory_message(title, member.mention, condition, additional_info)
                await send_message_to_awards_channel(guild, congrats)
                await asyncio.sleep(AWARD_DISPLAY_DELAY)
            else:
                await send_message_to_awards_channel(guild, "No user found with the most messages this week.")
                await asyncio.sleep(AWARD_DISPLAY_DELAY)
        else:
            await send_message_to_awards_channel(guild, "No messages found for Fluent in Yapanese award this week.")
            await asyncio.sleep(AWARD_DISPLAY_DELAY)

        # Autocorrect Victim Award
        if most_edits_user:
            member = guild.get_member(most_edits_user)
            if member:
                title = "Autocorrect Victim"
                condition = "editing the most messages"
                additional_info = f"Total edits: {most_edits_count}"
                congrats = create_congratulatory_message(title, member.mention, condition, additional_info)
                await send_message_to_awards_channel(guild, congrats)
                await asyncio.sleep(AWARD_DISPLAY_DELAY)
            else:
                await send_message_to_awards_channel(guild, "No user found with the most edits this week.")
                await asyncio.sleep(AWARD_DISPLAY_DELAY)
        else:
            await send_message_to_awards_channel(guild, "No edits found for the Autocorrect Victim award this week.")
            await asyncio.sleep(AWARD_DISPLAY_DELAY)

    message_reactions.clear()
    message_lengths.clear()
    message_counts.clear()
    edit_counts.clear()

# Run the bot
if TOKEN:
    bot.run(TOKEN)
else:
    print("Bot token not found. Please ensure the token.txt file exists and contains a valid token.")
