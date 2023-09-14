from configparser import ConfigParser
from datetime import datetime
import logging
from queue import Queue
import spotipy
import spotipy.util as sputil
from telegram.ext import Updater, CommandHandler, MessageHandler
from telegram.ext.filters import Filters
from threading import Lock, Timer


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(threadName)s - %(levelname)s :\t%(message)s')

config = ConfigParser()
config.read('config.ini')


users = {}
music_queue = Queue()
now_playing = None
np_lock = Lock()


# Init spotipy
token = sputil.prompt_for_user_token(
    'SpotMain',
    'app-remote-control streaming',
    client_id=config['spotify']['client_id'],
    client_secret=config['spotify']['client_secret'],
    redirect_uri=config['spotify']['client_redirect']
)

if not token:
    logging.error('Failed to get token!')

spotify = spotipy.Spotify(auth=token)

def auth_guard(cb):
    def check_token(bot, update, *args, **kwargs):
        global sp_oauth, spotify
        
        token_info = sp_oauth.get_cached_token()
        if not token_info or sp_oauth.is_token_expired(token_info):
            token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])

        token = token_info['access_token']
        spotify = spotipy.Spotify(auth=token)
        
        cb(bot, update, *args, **kwargs)
    
    return auth_guard

# Data
class User:
    def __init__(self, id, name):
        self.id = id
        self.name = name

        self.search_result = None
    

    def __str__(self):
        return '<User: {} - {}>'.format(self.name, self.id)


class Song:
    def __init__(self, uri, artist, title, length, suggested_by):
        self.uri = uri
        self.artist = artist
        self.title = title
        self.length = length

        self.suggested_by = suggested_by
    

    def __str__(self):
        return '<Song: {} - {} ({})>'.format(self.artist, self.title, self.uri)


# Operations
def perform_search(user, text):
    s = spotify.search(q=text, limit=1, type='track')
    if len(s['tracks']['items']) == 0:
        return None
    song = s['tracks']['items'][0]

    artist = 'Unknown'
    if len(song['artists']) != 0:
        artist = song['artists'][0]['name']

    return Song(
        uri=song['uri'],
        artist=artist,
        title=song['name'],
        length=song['duration_ms'] / 1000,
        suggested_by=user
    )


def handle_song_change():
    global now_playing

    np_lock.acquire()
    try:
        logging.info('Song change handling triggered.')

        if music_queue.empty():
            now_playing = None
            pause()
        
        else:
            next = music_queue.get()
            now_playing = next
            play_song(next)
            # Set timer for next handling
            t = Timer(next.length, handle_song_change)
            t.start()
    finally:
        np_lock.release()


def queue_song(song):
    music_queue.put(song)
    logging.info('Added to queue: {}'.format(song))
    if now_playing is None:
        handle_song_change()


def play_song(song):
    spotify.start_playback(uris=[song.uri])


def pause():
    spotify.pause_playback()


def get_user(message):
    sf = message.from_user.id
    username = message.from_user.username

    try:
        return users[sf]
    except KeyError:
        logging.info('Added user {} ({})'.format(username, sf))
        u = User(sf, username)
        users[sf] = u
        return u


# Commands
def confirm_song(bot, update):
    u = get_user(update.message)
    if u.search_result is None:
        update.message.reply_text('You have no active search results. Send me a message to search for a song.')
    else:
        queue_song(u.search_result)
        update.message.reply_text('{} - {} has been queued. There are approx. {} songs in the queue.'.format(
            u.search_result.artist, u.search_result.title, music_queue.qsize()
        ))
        u.search_result = None


def start(bot, update):
    get_user(update.message)
    update.message.reply_text('Hi! You can send me a song and/or artist name to search for music, then add it to the queue!')


# Events
def on_message(bot, update):
    u = get_user(update.message)
    s = perform_search(u, update.message.text)

    if s is None:
        update.message.reply_text('Sorry, but I couldn\'nt find any results for your search.')
    else:
        u.search_result = s
        update.message.reply_text('I found a song:\n{} - {}\nEnter (or tap) /confirm to add it '.format(s.artist, s.title)
            + 'to the queue, or just send a message to search again!')


# Set up bot
tg_updater = Updater(config['telegram']['token'])
d = tg_updater.dispatcher

d.add_handler(CommandHandler('start', start))
d.add_handler(CommandHandler('help', start))

# These handlers relates to spotify api, and need constant re-checking of the current token
d.add_handler(CommandHandler('confirm', auth_guard(confirm_song))
d.add_handler(MessageHandler(Filters.text, auth_guard(on_message))

if __name__ == '__main__':
    tg_updater.start_polling()
    logging.info('Bot is nearly ready.')
    tg_updater.idle()
