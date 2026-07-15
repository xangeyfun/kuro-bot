from discord import app_commands, Interaction
from discord.ext import commands, tasks
from dotenv import load_dotenv
import discord
import asyncio
import time
import json
import os

load_dotenv()
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents, status=discord.Status.online, activity=discord.Activity(type=discord.ActivityType.watching, name="Type / for commands"))
TOKEN = os.getenv("TOKEN") or ""
guild = discord.Object(id=int(os.getenv("GUILD_ID") or 0))
vote_active = False

if not os.path.exists("data.json") or os.stat("data.json").st_size == 0:
    with open("data.json", "w") as f:
        json.dump({
            "cooldowns": {},
            "active_crazy": {}
        }, f)

if os.path.exists("banned_ids.json"):
    with open("banned_ids.json", "r") as f:
        banned_ids = json.load(f)
else:
    with open("banned_ids.json", "w") as f:
        json.dump([], f)
    banned_ids = []

# Helpers

def load_data():
    with open("data.json", "r") as f:
        return json.load(f)
    
def save_data(data):
    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} ({bot.user.id})") # type: ignore
    try:
        synced = await bot.tree.sync(guild=guild)
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(f"Error syncing commands: {e}")

    if not check_crazy.is_running():
        check_crazy.start()

@app_commands.allowed_installs(guilds=True, users=False)
@app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
@bot.tree.command(name="vote", description="Vote for someone to go to the padded room", guild=guild)
async def vote(interaction: Interaction, member: discord.Member):
    data = load_data()
    cooldown = data["cooldowns"]

    if str(interaction.user.id) in cooldown and time.time() - cooldown[str(interaction.user.id)] < 900:
        await interaction.response.send_message("You can only vote once every 15 minutes.", ephemeral=True)
        return

    if interaction.user.id == member.id:
        await interaction.response.send_message("You cannot vote for yourself.", ephemeral=True)
        return

    if len(data["active_crazy"]):
        await interaction.response.send_message(f"There is already someone in the padded room. You cannot start a new vote until they are released. (<t:{round(data['active_crazy'][list(data['active_crazy'].keys())[0]])}:R>)", ephemeral=True)
        return

    global vote_active
    if vote_active:
        await interaction.response.send_message(f"There is already an active vote. Please wait until it is finished.", ephemeral=True)
        return 

    if not isinstance(interaction.channel, discord.TextChannel):
        await interaction.response.send_message("This command can only be used in text channels.", ephemeral=True)
        return

    vote_active = True
    try:
        data["cooldowns"][str(interaction.user.id)] = time.time()
        save_data(data)

        await interaction.response.send_message(f"Vote started for {member.mention}. Check the channel for the voting message.", ephemeral=True)
        padded_channel = bot.get_channel(1526952092462219284)
        if isinstance(padded_channel, discord.TextChannel):
            mention = padded_channel.mention
        message = await interaction.channel.send(f"{interaction.user.mention} has started a vote to send {member.mention} to {mention}!\nReact with 👍 to vote yes or 👎 to vote no. You have <t:{round(time.time()) + 60}:R> left to vote.", delete_after=70)

        await message.add_reaction("👍")
        await message.add_reaction("👎")

        await asyncio.sleep(60)

        message = await interaction.channel.fetch_message(message.id)

        yes_votes = 0
        no_votes = 0

        for reaction in message.reactions:
            if reaction.emoji == "👍":
                yes_votes = reaction.count - 1 
            elif reaction.emoji == "👎":
                no_votes = reaction.count - 1

        if yes_votes > no_votes:
            await interaction.channel.send(f"**{yes_votes}** people voted to send {member.mention} to {mention}! They will be released in <t:{round(time.time()) + 300}:R>.", delete_after=310)
            data["active_crazy"][str(member.id)] = time.time() + 300
            role = interaction.guild.get_role(1526950301066858587) # type: ignore
            if role:
                await member.add_roles(role)
                channel = bot.get_channel(1526952092462219284) # type: ignore
                if channel and isinstance(channel, discord.TextChannel):
                    await channel.send(f"{member.mention} You have been sent to the padded room.\nYou will be released in <t:{round(time.time()) + 300}:R>.", delete_after=310)
            save_data(data)
        else:
            await interaction.channel.send(f"{member.mention} has not been sent to {mention}.", delete_after=10)
            save_data(data)

    finally:
        vote_active = False

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.stickers:
        if "https://cdn.discordapp.com/stickers/1488531621996134430.png" in [sticker.url for sticker in message.stickers] and message.author.id not in banned_ids:
            await message.add_reaction("❓")
            await message.channel.send("<@&1488533311776227469>")
            
        if "https://cdn.discordapp.com/stickers/1488531621996134430.png" in [sticker.url for sticker in message.stickers] and message.author.id in banned_ids:
            await message.delete()
            await message.author.send(f"<@{message.author.id}> You have been banned from using the sticker for repeatedly spamming it. If you think this is a mistake, please DM the admins")

    await bot.process_commands(message)

@tasks.loop(seconds=5)
async def check_crazy():
    data = load_data()
    active_crazy = data["active_crazy"]
    current_time = time.time()
    changed = False

    for user in list(active_crazy):
        if current_time >= active_crazy[user]:
            guild = bot.get_guild(int(os.getenv("GUILD_ID") or 0))
            member = guild.get_member(int(user)) if guild else None
            if member:
                role = guild.get_role(1526950301066858587) # type: ignore
                if role:
                    await member.remove_roles(role)
                    channel = guild.get_channel(1487803812373725296) # type: ignore
                    if channel and isinstance(channel, discord.TextChannel):
                        await channel.send(f"{member.mention} has been released from the padded room.", delete_after=10)
            del active_crazy[user]
            changed = True
    if changed:
        save_data(data)

if __name__ == "__main__":
    bot.run(TOKEN)