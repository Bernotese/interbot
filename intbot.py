from asyncio import sleep
from decouple import config
from interactions import slash_command, slash_option, SlashContext, OptionType
from interactions import Client, Intents, listen
from beanie import Document, Indexed, init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List

key = config('API_KEY')

bot = Client(intents=Intents.DEFAULT)
# intents are what events we want to receive from discord, `DEFAULT` is usually fine

joined_players = []

# Database Stuff
class Players(Document):
    discord_id: int
    name: str
    elo: int
    wins: int
    losses: int

class Games(Document):
    members: List
    team1: List[Players]
    team2: List[Players]
    winner: int
    game_running: int # 1 game running / 0 game over

mongo_client = AsyncIOMotorClient("mongodb://10.0.0.40:27017/")  # Ersetze die Verbindungs-URL entsprechend deiner MongoDB-Instanz

async def check_db_players(name):
    await init_beanie(database=mongo_client.intbot, document_models=[Players])
    existing_entry = await Players.find_one({"name": name})
    return existing_entry is not None

async def check_if_game_running():
    await init_beanie(database=mongo_client.intbot, document_models=[Games])
    running_game = await Games.find_one({"game_running": 1})
    print(running_game)
    return running_game is not None

@slash_command(name="newplayer", description="Add new player | <Name> <Elo>")
@slash_option(
    name="name",
    description="Display Name",
    required=True,
    opt_type=OptionType.STRING
)
@slash_option(
    name="elo_points",
    description="Elopoints",
    required=True,
    opt_type=OptionType.INTEGER,
    min_value=1,
    max_value=100
)
async def newpalyer(ctx: SlashContext, name: str, elo_points: int):
    # Userid
    discord_id = ctx.author.id
    #Database Entry
    await init_beanie(database=mongo_client.intbot, document_models=[Players])
    player = Players(discord_id=int(discord_id), name=name, elo=elo_points, wins=0, losses=0)
    
    if await check_db_players(name):
        await ctx.send(f"Hi {name}, du wurdest bereits angelegt.")
    else:
        await player.insert()
        await ctx.send(f"Hi {name}, du wurdest mit einer Strat-Elo von {str(elo_points)} angelegt.")

@slash_command(name="newgame", description="star new game")
async def newgame(ctx: SlashContext):
    await init_beanie(database=mongo_client.intbot, document_models=[Games])

    if await check_if_game_running():
        await ctx.send(f"Beende erst das letzte Spiel.")
        return
    else:
        global new_game
        new_game = Games(members=[], team1=[], team2=[], winner=0, game_running=1)
        await new_game.insert()
        await ctx.send(f"Neues Spiel wurde erstellt.")

@slash_command(name="join", description="Join a new game")
async def joingame(ctx: SlashContext):
    user_id = ctx.author.id
    if not check_if_game_running():
        await ctx.send("Erstelle erst ein neues Spiel")
        return
    
    # Abruf des aktiven Spiels aus der Datenbank
    await init_beanie(database=mongo_client.intbot, document_models=[Games])
    active_game = await Games.find_one({"game_running": 1})

    if active_game:
        if user_id in active_game.members:
            await ctx.send("Du bist bereits beigetreten.")
        else:
            active_game.members.append(user_id)
            await active_game.replace(active_game)
            await ctx.send("Du bist dem Spiel beigetreten.")
    else:
        await ctx.send("Es gibt kein aktives Spiel.")

@listen()  # this decorator tells snek that it needs to listen for the corresponding event, and run this coroutine
async def on_ready():
    # This event is called when the bot is ready to respond to commands
    print("Ready")
    print(f"This bot is owned by {bot.owner}")

@listen()
async def on_message_create(event):
    # This event is called when a message is sent in a channel the bot can see
    print(f"message sent: {event.message.content}")

bot.start(str(key))