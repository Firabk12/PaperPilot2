import logging
from telegram import Update, ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
import google.generativeai as genai
import random

logger = logging.getLogger(__name__)

class ChatHandler:
    def __init__(self):
        self.active_chats = {}  # Store active chat sessions
        # Define allowed topics and their related keywords
        self.allowed_topics = {
            "physics": ["quantum", "relativity", "mechanics", "particles", "energy", "force", "waves", "matter"],
            "mathematics": ["algebra", "calculus", "geometry", "statistics", "probability", "theorem", "equation"],
            "computer_science": ["algorithm", "programming", "machine learning", "AI", "data structure", "computation"],
            "biology": ["genetics", "cells", "evolution", "organism", "molecular", "biology", "neuroscience"],
            "chemistry": ["molecule", "reaction", "compound", "element", "bond", "atomic", "chemical"],
            "astronomy": ["cosmos", "galaxy", "planet", "star", "universe", "space", "celestial", "astronomical"],
            "research": ["paper", "study", "experiment", "theory", "hypothesis", "methodology", "analysis"],
            "education": ["learning", "teaching", "academic", "study", "knowledge", "education", "research"]
        }

        # Fun off-topic responses
        self.off_topic_responses = [
            "🤓 Whoa there! Let's keep it scholarly! I'm like a professor who only talks about academic stuff.",
            "🎓 Hey! My brain is wired for science and research. Let's talk about something more... intellectual?",
            "📚 Plot twist: I'm actually a research nerd! Can we discuss something more academic?",
            "🔬 Sorry, I left my gaming console in the laboratory! Let's focus on research and learning!",
            "🤖 *Adjusts virtual glasses* I only speak the language of science and academia!",
            "🎯 Almost had me there! But I'm programmed to be a research enthusiast. Let's talk smart stuff!",
            "⚡ Oops! My knowledge circuits are purely academic. How about some fascinating research topics?",
            "🧠 Error 404: Casual chat not found! Would you like to discuss quantum physics instead?",
            "🌟 I'm like a library that only stocks research papers! Let's explore something scholarly!",
            "🔮 My crystal ball only shows academic content! Care to discuss some fascinating research?"
        ]

    def is_topic_relevant(self, query: str, model) -> bool:
        """Check if the query aligns with academic or research intent using the AI model."""
        check_prompt = f"""
        As an AI, determine if this query is related to academic, scientific, or research topics:
        Query: "{query}"

        Respond with only 'YES' if it’s relevant, or 'NO' if it’s not.
        """
        try:
            response = model.generate_content(check_prompt)
            return response.text.strip() == "YES"
        except Exception as e:
            logger.error(f"Error checking topic relevance: {str(e)}")
            return False  # Default to off-topic if there’s an error

    def generate_response(self, query: str, model) -> str:
        """Generate response using the AI model."""
        prompt = f"""
        As PaperPilot, a research-focused AI assistant, respond to this query:

        {query}

        Guidelines:
        - Focus on academic and scientific accuracy
        - Use scholarly tone while remaining engaging
        - Include relevant scientific concepts
        - Cite general academic knowledge when applicable
        - Keep responses clear and educational
        - If unsure, acknowledge limitations
        """

        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return "I apologize, but I encountered an error processing your query. Please try again."

    def start_chat(self, update: Update, context: CallbackContext) -> None:
        """Initialize a chat session."""
        user_id = update.effective_user.id
        self.active_chats[user_id] = True

        welcome_message = """
🎓 *Welcome to PaperPilot Academic Chat!*

I'm your research-focused AI companion, ready to discuss:
• 📚 Academic Topics
• 🔬 Scientific Concepts
• 🧮 Mathematics
• 💻 Computer Science
• 🌌 Physics & Astronomy
• 🧬 Biology & Chemistry
• 📊 Research Methodologies

*Guidelines:*
• Ask academic/research questions
• Stay focused on educational topics
• Engage in intellectual discussions

Use /endchat to end our conversation.

*Ready to explore the world of knowledge!* 🚀
"""
        keyboard = [[InlineKeyboardButton("❌ End Chat", callback_data="end_chat")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        update.message.reply_text(
            welcome_message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )

    def end_chat(self, update: Update, context: CallbackContext) -> None:
        """End the chat session."""
        user_id = update.effective_user.id
        if user_id in self.active_chats:
            del self.active_chats[user_id]

        end_messages = [
            "🎓 Class dismissed! Feel free to return when you're ready for more academic discussions!",
            "📚 Thanks for the scholarly chat! Come back when curiosity strikes!",
            "🔬 This concludes our intellectual exchange! Until next time!",
            "⚡ Chat session complete! Remember, knowledge is power!",
            "🌟 Thanks for engaging in academic discourse! See you in the next session!"
        ]

        update.effective_message.reply_text(
            random.choice(end_messages),
            parse_mode=ParseMode.MARKDOWN
        )

    def handle_message(self, update: Update, context: CallbackContext, model) -> None:
        """Handle incoming messages during chat with a slick placeholder."""
        user_id = update.effective_user.id

        if user_id not in self.active_chats:
            return

        query = update.message.text

        # Check relevance using the AI model
        if not self.is_topic_relevant(query, model):
            update.message.reply_text(
                random.choice(self.off_topic_responses),
                parse_mode=ParseMode.MARKDOWN
            )
            return

        # Send a dope placeholder message
        placeholder_variants = [
            "🧠 *Analyzing your query...* Hold tight, knowledge incoming!",
            "🔬 *Processing in the lab...* Results dropping soon!",
            "📚 *Flipping through the archives...* Gimme a sec!",
            "🧮 *Running the numbers...* Stay tuned, fam!",
            "🔍 *Peering into the void...* Insight coming hot!",
            "🎓 *PaperPilot at work...* Knowledge drop imminent!",
            "💻 *Compiling the science...* Almost there, bro!"
        ]
        placeholder = random.choice(placeholder_variants)
        placeholder_msg = context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=placeholder,
            parse_mode=ParseMode.MARKDOWN
        )

        # Generate the response
        response = self.generate_response(query, model)

        # Delete the placeholder and send the response
        context.bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=placeholder_msg.message_id
        )
        update.message.reply_text(
            response,
            parse_mode=ParseMode.MARKDOWN
        )