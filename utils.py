import random
import discord
from shared import awards_channels

async def ensure_awards_channel_and_permissions(guild, bot):
    """Ensure the awards channel exists and has proper permissions."""
    await ensure_awards_channel(guild, bot)
    channel_id = awards_channels.get(guild.id)
    if channel_id:
        channel = guild.get_channel(channel_id)
        if channel:
            # Update channel permissions to allow only the bot to send messages
            perms = discord.PermissionOverwrite()
            perms.send_messages = True
            perms.read_messages = True

            # Deny permissions for @everyone and other members
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(send_messages=False, read_messages=True),
                bot.user: perms
            }
            try:
                await channel.edit(overwrites=overwrites)
                print(f"Updated permissions for 'awards' channel in {guild.name}.")
            except discord.Forbidden:
                print(f"Cannot edit 'awards' channel permissions in {guild.name}. Missing permissions.")
            except discord.HTTPException as e:
                print(f"Failed to update 'awards' channel permissions in {guild.name}. HTTPException: {e}")
        else:
            print(f"'awards' channel not found in {guild.name}.")
    else:
        print(f"'awards' channel not set up for {guild.name}.")

async def ensure_awards_channel(guild, bot):
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
        except discord.HTTPException as e:
            print(f"Failed to create 'awards' channel in {guild.name}. HTTPException: {e}")
    else:
        print(f"Found 'awards' channel in {guild.name}")
    
    # Store the awards channel ID
    awards_channels[guild.id] = channel.id

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
