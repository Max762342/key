# -*- coding: utf-8 -*-
# Flore Tools Key Bot
# Benötigt: pip install discord.py

import discord
from discord.ext import commands
import json
import os
import time
import random
import string

TOKEN = "MTUxNTcyMTc1Mjg1OTExOTYzNg.GJYzZA.fPlPYF2zf-MHcGp_IT39i6kQP6KwjFIgv5ioqY"  # <-- Bot Token eintragen

ADMIN_ID       = 1186301320609673347
KEYS_CHANNEL   = 1515721188012200104
KEYS_FILE      = os.path.join(os.path.dirname(__file__), "keys.json")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

def load_keys():
    if not os.path.isfile(KEYS_FILE):
        return {}
    try:
        return json.load(open(KEYS_FILE, "r", encoding="utf-8"))
    except Exception:
        return {}

def save_keys(keys):
    json.dump(keys, open(KEYS_FILE, "w", encoding="utf-8"), indent=2)

def gen_key(length=24):
    return "FLORE-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=length))

def parse_duration(s):
    """'10s' -> 10, '10m' -> 600, '1h' -> 3600, '1d' -> 86400"""
    s = s.strip().lower()
    if s.endswith("s"):   return int(s[:-1])
    if s.endswith("m"):   return int(s[:-1]) * 60
    if s.endswith("h"):   return int(s[:-1]) * 3600
    if s.endswith("d"):   return int(s[:-1]) * 86400
    return int(s)

@bot.event
async def on_ready():
    print(f"[Flore Key Bot] Logged in as {bot.user}")

@bot.command(name="newkey", aliases=["getkey"])
async def newkey(ctx, duration: str = "1h"):
    if ctx.author.id != ADMIN_ID:
        await ctx.message.delete()
        return

    try:
        secs = parse_duration(duration)
    except Exception:
        await ctx.send("❌ Invalid duration. Use e.g. `10s`, `10m`, `1h`, `1d`", delete_after=5)
        return

    key = gen_key()
    expires = int(time.time()) + secs
    keys = load_keys()
    keys[key] = {"expires": expires, "created_by": ctx.author.id}
    save_keys(keys)

    # Key in den Keys-Channel posten
    channel = bot.get_channel(KEYS_CHANNEL)
    if channel:
        await channel.send(f"`{key}`")

    # Bestätigung an Admin per DM
    expire_str = f"<t:{expires}:R>"
    try:
        await ctx.author.send(f"✅ Key generated: `{key}`\nExpires: {expire_str} (`{duration}`)")
    except Exception:
        pass
    await ctx.message.delete()

@bot.command(name="keylist")
async def keylist(ctx):
    if ctx.author.id != ADMIN_ID:
        await ctx.message.delete()
        return

    keys = load_keys()
    now = int(time.time())
    lines = []
    for k, v in keys.items():
        exp = v.get("expires", 0)
        remaining = exp - now
        if remaining > 0:
            lines.append(f"`{k}` — expires <t:{exp}:R>")
        else:
            lines.append(f"~~`{k}`~~ — expired")

    if not lines:
        await ctx.author.send("No keys found.")
    else:
        await ctx.author.send("**Key List:**\n" + "\n".join(lines))
    await ctx.message.delete()

@bot.command(name="delkey")
async def delkey(ctx, key: str):
    if ctx.author.id != ADMIN_ID:
        await ctx.message.delete()
        return
    keys = load_keys()
    if key in keys:
        del keys[key]
        save_keys(keys)
        await ctx.author.send(f"✅ Key `{key}` deleted.")
    else:
        await ctx.author.send(f"❌ Key `{key}` not found.")
    await ctx.message.delete()

@bot.command(name="keydate")
async def keydate(ctx, key: str, duration: str):
    if ctx.author.id != ADMIN_ID:
        await ctx.message.delete()
        return
    
    keys = load_keys()
    if key not in keys:
        try:
            await ctx.author.send(f"❌ Key `{key}` not found.")
        except Exception:
            pass
        await ctx.message.delete()
        return
    
    try:
        secs = parse_duration(duration)
    except Exception:
        try:
            await ctx.author.send("❌ Invalid duration. Use e.g. `10s`, `10m`, `1h`, `1d`")
        except Exception:
            pass
        await ctx.message.delete()
        return
    
    expires = int(time.time()) + secs
    keys[key]["expires"] = expires
    save_keys(keys)
    expire_str = f"<t:{expires}:R>"
    try:
        await ctx.author.send(f"✅ Key `{key}` updated.\nNew expiry: {expire_str} (`{duration}`)")
    except Exception:
        pass
    await ctx.message.delete()

bot.run(TOKEN)
