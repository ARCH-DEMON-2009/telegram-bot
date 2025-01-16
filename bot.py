from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
import requests

# Replace with your bot token
BOT_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'

# Replace with your RapidAPI details
API_HOST = "gogoanime2.p.rapidapi.com"
API_KEY = "YOUR_RAPIDAPI_KEY"

# Function to fetch episode video URL
def fetch_episode(anime_name, season, episode):
    # Format anime name for the API
    search_url = f"https://{API_HOST}/search"
    params = {"keyw": anime_name}
    headers = {
        "x-rapidapi-host": API_HOST,
        "x-rapidapi-key": API_KEY,
    }

    # Search for the anime
    search_response = requests.get(search_url, headers=headers, params=params)
    if search_response.status_code != 200:
        return None, f"Error: Unable to fetch anime. {search_response.text}"

    search_results = search_response.json()
    if not search_results:
        return None, "No results found for the given anime name."

    # Assuming the first result is the most relevant
    anime_id = search_results[0]["animeId"]

    # Fetch episode links
    episodes_url = f"https://{API_HOST}/anime-details/{anime_id}"
    episodes_response = requests.get(episodes_url, headers=headers)
    if episodes_response.status_code != 200:
        return None, f"Error: Unable to fetch episodes. {episodes_response.text}"

    episodes_data = episodes_response.json()
    episode_list = episodes_data.get("episodesList", [])

    if not episode_list or episode > len(episode_list):
        return None, "Episode not found."

    # Get the episode URL
    episode_video_url = episode_list[episode - 1]["videoUrl"]
    return episode_video_url, None

# Start command
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Welcome! Send me the anime name to get started.")

# Handle anime name input
def anime_name(update: Update, context: CallbackContext):
    anime_name = update.message.text
    context.user_data['anime_name'] = anime_name
    update.message.reply_text(f"You entered: {anime_name}. Now, send the season number.")

# Handle season input
def season(update: Update, context: CallbackContext):
    season = update.message.text
    if not season.isdigit():
        update.message.reply_text("Please enter a valid season number.")
        return
    context.user_data['season'] = int(season)
    update.message.reply_text(f"Season {season} selected. Now, send the episode number.")

# Handle episode input
def episode(update: Update, context: CallbackContext):
    episode = update.message.text
    if not episode.isdigit():
        update.message.reply_text("Please enter a valid episode number.")
        return
    context.user_data['episode'] = int(episode)

    anime_name = context.user_data['anime_name']
    season = context.user_data['season']
    episode_number = context.user_data['episode']

    video_url, error = fetch_episode(anime_name, season, episode_number)
    if error:
        update.message.reply_text(error)
        return

    # Keyboard for navigation
    keyboard = [
        [InlineKeyboardButton("Next Episode", callback_data='next_episode')],
        [InlineKeyboardButton("Previous Episode", callback_data='prev_episode')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(f"Here is Season {season}, Episode {episode_number} of {anime_name}:")
    update.message.reply_video(video=video_url, reply_markup=reply_markup)

# Handle navigation buttons
def button(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    anime_name = context.user_data.get('anime_name', 'Unknown Anime')
    season = context.user_data.get('season', 1)
    episode = context.user_data.get('episode', 1)

    if query.data == 'next_episode':
        episode += 1
    elif query.data == 'prev_episode' and episode > 1:
        episode -= 1

    context.user_data['episode'] = episode
    video_url, error = fetch_episode(anime_name, season, episode)

    if error:
        query.edit_message_text(text=error)
        return

    keyboard = [
        [InlineKeyboardButton("Next Episode", callback_data='next_episode')],
        [InlineKeyboardButton("Previous Episode", callback_data='prev_episode')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    query.edit_message_text(text=f"Here is Season {season}, Episode {episode} of {anime_name}:")
    query.edit_message_media(media={'type': 'video', 'media': video_url}, reply_markup=reply_markup)

# Main function to start the bot
def main():
    updater = Updater(BOT_TOKEN, use_context=True)

    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, anime_name))
    dp.add_handler(MessageHandler(Filters.regex(r'^\d+$'), season))
    dp.add_handler(MessageHandler(Filters.regex(r'^\d+$'), episode))
    dp.add_handler(CallbackQueryHandler(button))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
