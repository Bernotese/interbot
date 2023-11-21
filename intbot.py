from decouple import config
from interactions import slash_command, slash_option, SlashContext, OptionType
from interactions import Client, Intents, listen
from beanie import Document, Indexed, init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List
from interactions import Embed, StringSelectMenu

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
    existing_entry = await Players.find_one({"name": name})
    return existing_entry is not None

async def check_if_game_running():
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
    # Erstellt einen neune Spieler (anlegen eines neuen Spielers)
    # Userid
    discord_id = ctx.author.id
    #DB Entry
    player = Players(discord_id=int(discord_id), name=name, elo=elo_points, wins=0, losses=0)
    
    if await check_db_players(name):
        await ctx.send(f"Hi {name}, du wurdest bereits angelegt.", ephemeral=True)
    else:
        await player.insert()
        await ctx.send(f"Hi {name}, du wurdest mit einer Strat-Elo von {str(elo_points)} angelegt.", ephemeral=True)

@slash_command(name="newgame", description="star new game")
async def newgame(ctx: SlashContext):
    # Startet eine neue Runde
    if await check_if_game_running():
        await ctx.send(f"Beende erst das letzte Spiel.", ephemeral=True)
        return
    else:
        global new_game
        new_game = Games(members=[], team1=[], team2=[], winner=0, game_running=1)
        await new_game.insert()
        await ctx.send(f"Neues Spiel wurde erstellt.")

@slash_command(name="join", description="Join a new game")
async def joingame(ctx: SlashContext):
    # Join einer bestehenden runde
    user_id = ctx.author.id
    if not check_if_game_running():
        await ctx.send("Erstelle erst ein neues Spiel", ephemeral=True)
        return
    
    # Abruf des aktiven Spiels aus der Datenbank
    active_game = await Games.find_one({"game_running": 1})

    if active_game:
        if user_id in active_game.members:
            await ctx.send("Du bist bereits beigetreten.", ephemeral=True)
        else:
            active_game.members.append(user_id)
            await active_game.replace(active_game)
            await ctx.send("Du bist dem Spiel beigetreten.", ephemeral=True)

async def get_all_active_members_names():
    active_game = await Games.find_one({"game_running": 1})
    members = active_game.members
    return members

@slash_command(name="startgame", description="start the game")
async def startgame(ctx: SlashContext):
    game_members_ids = await get_all_active_members_names()
    
    game_members = []
    for player in game_members_ids:
        p = await Players.find_one({"discord_id" : player})
        name = p.name
        print(f"Gefunden: " + name)
        game_members.append(name)

    print(len(game_members))

    game_info = Embed(title="Neues Spiel")
    game_info.set_thumbnail("https://upload.wikimedia.org/wikipedia/commons/1/1a/Faker_2020_interview.jpg")
    
    clear_names = " ,".join(game_members)


    game_info.description = f"{clear_names}"
    
    await ctx.send(embed=game_info)

    # components = [
    #     StringSelectMenu("Variation 1", "Variation 2", placeholder="Variation:", min_values=1, max_values=1),
    # ]

    # await ctx.send(embed=members, components=components)

    # Je nach auswahl Runde Starten mit den Verschiedenen Teams
    # Neuer Post mit dem Finalen Team
    # User in die jeweiligen Channel moven

@slash_command(name="test", description="test")
async def test(ctx: SlashContext):
    embed = Embed(title="Ich bin ein Embed")
    embed.description = "Hier können afaik 4000 Zeichen drin stehen"
    embed.set_thumbnail("https://upload.wikimedia.org/wikipedia/commons/1/1a/Faker_2020_interview.jpg")

    embed.add_field(name="field1", value="value1", inline=True)
    embed.add_field(name="field2", value="value2", inline=True)
    embed.add_field(name="field3", value="value3", inline=True)

    await ctx.send(embed=embed)

@listen()  # this decorator tells snek that it needs to listen for the corresponding event, and run this coroutine
async def on_ready():
    # This event is called when the bot is ready to respond to commands
    await init_beanie(database=mongo_client.intbot, document_models=[Games])
    await init_beanie(database=mongo_client.intbot, document_models=[Players])
    print("Ready")
    print(f"This bot is owned by {bot.owner}")


@listen()
async def on_message_create(event):
    # This event is called when a message is sent in a channel the bot can see
    print(f"message sent: {event.message.content}")

bot.start(str(key))