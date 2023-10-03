# NeteaseMusicBot
A Discord music bot for playing songs on the Netease Music platform, written in Python using discord.py.

## Note
This repo has not been updated to work with the new Discord bot APIs.

## Commands
NeteaseMusicBot supports the following commands:
- `nmb play <url>` or `nmb p <url>` plays/queues the song/playlist in the specified URL
- `nmb p <url> shuffle` plays/queues the playlist but shuffles it first
- `nmb p <song name>` searches for the given song and plays the first result (`<song name>` can contain spaces!)
- `nmb search <song name>` or `nmb s <song name>` searches for the given song and lists 5 results
- `nmb cancel` cancel the song selection from `nmb search <song name>`
- `nmb 1` to `nmb 5` selects one song from the search result and plays it
- `nmb queue` or `nmb q` displays the queue
- `nmb skip` or `nmb next` skips the current song
- `nmb jumpto <index>` or `nmb to <index>` jumps to the given position in queue
- `nmb delete <index>` or `nmb del <index>` removes the song at the given position in queue
- `nmb del <start> <end>` removes all songs from `<start>` to `<end>` in queue
- `nmb shuffle` shuffles the entire queue
- `nmb loop` toggles queue loop on/off
- `nmb leave` or `nmb gun` makes me disconnect from the voice channel
