# main.py

import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta, timezone
from config import TOKEN
from utils import ensure_awards_channel, ensure_awards_channel_and_permissions, create_congratulatory_message
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
from flask import Flask, jsonify
from threading import Thread
import socket
import os

# Define Flask app
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

@app.route('/status')
def status():
    return jsonify({"status": "Bot is running", "bot_name": bot.user.name})

def get_flask_url():
    # Get the Flask app URL from the environment or use a default
    port = os.getenv('PORT', 3000)
    hostname = socket.gethostname()
    url = f'http://{hostname}:{port}'
    return url

def run_flask():
    url = get_flask_url()
    print(f"Flask app is running at: {url}")
    app.run(host='0.0.0.0', port=3000)

# Define intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True
intents.reactions = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

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

        # Track link count for "Nigerian Prince" award
        if re.search(r'http[s]?://', message.content):
            if message.author.id not in link_counts:
                link_counts[message.author.id] = 0
            link_counts[message.author.id] += 1
            print(f"User {message.author.id} has sent {link_counts[message.author.id]} links.")

        # Track tag count for "I am Him/Her" award
        for user in message.mentions:
            user_id = user.id
            if user_id not in tag_counts:
                tag_counts[user_id] = 0
            tag_counts[user_id] += 1
            print(f"User {user_id} has been tagged {tag_counts[user_id]} times.")

        # Track image count for "Photographer" award
        if message.attachments:
            user_id = message.author.id
            if user_id not in image_counts:
                image_counts[user_id] = 0
            image_counts[user_id] += 1
            print(f"User {user_id} has posted {image_counts[user_id]} images.")

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

    # Track reactions added by users for "React-ive" award
    if user.id not in user_reaction_counts:
        user_reaction_counts[user.id] = 0
    user_reaction_counts[user.id] += 1
    print(f"User {user.id} has added {user_reaction_counts[user.id]} reactions.")

@tasks.loop(seconds=TASK_INTERVAL)
async def check_awards():
    print("Checking for awards...")   
    top_message = None
    top_reaction_count = 0
    
    longest_message = None
    max_length = 0
    
    most_messages_user = None
    most_messages_count = 0
    
    most_edits_user = None
    most_edits_count = 0

    most_links_user = None
    most_links_count = 0

    most_reactions_user = None
    most_reactions_count = 0
    
    most_tagged_user = None
    most_tagged_count = 0
    
    most_images_user = None
    most_images_count = 0

    one_week_ago = datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(weeks=1)

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

    # Determine the user with the most links sent for "Nigerian Prince" award
    for user_id, count in link_counts.items():
        print(f"User {user_id} has sent {count} links.")
        if count > most_links_count:
            most_links_count = count
            most_links_user = user_id

    # Determine the user with the most reactions given for "React-ive" award
    for user_id, count in user_reaction_counts.items():
        print(f"User {user_id} has given {count} reactions.")
        if count > most_reactions_count:
            most_reactions_count = count
            most_reactions_user = user_id

    # I am Him/Her Award (Most Tagged)
    for user_id, count in tag_counts.items():  # Assuming tag_counts dictionary
        print(f"User {user_id} was tagged {count} times.")
        if count > most_tagged_count:
            most_tagged_count = count
            most_tagged_user = user_id

    # Photographer Award (Most Images Posted)
    for user_id, count in image_counts.items():  # Assuming image_counts dictionary
        print(f"User {user_id} posted {count} images.")
        if count > most_images_count:
            most_images_count = count
            most_images_user = user_id

    # Notify guilds about the awards
    for guild in bot.guilds:
        # Emoji Magnet Award
        if top_message:
            title = "Emoji Magnet"
            condition = "receiving the most reactions on your message"
            additional_info = f"""{top_message.content} 📈 Reactions: {top_reaction_count}"""
            congrats = create_congratulatory_message(title, top_message.author.mention, condition, additional_info)
            await send_message_to_awards_channel(guild, congrats)
        else:
            print(f"No top message found this week.")

        await asyncio.sleep(AWARD_DISPLAY_DELAY)

        # Waffle Maker Award
        if longest_message:
            title = "Waffle Maker"
            condition = "sending the longest message"
            additional_info = f"""{longest_message.content} 📏 Length: {max_length} characters"""
            congrats = create_congratulatory_message(title, longest_message.author.mention, condition, additional_info)
            await send_message_to_awards_channel(guild, congrats)
        else:
            print(f"No message found with the longest length this week.")

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
            else:
               print(f"No user found with the most messages this week.")
        else:
            print(f"No messages found for Fluent in Yapanese award this week.")

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
            else:
                print(f"No user found with the most edits this week.")
        else:
            print(f"No edits found for the Autocorrect Victim award this week.")

        await asyncio.sleep(AWARD_DISPLAY_DELAY)

        # Nigerian Prince Award
        if most_links_user:
            member = guild.get_member(most_links_user)
            if member:
                title = "Nigerian Prince"
                condition = "sending the most links"
                additional_info = f"Links sent: {most_links_count}"
                congrats = create_congratulatory_message(title, member.mention, condition, additional_info)
                await send_message_to_awards_channel(guild, congrats)
            else:
                print(f"No user found with the most links this week.")
        else:
            print(f"No messages found for Nigerian Prince award this week.")

        await asyncio.sleep(AWARD_DISPLAY_DELAY)

        # React-ive Award
        if most_reactions_user:
            member = guild.get_member(most_reactions_user)
            if member:
                title = "React-ive"
                condition = "sending the most reactions on messages"
                additional_info = f"Reactions given: {most_reactions_count}"
                congrats = create_congratulatory_message(title, member.mention, condition, additional_info)
                await send_message_to_awards_channel(guild, congrats)
            else:
                print(f"No user found with the most reactions given this week.")
        else:
            print(f"No reactions found for React-ive award this week.")

        await asyncio.sleep(AWARD_DISPLAY_DELAY)

        # I am Him/Her Award
        if most_tagged_user:
            member = guild.get_member(most_tagged_user)
            if member:
                title = "I am Him/Her"
                condition = "being tagged the most"
                additional_info = f"Times tagged: {most_tagged_count}"
                congrats = create_congratulatory_message(title, member.mention, condition, additional_info)
                await send_message_to_awards_channel(guild, congrats)
            else:
                print(f"No user found with the HIM/HER award given this week.")
        else:
            print(f"No reactions found for HIM/HER award  this week.")

        await asyncio.sleep(AWARD_DISPLAY_DELAY)

        # Photographer Award
        if most_images_user:
            member = guild.get_member(most_images_user)
            if member:
                title = "Photographer"
                condition = "posting the most images"
                additional_info = f"Images posted: {most_images_count}"
                congrats = create_congratulatory_message(title, member.mention, condition, additional_info)
                await send_message_to_awards_channel(guild, congrats)
            else:
                print(f"No user found with the Photographer award given this week.")
        else:
            print(f"No reactions found for Photographer award  this week.")

        await asyncio.sleep(AWARD_DISPLAY_DELAY)

    message_reactions.clear()
    message_lengths.clear()
    message_counts.clear()
    edit_counts.clear()
    link_counts.clear()
    user_reaction_counts.clear()
    tag_counts.clear()
    image_counts.clear()

# Run Flask in a separate thread
flask_thread = Thread(target=run_flask)
flask_thread.start()

# Run the bot
if TOKEN:
    bot.run(TOKEN)
else:
    print("Bot token not found. Please ensure the token.txt file exists and contains a valid token.")
