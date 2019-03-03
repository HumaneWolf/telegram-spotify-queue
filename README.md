# Telegram Spotify Queue

This is a Telegram bot that uses the Spotify playback API to allow users to queue songs via Telegram.


## Features

* Keeps track of the queue, and starts the next song on time.
* Allows users to search for songs by sending a message - before they confirm it and queue it.


## To do / ideas

* Clean up Spotipy, maybe just write our own API wrapper.
    * I started using it as it was listed on the Spotify API Documentation. Turns out the version on PIP does not seem to be up to date..
* Blacklisting users
* User rate limiting
* Simple HTTP API exposing whether it is playing, queue size, and what song it is playing.
* A way to remote control the queue:
    * Remove songs
    * Skip songs
    * etc.


## Setting it up

1. Install Python 3.7.
2. Install pipenv.
3. Run pipenv sync to install dependencies.
4. Create the config.ini file, and add a Telegram bot token, and the Spotify OAuth info.
    * You can get the bot token by creating a bot using @BotFather on Telegram.
    * You can get the Spotify OAuth info by creating an application on the Spotify Developer Portal.
5. Run the bot.

The first time you run it, it will open a Spotify login page in your browser. Log in, then copy/paste the resulting link into the terminal window running the bot, and press enter. This is not required when running the bot again later.

You might need to start playing music on the desired Spotify device manually, so that Spotify identifies it as the active device.
