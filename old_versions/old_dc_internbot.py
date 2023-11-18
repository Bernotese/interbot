import discord
from discord.ext import commands

# Intents erstellen
intents = discord.Intents.all()
intents.members = True  # Erlaubt es, Member-Updates zu empfangen (z.B. wenn jemand dem Server beitritt)

# Erstelle einen Bot mit Intents
bot = commands.Bot(command_prefix='!', intents=intents)

# Eine Liste, um die Spieler zu speichern
spieler_liste = []

# Event, das aufgerufen wird, wenn der Bot gestartet ist
@bot.event
async def on_ready():
    print(f'Eingeloggt als {bot.user.name}')

# Command zum Hinzufügen eines Spielers
@bot.command(name='join')
async def join(ctx, skill: int):
    # Überprüfe, ob der Benutzer bereits in der Liste ist
    for spieler in spieler_liste:
        if spieler['name'] == ctx.author.name:
            await ctx.send('Du bist bereits in der Liste.')
            return
    
    if 1 <= skill <= 3:
        spieler_liste.append({'name': ctx.author.name, 'skill': skill})
        await ctx.send(f'Spieler {ctx.author.name} wurde der Liste hinzugefügt. Skill: {skill}')
    else:
        await ctx.send('Ungültige Skill-Gruppe. Bitte wähle eine Skill-Gruppe zwischen 1 und 3.')

# Command zum Anzeigen der Spielerliste
@bot.command(name='ls')
async def player_list(ctx):
    if spieler_liste:
        await ctx.send('Spieler in der Runde:')
        for spieler in spieler_liste:
            await ctx.send(f'{spieler["name"]} - Skill: {spieler["skill"]}')
    else:
        await ctx.send('Keine Spieler in der Runde.')

# Command zum Mischen der Teams
@bot.command(name='shuffle')
async def shuffle_teams(ctx):
    if len(spieler_liste) < 2:
        await ctx.send('Es müssen mindestens zwei Spieler in der Liste sein, um Teams zu erstellen.')
    else:
        # Mische die Spielerliste nach dem Skill
        sorted_spieler = sorted(spieler_liste, key=lambda x: x['skill'])
        
        # Teile die Spielerliste in zwei Teams
        team1 = sorted_spieler[:len(sorted_spieler)//2]
        team2 = sorted_spieler[len(sorted_spieler)//2:]
        
        
# Command zum Zurücksetzen der Spielerliste
@bot.command(name='reset')
async def reset(ctx):
    global spieler_liste
    spieler_liste = []
    await ctx.send('Spielerliste wurde zurückgesetzt.')

# Command zum Anzeigen der Skill-Informationen
@bot.command(name='info')
async def info(ctx):
    await ctx.send('Skill Rating:\n1: Profi\n2: Amateur\n3: Anfänger')

# Command zum Teilen der Spieler in zwei Teams und Verschieben in die Voice-Channels
@bot.command(name='start')
async def start(ctx):
    if len(spieler_liste) < 2:
        await ctx.send('Es müssen mindestens zwei Spieler in der Liste sein, um Teams zu erstellen und zu verschieben.')
    else:             
        # Mische die Spielerliste nach dem Skill
        sorted_spieler = sorted(spieler_liste, key=lambda x: x['skill'])
        
        # Teile die Spielerliste in zwei Teams
        team1 = []
        team2 = []

        for index, spieler in enumerate(sorted_spieler):
            if index % 2 == 0:
                team1.append(spieler)
            else:
                team2.append(spieler)
        
        await ctx.send('Teams wurden erstellt:')
        await ctx.send('Team 1:')
        for spieler in team1:
            await ctx.send(f'{spieler["name"]} - Skill: {spieler["skill"]}')
        
        await ctx.send('Team 2:')
        for spieler in team2:
            await ctx.send(f'{spieler["name"]} - Skill: {spieler["skill"]}')

        # Finde die Voice-Channels mit den Namen "team-a" und "team-b"
        channel_a = discord.utils.get(ctx.guild.voice_channels, name='team-a')
        channel_b = discord.utils.get(ctx.guild.voice_channels, name='team-b')

        if not channel_a or not channel_b:
            await ctx.send('Die Voice-Channels "team-a" und "team-b" müssen vorhanden sein.')
            return

        # Verschiebe Spieler von Team 1 in Voice-Channel A
        for spieler in team1:
            member = ctx.guild.get_member_named(spieler['name'])
            if member:
                await member.move_to(channel_a)

        # Verschiebe Spieler von Team 2 in Voice-Channel B
        for spieler in team2:
            member = ctx.guild.get_member_named(spieler['name'])
            if member:
                await member.move_to(channel_b)

        await ctx.send('Spieler wurden in faire Teams aufgeteilt und verschoben.')

@bot.command(name='end')
async def end(ctx):
    global spieler_liste
    spieler_liste = []

    # Finde den Voice-Channel mit dem Namen "allgemein"
    general_channel = discord.utils.get(ctx.guild.voice_channels, name='Allgemein')

    if not general_channel:
        await ctx.send('Der Voice-Channel "allgemein" muss vorhanden sein.')
        return

    # Verschiebe alle Spieler in den Allgemein-Channel
    for member in ctx.guild.members:
        if member.voice:
            await member.move_to(general_channel)

    await ctx.send('Alle Spieler wurden zurück in den Allgemein-Channel verschoben.')

# Führe den Bot mit dem Token aus
bot.run('MTE3NDc3MzM1NzA3ODY2MzIzOA.GAOzeV.OjdGfknLm_1q6nFU9650HTWG6OLzRYF1TEupSE')