import os
import logging
import tempfile
import requests
from datetime import datetime
from telegram import Update, ChatAction, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
import speech_recognition as sr
from pydub import AudioSegment
from random import choice

class VoiceSearchHandler:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.logger = logging.getLogger(__name__)

        # Cool emojis for different actions
        self.EMOJIS = {
            'processing': '🎧',
            'success': '🎯',
            'error': '❌',
            'search': '🔍',
            'voice': '🎙️',
            'retry': '🔄'
        }

        # Fun loading messages
        self.LOADING_MESSAGES = [
            "🎧 Tuning in to your brilliant thoughts...",
            "🎭 Converting your voice into research magic...",
            "🌟 Processing your awesome request...",
            "🚀 Preparing for paper blast-off...",
            "🧠 Neural networks processing your voice..."
        ]

    def download_voice_file(self, file_url: str, token: str) -> bytes:
        """Download voice file from Telegram servers."""
        headers = {'User-Agent': 'PaperPilotBot/1.0'}
        response = requests.get(file_url, headers=headers)
        return response.content

    def process_voice(self, update: Update, context: CallbackContext) -> None:
        """Main handler for voice messages."""
        chat_id = update.effective_chat.id
        message_id = update.message.message_id

        # Send typing action
        context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

        # Initial processing message with cool loading animation
        processing_msg = update.message.reply_text(
            f"{self.EMOJIS['processing']} Processing your voice search...\n"
            f"{self.get_random_loading_message()}",
            quote=True
        )

        try:
            # Get voice file info
            voice = update.message.voice.get_file()

            # Create temp directory that works in PythonAnywhere
            with tempfile.TemporaryDirectory(dir='/tmp') as temp_dir:
                # Download and save voice file
                voice_content = self.download_voice_file(
                    voice.file_path,
                    context.bot.token
                )

                ogg_path = os.path.join(temp_dir, f'voice_{message_id}.ogg')
                wav_path = os.path.join(temp_dir, f'voice_{message_id}.wav')

                # Save voice content
                with open(ogg_path, 'wb') as f:
                    f.write(voice_content)

                # Convert to WAV using pydub
                audio = AudioSegment.from_ogg(ogg_path)
                audio.export(wav_path, format='wav')

                # Transcribe audio
                text = self.transcribe_audio(wav_path)

                # Create cool inline keyboard for actions
                keyboard = [
                    [
                        InlineKeyboardButton("🔄 Try Again", callback_data=f"retry_voice_{message_id}"),
                        InlineKeyboardButton("✏️ Edit Query", callback_data=f"edit_voice_{message_id}")
                    ],
                    [
                        InlineKeyboardButton("🎯 Search Papers", callback_data=f"search_voice_{text}")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                # Clean special characters for MarkdownV2
                safe_text = text.replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace(']', '\\]').replace('`', '\\`')

                # Update message with transcription result
                processing_msg.edit_text(
                    f"{self.EMOJIS['success']} *Voice Transcription Complete\\!*\n\n"
                    f"🎙️ I heard:\n"
                    f"`{safe_text}`\n\n"
                    f"Choose an action below:",
                    reply_markup=reply_markup,
                    parse_mode='MarkdownV2'
                )

                # Store the transcribed text in context for later use
                if 'voice_searches' not in context.user_data:
                    context.user_data['voice_searches'] = {}
                context.user_data['voice_searches'][message_id] = text

        except Exception as e:
            self.logger.error(f"Voice processing error: {str(e)}")
            error_keyboard = [[
                InlineKeyboardButton("🔄 Try Again", callback_data=f"retry_voice_{message_id}")
            ]]
            processing_msg.edit_text(
                f"{self.EMOJIS['error']} Oops! Something went wrong.\n"
                f"Error: {str(e)}\n\n"
                "Please try again or use text search.",
                reply_markup=InlineKeyboardMarkup(error_keyboard)
            )

    def transcribe_audio(self, audio_path: str) -> str:
        """Transcribe the audio file to text using Google Speech Recognition."""
        with sr.AudioFile(audio_path) as source:
            audio = self.recognizer.record(source)
            try:
                text = self.recognizer.recognize_google(audio)
                return text
            except sr.UnknownValueError:
                raise ValueError("Could not understand the audio")
            except sr.RequestError:
                raise ValueError("Speech recognition service unavailable")

    def get_random_loading_message(self) -> str:
        """Get a random fun loading message."""
        return choice(self.LOADING_MESSAGES)

    def handle_voice_callback(self, update: Update, context: CallbackContext) -> None:
        """Handle callback queries from voice message buttons."""
        query = update.callback_query
        try:
            data_parts = query.data.split('_')
            action = data_parts[0]  # 'retry', 'edit', or 'search'

            if action == 'retry':
                # Delete old message and ask for new voice message
                query.message.delete()
                context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=f"{self.EMOJIS['voice']} Send another voice message!"
                )

            elif action == 'edit':
                # Get the message ID from the correct part of data_parts
                msg_id = data_parts[2]  # Since format is 'edit_voice_<message_id>'
                # Allow user to edit the transcribed text
                original_text = context.user_data.get('voice_searches', {}).get(int(msg_id), '')

                # Escape ALL special characters for MarkdownV2
                safe_text = self.escape_markdown_v2(original_text)

                query.message.edit_text(
                    f"✏️ *Edit your search query:*\n\n"
                    f"Current query: `{safe_text}`\n\n"
                    "Reply to this message with your edited query\\.",
                    parse_mode='MarkdownV2'
                )

            elif action == 'search':
                # Get the search text (everything after 'search_voice_')
                search_text = query.data[12:]  # Skip 'search_voice_'
                context.args = search_text.split()

                # Call the search_papers function
                from main import search_papers
                update.message = query.message
                search_papers(update, context)

            # Answer the callback query to remove the loading state
            query.answer()

        except Exception as e:
            self.logger.error(f"Callback error: {str(e)}")
            query.answer("An error occurred. Please try again.", show_alert=True)
            # Send a message to try again in plain text (no markdown)
            context.bot.send_message(
                chat_id=query.message.chat_id,
                text=f"{self.EMOJIS['error']} Something went wrong. Please try again."
            )

    def handle_edited_message(self, update: Update, context: CallbackContext) -> None:
        """Handle edited search query messages."""
        if update.message.reply_to_message and "Edit your search query" in update.message.reply_to_message.text:
            # Get the edited text
            edited_text = update.message.text

            # Escape the text for display
            safe_text = self.escape_markdown_v2(edited_text)

            # Create search keyboard
            keyboard = [[
                InlineKeyboardButton("🔍 Search with Edited Query", callback_data=f"search_voice_{edited_text}")
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Send confirmation message
            try:
                update.message.reply_text(
                    f"✏️ *Query edited successfully\\!*\n\n"
                    f"New query: `{safe_text}`\n\n"
                    f"Click below to search with this query:",
                    reply_markup=reply_markup,
                    parse_mode='MarkdownV2'
                )
            except Exception as e:
                self.logger.error(f"Error sending edited message: {str(e)}")
                # Fallback to plain text if markdown fails
                update.message.reply_text(
                    "✏️ Query edited successfully!\n\n"
                    f"New query: {edited_text}\n\n"
                    "Click below to search with this query:",
                    reply_markup=reply_markup
                )

    def escape_markdown_v2(self, text: str) -> str:
        """Helper function to escape MarkdownV2 special characters."""
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in special_chars:
            text = text.replace(char, f'\\{char}')
        return text

    def cleanup_temp_files(self, temp_dir: str) -> None:
        """Clean up temporary voice files."""
        try:
            for file in os.listdir(temp_dir):
                if file.startswith('voice_') and (file.endswith('.ogg') or file.endswith('.wav')):
                    os.remove(os.path.join(temp_dir, file))
        except Exception as e:
            self.logger.error(f"Error cleaning up temp files: {str(e)}")