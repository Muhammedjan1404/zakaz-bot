import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    filters, ContextTypes, ConversationHandler
)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Define conversation states
COURSE, SEMESTER, FACULTY, SUBJECTS, DEADLINE, TASK_SOURCE, WORK_TYPE = range(7)

# Mock data (replace with your actual data)
FACULTIES = ["Факультет 1", "Факультет 2", "Факультет 3"]
COURSES = ["1 курс", "2 курс", "3 курс", "4 курс"]
SUBJECTS_BY_FACULTY = {
    "Факультет 1": ["Предмет 1", "Предмет 2", "Предмет 3"],
    "Факультет 2": ["Предмет 4", "Предмет 5", "Предмет 6"],
    "Факультет 3": ["Предмет 7", "Предмет 8", "Предмет 9"]
}
WORK_TYPES = ["Промежуточная работа", "Практическая работа", "Проектная работа", "Задание за весь семестр"]

# Store user data
try:
    from collections import defaultdict
    user_data = defaultdict(dict)
except ImportError:
    user_data = {}

# Helper function to create inline keyboard
def create_keyboard(options, columns=2):
    keyboard = []
    for i in range(0, len(options), columns):
        row = [
            InlineKeyboardButton(option, callback_data=str(option))
            for option in options[i:i + columns]
        ]
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

# Command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the conversation and ask for course."""
    await update.message.reply_text(
        "Добро пожаловать в бота для заказа учебных работ!\n\n"
        "Пожалуйста, выберите ваш курс:",
        reply_markup=create_keyboard(COURSES, 2)
    )
    return COURSE

async def course_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store course and ask for semester."""
    query = update.callback_query
    await query.answer()
    
    course = query.data
    user_id = query.from_user.id
    user_data[user_id] = {'course': course}
    
    # Determine available semesters based on course
    course_num = int(course.split()[0])
    semesters = [f"{2*course_num - 1} семестр", f"{2*course_num} семестр"]
    
    await query.edit_message_text(
        f"Вы выбрали {course}. Теперь выберите семестр:",
        reply_markup=create_keyboard(semesters, 2)
    )
    return SEMESTER

async def semester_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store semester and ask for faculty."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_data[user_id]['semester'] = query.data
    
    await query.edit_message_text(
        "Отлично! Теперь выберите ваш факультет:",
        reply_markup=create_keyboard(FACULTIES, 2)
    )
    return FACULTY

async def faculty_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store faculty and ask for subjects."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    faculty = query.data
    user_data[user_id]['faculty'] = faculty
    
    # Get subjects for the selected faculty
    subjects = SUBJECTS_BY_FACULTY.get(faculty, [])
    
    if not subjects:
        await query.edit_message_text(
            "Извините, для вашего факультета пока нет доступных предметов."
        )
        return ConversationHandler.END
    
    user_data[user_id]['subjects'] = []
    
    # Create a message with instructions
    message = (
        "Выберите предмет(ы).\n"
        "• Нажмите на предмет, чтобы выбрать/отменить выбор.\n"
        "• Когда закончите, нажмите 'Готово'."
    )
    
    # Add a "Готово" button
    keyboard = create_keyboard(subjects, 2).inline_keyboard
    keyboard.append([InlineKeyboardButton("Готово", callback_data="done")])
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SUBJECTS

async def subjects_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle subject selection and ask for deadline when done."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    selected_subject = query.data
    
    if selected_subject == "done":
        if not user_data[user_id].get('subjects'):
            await query.edit_message_text(
                "Пожалуйста, выберите хотя бы один предмет.",
                reply_markup=query.message.reply_markup
            )
            return SUBJECTS
        
        await query.edit_message_text(
            "Укажите срок сдачи задания (в формате ДД.ММ.ГГГГ):"
        )
        return DEADLINE
    
    # Toggle subject selection
    if 'subjects' not in user_data[user_id]:
        user_data[user_id]['subjects'] = []
    
    if selected_subject in user_data[user_id]['subjects']:
        user_data[user_id]['subjects'].remove(selected_subject)
    else:
        user_data[user_id]['subjects'].append(selected_subject)
    
    # Update the message to show current selection
    selected_text = "\n".join([f"• {subj}" for subj in user_data[user_id]['subjects']])
    message = (
        f"Выбранные предметы:\n{selected_text if selected_text else 'Нет выбранных предметов'}\n\n"
        "Выберите предмет(ы) или нажмите 'Готово':"
    )
    
    # Update the keyboard to show selected items
    keyboard = []
    subjects = SUBJECTS_BY_FACULTY.get(user_data[user_id].get('faculty', ''), [])
    
    for subject in subjects:
        prefix = "✅ " if subject in user_data[user_id].get('subjects', []) else ""
        keyboard.append([InlineKeyboardButton(f"{prefix}{subject}", callback_data=subject)])
    
    keyboard.append([InlineKeyboardButton("Готово", callback_data="done")])
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SUBJECTS

async def deadline_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store deadline and ask for task source."""
    user_id = update.message.from_user.id
    deadline_text = update.message.text
    
    try:
        # Validate date format
        deadline = datetime.strptime(deadline_text, "%d.%m.%Y")
        if deadline.date() < datetime.now().date():
            await update.message.reply_text(
                "Дата не может быть в прошлом. Пожалуйста, введите корректную дату:"
            )
            return DEADLINE
            
        user_data[user_id]['deadline'] = deadline_text
        
        # Create keyboard for task source selection
        keyboard = [
            [InlineKeyboardButton("Загрузить файл с заданием", callback_data="upload")],
            [InlineKeyboardButton("Войти в Moodle", callback_data="moodle")]
        ]
        
        await update.message.reply_text(
            "Как вы хотите предоставить задание?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return TASK_SOURCE
        
    except ValueError:
        await update.message.reply_text(
            "Некорректный формат даты. Пожалуйста, введите дату в формате ДД.ММ.ГГГГ:"
        )
        return DEADLINE

async def task_source_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store task source and ask for work type."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    task_source = query.data
    user_data[user_id]['task_source'] = "загрузка файла" if task_source == "upload" else "вход в Moodle"
    
    # Ask for work type
    await query.edit_message_text(
        "Выберите тип работы:",
        reply_markup=create_keyboard(WORK_TYPES, 1)
    )
    return WORK_TYPE

async def work_type_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store work type and show summary."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    work_type = query.data
    user_data[user_id]['work_type'] = work_type
    
    # Prepare summary
    summary = (
        "📋 *Ваша заявка оформлена!*\n\n"
        f"*Курс:* {user_data[user_id].get('course', 'Не указано')}\n"
        f"*Семестр:* {user_data[user_id].get('semester', 'Не указан')}\n"
        f"*Факультет:* {user_data[user_id].get('faculty', 'Не указан')}\n"
        f"*Предмет(ы):* {', '.join(user_data[user_id].get('subjects', ['Не указаны']))}\n"
        f"*Срок сдачи:* {user_data[user_id].get('deadline', 'Не указан')}\n"
        f"*Способ загрузки:* {user_data[user_id].get('task_source', 'Не указан')}\n"
        f"*Тип работы:* {work_type}\n\n"
        "Спасибо за заказ! С вами свяжется наш менеджер для уточнения деталей."
    )
    
    await query.edit_message_text(
        summary,
        parse_mode='Markdown'
    )
    
    # Here you would typically save the order to a database
    # and notify the admin about the new order
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel and end the conversation."""
    user_id = update.message.from_user.id
    if user_id in user_data:
        del user_data[user_id]
    
    await update.message.reply_text(
        'Заказ отменен. Если хотите начать заново, нажмите /start.'
    )
    return ConversationHandler.END

def main() -> None:
    """Run the bot."""
    # Create the Application
    application = Application.builder().token(os.getenv('BOT_TOKEN')).build()

    # Add conversation handler with the states
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            COURSE: [CallbackQueryHandler(course_selected)],
            SEMESTER: [CallbackQueryHandler(semester_selected)],
            FACULTY: [CallbackQueryHandler(faculty_selected)],
            SUBJECTS: [CallbackQueryHandler(subjects_selected)],
            DEADLINE: [MessageHandler(filters.TEXT & ~filters.COMMAND, deadline_received)],
            TASK_SOURCE: [CallbackQueryHandler(task_source_selected)],
            WORK_TYPE: [CallbackQueryHandler(work_type_selected)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)

    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    if not os.getenv('BOT_TOKEN'):
        print("Ошибка: Не задан токен бота. Пожалуйста, укажите его в файле .env")
        exit(1)
    main()
