# Netease Music Bot by Legendword (legendword.com)
# Version 1.0

import json
import urllib3

import asyncio

import os
import re

import discord
from dotenv import load_dotenv

from discord.ext import commands

import youtube_dl

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

bot = commands.Bot(command_prefix='nmb ', case_insensitive=True)

bot.remove_command('help')

queue = {}

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name='nmb help'))
    print(f'{bot.user.name} has connected to Discord!')

@bot.command(name='help', aliases=['?'])
async def help(ctx):
    help_text = '''

**Commands**
- `nmb help` displays this message
- `nmb play <url>` or `nmb p <url>` plays the song/playlist in the specified URL
- `nmb skip` or `nmb next` skips the current song
- `nmb queue` or `nmb q` displays the queue
- `nmb loop` toggles queue loop on/off
- `nmb leave` or `nmb gun` makes me disconnect from the voice channel

**URL Examples**
A valid __Song URL__ looks like: `https://music.163.com/song?id=476323553`
A valid __Playlist URL__ looks like: `https://music.163.com/playlist?id=810793370`

**Note**
Queue Loop is enabled by default, meaning that NMB will play from the top once it reaches the end of the queue.
If Queue Loop is disabled, NMB will automatically leave the voice channel and clear the queue once it reaches the end.
Songs labelled with ***[VIP]*** are Netease VIP-exclusive songs. Although most VIP songs allow free online listening, some can't be played online. Songs that can't be played will simply be skipped.
Loading long playlists can take a while, so please be patient while waiting for NMB to respond when loading a long playlist.
To save resources, only the first 10 songs will be displayed when showing a playlist with more than 10 songs, and only the next 20 songs will be displayed when showing a queue with more than 20 songs.
If you encounter any bugs or would like to suggest a feature, view the [NMB GitHub page]() for more information.
    '''
    await ctx.send(embed=discord.Embed(title='NMB Help', type='rich', description=help_text, color=discord.Color.red()))

@bot.command(name='test')
async def test(ctx):
    channel = ctx.author.voice.channel
    voice_channel = await channel.connect()

@bot.command(name='leave', aliases=['disconnect','gun'])
async def leave(ctx):
    sq = get_queue(ctx.guild.id, ctx.channel, ctx.voice_client)
    await ctx.voice_client.disconnect()
    sq['is_playing'] = False
    sq['is_connected'] = False

@bot.command(name='skip', aliases=['next'])
async def skip(ctx):
    sq = get_queue(ctx.guild.id, ctx.channel, ctx.voice_client)
    sq['voice_client'].stop()

@bot.command(name='loop')
async def loop(ctx):
    sq = get_queue(ctx.guild.id, ctx.channel, ctx.voice_client)
    if sq['loop_queue'] == True:
        sq['loop_queue'] = False
    else:
        sq['loop_queue'] = True
    await ctx.send(embed=discord.Embed(description='Queue Loop is now '+('**enabled**' if sq['loop_queue'] else '**disabled**'), type='rich', color=discord.Color.red()))

@bot.command(name='queue', aliases=['q'])
async def showqueue(ctx):
    sq = get_queue(ctx.guild.id, ctx.channel, ctx.voice_client)

    title = ''
    desc = ''
    if sq['is_connected'] == False:
        title = 'Queue (0/0)'
        desc = 'Not Connected to Voice Channel.\nUse `nmb play <url>` to start playing.'
    else:
        title = 'Queue ('+str(sq['pos']+1)+'/'+str(len(sq['songs']))+')'
        if (len(sq['songs'])>20):
            desc += '_Next in Queue:_'
            for i in range(sq['pos'], min(sq['pos']+20, len(sq['songs']))):
                if sq['songs'][i].get('name') == None:
                    sq['songs'][i] = fetch_song_info(sq['songs'][i]['id'])
                desc += '\n'+('>  ' if sq['pos']==i else '   ')+str(i+1)+'. **'+sq['songs'][i]['name']+'** - '+sq['songs'][i]['artists']+' ('+sq['songs'][i]['duration']+')'+(' ***[VIP]***' if sq['songs'][i]['vip']==True else '')
        else:
            for i in range(len(sq['songs'])):
                if sq['songs'][i].get('name') == None:
                    sq['songs'][i] = fetch_song_info(sq['songs'][i]['id'])
                desc += '\n'+('>  ' if sq['pos']==i else '   ')+str(i+1)+'. **'+sq['songs'][i]['name']+'** - '+sq['songs'][i]['artists']+' ('+sq['songs'][i]['duration']+')'+(' ***[VIP]***' if sq['songs'][i]['vip']==True else '')
    await ctx.send(embed=discord.Embed(title=title, description=desc, type='rich', color=discord.Color.red()))

@bot.command(name='play', aliases=['p'])
async def play(ctx, url):
    sq = get_queue(ctx.guild.id, ctx.channel, ctx.voice_client)

    sid = None
    smode = 'song'

    if re.search('\?',url) == None:
        await ctx.send(embed=discord.Embed(title='Error', description='URL format not supported, check `nmb help` for more information', type='rich', color=discord.Color.red()))
    else:
        if re.search('song\?',url) == None:
            if re.search('playlist\?',url) == None:
                await ctx.send(embed=discord.Embed(title='Error', description='URL format not supported, check `nmb help` for more information', type='rich', color=discord.Color.red()))
            else:
                #playlist
                smode = 'playlist'
                info = re.split('playlist\?',url)[1]
                if re.search('\&',info) == None:
                    if info.startswith('id='):
                        sid = info[3:]
                    else:
                        await ctx.send(embed=discord.Embed(title='Error', description='Playlist Id not found in URL', type='rich', color=discord.Color.red()))
                else:
                    flag = False
                    for dd in re.split('\&',info):
                        if dd.startswith('id='):
                            sid = dd[3:]
                            flag = True
                            break
                    if flag == False:
                        await ctx.send(embed=discord.Embed(title='Error', description='Playlist Id not found in URL', type='rich', color=discord.Color.red()))  
        else:
            #song
            info = re.split('song\?',url)[1]
            if re.search('\&',info) == None:
                if info.startswith('id='):
                    sid = info[3:]
                else:
                    await ctx.send(embed=discord.Embed(title='Error', description='Song Id not found in URL', type='rich', color=discord.Color.red()))
            else:
                flag = False
                for dd in re.split('\&',info):
                    if dd.startswith('id='):
                        sid = dd[3:]
                        flag = True
                        break
                if flag == False:
                    await ctx.send(embed=discord.Embed(title='Error', description='Song Id not found in URL', type='rich', color=discord.Color.red()))
    
    
    if sid != None:
        if ctx.voice_client == None or sq['is_connected'] == False:
            sq['voice_client'] = await ctx.author.voice.channel.connect()
            sq['is_connected'] = True
            sq['pos'] = 0
        if smode == 'song':
            song_info = fetch_song_info(sid)
            sq['songs'].append(song_info)
            if len(sq['songs']) == 1:
                sq['pos'] = 0
                sq['is_playing'] = True
                sq['voice_client'].play(discord.FFmpegPCMAudio(song_info['url']), after=lambda e:playback_finished(e,ctx.guild.id))
                embd = discord.Embed(title=('Now Playing: '+song_info['name']+' - '+song_info['artists']), description=('Length: '+song_info['duration']), type='rich', color=discord.Color.red())
                embd.set_thumbnail(url=song_info['album_cover'])
                await sq['text_channel'].send(embed=embd)
            else:
                await ctx.send(embed=discord.Embed(title=('Queued: '+str(len(sq['songs']))+'. '+song_info['name']+' - '+song_info['artists']), description=('Currently Playing '+str(sq['pos']+1)+'/'+str(len(sq['songs']))), type='rich', color=discord.Color.red()))
        elif smode == 'playlist':
            playlist_info = fetch_playlist_info(sid)
            title = playlist_info['name']
            description = 'Playlist Description: _'+playlist_info['description']+'_\n'
            ic = 1
            for i in playlist_info['list']:
                if ic<=10:
                    sinfo = fetch_song_info(i)
                    sq['songs'].append(sinfo)
                    description += '\n   '+str(ic)+'. **'+sinfo['name']+'** - '+sinfo['artists']+' ('+sinfo['duration']+')'
                    if sinfo['vip'] == True:
                        description += ' ***[VIP]***'
                    ic += 1
                else:
                    sq['songs'].append({'id':i})
            if ic == 11:
                description += '\n   _...and '+str(len(playlist_info['list'])-10)+' more_'
            embd = discord.Embed(title=title, description=description, type='rich', color=discord.Color.red())
            embd.set_thumbnail(url=playlist_info['cover'])
            embd.set_author(name=('Playlist by '+playlist_info['creator_name']))
            await sq['text_channel'].send(embed=embd)
        else:
            pass
        if sq['is_playing'] == False and sq['pos'] == 0:
            sq['is_playing'] = True
            sq['voice_client'].play(discord.FFmpegPCMAudio(sq['songs'][0]['url']), after=lambda e:playback_finished(e,ctx.guild.id))
            await sq['text_channel'].send(embed=discord.Embed(title=('Started Playing: '+sq['songs'][0]['name']+' - '+sq['songs'][0]['artists']), description=('Length: '+sq['songs'][0]['duration']+('\n***(Playback of VIP Songs is not guaranteed, skipping might occur)***') if sq['songs'][0]['vip']==True else ''), type='rich', color=discord.Color.red()).set_thumbnail(url=sq['songs'][0]['album_cover']))
        ### IMPORTANT: backup music source url: 'https://music.163.com/song/media/outer/url?id='+sid+'.mp3'


def get_queue(gid, text, voice):
    if queue.get(gid) == None:
        sq = {'is_connected':False,'is_playing':False,'pos':0,'loop_queue':True,'songs':[],'text_channel':text,'voice_client':voice}
        queue[gid] = sq
        return sq
    else:
        return queue.get(gid)

def playback_finished(err,gid):
    print("Finished playing a song in guild #", gid)
    sq = queue[gid]

    if not sq['voice_client'].is_connected():
        sq['is_playing'] = False
        sq['is_connected'] = False
        sq['songs'] = []
        return

    if sq['pos']+1 == len(sq['songs']):
        #end of queue
        if sq['loop_queue'] == True:
            sq['pos'] = 0
        else:
            sq['is_connected'] = False
            sq['is_playing'] = False
            sq['songs'] = []
            coro = sq['text_channel'].send(embed=discord.Embed(title='Queue Finished', description='To Loop Queue, type `nmb loop`', type='rich', color=discord.Color.red()))
            fut = asyncio.run_coroutine_threadsafe(coro, bot.loop)
            try:
                fut.result()
            except:
                pass
            coro = sq['voice_client'].disconnect()
            fut = asyncio.run_coroutine_threadsafe(coro, bot.loop)
            try:
                fut.result()
            except:
                pass
            return
    else:
        sq['pos'] = sq['pos'] + 1

    song_info = sq['songs'][sq['pos']]
    if song_info.get('name') == None:
        song_info = fetch_song_info(song_info['id'])
    try:
        sq['voice_client'].play(discord.FFmpegPCMAudio(song_info['url']), after=lambda e:playback_finished(e,gid))
    except:
        sq['is_playing'] = False
        sq['is_connected'] = False
        sq['songs'] = []
        return
    if song_info['vip'] == True:
        embd = discord.Embed(title=('Now Playing: '+song_info['name']+' - '+song_info['artists']), description=('#'+str(sq['pos']+1)+' in Queue, Length '+song_info['duration']+'\n***(Playback of VIP Songs is not guaranteed, skipping might occur)***'), type='rich', color=discord.Color.red()).set_thumbnail(url=song_info['album_cover'])
    else:
        embd = discord.Embed(title=('Now Playing: '+song_info['name']+' - '+song_info['artists']), description=('#'+str(sq['pos']+1)+' in Queue, Length '+song_info['duration']), type='rich', color=discord.Color.red()).set_thumbnail(url=song_info['album_cover'])
    
    coro = sq['text_channel'].send(embed=embd)
    fut = asyncio.run_coroutine_threadsafe(coro, bot.loop)
    try:
        fut.result()
    except:
        pass

def format_double_zero(num):
    if num == 0:
        return '00'
    elif num < 10:
        return '0'+str(num)
    else:
        return str(num)

def fetch_playlist_info(sid):
    http = urllib3.PoolManager()
    pl = {}
    rs = http.request('GET', 'https://api.imjad.cn/cloudmusic/?type=playlist&id='+str(sid))
    sd = json.loads(rs.data.decode('utf8'))
    pl['name'] = sd['playlist']['name']
    pl['id'] = sd['playlist']['id']
    pl['creator_id'] = sd['playlist']['creator']['userId']
    pl['creator_name'] = sd['playlist']['creator']['nickname']
    pl['list'] = [ i['id'] for i in sd['playlist']['trackIds'] ]
    pl['cover'] = sd['playlist']['coverImgUrl']
    pl['description'] = 'None' if sd['playlist'].get('description') == None else sd['playlist']['description']
    return pl

def fetch_song_info(sid):
    http = urllib3.PoolManager()
    rs = http.request('GET', 'https://api.imjad.cn/cloudmusic/?type=song&id='+str(sid))
    song = {}
    song['url'] = json.loads(rs.data.decode('utf8'))['data'][0]['url']
    rs = http.request('GET', 'https://api.imjad.cn/cloudmusic/?type=detail&id='+str(sid))
    sd = json.loads(rs.data.decode('utf8'))['songs'][0]
    song['name'] = sd['name']
    song['id'] = sd['id']
    song['artists'] = ' / '.join([ i['name'] for i in sd['ar'] ])
    song['vip'] = False if sd['fee']==0 else True
    song['album'] = sd['al']['name']
    song['album_cover'] = sd['al']['picUrl']
    song['duration_raw'] = sd['dt']
    dur_sec = sd['dt']//1000
    if dur_sec < 3600: #less than 1 hour long
        song['duration'] = format_double_zero(dur_sec//60) + ':' + format_double_zero(dur_sec%60)
    else:
        song['duration'] = str(dur_sec//3600) + ':' + format_double_zero((dur_sec%3600)//60) + ':' + format_double_zero(dur_sec%60)
    return song

bot.run(TOKEN)
