import logging
from datetime import datetime
from typing import List, Dict, Optional
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import CallbackContext
from telegram.error import BadRequest

logger = logging.getLogger(__name__)

class AdminManager:
    def __init__(self):
        # First, set the owner ID (your Telegram ID)
        self.owner_id = 6111380028  # Replace with your actual Telegram ID if different

        # Then create necessary directories
        self.data_dir = "bot_data"
        self.admin_file = os.path.join(self.data_dir, "admins.json")
        self.stats_file = os.path.join(self.data_dir, "statistics.json")
        self.users_file = os.path.join(self.data_dir, "users.json")
        self.restrictions_file = os.path.join(self.data_dir, "restrictions.json")

        # Ensure directories exist
        os.makedirs(self.data_dir, exist_ok=True)

        # Initialize data files if they don't exist
        self._initialize_files()

    def _initialize_files(self):
        """Initialize JSON files if they don't exist."""
        default_files = {
            self.admin_file: {
                "admins": [self.owner_id],
                "owner": self.owner_id
            },
            self.stats_file: {
                "total_users": 0,
                "total_searches": 0,
                "total_downloads": 0,
                "total_summaries": 0,
                "active_users_today": 0,
                "last_reset": datetime.utcnow().strftime("%Y-%m-%d")
            },
            self.users_file: {},
            self.restrictions_file: {
                "blocked": [],
                "restricted": {}
            }
        }

        for file_path, default_data in default_files.items():
            if not os.path.exists(file_path):
                with open(file_path, 'w') as f:
                    json.dump(default_data, f, indent=4)

    def _load_data(self, file_path: str) -> dict:
        """Load data from JSON file."""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading {file_path}: {str(e)}")
            return {}

    def _save_data(self, file_path: str, data: dict) -> None:
        """Save data to JSON file."""
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving to {file_path}: {str(e)}")

    def is_admin(self, user_id: int) -> bool:
        """Check if user is an admin."""
        data = self._load_data(self.admin_file)
        return user_id in data.get("admins", [])

    def is_owner(self, user_id: int) -> bool:
        """Check if user is the owner."""
        return user_id == self.owner_id

    def show_admin_panel(self, update: Update, context: CallbackContext) -> None:
        """Display the admin control panel."""
        user_id = update.effective_user.id

        if not self.is_admin(user_id):
            update.message.reply_text("🚫 You don't have permission to access admin controls.")
            return

        keyboard = [
            [InlineKeyboardButton("📊 Statistics", callback_data="admin_stats")],
            [InlineKeyboardButton("👥 Manage Users", callback_data="admin_users")],
            [InlineKeyboardButton("🚫 Manage Restrictions", callback_data="admin_restrictions")],
            [InlineKeyboardButton("👮‍♂️ Manage Admins", callback_data="admin_admins")]
        ]

        if self.is_owner(user_id):
            keyboard.append([InlineKeyboardButton("📢 Broadcast Message", callback_data="admin_broadcast")])

        reply_markup = InlineKeyboardMarkup(keyboard)

        stats = self._load_data(self.stats_file)
        message = f"""
🛠 *Admin Control Panel*

Current Statistics:
• 👥 Total Users: {stats.get('total_users', 0)}
• 🔍 Total Searches: {stats.get('total_searches', 0)}
• 📥 Total Downloads: {stats.get('total_downloads', 0)}
• 🤖 Total Summaries: {stats.get('total_summaries', 0)}
• 📊 Active Today: {stats.get('active_users_today', 0)}

Select an option to manage:
"""

        if update.callback_query:
            update.callback_query.answer()
            update.callback_query.edit_message_text(
                text=message,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            update.message.reply_text(
                text=message,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )

    def handle_stats(self, update: Update, context: CallbackContext) -> None:
        """Show detailed statistics."""
        query = update.callback_query
        stats = self._load_data(self.stats_file)
        users = self._load_data(self.users_file)

        active_today = len([u for u in users.values()
                          if datetime.strptime(u['last_active'], "%Y-%m-%d %H:%M:%S").date()
                          == datetime.utcnow().date()])

        message = f"""
📊 *Detailed Statistics*

👥 *User Stats:*
• Total Users: {stats.get('total_users', 0)}
• Active Today: {active_today}

🔍 *Activity Stats:*
• Total Searches: {stats.get('total_searches', 0)}
• Total Downloads: {stats.get('total_downloads', 0)}
• Total Summaries: {stats.get('total_summaries', 0)}

📈 *System Stats:*
• Last Reset: {stats.get('last_reset', 'Never')}
• Data Points: {len(users)}

« Back to return to main menu
"""
        keyboard = [[InlineKeyboardButton("« Back", callback_data="admin_panel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )

    def update_stats(self, action: str) -> None:
        """Update bot statistics."""
        stats = self._load_data(self.stats_file)

        if action in ["searches", "downloads", "summaries"]:
            stats[f"total_{action}"] = stats.get(f"total_{action}", 0) + 1

        self._save_data(self.stats_file, stats)

    def update_user_stats(self, user_id: int, username: str, action: str) -> None:
        """Update user statistics."""
        stats = self._load_data(self.stats_file)
        users = self._load_data(self.users_file)

        if str(user_id) not in users:
            users[str(user_id)] = {
                "username": username,
                "first_seen": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                "last_active": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                "total_actions": 0,
                "actions": {
                    "searches": 0,
                    "downloads": 0,
                    "summaries": 0
                }
            }
            stats["total_users"] += 1
        else:
            users[str(user_id)]["last_active"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            users[str(user_id)]["username"] = username

        users[str(user_id)]["total_actions"] += 1
        if action in users[str(user_id)]["actions"]:
            users[str(user_id)]["actions"][action] += 1

        self._save_data(self.users_file, users)
        self._save_data(self.stats_file, stats)

    def handle_users(self, update: Update, context: CallbackContext) -> None:
        """Show user management panel."""
        query = update.callback_query
        users = self._load_data(self.users_file)

        # Create a paginated user list (10 users per page)
        page = context.user_data.get('user_page', 0)
        users_list = list(users.items())
        total_pages = (len(users_list) - 1) // 10 + 1
        start_idx = page * 10
        end_idx = start_idx + 10
        current_users = users_list[start_idx:end_idx]

        message = "👥 *User Management Panel*\n\n"

        for user_id, user_data in current_users:
            username = user_data.get('username', 'No username')
            last_active = user_data.get('last_active', 'Never')
            total_actions = user_data.get('total_actions', 0)
            message += f"*ID:* `{user_id}`\n"
            message += f"*Username:* @{username}\n"
            message += f"*Last Active:* {last_active}\n"
            message += f"*Total Actions:* {total_actions}\n"
            message += "─────────────────\n"

        # Create navigation keyboard
        keyboard = []
        nav_row = []

        if page > 0:
            nav_row.append(InlineKeyboardButton("◀️ Previous", callback_data="users_prev"))

        if end_idx < len(users_list):
            nav_row.append(InlineKeyboardButton("Next ▶️", callback_data="users_next"))

        if nav_row:
            keyboard.append(nav_row)

        keyboard.extend([
            [InlineKeyboardButton("🚫 Restrict User", callback_data="users_restrict"),
             InlineKeyboardButton("⛔️ Block User", callback_data="users_block")],
            [InlineKeyboardButton("« Back to Admin Panel", callback_data="admin_panel")]
        ])

        message += f"\nPage {page + 1}/{total_pages}"

        reply_markup = InlineKeyboardMarkup(keyboard)

        query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )

    def handle_user_navigation(self, update: Update, context: CallbackContext) -> None:
        """Handle user list navigation."""
        query = update.callback_query
        action = query.data.split('_')[1]

        if action == 'prev':
            context.user_data['user_page'] = max(0, context.user_data.get('user_page', 0) - 1)
        elif action == 'next':
            context.user_data['user_page'] = context.user_data.get('user_page', 0) + 1

        self.handle_users(update, context)

    def restrict_user(self, update: Update, context: CallbackContext, user_id: int, duration_hours: int) -> None:
        """Restrict a user for specified duration."""
        restrictions = self._load_data(self.restrictions_file)

        end_time = datetime.utcnow().replace(microsecond=0) + datetime.timedelta(hours=duration_hours)

        restrictions["restricted"][str(user_id)] = {
            "end_time": end_time.strftime("%Y-%m-%d %H:%M:%S"),
            "restricted_by": update.effective_user.id,
            "reason": context.user_data.get('restrict_reason', 'No reason provided')
        }

        self._save_data(self.restrictions_file, restrictions)

    def block_user(self, update: Update, context: CallbackContext, user_id: int) -> None:
        """Permanently block a user."""
        restrictions = self._load_data(self.restrictions_file)

        if user_id not in restrictions["blocked"]:
            restrictions["blocked"].append(user_id)

        self._save_data(self.restrictions_file, restrictions)

    def unblock_user(self, update: Update, context: CallbackContext, user_id: int) -> None:
        """Unblock a user."""
        restrictions = self._load_data(self.restrictions_file)

        if user_id in restrictions["blocked"]:
            restrictions["blocked"].remove(user_id)

        if str(user_id) in restrictions["restricted"]:
            del restrictions["restricted"][str(user_id)]

        self._save_data(self.restrictions_file, restrictions)

    def handle_broadcast(self, update: Update, context: CallbackContext) -> None:
        """Show broadcast message panel."""
        query = update.callback_query

        message = """
📢 *Broadcast Message Panel*

First, select your target audience:

👥 *Target Options:*
• 📌 All Users
• ⚡️ Active Users (Last 24h)
• 🎯 Specific User(s)

Choose wisely! Your message will only be sent to the selected audience.
"""
        keyboard = [
            [InlineKeyboardButton("📌 All Users", callback_data="broadcast_target_all")],
            [InlineKeyboardButton("⚡️ Active Users", callback_data="broadcast_target_active")],
            [InlineKeyboardButton("🎯 Specific User(s)", callback_data="broadcast_target_specific")],
            [InlineKeyboardButton("« Back to Admin Panel", callback_data="admin_panel")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )

    def handle_broadcast_target(self, update: Update, context: CallbackContext) -> None:
        """Handle broadcast target selection."""
        query = update.callback_query
        target = query.data.split('_')[2]  # broadcast_target_[all|active|specific]

        # Store the target in context
        context.user_data['broadcast_target'] = target

        if target == 'specific':
            return self.show_user_selection(update, context)
        else:
            return self.show_broadcast_type(update, context)

    def show_user_selection(self, update: Update, context: CallbackContext) -> None:
        """Show user selection panel for specific targeting."""
        query = update.callback_query
        users = self._load_data(self.users_file)

        # Get current page from context or default to 0
        page = context.user_data.get('broadcast_user_page', 0)
        users_list = list(users.items())
        total_pages = (len(users_list) - 1) // 5 + 1
        start_idx = page * 5
        end_idx = start_idx + 5

        # Get selected users from context or initialize empty list
        selected_users = context.user_data.get('broadcast_selected_users', [])

        message = """
🎯 *Select Target Users*

Choose users to receive your broadcast:
✅ = Selected  |  ⭕️ = Not Selected

"""
        keyboard = []

        # Add user selection buttons
        for user_id, user_data in users_list[start_idx:end_idx]:
            username = user_data.get('username', 'No username')
            is_selected = user_id in selected_users
            select_text = "✅" if is_selected else "⭕️"
            user_text = f"{select_text} @{username}"
            keyboard.append([InlineKeyboardButton(
                user_text,
                callback_data=f"broadcast_select_user_{user_id}"
            )])

        # Add navigation buttons
        nav_row = []
        if page > 0:
            nav_row.append(InlineKeyboardButton("◀️ Previous", callback_data="broadcast_users_prev"))
        if end_idx < len(users_list):
            nav_row.append(InlineKeyboardButton("Next ▶️", callback_data="broadcast_users_next"))
        if nav_row:
            keyboard.append(nav_row)

        # Add control buttons
        keyboard.extend([
            [InlineKeyboardButton("✅ Confirm Selection", callback_data="broadcast_users_confirm")],
            [InlineKeyboardButton("« Back to Target Selection", callback_data="admin_broadcast")]
        ])

        message += f"\nSelected: {len(selected_users)} user(s)\nPage {page + 1}/{total_pages}"

        reply_markup = InlineKeyboardMarkup(keyboard)

        query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )

    def handle_user_selection(self, update: Update, context: CallbackContext) -> None:
        """Handle user selection for specific targeting."""
        query = update.callback_query
        action = query.data.split('_')[2]  # broadcast_select_[user|prev|next|confirm]

        if action == 'user':
            user_id = query.data.split('_')[3]
            selected_users = context.user_data.get('broadcast_selected_users', [])

            if user_id in selected_users:
                selected_users.remove(user_id)
            else:
                selected_users.append(user_id)

            context.user_data['broadcast_selected_users'] = selected_users
            self.show_user_selection(update, context)

        elif action == 'prev':
            context.user_data['broadcast_user_page'] = max(0, context.user_data.get('broadcast_user_page', 0) - 1)
            self.show_user_selection(update, context)

        elif action == 'next':
            context.user_data['broadcast_user_page'] = context.user_data.get('broadcast_user_page', 0) + 1
            self.show_user_selection(update, context)

        elif action == 'confirm':
            self.show_broadcast_type(update, context)

    def show_broadcast_type(self, update: Update, context: CallbackContext) -> None:
        """Show broadcast type selection after target is chosen."""
        query = update.callback_query
        target = context.user_data.get('broadcast_target', 'all')

        target_desc = {
            'all': 'All Users',
            'active': 'Active Users (Last 24h)',
            'specific': f"Selected Users ({len(context.user_data.get('broadcast_selected_users', []))})"
        }

        message = f"""
📢 *Broadcast Message Panel*

*Target Audience:* {target_desc[target]}

Select message type:
• 📝 Text Message
• 🖼 Photo with Caption
• 🎥 Video with Caption
• 📄 Document with Caption
"""

        keyboard = [
            [InlineKeyboardButton("📝 Text Message", callback_data="broadcast_type_text"),
             InlineKeyboardButton("🖼 Photo", callback_data="broadcast_type_photo")],
            [InlineKeyboardButton("🎥 Video", callback_data="broadcast_type_video"),
             InlineKeyboardButton("📄 Document", callback_data="broadcast_type_document")],
            [InlineKeyboardButton("« Change Target", callback_data="admin_broadcast")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )

    def handle_restrictions(self, update: Update, context: CallbackContext) -> None:
        """Show restriction management panel."""
        query = update.callback_query
        restrictions = self._load_data(self.restrictions_file)
        users = self._load_data(self.users_file)

        # Get current page from context or default to 0
        page = context.user_data.get('restriction_page', 0)

        # Combine blocked and restricted users
        restricted_users = []

        # Add blocked users
        for user_id in restrictions.get("blocked", []):
            user_data = users.get(str(user_id), {})
            restricted_users.append({
                "id": user_id,
                "username": user_data.get("username", "Unknown"),
                "type": "Blocked",
                "end_time": "Permanent",
                "restricted_by": "Admin"
            })

        # Add temporarily restricted users
        for user_id, data in restrictions.get("restricted", {}).items():
            user_data = users.get(str(user_id), {})
            end_time = datetime.strptime(data["end_time"], "%Y-%m-%d %H:%M:%S")
            if datetime.utcnow() < end_time:  # Only show active restrictions
                restricted_users.append({
                    "id": int(user_id),
                    "username": user_data.get("username", "Unknown"),
                    "type": "Restricted",
                    "end_time": data["end_time"],
                    "restricted_by": data.get("restricted_by", "Unknown")
                })

        total_pages = (len(restricted_users) - 1) // 5 + 1 if restricted_users else 1
        start_idx = page * 5
        end_idx = start_idx + 5

        message = """
🚫 *Restriction Management*

Current restricted/blocked users:
"""

        if not restricted_users:
            message += "\nNo users are currently restricted or blocked."
        else:
            for user in restricted_users[start_idx:end_idx]:
                message += f"\n*User:* @{user['username']} (`{user['id']}`)"
                message += f"\n*Type:* {user['type']}"
                message += f"\n*Until:* {user['end_time']}"
                message += "\n───────────────"

        keyboard = [
            [InlineKeyboardButton("🚫 Restrict User", callback_data="restrict_add"),
             InlineKeyboardButton("⛔️ Block User", callback_data="restrict_block")],
            [InlineKeyboardButton("✅ Remove Restriction", callback_data="restrict_remove")]
        ]

        # Add navigation buttons if needed
        if total_pages > 1:
            nav_row = []
            if page > 0:
                nav_row.append(InlineKeyboardButton("◀️ Previous", callback_data="restrict_prev"))
            if page < total_pages - 1:
                nav_row.append(InlineKeyboardButton("Next ▶️", callback_data="restrict_next"))
            if nav_row:
                keyboard.append(nav_row)

        keyboard.append([InlineKeyboardButton("« Back to Admin Panel", callback_data="admin_panel")])

        message += f"\n\nPage {page + 1}/{total_pages}"
        reply_markup = InlineKeyboardMarkup(keyboard)

        query.edit_message_text(text=message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

    def handle_admin_management(self, update: Update, context: CallbackContext) -> None:
        """Show admin management panel."""
        query = update.callback_query
        admin_data = self._load_data(self.admin_file)
        users = self._load_data(self.users_file)

        admins = admin_data.get("admins", [])
        owner = admin_data.get("owner", self.owner_id)

        message = """
👮‍♂️ *Admin Management*

Current admins:
"""

        for admin_id in admins:
            user_data = users.get(str(admin_id), {})
            username = user_data.get("username", "Unknown")
            is_owner = admin_id == owner
            message += f"\n{'👑' if is_owner else '👮‍♂️'} @{username} (`{admin_id}`)"
            if is_owner:
                message += " - *Owner*"

        keyboard = []

        # Only owner can add/remove admins
        if update.effective_user.id == owner:
            keyboard.extend([
                [InlineKeyboardButton("➕ Add Admin", callback_data="admin_add")],
                [InlineKeyboardButton("➖ Remove Admin", callback_data="admin_remove")]
            ])

        keyboard.append([InlineKeyboardButton("« Back to Admin Panel", callback_data="admin_panel")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(text=message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

    def handle_restriction_action(self, update: Update, context: CallbackContext) -> None:
        """Handle restriction actions (add/remove/navigate)."""
        query = update.callback_query
        action = query.data.split('_')[1]

        if action in ['prev', 'next']:
            page = context.user_data.get('restriction_page', 0)
            context.user_data['restriction_page'] = page + (1 if action == 'next' else -1)
            return self.handle_restrictions(update, context)

        elif action == 'add':
            message = """
🚫 *Add Restriction*

Send the user's ID or username and duration in this format:
`username/ID duration_in_hours reason`

Example:
`123456789 24 Spamming`
or
`@username 48 Violation of rules`

Send /cancel to cancel this operation.
"""
            context.user_data['expecting_restriction'] = True
            keyboard = [[InlineKeyboardButton("« Cancel", callback_data="restrict_cancel")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(text=message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

        elif action == 'block':
            message = """
⛔️ *Block User*

Send the user's ID or username to block:
`username/ID reason`

Example:
`123456789 Repeated violations`
or
`@username Severe spam`

Send /cancel to cancel this operation.
"""
            context.user_data['expecting_block'] = True
            keyboard = [[InlineKeyboardButton("« Cancel", callback_data="restrict_cancel")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(text=message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

        elif action == 'remove':
            message = """
✅ *Remove Restriction*

Send the user's ID or username to unblock/unrestrict:
`username/ID`

Example:
`123456789`
or
`@username`

Send /cancel to cancel this operation.
"""
            context.user_data['expecting_unrestrict'] = True
            keyboard = [[InlineKeyboardButton("« Cancel", callback_data="restrict_cancel")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(text=message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

        elif action == 'cancel':
            context.user_data.pop('expecting_restriction', None)
            context.user_data.pop('expecting_block', None)
            context.user_data.pop('expecting_unrestrict', None)
            return self.handle_restrictions(update, context)

    def handle_admin_action(self, update: Update, context: CallbackContext) -> None:
        """Handle admin management actions (add/remove)."""
        query = update.callback_query
        action = query.data.split('_')[1]

        if update.effective_user.id != self.owner_id:
            query.answer("Only the owner can manage admins!")
            return

        if action == 'add':
            message = """
➕ *Add New Admin*

Send the user's ID or username to promote to admin:
`username/ID`

Example:
`123456789`
or
`@username`

Send /cancel to cancel this operation.
"""
            context.user_data['expecting_admin_add'] = True

        elif action == 'remove':
            message = """
➖ *Remove Admin*

Send the user's ID or username to demote:
`username/ID`

Example:
`123456789`
or
`@username`

Send /cancel to cancel this operation.
"""
            context.user_data['expecting_admin_remove'] = True

        keyboard = [[InlineKeyboardButton("« Cancel", callback_data="admin_cancel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(text=message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

    def is_user_restricted(self, user_id: int) -> bool:
        """Check if user is restricted or blocked."""
        restrictions = self._load_data(self.restrictions_file)

        if user_id in restrictions.get("blocked", []):
            return True

        if str(user_id) in restrictions.get("restricted", {}):
            restriction = restrictions["restricted"][str(user_id)]
            end_time = datetime.strptime(restriction["end_time"], "%Y-%m-%d %H:%M:%S")

            if datetime.utcnow() < end_time:
                return True
            else:
                del restrictions["restricted"][str(user_id)]
                self._save_data(self.restrictions_file, restrictions)

        return False