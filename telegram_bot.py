import os
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    filters, ContextTypes, ConversationHandler
)
from app import app, db, User, Assignment
from dotenv import load_dotenv

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
WORK_TYPES = ["Промежуточная работа", "Практическая работа", "Проектная работа", "Задание за весь семестр"]

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
        "👋 Добро пожаловать в бота для заказа учебных работ!\n\n"
        "📚 Пожалуйста, выберите ваш курс:",
        reply_markup=create_keyboard(COURSES, 2)
    )
    return COURSE

async def course_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store course and ask for semester."""
    query = update.callback_query
    await query.answer()
    
    course = query.data
    user_id = query.from_user.id
    context.user_data['course'] = course
    
    # Determine available semesters based on course
    course_num = int(course.split()[0])
    semesters = [f"{2*course_num - 1} семестр", f"{2*course_num} семестр"]
    
    await query.edit_message_text(
        f"🎓 Вы выбрали {course}.\n\n"
        "📆 Теперь выберите семестр:",
        reply_markup=create_keyboard(semesters, 2)
    )
    return SEMESTER

async def semester_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store semester and ask for faculty."""
    query = update.callback_query
    await query.answer()
    
    context.user_data['semester'] = query.data
    
    await query.edit_message_text(
        "🏛️ Отлично! Теперь выберите ваш факультет:",
        reply_markup=create_keyboard(FACULTIES, 2)
    )
    return FACULTY

async def faculty_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store faculty and ask for subjects."""
    query = update.callback_query
    await query.answer()
    
    faculty = query.data
    context.user_data['faculty'] = faculty
    
    # Get subjects for the selected faculty (in a real app, fetch from database)
    subjects = [f"Предмет {i+1}" for i in range(3)]  # Mock data
    
    context.user_data['subjects'] = []
    
    # Create a message with instructions
    message = (
        "📚 Выберите предмет(ы).\n"
        "• Нажмите на предмет, чтобы выбрать/отменить выбор.\n"
        "• Когда закончите, нажмите 'Готово'."
    )
    
    # Add a "Готово" button
    keyboard = create_keyboard(subjects, 2).inline_keyboard
    keyboard.append([InlineKeyboardButton("✅ Готово", callback_data="done")])
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SUBJECTS

async def subjects_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle subject selection and ask for deadline when done."""
    query = update.callback_query
    await query.answer()
    
    selected_subject = query.data
    
    if selected_subject == "done":
        if not context.user_data.get('subjects'):
            await query.edit_message_text(
                "Пожалуйста, выберите хотя бы один предмет.",
                reply_markup=query.message.reply_markup
            )
            return SUBJECTS
        
        await query.edit_message_text(
            "📅 Укажите срок сдачи задания (в формате ДД.ММ.ГГГГ):"
        )
        return DEADLINE
    
    # Toggle subject selection
    if 'subjects' not in context.user_data:
        context.user_data['subjects'] = []
    
    if selected_subject in context.user_data['subjects']:
        context.user_data['subjects'].remove(selected_subject)
    else:
        context.user_data['subjects'].append(selected_subject)
    
    # Update the message to show current selection
    selected_text = "\n".join([f"• {subj}" for subj in context.user_data['subjects']])
    message = (
        f"📋 Выбранные предметы:\n{selected_text if selected_text else 'Нет выбранных предметов'}\n\n"
        "Выберите предмет(ы) или нажмите 'Готово':"
    )
    
    # Update the keyboard to show selected items
    keyboard = []
    for subject in [f"Предмет {i+1}" for i in range(3)]:  # Mock subjects
        prefix = "✅ " if subject in context.user_data.get('subjects', []) else ""
        keyboard.append([InlineKeyboardButton(f"{prefix}{subject}", callback_data=subject)])
    
    keyboard.append([InlineKeyboardButton("✅ Готово", callback_data="done")])
    
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
                "❌ Дата не может быть в прошлом. Пожалуйста, введите корректную дату:"
            )
            return DEADLINE
            
        context.user_data['deadline'] = deadline_text
        
        # Create keyboard for task source selection
        keyboard = [
            [InlineKeyboardButton("📤 Загрузить файл с заданием", callback_data="upload")],
            [InlineKeyboardButton("🔗 Войти в Moodle", callback_data="moodle")]
        ]
        
        await update.message.reply_text(
            "📎 Как вы хотите предоставить задание?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return TASK_SOURCE
        
    except ValueError:
        await update.message.reply_text(
            "❌ Некорректный формат даты. Пожалуйста, введите дату в формате ДД.ММ.ГГГГ:"
        )
        return DEADLINE

async def task_source_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store task source and ask for work type."""
    query = update.callback_query
    await query.answer()
    
    task_source = query.data
    context.user_data['task_source'] = "загрузка файла" if task_source == "upload" else "вход в Moodle"
    
    # Ask for work type
    await query.edit_message_text(
        "📝 Выберите тип работы:",
        reply_markup=create_keyboard(WORK_TYPES, 1)
    )
    return WORK_TYPE

async def work_type_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store work type and show summary."""
    query = update.callback_query
    await query.answer()
    
    work_type = query.data
    user_data = context.user_data
    
    # Prepare summary
    summary = (
        "📋 *Ваша заявка оформлена!*\n\n"
        f"*Курс:* {user_data.get('course', 'Не указано')}\n"
        f"*Семестр:* {user_data.get('semester', 'Не указан')}\n"
        f"*Факультет:* {user_data.get('faculty', 'Не указан')}\n"
        f"*Предмет(ы):* {', '.join(user_data.get('subjects', ['Не указаны']))}\n"
        f"*Срок сдачи:* {user_data.get('deadline', 'Не указан')}\n"
        f"*Способ загрузки:* {user_data.get('task_source', 'Не указан')}\n"
        f"*Тип работы:* {work_type}\n\n"
        "✅ Спасибо за заказ! С вами свяжется наш менеджер для уточнения деталей."
    )
    
    # Save to database
    with app.app_context():
        # Check if user exists, if not create one
        user = User.query.filter_by(telegram_id=str(query.from_user.id)).first()
        if not user:
            user = User(
                username=f"tg_{query.from_user.id}",
                password="telegram_user",  # In production, generate a secure password
                telegram_id=str(query.from_user.id)
            )
            db.session.add(user)
            db.session.commit()
        
        # Create assignment
        assignment = Assignment(
            course=user_data.get('course', ''),
            semester=user_data.get('semester', ''),
            faculty=user_data.get('faculty', ''),
            subjects=", ".join(user_data.get('subjects', [])),
            deadline=user_data.get('deadline', ''),
            task_source=user_data.get('task_source', ''),
            work_type=work_type,
            user_id=user.id,
            status='pending',
            created_at=datetime.utcnow()
        )
        db.session.add(assignment)
        db.session.commit()
    
    await query.edit_message_text(
        summary,
        parse_mode='Markdown'
    )
    
    # Clear user data
    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel and end the conversation."""
    context.user_data.clear()
    
    await update.message.reply_text(
        '❌ Заказ отменен. Если хотите начать заново, нажмите /start.'
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
    print("Starting bot...")
    application.run_polling()

if __name__ == '__main__':
    if not os.getenv('BOT_TOKEN'):
        print("Ошибка: Не задан токен бота. Пожалуйста, укажите его в файле .env")
        exit(1)
    
    # Initialize database tables if they don't exist
    with app.app_context():
        db.create_all()
    
    main()
