import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

# Bot Token
bot_token = "7582179423:AAEGbCIGhreGppP-SKvFzSn814AjqZjZ9u0"

# Gradio App URL (Replace with your Gradio app URL)
GRADIO_URL = "http://your-gradio-app-url.com/predict"

# Directory for storing media files
MEDIA_DIR = 'media_files'
os.makedirs(MEDIA_DIR, exist_ok=True)

# Function to clean up files after sending them to the user
def clean_up_files(*file_paths):
    """Delete files to save disk space after processing."""
    for file_path in file_paths:
        if os.path.exists(file_path):
            os.remove(file_path)

# Step 1: Start command - Sends welcome message and prompts user to join the channel
async def start(update: Update, context):
    keyboard = [[InlineKeyboardButton("Join Channel", url="https://t.me/TheHub700")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        'Welcome! Please join our channel to proceed.',
        reply_markup=reply_markup
    )

# Step 2: Handle Photo Uploads for face swapping
async def handle_photo(update: Update, context):
    user_id = update.message.from_user.id
    file = await context.bot.get_file(update.message.photo[-1].file_id)

    # Use the user_id and file_id to create a unique filename for this user
    file_path = os.path.join(MEDIA_DIR, f"{user_id}_{update.message.photo[-1].file_id}.jpg")
    await file.download(file_path)

    # Send the photo to Gradio for face-swapping
    swapped_photo = process_media_through_gradio(file_path, 'photo', user_id)
    
    if swapped_photo:
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(swapped_photo, 'rb'))
        clean_up_files(file_path, swapped_photo)  # Clean up both original and processed files
    else:
        await update.message.reply_text("An error occurred during processing.")

# Step 3: Handle Video Uploads for face swapping
async def handle_video(update: Update, context):
    user_id = update.message.from_user.id
    file = await context.bot.get_file(update.message.video.file_id)

    # Use the user_id and file_id to create a unique filename for this user
    file_path = os.path.join(MEDIA_DIR, f"{user_id}_{update.message.video.file_id}.mp4")
    await file.download(file_path)

    # Send the video to Gradio for face-swapping
    swapped_video = process_media_through_gradio(file_path, 'video', user_id)
    
    if swapped_video:
        await context.bot.send_video(chat_id=update.effective_chat.id, video=open(swapped_video, 'rb'))
        clean_up_files(file_path, swapped_video)  # Clean up both original and processed files
    else:
        await update.message.reply_text("An error occurred during processing.")

# Step 4: Function to send media to Gradio and receive the processed result
def process_media_through_gradio(media_path, media_type, user_id):
    try:
        # Send file to Gradio via POST request
        files = {'file': open(media_path, 'rb')}
        response = requests.post(GRADIO_URL, files=files)

        if response.status_code == 200:
            # Save the output (assuming Gradio returns the processed media as a file)
            output_file_path = os.path.join(MEDIA_DIR, f"{user_id}_swapped_output_{os.path.basename(media_path)}")
            with open(output_file_path, 'wb') as f:
                f.write(response.content)
            return output_file_path
        else:
            print(f"Error: {response.status_code}, {response.text}")
            return None
    except Exception as e:
        print(f"Exception during Gradio request: {e}")
        return None

# Step 5: Build the application and add handlers
if __name__ == '__main__':
    # Initialize bot
    application = ApplicationBuilder().token(bot_token).build()

    # Command Handlers
    application.add_handler(CommandHandler('start', start))

    # Media Handlers
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.VIDEO, handle_video))

    # Start polling for updates
    application.run_polling()
  
