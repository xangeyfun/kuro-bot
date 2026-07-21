from discord import app_commands, Interaction
from discord.ext import commands, tasks
from dotenv import load_dotenv
import discord
import asyncio
import time
import json
import os
import random

load_dotenv()
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents, status=discord.Status.online, activity=discord.Activity(type=discord.ActivityType.watching, name="Type / for commands"))
TOKEN = os.getenv("TOKEN") or ""
vote_active = False

if not os.path.exists("data.json") or os.stat("data.json").st_size == 0:
    with open("data.json", "w") as f:
        json.dump({
            "cooldowns": {},
            "active_crazy": {},
            "stats": {}
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
@bot.tree.command(name="stats", description="Get the bot's statistics") #, guild=guild)
async def stats(interaction: Interaction):
    data = load_data()
    stats = data["stats"]

    total_votes = stats.get("total_votes", 0)
    user_votes = stats.get(str(interaction.user.id), {}).get("votes", 0)

    await interaction.response.send_message(f"Total votes cast: {total_votes}\nYour votes: {user_votes}", ephemeral=True)

@app_commands.allowed_installs(guilds=True, users=False)
@app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
@bot.tree.command(name="profile", description="Get a user's profile statistics") #, guild=guild)
async def profile(interaction: Interaction, member: discord.Member):
    data = load_data()
    stats = data["stats"]

    times_sent = stats.get(str(member.id), {}).get("times_sent", 0)

    await interaction.response.send_message(f"{member.mention}'s profile:\nTimes sent to the padded room: {times_sent}", ephemeral=True)

@app_commands.allowed_installs(guilds=True, users=False)
@app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
@bot.tree.command(name="leaderboard", description="Get the leaderboard of users sent to the padded room") #, guild=guild)
async def leaderboard(interaction: Interaction):
    data = load_data()
    stats = data["stats"]

    leaderboard = sorted(
        ((user_id, user_stats.get("times_sent", 0)) for user_id, user_stats in stats.items() if user_id != "total_votes"),
        key=lambda x: x[1],
        reverse=True
    )

    if not leaderboard:
        await interaction.response.send_message("No users have been sent to the padded room yet.", ephemeral=True)
        return

    leaderboard_message = "Leaderboard of users sent to the padded room:\n"
    for rank, (user_id, times_sent) in enumerate(leaderboard, start=1):
        member = interaction.guild.get_member(int(user_id))
        if member:
            leaderboard_message += f"{rank}. {member.mention} - {times_sent} times\n"

    await interaction.response.send_message(leaderboard_message, ephemeral=True)

throw_sentences = {
    "Rock": [
        "It's not just a boulder... it's a ROCK!",
        "The pioneers used to ride these babies for miles!",
        "Solid as a promise you won't keep.",
    ],
    "Potato": [
        "It's raw, it's disgusting, it's... a potato.",
        "Disappointing in every way, just like a real potato.",
        "The saddest projectile known to mankind.",
    ],
    "Brick": [
        "Brick by brick, sanity leaves the building.",
        "This is a load-bearing brick of bad decisions.",
        "Construction workers HATE this one trick.",
    ],
    "Rubber Duck": [
        "Quack quack, motherf-",
        "Every coder needs a therapist, even in a padded room.",
        "This one judges you silently.",
    ],
    "Fish": [
        "It's slimy, it smells, and it's judging you.",
        "This fish has seen things you wouldn't believe.",
        "Smells like a bad decision wrapped in scales.",
    ],
    "Coconut": [
        "Smash! Coconut crit for 1 damage.",
        "If it were a spherical cow, it would be physics.",
        "Tropical violence at its finest.",
    ],
    "Cheese Wheel": [
        "Wheel of morality, turn turn turn...",
        "Aged 3 years for maximum emotional damage.",
        "The smell alone is a weapon.",
    ],
    "Baguette": [
        "The French are NOT going to be happy about this.",
        "Bonne dégustation, idiot.",
        "Crusty on the outside, deadly on the inside.",
    ],
    "Cactus": [
        "Hugs? In THIS economy?",
        "The only relationship that can't hurt you... until now.",
        "Pain is just weakness leaving the body. And the cactus.",
    ],
    "Office Chair": [
        "Ergonomic for maximum backstabbing.",
        "Rolling into the padded room at 3am like...",
        "It has lumbar support for your emotional damage.",
    ],
    "Gaming Laptop": [
        "It has RGB so it goes faster.",
        "This one's for all the rage quitters.",
        "300 FPS of pure chaos.",
    ],
    "Keyboard": [
        "Ctrl+Z THIS!",
        "It's mechanical, so it sounds painful.",
        "Type or die. Mostly die.",
    ],
    "Mouse": [
        "Not the animal, the other kind of pest.",
        "Left click to throw, right click to cry.",
        "DPI set to maximum destruction.",
    ],
    "Teddy Bear": [
        "Who's your cuddle buddy NOW?",
        "This one has seen some things.",
        "Cuteness is just a facade for pure evil.",
    ],
    "Wet Sock": [
        "The most hated item in all of existence.",
        "Why do they always come out of the dryer wet? WHY?",
        "Squish squish, you're welcome.",
    ],
    "Plunger": [
        "It's not just for toilets anymore.",
        "A noble tool for an ignoble purpose.",
        "For when you need to unclog someone's sanity.",
    ],
    "Toilet": [
        "When you gotta go, you gotta go... into the padded room.",
        "Flush twice, it's a long way to the padded room.",
        "Porcelain throne of justice.",
    ],
    "Shopping Cart": [
        "Abandoned in a parking lot, just like your hopes and dreams.",
        "It has a wobbly wheel, so it's extra funny.",
        "The wobbly wheel of misfortune.",
    ],
    "Television": [
        "BREAKING NEWS: Local idiot throws TV into padded room.",
        "Watch this! ...oh wait, you can't anymore.",
        "The screen is cracked, just like your mental health.",
    ],
    "Fire Extinguisher": [
        "In case of emergency: throw at padded room.",
        "STOP DROP AND ROLL INTO THE PADDED ROOM.",
        "This meeting could have been a fire.",
    ],
    "Mattress": [
        "Bouncy castle for the soul.",
        "Memory foam remembers everything... especially your failures.",
        "Now everyone can nap in the padded room.",
    ],
    "Door": [
        "Closing doors on your sanity since forever.",
        "It's a door. What did you expect, a knocker?",
        "Beware of dog. There is no dog. Just a door.",
    ],
    "Satellite": [
        "Receiving signals of pure chaos.",
        "This one cost 3 billion dollars on sale.",
        "Now the padded room has Wi-Fi.",
    ],
    "Rocket": [
        "To the MOON! Wait, wrong command.",
        "Houston, we have a problem.",
        "3... 2... 1... YEET!",
    ],
    "The Moon": [
        "One small step for man, one giant throw for mankind.",
        "The moon is beautiful tonight... as a projectile.",
        "That's no moon... oh wait, it is.",
    ],
}

@app_commands.allowed_installs(guilds=True, users=False)
@app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
@app_commands.choices(item=[
    app_commands.Choice(name="🪨 Rock", value="Rock"),
    app_commands.Choice(name="🥔 Potato", value="Potato"),
    app_commands.Choice(name="🧱 Brick", value="Brick"),
    app_commands.Choice(name="🦆 Rubber Duck", value="Rubber Duck"),
    app_commands.Choice(name="🐟 Fish", value="Fish"),
    app_commands.Choice(name="🥥 Coconut", value="Coconut"),
    app_commands.Choice(name="🧀 Cheese Wheel", value="Cheese Wheel"),
    app_commands.Choice(name="🥖 Baguette", value="Baguette"),
    app_commands.Choice(name="🌵 Cactus", value="Cactus"),
    app_commands.Choice(name="🪑 Office Chair", value="Office Chair"),
    app_commands.Choice(name="💻 Gaming Laptop", value="Gaming Laptop"),
    app_commands.Choice(name="⌨️ Keyboard", value="Keyboard"),
    app_commands.Choice(name="🖱️ Mouse", value="Mouse"),
    app_commands.Choice(name="🧸 Teddy Bear", value="Teddy Bear"),
    app_commands.Choice(name="🧦 Wet Sock", value="Wet Sock"),
    app_commands.Choice(name="🪠 Plunger", value="Plunger"),
    app_commands.Choice(name="🚽 Toilet", value="Toilet"),
    app_commands.Choice(name="🛒 Shopping Cart", value="Shopping Cart"),
    app_commands.Choice(name="📺 Television", value="Television"),
    app_commands.Choice(name="🧯 Fire Extinguisher", value="Fire Extinguisher"),
    app_commands.Choice(name="🛏️ Mattress", value="Mattress"),
    app_commands.Choice(name="🚪 Door", value="Door"),
    app_commands.Choice(name="🛰️ Satellite", value="Satellite"),
    app_commands.Choice(name="🚀 Rocket", value="Rocket"),
    app_commands.Choice(name="🌕 The Moon", value="The Moon"),
])
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

    sentence = random.choice(throw_sentences[item])

    padded_channel = bot.get_channel(1526952092462219284)
    if isinstance(padded_channel, discord.TextChannel):
        await padded_channel.send(f"{interaction.user.mention} has thrown **{item}** into the padded room!\n> {sentence}")
        await interaction.response.send_message(f"You have thrown **{item}** into the padded room.\n> {sentence}", ephemeral=True)
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

    data = load_data()
    cooldown = data["cooldowns"]

    if str(interaction.user.id) in cooldown and time.time() - cooldown[str(interaction.user.id)] < 900:
        await interaction.response.send_message(f"You are on cooldown. You can vote again **<t:{round(cooldown[str(interaction.user.id)] + 900)}:R>**.", ephemeral=True)
        return

    if interaction.user.id == member.id:
        await interaction.response.send_message("You cannot vote for yourself.", ephemeral=True)
        return

    if len(data["active_crazy"]):
        await interaction.response.send_message(f"There is already someone in the padded room. You cannot start a new vote until they are released. (**<t:{round(data['active_crazy'][list(data['active_crazy'].keys())[0]])}:R>**)", ephemeral=True)
        return

    global vote_active
    if vote_active:
        await interaction.response.send_message(f"There is already an active vote. Please wait until it is finished.", ephemeral=True)
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

            data["stats"][str(member.id)] = {"times_sent": data["stats"].get(str(member.id), {}).get("times_sent", 0) + 1}
            data["stats"][str(interaction.user.id)] = {"votes": data["stats"].get(str(interaction.user.id), {}).get("votes", 0) + 1}
            data["stats"]["total_votes"] = data["stats"].get("total_votes", 0) + 1
            
            save_data(data)
        else:
            await interaction.channel.send(f"{member.mention} has not been sent to {mention}.")
            save_data(data)

    finally:
        vote_active = False

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.strip().lower() == "quack":
        await message.add_reaction("🦆")
        await message.channel.send("Quack! 🦆")

    if message.content.strip().lower() == "meow":
        await message.add_reaction("🐱")
        await message.channel.send("Meow! 🐱")

    if message.content.strip().lower() == "woof":
        await message.add_reaction("🐶")
        await message.channel.send("Woof! 🐶")

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
