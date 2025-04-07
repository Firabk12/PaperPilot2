from datetime import datetime, timedelta
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import CallbackContext, ConversationHandler
from telegram.error import BadRequest

logger = logging.getLogger(__name__)

# States for the conversation
CHOOSING_FILTER, ENTER_DATE_FROM, ENTER_DATE_TO, ENTER_AUTHOR, ENTER_MIN_CITATIONS, SAVE_FILTER = range(6)

def initialize_filters(context: CallbackContext) -> None:
    """Initialize advanced search filters if they don't exist"""
    if 'advanced_filters' not in context.user_data:
        context.user_data['advanced_filters'] = {
            'date_from': None,
            'date_to': None,
            'author': None,
            'min_citations': None,
            'categories': []
        }

def show_advanced_search_menu(update: Update, context: CallbackContext, execute_search_func=None) -> int:
    """Show advanced search filters menu"""
    logger.info("Showing advanced search menu")

    query = update.callback_query
    if query:
        try:
            query.answer()
        except Exception as e:
            logger.error(f"Error answering callback query: {str(e)}")

    try:
        # Initialize filters if they don't exist
        if 'advanced_filters' not in context.user_data:
            context.user_data['advanced_filters'] = {
                'date_from': None,
                'date_to': None,
                'author': None,
                'min_citations': None,
                'categories': []
            }

        filters = context.user_data['advanced_filters']

        # Create keyboard
        keyboard = [
            [
                InlineKeyboardButton("📅 Date Range", callback_data="filter_date"),
                InlineKeyboardButton("👤 Author", callback_data="filter_author")
            ],
            [
                InlineKeyboardButton("📊 Citations", callback_data="filter_citations"),
                InlineKeyboardButton("🔖 Categories", callback_data="filter_categories")
            ],
            [
                InlineKeyboardButton("🔍 Execute Search", callback_data="filter_execute"),
                InlineKeyboardButton("« Back", callback_data="back_to_search_options")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Safely format current filters with default values
        date_range = "Not set"
        if filters.get('date_from') and filters.get('date_to'):
            date_range = f"{filters['date_from']} to {filters['date_to']}"

        author = filters.get('author', "Not set")
        citations = filters.get('min_citations', "Not set")
        categories = ", ".join(filters.get('categories', [])) or "Not set"

        # Build message
        message = (
            "*Advanced Search Filters* 🔬\n\n"
            "*Current Filters:*\n"
            f"📅 Date Range: {date_range}\n"
            f"👤 Author: {author}\n"
            f"📊 Min Citations: {citations}\n"
            f"🔖 Categories: {categories}\n\n"
            "_Select a filter to modify_"
        )

        # Add timestamp to force message update
        message += f"\n\n_{datetime.utcnow().strftime('%H:%M:%S.%f')[:10]}_"

        if query:
            try:
                query.edit_message_text(
                    message,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.MARKDOWN
                )
            except BadRequest as e:
                if "Message is not modified" in str(e):
                    # Ignore "message not modified" error
                    pass
                else:
                    logger.error(f"BadRequest error: {str(e)}")
                    raise
        else:
            update.message.reply_text(
                message,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )

        logger.info("Advanced search menu displayed successfully")
        return CHOOSING_FILTER

    except Exception as e:
        logger.error(f"Error showing advanced search menu: {str(e)}", exc_info=True)
        error_message = (
            "❌ An error occurred while displaying the advanced search menu.\n"
            "Please try using /search again."
        )

        try:
            if query:
                query.edit_message_text(
                    error_message,
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("« Back to Search", callback_data="back_to_search_options")
                    ]]),
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                update.message.reply_text(error_message)
        except Exception as e2:
            logger.error(f"Error sending error message: {str(e2)}")

        return ConversationHandler.END

def handle_filter_selection(update: Update, context: CallbackContext) -> int:
    """Handle filter selection"""
    query = update.callback_query
    logger.info(f"Filter selection callback received: {query.data}")

    try:
        query.answer()  # Acknowledge the callback query
        initialize_filters(context)  # Initialize filters if they don't exist

        if query.data == "filter_date":
            keyboard = [
                [
                    InlineKeyboardButton("Last Week", callback_data="date_last_week"),
                    InlineKeyboardButton("Last Month", callback_data="date_last_month")
                ],
                [
                    InlineKeyboardButton("Last Year", callback_data="date_last_year"),
                    InlineKeyboardButton("Custom", callback_data="date_custom")
                ],
                [InlineKeyboardButton("« Back", callback_data="back_to_filters")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Show current date filter if exists
            current_filter = ""
            if context.user_data['advanced_filters'].get('date_from') and context.user_data['advanced_filters'].get('date_to'):
                current_filter = f"\nCurrent: {context.user_data['advanced_filters']['date_from']} to {context.user_data['advanced_filters']['date_to']}"

            query.edit_message_text(
                f"*Select Date Range* 📅\n{current_filter}\n\n"
                "Choose a predefined range or select 'Custom' to enter specific dates.",
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            return ENTER_DATE_FROM

        elif query.data == "filter_author":
            logger.info("Showing author search options")
            keyboard = [
                [
                    InlineKeyboardButton("Exact Match", callback_data="author_exact"),
                    InlineKeyboardButton("Last Name", callback_data="author_last")
                ],
                [InlineKeyboardButton("« Back", callback_data="back_to_filters")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            query.edit_message_text(
                "*Choose Author Search Type* 👤\n\n"
                "• *Exact Match:* Search for exact author name\n"
                "• *Last Name:* Search by last name only\n",
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            return ENTER_AUTHOR


        elif query.data == "filter_citations":
            logger.info("Showing citations options")
            keyboard = [
                [
                    InlineKeyboardButton("≥ 10", callback_data="citations_10"),
                    InlineKeyboardButton("≥ 50", callback_data="citations_50"),
                    InlineKeyboardButton("≥ 100", callback_data="citations_100")
                ],
                [InlineKeyboardButton("« Back", callback_data="back_to_filters")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            query.edit_message_text(
                "*Select Minimum Citations* 📊\n\n"
                "Choose the minimum number of citations required.",
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            return ENTER_MIN_CITATIONS

        elif query.data == "filter_categories":
            logger.info("Showing categories options")
            keyboard = [
                [
                    InlineKeyboardButton("Physics", callback_data="category_physics"),
                    InlineKeyboardButton("CS", callback_data="category_cs")
                ],
                [
                    InlineKeyboardButton("Math", callback_data="category_math"),
                    InlineKeyboardButton("Biology", callback_data="category_biology")
                ],
                [InlineKeyboardButton("« Back", callback_data="back_to_filters")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            query.edit_message_text(
                "*Select Categories* 🔖\n\n"
                "Choose one or more research categories:",
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            return CHOOSING_FILTER

        else:
            logger.warning(f"Unexpected callback data: {query.data}")
            return CHOOSING_FILTER

    except Exception as e:
        logger.error(f"Error in filter selection: {str(e)}", exc_info=True)
        try:
            query.edit_message_text(
                "❌ An error occurred. Please try again.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("« Back", callback_data="back_to_filters")
                ]]),
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e2:
            logger.error(f"Error sending error message: {str(e2)}")

        return CHOOSING_FILTER

def handle_category_selection(update: Update, context: CallbackContext) -> int:
    """Handle category selection"""
    query = update.callback_query
    query.answer()

    try:
        category = query.data.split('_')[1]
        initialize_filters(context)

        if 'categories' not in context.user_data['advanced_filters']:
            context.user_data['advanced_filters']['categories'] = []

        categories = context.user_data['advanced_filters']['categories']

        # Toggle category
        if category in categories:
            categories.remove(category)
            query.answer(f"Removed {category}")
        else:
            categories.append(category)
            query.answer(f"Added {category}")

        # Update the menu with current selections
        keyboard = [
            [
                InlineKeyboardButton(
                    f"{'✅' if 'physics' in categories else '⭕️'} Physics",
                    callback_data="category_physics"
                ),
                InlineKeyboardButton(
                    f"{'✅' if 'cs' in categories else '⭕️'} CS",
                    callback_data="category_cs"
                )
            ],
            [
                InlineKeyboardButton(
                    f"{'✅' if 'math' in categories else '⭕️'} Math",
                    callback_data="category_math"
                ),
                InlineKeyboardButton(
                    f"{'✅' if 'biology' in categories else '⭕️'} Biology",
                    callback_data="category_biology"
                )
            ],
            [InlineKeyboardButton("« Back", callback_data="back_to_filters")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        query.edit_message_text(
            "*Select Categories* 🔖\n\n"
            f"Selected categories:\n{', '.join(categories) if categories else 'None'}\n\n"
            "Click to toggle categories:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )

        return CHOOSING_FILTER

    except Exception as e:
        logger.error(f"Error in category selection: {str(e)}")
        return CHOOSING_FILTER

def handle_date_input(update: Update, context: CallbackContext) -> int:
    """Handle date input through buttons"""
    query = update.callback_query
    query.answer()
    logger.info(f"Processing date input: {query.data}")

    try:
        initialize_filters(context)

        if not query.data.startswith("date_"):
            return CHOOSING_FILTER

        option = query.data.split("_")[1]
        end_date = datetime.utcnow()

        # Handle different date range options
        if option in ["last_week", "last_month", "last_year"]:
            if option == "last_week":
                start_date = end_date - timedelta(days=7)
                date_description = "Last 7 days"
            elif option == "last_month":
                start_date = end_date - timedelta(days=30)
                date_description = "Last 30 days"
            else:  # last_year
                start_date = end_date - timedelta(days=365)
                date_description = "Last year"

            # Store the dates
            context.user_data['advanced_filters']['date_from'] = start_date.strftime('%Y-%m-%d')
            context.user_data['advanced_filters']['date_to'] = end_date.strftime('%Y-%m-%d')

            # Show confirmation and return to main menu
            query.answer(f"Date range set to {date_description}", show_alert=True)
            return show_advanced_search_menu(update, context)

        elif option == "custom":
            keyboard = [[InlineKeyboardButton("« Back", callback_data="back_to_filters")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            query.edit_message_text(
                "*Enter Start Date* 📅\n\n"
                "Please enter the start date in YYYY-MM-DD format:\n"
                "Example: `2024-01-01`",
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            context.user_data['awaiting_custom_date'] = True
            context.user_data['awaiting_date_start'] = True  # Add this flag
            return ENTER_DATE_FROM

        return CHOOSING_FILTER

    except Exception as e:
        logger.error(f"Error handling date input: {str(e)}")
        query.edit_message_text(
            "❌ An error occurred. Please try again.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("« Back", callback_data="back_to_filters")
            ]]),
            parse_mode=ParseMode.MARKDOWN
        )
        return CHOOSING_FILTER

def handle_custom_date_message(update: Update, context: CallbackContext) -> int:
    """Handle custom date input messages"""
    logger.info("Handling custom date message")  # Add logging

    try:
        if not context.user_data.get('awaiting_custom_date'):
            logger.info("Not awaiting custom date")
            return CHOOSING_FILTER

        date_text = update.message.text.strip()
        logger.info(f"Received date text: {date_text}")

        # Initialize filters if needed
        initialize_filters(context)

        try:
            input_date = datetime.strptime(date_text, '%Y-%m-%d')
        except ValueError:
            update.message.reply_text(
                "❌ Invalid date format! Please use YYYY-MM-DD format.\n"
                "Example: 2024-01-01",
                parse_mode=ParseMode.MARKDOWN
            )
            return ENTER_DATE_FROM if 'date_from' not in context.user_data['advanced_filters'] else ENTER_DATE_TO

        # Handle start date
        if 'date_from' not in context.user_data['advanced_filters']:
            context.user_data['advanced_filters']['date_from'] = date_text

            # Ask for end date
            keyboard = [[InlineKeyboardButton("« Back", callback_data="back_to_filters")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            update.message.reply_text(
                "*Enter End Date* 📅\n\n"
                "Please enter the end date in YYYY-MM-DD format:\n"
                "Example: `2024-12-31`",
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            return ENTER_DATE_TO

        # Handle end date
        else:
            start_date = datetime.strptime(context.user_data['advanced_filters']['date_from'], '%Y-%m-%d')
            if input_date < start_date:
                update.message.reply_text(
                    "❌ End date must be after start date!",
                    parse_mode=ParseMode.MARKDOWN
                )
                return ENTER_DATE_TO

            context.user_data['advanced_filters']['date_to'] = date_text
            context.user_data['awaiting_custom_date'] = False  # Clear the flag

            update.message.reply_text(
                f"✅ Date range set: {context.user_data['advanced_filters']['date_from']} "
                f"to {date_text}"
            )

            # Return to main menu
            return show_advanced_search_menu(update, context)

    except Exception as e:
        logger.error(f"Error in handle_custom_date_message: {str(e)}", exc_info=True)
        update.message.reply_text(
            "❌ An error occurred. Please try again.",
            parse_mode=ParseMode.MARKDOWN
        )
        return CHOOSING_FILTER

def handle_author_input(update: Update, context: CallbackContext) -> int:
    """Handle author input (both buttons and text)"""
    try:
        # Handle callback query (button press)
        if update.callback_query:
            query = update.callback_query
            query.answer()

            if query.data.startswith("author_"):
                author_type = query.data.split("_")[1]
                context.user_data['author_type'] = author_type

                keyboard = [[InlineKeyboardButton("« Back", callback_data="back_to_filters")]]
                reply_markup = InlineKeyboardMarkup(keyboard)

                query.edit_message_text(
                    f"*Enter Author Name* 👤\n\n"
                    f"Type: {author_type.title()}\n"
                    f"Please enter the author name:",
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.MARKDOWN
                )
                context.user_data['awaiting_author'] = True
                return ENTER_AUTHOR

        # Handle text input
        elif update.message and context.user_data.get('awaiting_author'):
            author = update.message.text.strip()
            if not author:
                update.message.reply_text("❌ Please enter a valid author name")
                return ENTER_AUTHOR

            context.user_data['advanced_filters']['author'] = author
            context.user_data['awaiting_author'] = False

            update.message.reply_text(f"✅ Author filter set: {author}")
            return show_advanced_search_menu(update, context)

        return CHOOSING_FILTER

    except Exception as e:
        logger.error(f"Error in handle_author_input: {str(e)}")
        message = "❌ An error occurred. Please try again."
        if update.callback_query:
            update.callback_query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("« Back", callback_data="back_to_filters")
                ]])
            )
        else:
            update.message.reply_text(message)
        return CHOOSING_FILTER

def handle_citations_input(update: Update, context: CallbackContext) -> int:
    """Handle citations input"""
    query = update.callback_query
    query.answer()
    logger.info(f"Processing citations input: {query.data}")

    try:
        if query.data.startswith("citations_"):
            citations = int(query.data.split("_")[1])
            context.user_data.setdefault('advanced_filters', {})
            context.user_data['advanced_filters']['min_citations'] = citations
            return show_advanced_search_menu(update, context)

    except Exception as e:
        logger.error(f"Error handling citations input: {str(e)}")
        query.edit_message_text(
            "❌ An error occurred. Please try again.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("« Back", callback_data="back_to_filters")
            ]]),
            parse_mode=ParseMode.MARKDOWN
        )

    return CHOOSING_FILTER


def handle_filter_execute(update: Update, context: CallbackContext) -> int:
    """Execute search with advanced filters"""
    query = update.callback_query
    query.answer()
    logger.info("Executing advanced search with filters")

    try:
        filters = context.user_data.get('advanced_filters', {})
        search_parts = []

        # Build search query from filters
        if filters.get('date_from') and filters.get('date_to'):
            search_parts.append(f"submittedDate:[{filters['date_from']} TO {filters['date_to']}]")

        if filters.get('author'):
            author_type = context.user_data.get('author_type', 'exact')
            author = filters['author']
            if author_type == 'last':
                search_parts.append(f"au:*{author}")
            else:
                search_parts.append(f"au:\"{author}\"")

        if filters.get('categories'):
            cats = ' OR '.join(f"cat:{cat}" for cat in filters['categories'])
            if cats:
                search_parts.append(f"({cats})")

        if not search_parts:
            query.edit_message_text(
                "❌ Please set at least one filter before searching!\n\n"
                "Use the buttons below to set your search filters.",
                reply_markup=query.message.reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            return CHOOSING_FILTER

        # Build the final query
        search_query = ' AND '.join(f"({part})" for part in search_parts)

        # Store the query for execute_search function
        context.user_data['search_query'] = search_query

        query.edit_message_text(
            "🔍 Searching with advanced filters...\n\n"
            f"Query: {search_query}",
            parse_mode=ParseMode.MARKDOWN
        )

        # Create a new update object with the search query
        new_update = Update(update.update_id)
        new_update.message = update.effective_message
        context.args = search_query.split()

        # Execute the search
        execute_search(new_update, context)

        return ConversationHandler.END

    except Exception as e:
        logger.error(f"Error executing search: {str(e)}")
        query.edit_message_text(
            "❌ An error occurred while searching. Please try again.",
            parse_mode=ParseMode.MARKDOWN
        )
        return ConversationHandler.END

def cancel_search(update: Update, context: CallbackContext) -> int:
    """Cancel the search process"""
    try:
        if update.callback_query:
            update.callback_query.edit_message_text(
                "🚫 Search cancelled. Use /search to start a new search."
            )
        else:
            update.message.reply_text(
                "🚫 Search cancelled. Use /search to start a new search."
            )
    except Exception as e:
        logger.error(f"Error canceling search: {str(e)}")
        if update.effective_message:
            update.effective_message.reply_text(
                "❌ An error occurred. Please use /search to start over."
            )

    return ConversationHandler.END