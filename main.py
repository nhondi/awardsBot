# main.py

import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta, timezone
from config import TOKEN
from utils import ensure_awards_channel_and_permissions, create_congratulatory_message
from shared import (
    message_reactions,
    message_lengths,
    awards_channels,
    message_counts,
    edit_counts,
    link_counts,
    user_reaction_counts,
    tag_counts,
    image_counts
)
from constants import TASK_INTERVAL, AWARD_DISPLAY_DELAY
import asyncio
import re

# Define intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True
intents.reactions = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

async def send_message_to_awards_channel(guild, message_content):
    """
    Sends a message to the awards channel of the specified guild.
    Ensures the bot has permissions and the channel exists.
    """
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
    else:
        print(f"'awards' channel not set up for {guild.name}.")

async def send_update_message():
    """
    Sends an update message to the awards channel in all guilds.
    """
    print(f"The bot '{bot.user.name}' has been updated!")
    #for guild in bot.guilds:
        #await send_message_to_awards_channel(guild, f"The bot '{bot.user.name}' has been updated!")

@bot.event
async def on_ready():
    """
    Event triggered when the bot is ready.
    Initializes and starts tasks.
    """
    print(f'Logged in as {bot.user.name}')
    print("Bot is online.")
    await bot.tree.sync()
    print("Application commands synced.")
    await send_update_message()
    check_awards.start()
    activityCheck.start()

@bot.event
async def on_guild_join(guild):
    """
    Event triggered when the bot joins a new guild.
    Ensures the awards channel and permissions are set up.
    """
    print(f"Joined new guild: {guild.name}")
    await ensure_awards_channel_and_permissions(guild, bot)

@bot.event
async def on_member_join(member):
    """
    Event triggered when a new member joins a guild.
    Ensures the awards channel and permissions are set up.
    """
    if member.guild.id not in awards_channels:
        await ensure_awards_channel_and_permissions(member.guild, bot)

@bot.event
async def on_message(message):
    """
    Event triggered when a message is sent in any channel.
    Tracks messages, links, tags, and images for awards.
    """
    if message.author.bot:
        return

    guild_id = message.guild.id if message.guild else None
    awards_channel_id = awards_channels.get(guild_id)

    if guild_id and message.channel.id != awards_channel_id:
        # Track message length
        if message.id not in message_lengths:
            message_lengths[message.id] = {"message": message, "length": len(message.content)}

        # Track message count
        message_counts[message.author.id] = message_counts.get(message.author.id, 0) + 1
        print(f"User {message.author.id} has sent {message_counts[message.author.id]} messages.")

        # Track link count
        if re.search(r'http[s]?://', message.content):
            link_counts[message.author.id] = link_counts.get(message.author.id, 0) + 1
            print(f"User {message.author.id} has sent {link_counts[message.author.id]} links.")

        # Track tag count
        for user in message.mentions:
            tag_counts[user.id] = tag_counts.get(user.id, 0) + 1
            print(f"User {user.id} has been tagged {tag_counts[user.id]} times.")

        # Track image count
        if message.attachments:
            image_counts[message.author.id] = image_counts.get(message.author.id, 0) + 1
            print(f"User {message.author.id} has posted {image_counts[message.author.id]} images.")

    await bot.process_commands(message)

@bot.event
async def on_message_edit(before, after):
    """
    Event triggered when a message is edited.
    Tracks the number of message edits for awards.
    """
    if before.author.bot:
        return

    guild_id = before.guild.id if before.guild else None
    if guild_id and before.id != awards_channels.get(guild_id):
        edit_counts[before.author.id] = edit_counts.get(before.author.id, 0) + 1
        print(f"User {before.author.id} has edited a message. Total edits: {edit_counts[before.author.id]}")

@bot.event
async def on_reaction_add(reaction, user):
    """
    Event triggered when a reaction is added to a message.
    Tracks reactions added and updates reaction counts.
    """
    if user.bot:
        return

    message = reaction.message
    print(f"Reaction added: {reaction.emoji} by {user} on message: {message.id}")

    if message.id not in message_reactions:
        message_reactions[message.id] = {"message": message, "reaction_count": 0}
    message_reactions[message.id]["reaction_count"] += 1

    # Track reactions added by users
    user_reaction_counts[user.id] = user_reaction_counts.get(user.id, 0) + 1
    print(f"User {user.id} has added {user_reaction_counts[user.id]} reactions.")

@tasks.loop(minutes=1)
async def activityCheck():
    """
    Task loop that prints a status message every minute.
    """
    print("Bot Alive and Active")

@tasks.loop(seconds=TASK_INTERVAL)
async def check_awards():
    """
    Task loop that checks and updates awards based on user activity.
    """
    print("Checking for awards...")
    one_week_ago = datetime.now(timezone.utc) - timedelta(weeks=1)

    awards_data = {
        "top_message": {"message": None, "reaction_count": 0},
        "longest_message": {"message": None, "length": 0},
        "most_messages_user": {"user_id": None, "count": 0},
        "most_edits_user": {"user_id": None, "count": 0},
        "most_links_user": {"user_id": None, "count": 0},
        "most_reactions_user": {"user_id": None, "count": 0},
        "most_tagged_user": {"user_id": None, "count": 0},
        "most_images_user": {"user_id": None, "count": 0},
    }

    # Check message reactions
    for message_id, data in message_reactions.items():
        if data["message"].created_at > one_week_ago:
            if data["reaction_count"] > awards_data["top_message"]["reaction_count"]:
                awards_data["top_message"] = {"message": data["message"], "reaction_count": data["reaction_count"]}

    # Check message lengths
    for message_id, data in message_lengths.items():
        if data["message"].created_at > one_week_ago:
            if data["length"] > awards_data["longest_message"]["length"]:
                awards_data["longest_message"] = {"message": data["message"], "length": data["length"]}

    # Determine the top users for various awards
    for user_id, count in message_counts.items():
        if count > awards_data["most_messages_user"]["count"]:
            awards_data["most_messages_user"] = {"user_id": user_id, "count": count}

    for user_id, count in edit_counts.items():
        if count > awards_data["most_edits_user"]["count"]:
            awards_data["most_edits_user"] = {"user_id": user_id, "count": count}

    for user_id, count in link_counts.items():
        if count > awards_data["most_links_user"]["count"]:
            awards_data["most_links_user"] = {"user_id": user_id, "count": count}

    for user_id, count in user_reaction_counts.items():
        if count > awards_data["most_reactions_user"]["count"]:
            awards_data["most_reactions_user"] = {"user_id": user_id, "count": count}

    for user_id, count in tag_counts.items():
        if count > awards_data["most_tagged_user"]["count"]:
            awards_data["most_tagged_user"] = {"user_id": user_id, "count": count}

    for user_id, count in image_counts.items():
        if count > awards_data["most_images_user"]["count"]:
            awards_data["most_images_user"] = {"user_id": user_id, "count": count}

    # Notify guilds about the awards
    for guild in bot.guilds:
        for award_name, award_info in awards_data.items():
            if (award_info.get("message") or award_info.get("user_id") is not None):
                title = {
                    "top_message": "Emoji Magnet",
                    "longest_message": "Waffle Maker",
                    "most_messages_user": "Fluent in Yapanese",
                    "most_edits_user": "Autocorrect Victim",
                    "most_links_user": "Nigerian Prince",
                    "most_reactions_user": "React-ive",
                    "most_tagged_user": "I am Him/Her",
                    "most_images_user": "Photographer",
                }[award_name]

                condition = {
                    "top_message": "receiving the most reactions on your message",
                    "longest_message": "sending the longest message",
                    "most_messages_user": "sending the most messages",
                    "most_edits_user": "editing the most messages",
                    "most_links_user": "sending the most links",
                    "most_reactions_user": "sending the most reactions on messages",
                    "most_tagged_user": "being tagged the most",
                    "most_images_user": "posting the most images",
                }[award_name]

                additional_info = (
                    f"{award_info.get('message').content} 📈 Reactions: {award_info.get('reaction_count')}"
                    if award_name in {"top_message"}
                    else f"{award_info.get('message').content} 📏 Length: {award_info.get('length')} characters"
                    if award_name in {"longest_message"}
                    else f"{condition}: {award_info.get('count')}"
                )

                member = guild.get_member(award_info.get("user_id")) if award_info.get("user_id") else None
                congrats = create_congratulatory_message(title, member.mention if member else "Everyone", condition, additional_info)
                await send_message_to_awards_channel(guild, congrats)
                await asyncio.sleep(AWARD_DISPLAY_DELAY)

    # Clear tracked data
    message_reactions.clear()
    message_lengths.clear()
    message_counts.clear()
    edit_counts.clear()
    link_counts.clear()
    user_reaction_counts.clear()
    tag_counts.clear()
    image_counts.clear()

# Run the bot
if TOKEN:
    bot.run(TOKEN)
else:
    print("Bot token not found. Please ensure the TOKEN is set.")
