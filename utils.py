import random
import discord

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
    else:
        print(f"Found 'awards' channel in {guild.name}")
    
    # Store the awards channel ID
    bot.awards_channels[guild.id] = channel.id

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
