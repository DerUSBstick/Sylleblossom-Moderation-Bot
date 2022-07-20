from turtle import clear
import discord
from discord.ext import commands
from discord.ext import tasks
import json
import time
import datetime
import os
import asyncio
import aiohttp
import urllib.request
from PIL import Image
import io
from discord_components import DiscordComponents, Button, ButtonStyle, InteractionType, component, Select, SelectOption

start = time.time() #When the bot started
prefix = "-"
intents = discord.Intents.default()
intents.presences = True
intents.members = True
intents.messages = True
bot = commands.Bot(command_prefix=prefix, case_insensitive=True, intents=intents)

@bot.command()
async def stats(ctx):
    with open("stats.json") as f:
        stats = json.load(f)
    VISION_EMOJIS = {
        "Anemo": "<:Anemo:854743841289273384>",
        "Pyro": "<:Pyro:854743894012985375>",
        "Hydro": "<:Hydro:854743924110655488>",
        "Electro": "<:Electro:854743861019803658>",
        "Cryo": "<:Cryo:854743908756226078>",
        "Geo": "<:Geo:854743937918566401>",
        "Dendro": "<:Dendro:854743874492039168>"
    }
    desc = ""
    if ctx.message.author.id not in stats["1-year-anniversary"]["participants"]:
        return await ctx.send("You did not participate in the 1-Year Anniversary. There are no stats for your ID.")
    desc = "You participated for the following Visions:\n\n"
    for VISION in stats["1-year-anniversary"][f"{ctx.message.author.id}"]["team"]:
        emoji = VISION_EMOJIS[f"{VISION}"]
        desc += f"{emoji} {VISION}\n"
    polls = stats["1-year-anniversary"][f"{ctx.message.author.id}"]["polls"]
    correct_answers = stats["1-year-anniversary"][f"{ctx.message.author.id}"]["correct_answers"]
    wrong_answers = stats["1-year-anniversary"][f"{ctx.message.author.id}"]["wrong_answers"]
    dismissed_votes = stats["1-year-anniversary"][f"{ctx.message.author.id}"]["dismissed_answers"]
    desc += f"\nYou voted in **{polls}/44** Polls. Out of **{polls}** Answers, **{correct_answers}** were correct and **{wrong_answers}** not. Due to voting multiple times on a poll, **{dismissed_votes}** Votes have not been counted."


    embed = discord.Embed(title="1-Year-Anniversary Stats", description=desc, color=0x00bfff)
    embed.set_footer(text=ctx.message.author, icon_url=ctx.message.author.avatar_url)
    await ctx.send(embed=embed)

def parse_duration(duration: int):
    minutes, seconds = divmod(duration, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)

    duration = []
    if days > 0:
        if days > 1:
            duration.append('{} days'.format(days))
        else:
            duration.append('{} day'.format(days))
    if hours > 0:
        if hours > 1:
            duration.append('{} hours'.format(hours))
        else:
            duration.append('{} hour'.format(hours))
    if minutes > 0:
        if minutes > 1:
            duration.append('{} minutes'.format(minutes))
        else:
            duration.append('{} minute'.format(minutes))
    if seconds > 0:
        if seconds > 1:
            duration.append('{} seconds'.format(seconds))
        else:
            duration.append('{} second'.format(seconds))
    else:
        duration.append('-')

    return ', '.join(duration)

def convert_to_unix(time):
    time = time.replace("-", "/")
    result = datetime.datetime.strptime(time, "%Y/%m/%dT%H:%M:%SZ").timestamp()
    return int(round(result))

async def create_logs(reason, user: int, moderator: int, action):
    user = await bot.fetch_user(user)
    moderator = await bot.fetch_user(moderator)
    embed = discord.Embed(title=f"{action}", description=f"Offender: {user} {user.mention}\nReason: {reason}\nResponsible moderator: {moderator}", color=0x00fff8)
    embed.set_footer(text=f"{user.id}")
    embed.timestamp = datetime.datetime.now()
    channel = bot.get_channel(979335099143319562)
    await channel.send(embed=embed)

#Checks if the Husbando bots are online
#If not, bot gets marked as temporarely offline, after 5 minutes the channel gets locked and a message appears
#If the bot is back online, the message gets deleted and the channel opened up again
@tasks.loop(seconds=15)
async def check_status():
    msg = ""
    with open("bots.json") as f:
        data = json.load(f)
    guild = bot.get_guild(854733975197188108)
    bots = [857333365636202507, 887684485469073448, 872205461636648961, 886626811444871188]
    for x in bots:
        #user = await bot.fetch_user(x)
        user = guild.get_member(x)
        if user.status == discord.Status.online:
            if data[user.name]["status"] == 0:
                channel = bot.get_channel(data[user.name]["channel"])
                await channel.set_permissions(guild.default_role, send_messages=None)
                message = await channel.fetch_message(data[user.name]["message"])
                await message.delete()
                data[user.name]["message"] = 0
                data[user.name]["status"] = 1

            data[user.name]["down"] = round(time.time())
            msg += f"{user.name} is currently Online <a:Success:778267705643892757>\n\n"
        elif user.status == discord.Status.offline:
            if time.time() - data[user.name]["down"] < 30:
                print(round(time.time() - data[user.name]["down"]))
                msg += f"{user.name} is currently Offline <a:Loading:778267707715485696>\n\n"
            else:
                if data[user.name]["status"] == 1:
                    channel = bot.get_channel(data[user.name]["channel"])
                    await channel.set_permissions(guild.default_role, send_messages=False)
                    message = await channel.send(f"{user.name} is currently experiencing an Outage. Check <#892102362813055026> for further Informations")
                    data[user.name]["status"] = 0
                    data[user.name]["message"] = message.id
                down_time = parse_duration(round(time.time() - data[user.name]["down"]))
                msg += f"{user.name} is currently experiencing an Outage since {down_time} <a:Error:778267709904519209>\n\n"
                channel = bot.get_channel(data[user.name]["channel"])
    
    embed = discord.Embed(title="Status", description=msg, color=0x0062ff, timestamp=datetime.datetime.utcnow())
    channel = bot.get_channel(965523098885582848)
    message = await channel.fetch_message(965674314462552064)
    await message.edit(content=None, embed=embed)
    
    with open("bots.json", "w+") as f:
        json.dump(data, f, indent=4)

@tasks.loop(minutes=5)
async def subscriber_counter():
    guild = bot.get_guild(980034765501636608)
    channel_id = "YT_CHANNEL_ID"
    key = "YT_API_KEY"

    data = urllib.request.urlopen(f"https://www.googleapis.com/youtube/v3/channels?part=statistics&id={channel_id}&key={key}").read()
    subs = json.loads(data)['items'][0]['statistics']['subscriberCount']
    channel_counter = bot.get_channel(980034765501636608)
    await channel_counter.edit(name=f"{subs} Subs")
       
#Simple Ping command
@bot.command()
async def ping(ctx):
    await ctx.send(f"{round(bot.latency*1000, 4)}ms")

#Command to see, how long the bot has been online
#Cooldown of 5 seconds
@bot.command()
@commands.cooldown(1, 5, commands.BucketType.member)
async def uptime(ctx):
    cur = time.time()
    diff = int(round(cur - start))
    await ctx.send(f'Uptime: {parse_duration(diff)}')

#Give and Remove someones Image Permissions in #artworks and so on
@bot.command()
@commands.has_any_role(974770032993267803, 939558108609523742, 895753360920178699)
async def imperms(ctx, user: discord.Member, *, reason=None):
    guild = ctx.guild
    user = ctx.guild.get_member(user.id)
    role = guild.get_role(958047463179169842)
    try:
        if role in user.roles:
            action = "Image Permissions Granted"
            await user.remove_roles(role)
            await ctx.send(f"{user.mention} has been Granted Image Permissions")
        else:
            action = "Image Permissions Denied"
            await user.add_roles(role)
            await ctx.send(f"Image Permissions have been denied for {user.mention}")
        await create_logs(reason, user.id, ctx.message.author.id, action)
    except Exception as e:
        print(e)
        
#Counting Module
@bot.command()
@commands.is_owner()
async def leaderboard(ctx):
    message = await ctx.send(
        components=[
            Select(
                placeholder="Choose an leaderboard",
                options=[
                    SelectOption(label="Counting Leaderboard", value="counting")
                ],
                custom_id="leaderboard"
            )
        ]
        )
    while True:
        try:
            res = await bot.wait_for("select_option", timeout=30)

            if res.custom_id == "leaderboard" and res.channel.id == ctx.channel.id and res.component[0].value == "counting":
                with open("counting.json") as f:
                    counting = json.load(f)
                leaderboard_data = {}
                for USER in counting["users"]:
                    leaderboard_data[f"{USER}"] = counting[f"{USER}"]
                top_users = {k: v for k, v in sorted(leaderboard_data.items(), key=lambda item: item[1], reverse=True)}
                names = ''
                for position, user in enumerate(top_users):
                    names += f'{position+1} - <@!{user}> with {top_users[user]}\n'
                    if position == 9:
                        break
                embed = discord.Embed(title="Leaderboard")
                embed.add_field(name="Names", value=names, inline=False)
                await message.delete()
                await ctx.send(embed=embed)
        except asyncio.TimeoutError:
            break

@bot.event
async def on_member_join(member):
    responses = [
        "{m} joined the party.",
        "Glad you're here, {m}",
        "{m} just joined. Everyone, look busy!",
        "A wild {m} has appeared.",
        "Brace yourselves. {m} just joined the server.",
        "{m] just slid into the server.",
        "It's a bird! It's a plane! Nevermind, it's just {m}",
        "Never gonna give {m} up. Never gonna let {m} down.",
        "Hey! Listen! {m} has joined!",
        "We've been expecting you {m}.",
        "Welcome, {m}. We hope youi brought pizza.",
        "Heyo, {m} deserve a warming welcome!",
        "{m} is here finally so bring the pizza over everyone!",
        "{m}! Thank you for coming!",
        "{m} has come on to the stage, give them some applause."
    ]
    if member.guild.id == 854733975197188108:
        channel = bot.get_channel(854733975977197568)
        response = random.choice(responses).replace("{m}", f"{member.mention}")
        await channel.send(response)

async def boost_webhook(user):
    async with aiohttp.ClientSession() as session:
        webhook = Webhook.from_url(f'https://discord.com/api/webhooks/', adapter=AsyncWebhookAdapter(session))
        await webhook.send(content=f"Woah! {user.mention} Thank you ever so much for the boost! You're a real one <:grabsyouwithlove:973217151135645696>", username="Sylle", avatar_url="https://media.discordapp.net/attachments/")
        await webhook.send(content="https://media.discordapp.net/attachments/", username="Sylle", avatar_url="https://media.discordapp.net/attachments/")
        await session.close()
        
async def counting_message(message):
    if message.webhook_id == None:
        with open("counting.json") as f:
            counting = json.load(f)
        if message.content != str(counting["current_count"]):
            return await message.delete()
        counting["current_count"] += 1
        if message.author.id in counting["users"]:
            counting[f"{message.author.id}"] += 1
        else:
            counting["users"].append(message.author.id)
            counting[f"{message.author.id}"] = 1
        await counting_webhook(message.author.name, message.author.avatar_url, counting["current_count"] - 1)
        if counting["webhook"]["last"] < 3:
            counting["webhook"]["last"] += 1
        else:
            counting["webhook"]["last"] = 1
        counting["recovery"] = {
            "last_message": f"{message.created_at}",
            "user": message.author.id
        }
        with open("counting.json", "w+") as f:
            json.dump(counting, f, indent=4)
        await message.delete()

async def counting_webhook(USERNAME, USER_AVATAR_URL, NUMBER):
    with open("counting.json") as f:
        data = json.load(f)
    last = data["webhook"]["last"]
    webhook = data["webhook"][f"{last}"]
    async with aiohttp.ClientSession() as session:
        webhook = Webhook.from_url(f'{webhook}', adapter=AsyncWebhookAdapter(session))
        await webhook.send(content=NUMBER, username=USERNAME, avatar_url=USER_AVATAR_URL)
        await session.close()

async def counting_recovery_mode():
    messages = [0]
    while messages != []:
        with open("counting.json") as f:
            data = json.load(f)
        channel = bot.get_channel(data["channel"])
        time = await convert_to_date(data["recovery"]["last_message"])
        messages = await channel.history(limit=3, after=time).flatten()
        if messages != []:
            for message in messages:
                await counting_message(message)
async def convert_to_date(time):
    time = time.split(".")[0].replace("-", "/")
    result = datetime.datetime.strptime(time, "%Y/%m/%d %H:%M:%S")
    return result        
        
@bot.event
async def on_message(message):
    if f"{message.type}" == "MessageType.premium_guild_subscription":
        await boost_webhook(message.author)
    if message.attachments != []:
        im = 0
        log_channel = bot.get_channel(965623933871226890)
        for x in message.attachments:
            embed = discord.Embed(title=f"{message.author.name} posted an Image")
            embed.set_image(url=x)
            embed.set_footer(text=f"{message.channel.id}_{message.author.id}_{message.id}_{im}")
            await log_channel.send(embed=embed)
            im += 1
    if message.channel.id == 981634202049069106:
        await counting_message(message)
    await bot.process_commands(message)
        
@bot.event
async def on_ready():
    DiscordComponents(bot)
    await counting_recovery_mode()
    subscriber_counter.start()
    check_status.start()
    print(f"Logged in")

bot.run("BOT_TOKEN")
