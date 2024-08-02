import discord
from discord import app_commands
from discord.ext import commands
from utils import ensure_awards_channel, create_congratulatory_message

def setup_commands(bot):
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
            await ensure_awards_channel(interaction.guild, bot)
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
