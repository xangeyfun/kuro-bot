from discord import app_commands, Interaction
from discord.ext import commands, tasks
from dotenv import load_dotenv
import discord
import asyncio
import time
import json
import os
import random
import re

load_dotenv()
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents, status=discord.Status.online, activity=discord.Activity(type=discord.ActivityType.watching, name="Type / for commands"))
TOKEN = os.getenv("TOKEN") or ""
meow = re.compile(r"^(m+e+o+w+|m+r+o+w+|n+y+a+)\s*~*\s*[.!?]*\s*(:3+)?$", re.IGNORECASE)
woof = re.compile(r"^(w+o+f+|b+a+r+k+|a+r+f+|r+u+f+|a+w+o+)\s*~*\s*[.!?]*\s*(:3+)?$", re.IGNORECASE)
vote_active = False

meow_responses = [
    "Meow! 🐱",
    "Mew! 🐱",
    "Mrow! 🐱",
    "Mrrp! 🐱",
    "Mrrr! 🐱",
    "Purr... 🐱",
    "Purrr... 🐱",
    "meow :3 🐱",
    "mrow :3",
    "mrrp :3",
    "meow meow!! 🐱",
    "meow meow meow! 🐱",
    "MEOOOOW!!! 🐱",
    "MEEEOOOOW!!! 🐱",
    "MEOW!!!",
    "MEEEEOW!!! 🐱",
    "Mrrrrowww! 🐱",
    "Mrrr... meow.",
    "*meows* 🐱",
    "M E O W 🐱",
    "m e o w :3",
    "meow? 🐱",
    "meow!!! :3",
    "meow :333 🐱",
    "mrowwww :3",
    "mrrrp! :3",
    "prrrrrr 🐱",
    "prrrt! 🐱",
    "nya! 🐱",
    "nyaa~ 🐱",
    "nyaa :3",
    "Nya! 🐱",
    "Nyaa~ 🐱",
    "Mew mew! 🐱",
    "Mrow mrow! 🐱",
]

woof_responses = [
    "Woof! 🐶",
    "Bark! 🐶",
    "Arf! 🐶",
    "Ruff! 🐶",
    "Wruff! 🐶",
    "Awoof! 🐶",
    "woof :3 🐶",
    "arf :3",
    "woof woof!! 🐶",
    "WOOF!!! 🐶",
    "WOOOOOOF!!! 🐶",
    "*woofs* 🐶",
    "W O O F 🐶",
    "w o o f :3",
    "woof? 🐶",
    "woof!!! :3",
    "woof :333 🐶",
    "ruff ruff! 🐶",
    "arf arf! 🐶",
    "AWOOOOOO! 🐶",
    "Awooo! 🐶",
    "Awooo :3 🐶",
]

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
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(f"Error syncing commands: {e}")

    if not check_crazy.is_running():
        check_crazy.start()

@bot.event
async def on_interaction(interaction: Interaction):
    if interaction.type == discord.InteractionType.application_command:
        print(f"Command '/{interaction.data['name']}' invoked by '{interaction.user}' in '{interaction.guild}' (ID: {interaction.guild_id})")
    elif interaction.type == discord.InteractionType.component:
        print(f"Component interaction invoked by '{interaction.user}' in '{interaction.guild}' (ID: {interaction.guild_id})")

@app_commands.allowed_installs(guilds=True, users=False)
@app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
@bot.tree.command(name="ping", description="Check the bot's latency") #, guild=guild)
async def ping(interaction: Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f"Pong! Latency: {latency}ms", ephemeral=True)

@app_commands.allowed_installs(guilds=True, users=False)
@app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
@bot.tree.command(name="github", description="Get the bot's GitHub repository link") #, guild=guild)
async def github(interaction: Interaction):
    await interaction.response.send_message("You can find the bot's source code on GitHub:\nhttps://github.com/xangeyfun/kuro-bot", ephemeral=True)

@app_commands.allowed_installs(guilds=True, users=False)
@app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
@bot.tree.command(name="throw", description="Throw an item into the padded room") #, guild=guild)
async def throw(interaction: Interaction, item: str):
    if interaction.guild and interaction.guild.id != 1487803811178352832:
        await interaction.response.send_message("Sorry, you cannot use that here! This command is only available at:\n- https://discord.gg/MhBG6fgPmS", ephemeral=True)
        return

    data = load_data()

    if str(interaction.user.id) in data["active_crazy"]:
        await interaction.response.send_message("You are currently in the padded room and cannot throw items.", ephemeral=True)
        return
    
    if len(data["active_crazy"]) == 0:
        await interaction.response.send_message("There is no one in the padded room to throw items at.", ephemeral=True)
        return

    padded_channel = bot.get_channel(1526952092462219284)
    if isinstance(padded_channel, discord.TextChannel):
        await padded_channel.send(f"{interaction.user.mention} has thrown **{item}** into the padded room!", allowed_mentions=discord.AllowedMentions(users=[interaction.user], roles=False, everyone=False))
        await interaction.response.send_message(f"You have thrown **{item}** into the padded room.", ephemeral=True)
    else:
        await interaction.response.send_message("The padded room channel could not be found.", ephemeral=True)

@app_commands.allowed_installs(guilds=True, users=False)
@app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
@bot.tree.command(name="vote", description="Vote for someone to go to the padded room") #, guild=guild)
async def vote(interaction: Interaction, member: discord.Member):
    if interaction.guild and interaction.guild.id != 1487803811178352832:
        await interaction.response.send_message("Sorry, you cannot use that here! This command is only available at:\n- https://discord.gg/MhBG6fgPmS", ephemeral=True)
        return

    if not isinstance(interaction.channel, discord.TextChannel):
        await interaction.response.send_message("This command can only be used in text channels.", ephemeral=True)
        return

    if interaction.user.id == member.id:
        await interaction.response.send_message("You cannot vote for yourself.", ephemeral=True)
        return

    if member.bot:
        await interaction.response.send_message("You cannot vote for a bot.", ephemeral=True)
        return

    global vote_active
    if vote_active:
        await interaction.response.send_message(f"There is already an active vote. Please wait until it is finished.", ephemeral=True)
        return 

    data = load_data()
    cooldown = data["cooldowns"]

    if str(interaction.user.id) in cooldown and time.time() - cooldown[str(interaction.user.id)] < 900:
        await interaction.response.send_message(f"You are on cooldown. You can vote again **<t:{round(cooldown[str(interaction.user.id)] + 900)}:R>**.", ephemeral=True)
        return

    if len(data["active_crazy"]):
        await interaction.response.send_message(f"There is already someone in the padded room. You cannot start a new vote until they are released. (**<t:{round(data['active_crazy'][list(data['active_crazy'].keys())[0]])}:R>**)", ephemeral=True)
        return

    vote_active = True
    try:
        data["cooldowns"][str(interaction.user.id)] = time.time()
        save_data(data)

        await interaction.response.send_message(f"Vote started for {member.mention}. Check the channel for the voting message.", ephemeral=True)
        padded_channel = bot.get_channel(1526952092462219284)
        if isinstance(padded_channel, discord.TextChannel):
            mention = padded_channel.mention
        else:
            mention = "the padded room"
        message = await interaction.channel.send(f"{interaction.user.mention} has started a vote to send {member.mention} to {mention}!\n**React with 👍 to vote yes or 👎 to vote no**. The vote will end **<t:{round(time.time()) + 60}:R>**.")

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
            await interaction.channel.send(f"**{yes_votes}** people voted to send {member.mention} to {mention}! They will be released **<t:{round(time.time()) + 300}:R>**.")
            data["active_crazy"][str(member.id)] = time.time() + 300
            role = interaction.guild.get_role(1526950301066858587) # type: ignore
            if role:
                await member.add_roles(role)
                channel = bot.get_channel(1526952092462219284) # type: ignore
                if channel and isinstance(channel, discord.TextChannel):
                    await channel.send(f"{member.mention} You have been sent to the padded room. You will be released **<t:{round(time.time()) + 300}:R>**.")

            save_data(data)
        else:
            await interaction.channel.send(f"{member.mention} has not been sent to {mention}.")
            save_data(data)

    finally:
        vote_active = False

@bot.event
async def on_message(message):
    if message.author == bot.user or message.author.bot:
        return

    elif meow.search(message.content.strip()):
        await message.add_reaction("🐱")
        await message.channel.send(random.choice(meow_responses))

    elif woof.search(message.content.strip()):
        await message.add_reaction("🐶")
        await message.channel.send(random.choice(woof_responses))

    if message.stickers:
        if "https://cdn.discordapp.com/stickers/1488531621996134430.png" in [sticker.url for sticker in message.stickers] and message.author.id not in banned_ids:
            await message.add_reaction("❓")
            await message.channel.send("<@&1488533311776227469>")
            
        if "https://cdn.discordapp.com/stickers/1488531621996134430.png" in [sticker.url for sticker in message.stickers] and message.author.id in banned_ids:
            await message.delete()
            await message.author.send(f"<@{message.author.id}> You have been banned from using the sticker. If you think this is a mistake, please DM the admins")

    await bot.process_commands(message)

@bot.event
async def on_member_join(member):
    data = load_data()
    if str(member.id) in data["active_crazy"]:
        role = member.guild.get_role(1526950301066858587)
        if role:
            await member.add_roles(role)
            channel = member.guild.get_channel(1526952092462219284) # type: ignore
            if channel and isinstance(channel, discord.TextChannel):
                await channel.send(f"{member.mention} You have been sent to the padded room. You will be released **<t:{round(data['active_crazy'][str(member.id)]):R}>**.")

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
                        await channel.send(f"{member.mention} has been released from the padded room.")
            del active_crazy[user]
            changed = True
    if changed:
        save_data(data)

if __name__ == "__main__":
    bot.run(TOKEN)
