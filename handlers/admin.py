import asyncio
import aiosqlite
from datetime import datetime
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from typing import cast
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import BOT_TOKEN, ADMIN_ID, DATABASE_PATH, PREMIUM_PRICE_UZS
from database import get_user, update_user_activity
from keyboards import get_admin_menu

router = Router()

class AdminStates(StatesGroup):
    creating_section = State()
    creating_quiz = State()
    broadcast_text = State()

def admin_only(func):
    """Safe decorator for admin access"""
    async def wrapper(update, *args, **kwargs):
        try:
            user_id = None
            if isinstance(update, Message) and update.from_user:
                user_id = update.from_user.id
            elif isinstance(update, CallbackQuery) and update.from_user:
                user_id = update.from_user.id
            
            if user_id != ADMIN_ID:
                if isinstance(update, Message):
                    await update.answer("❌ Sizda admin huquqlari yo'q!")
                elif isinstance(update, CallbackQuery):
                    try:
                        await update.answer("❌ Sizda admin huquqlari yo'q!", show_alert=True)
                    except:
                        pass
                return
            
            return await func(update, *args, **kwargs)
        except Exception as e:
            print(f"Admin decorator error: {e}")
            return
    return wrapper

@router.callback_query(F.data == "admin_panel")
@admin_only
async def admin_panel(callback: CallbackQuery, state: FSMContext):
    """Safe admin panel handler"""
    try:
        await state.clear()
        
        if not callback.message:
            await callback.answer("❌ Xatolik yuz berdi", show_alert=True)
            return
            
        message = cast(Message, callback.message)
        await message.edit_text(
            "🔧 <b>Admin Panel</b>\n\n"
            "🎯 Botni boshqarish uchun quyidagi tugmalardan foydalaning:",
            reply_markup=get_admin_menu()
        )
        
        await callback.answer()
        
    except Exception as e:
        print(f"Admin panel error: {e}")
        try:
            await callback.answer("❌ Xatolik yuz berdi", show_alert=True)
        except:
            pass

@router.callback_query(F.data == "admin_stats") 
@admin_only
async def admin_stats(callback: CallbackQuery):
    """Safe admin stats handler"""
    try:
        if not callback.message:
            await callback.answer("❌ Xatolik yuz berdi", show_alert=True)
            return
            
        total_users = 0
        premium_users = 0
        active_today = 0
        total_sections = 0
        total_quizzes = 0
        
        try:
            async with aiosqlite.connect(DATABASE_PATH) as db:
                # Total users
                cursor = await db.execute("SELECT COUNT(*) FROM users")
                result = await cursor.fetchone()
                total_users = result[0] if result else 0
                
                # Premium users  
                cursor = await db.execute("SELECT COUNT(*) FROM users WHERE is_premium = 1")
                result = await cursor.fetchone()
                premium_users = result[0] if result else 0
                
                # Active today
                cursor = await db.execute("""
                    SELECT COUNT(*) FROM users 
                    WHERE last_activity > datetime('now', '-1 day')
                """)
                result = await cursor.fetchone()
                active_today = result[0] if result else 0
                
                # Total sections
                cursor = await db.execute("SELECT COUNT(*) FROM sections")
                result = await cursor.fetchone()
                total_sections = result[0] if result else 0
                
                # Total quizzes
                cursor = await db.execute("SELECT COUNT(*) FROM quizzes")
                result = await cursor.fetchone()
                total_quizzes = result[0] if result else 0
                
        except Exception as db_error:
            print(f"Database error: {db_error}")

        stats_text = f"""📊 <b>Bot Statistikasi</b>

👥 <b>Foydalanuvchilar:</b>
• Jami: {total_users}
• Premium: {premium_users}
• Bugun faol: {active_today}

📚 <b>Kontent:</b>
• Bo'limlar: {total_sections}
• Testlar: {total_quizzes}

💰 <b>Premium narxi:</b> {PREMIUM_PRICE_UZS:,} so'm"""

        message = cast(Message, callback.message)
        await message.edit_text(
            stats_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Admin panel", callback_data="admin_panel")]
            ])
        )
        
        await callback.answer()
        
    except Exception as e:
        print(f"Admin stats error: {e}")
        try:
            await callback.answer("❌ Xatolik yuz berdi", show_alert=True)
        except:
            pass

@router.callback_query(F.data == "admin_broadcast")
@admin_only
async def admin_broadcast_menu(callback: CallbackQuery, state: FSMContext):
    """Safe broadcast menu"""
    try:
        await state.clear()
        
        if not callback.message:
            await callback.answer("❌ Xatolik yuz berdi", show_alert=True)
            return
            
        message = cast(Message, callback.message)
        await message.edit_text(
            "📢 <b>Barchaga xabar yuborish</b>\n\n"
            "🎯 Barcha aktiv foydalanuvchilarga matn xabar yuborish\n\n"
            "⚠️ Xabar yuborishdan oldin tekshirish bo'ladi",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📝 Matn xabar yuborish", callback_data="broadcast_text")],
                [InlineKeyboardButton(text="🔙 Admin panel", callback_data="admin_panel")]
            ])
        )
        
        await callback.answer()
        
    except Exception as e:
        print(f"Broadcast menu error: {e}")
        try:
            await callback.answer("❌ Xatolik yuz berdi", show_alert=True)
        except:
            pass

@router.callback_query(F.data == "broadcast_text")
@admin_only 
async def broadcast_text_start(callback: CallbackQuery, state: FSMContext):
    """Safe broadcast text start"""
    try:
        await state.set_state(AdminStates.broadcast_text)
        
        if not callback.message:
            await callback.answer("❌ Xatolik yuz berdi", show_alert=True)
            return
            
        message = cast(Message, callback.message)
        await message.edit_text(
            "📝 <b>Matn xabar yozish</b>\n\n"
            "Barcha foydalanuvchilarga yubormoqchi bo'lgan xabaringizni yozing:\n\n"
            "💡 /cancel - bekor qilish",
            reply_markup=None
        )
        
        await callback.answer()
        
    except Exception as e:
        print(f"Broadcast text start error: {e}")
        try:
            await callback.answer("❌ Xatolik yuz berdi", show_alert=True)
        except:
            pass

@router.message(AdminStates.broadcast_text)
@admin_only
async def broadcast_text_received(message: Message, state: FSMContext):
    """Safe broadcast text handler"""
    try:
        if not message or not message.text:
            return
            
        if message.text == "/cancel":
            await state.clear()
            await message.answer("❌ Bekor qilindi")
            return
        
        # Save message
        await state.update_data(message_text=message.text, message_type="text")
        
        # Show confirmation
        await message.answer(
            f"📋 <b>Tasdiqlash</b>\n\n"
            f"📝 <b>Xabar:</b>\n{message.text}\n\n"
            f"⚠️ Bu xabar barchaga yuboriladi!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Yuborish", callback_data="confirm_broadcast"),
                    InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_broadcast")
                ]
            ])
        )
        
    except Exception as e:
        print(f"Broadcast text received error: {e}")

@router.callback_query(F.data == "confirm_broadcast")
@admin_only
async def confirm_broadcast(callback: CallbackQuery, state: FSMContext):
    """Safe broadcast confirmation"""
    try:
        data = await state.get_data()
        
        if not data or not callback.message:
            await callback.answer("❌ Xatolik!", show_alert=True)
            return
            
        message = cast(Message, callback.message)
        await message.edit_text("🚀 Yuborilmoqda...")
        
        # Send to all users
        sent_count = await send_broadcast_message(data)
        
        await state.clear()
        await message.edit_text(
            f"✅ <b>Xabar yuborildi!</b>\n\n"
            f"📊 {sent_count} ta foydalanuvchiga yuborildi",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Admin panel", callback_data="admin_panel")]
            ])
        )
        
        await callback.answer()
        
    except Exception as e:
        print(f"Confirm broadcast error: {e}")
        try:
            await callback.answer("❌ Xatolik yuz berdi", show_alert=True)
        except:
            pass

@router.callback_query(F.data == "cancel_broadcast")
@admin_only
async def cancel_broadcast(callback: CallbackQuery, state: FSMContext):
    """Safe broadcast cancel"""
    try:
        await state.clear()
        
        if not callback.message:
            await callback.answer("❌ Xatolik yuz berdi", show_alert=True)
            return
            
        message = cast(Message, callback.message)
        await message.edit_text(
            "❌ <b>Xabar yuborish bekor qilindi</b>",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Admin panel", callback_data="admin_panel")]
            ])
        )
        
        await callback.answer()
        
    except Exception as e:
        print(f"Cancel broadcast error: {e}")
        try:
            await callback.answer("❌ Xatolik yuz berdi", show_alert=True)
        except:
            pass

async def send_broadcast_message(data):
    """Safe broadcast sender"""
    bot = Bot(token=BOT_TOKEN)
    sent_count = 0
    
    try:
        # Get all users
        async with aiosqlite.connect(DATABASE_PATH) as db:
            cursor = await db.execute("SELECT user_id FROM users")
            users = await cursor.fetchall()
        
        message_text = data.get("message_text", "")
        
        if not message_text:
            return 0
            
        for (user_id,) in users:
            try:
                await bot.send_message(user_id, message_text)
                sent_count += 1
                await asyncio.sleep(0.05)  # Rate limiting
            except Exception:
                continue
        
        await bot.session.close()
        return sent_count
        
    except Exception as e:
        print(f"Broadcast error: {e}")
        try:
            await bot.session.close()
        except:
            pass
        return sent_count

# ================================
# OTHER ADMIN HANDLERS - SAFE STUBS
# ================================

@router.callback_query(F.data == "admin_sections")
@admin_only
async def admin_sections(callback: CallbackQuery):
    """Safe admin sections handler"""
    try:
        if not callback.message:
            await callback.answer("❌ Xatolik yuz berdi", show_alert=True)
            return
            
        message = cast(Message, callback.message)
        await message.edit_text(
            "📚 <b>Bo'limlar boshqaruvi</b>\n\n"
            "Bu funksiya hozircha ishlab chiqilmoqda...",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Admin panel", callback_data="admin_panel")]
            ])
        )
        await callback.answer()
    except Exception as e:
        print(f"Admin sections error: {e}")
        try:
            await callback.answer("❌ Xatolik yuz berdi", show_alert=True)
        except:
            pass

@router.callback_query(F.data == "admin_content")
@admin_only
async def admin_content(callback: CallbackQuery):
    """Safe admin content handler"""
    try:
        if not callback.message:
            await callback.answer("❌ Xatolik yuz berdi", show_alert=True)
            return
            
        message = cast(Message, callback.message)
        await message.edit_text(
            "📁 <b>Kontent boshqaruvi</b>\n\n"
            "Bu funksiya hozircha ishlab chiqilmoqda...",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Admin panel", callback_data="admin_panel")]
            ])
        )
        await callback.answer()
    except Exception as e:
        print(f"Admin content error: {e}")
        try:
            await callback.answer("❌ Xatolik yuz berdi", show_alert=True)
        except:
            pass

@router.callback_query(F.data == "admin_quiz")
@admin_only
async def admin_quiz(callback: CallbackQuery):
    """Safe admin quiz handler"""
    try:
        if not callback.message:
            await callback.answer("❌ Xatolik yuz berdi", show_alert=True)
            return
            
        message = cast(Message, callback.message)
        await message.edit_text(
            "🧠 <b>Testlar boshqaruvi</b>\n\n"
            "Bu funksiya hozircha ishlab chiqilmoqda...",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Admin panel", callback_data="admin_panel")]
            ])
        )
        await callback.answer()
    except Exception as e:
        print(f"Admin quiz error: {e}")
        try:
            await callback.answer("❌ Xatolik yuz berdi", show_alert=True)
        except:
            pass

# MISSING ADMIN HANDLERS
@router.callback_query(F.data == "admin_premium")
@admin_only
async def admin_premium(callback: CallbackQuery):
    """Admin premium management"""
    try:
        if not callback.message:
            await callback.answer("❌ Xatolik yuz berdi", show_alert=True)
            return
            
        message = cast(Message, callback.message)
        await message.edit_text(
            "💎 <b>Premium boshqaruv</b>\n\n"
            "Bu funksiya hozircha ishlab chiqilmoqda...",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Admin panel", callback_data="admin_panel")]
            ])
        )
        await callback.answer()
    except Exception as e:
        print(f"Admin premium error: {e}")
        try:
            await callback.answer("❌ Xatolik yuz berdi", show_alert=True)
        except:
            pass

@router.callback_query(F.data == "admin_payments")
@admin_only
async def admin_payments(callback: CallbackQuery):
    """Admin payments management"""  
    try:
        if not callback.message:
            await callback.answer("❌ Xatolik yuz berdi", show_alert=True)
            return
            
        message = cast(Message, callback.message)
        await message.edit_text(
            "💳 <b>To'lov tasdiqlash</b>\n\n"
            "Bu funksiya hozircha ishlab chiqilmoqda...",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Admin panel", callback_data="admin_panel")]
            ])
        )
        await callback.answer()
    except Exception as e:
        print(f"Admin payments error: {e}")
        try:
            await callback.answer("❌ Xatolik yuz berdi", show_alert=True)
        except:
            pass

@router.callback_query(F.data == "content_delete_menu")
@admin_only
async def content_delete_menu(callback: CallbackQuery):
    """Content delete menu"""
    try:
        if not callback.message:
            await callback.answer("❌ Xatolik yuz berdi", show_alert=True)
            return
            
        message = cast(Message, callback.message)
        await message.edit_text(
            "🗑️ <b>Content o'chirish</b>\n\n"
            "Bu funksiya hozircha ishlab chiqilmoqda...",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Admin panel", callback_data="admin_panel")]
            ])
        )
        await callback.answer()
    except Exception as e:
        print(f"Content delete error: {e}")
        try:
            await callback.answer("❌ Xatolik yuz berdi", show_alert=True)
        except:
            pass

@router.callback_query(F.data == "admin_test_messages")
@admin_only
async def admin_test_messages(callback: CallbackQuery):
    """Admin test messages"""
    try:
        if not callback.message:
            await callback.answer("❌ Xatolik yuz berdi", show_alert=True)
            return
            
        message = cast(Message, callback.message)
        await message.edit_text(
            "📨 <b>Test xabarlar</b>\n\n"
            "Bu funksiya hozircha ishlab chiqilmoqda...",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Admin panel", callback_data="admin_panel")]
            ])
        )
        await callback.answer()
    except Exception as e:
        print(f"Test messages error: {e}")
        try:
            await callback.answer("❌ Xatolik yuz berdi", show_alert=True)
        except:
            pass

@router.callback_query(F.data == "admin_delete_sections")
@admin_only
async def admin_delete_sections(callback: CallbackQuery):
    """Admin delete sections"""
    try:
        if not callback.message:
            await callback.answer("❌ Xatolik yuz berdi", show_alert=True)
            return
            
        message = cast(Message, callback.message)
        await message.edit_text(
            "🗑 <b>Bo'limlarni o'chirish</b>\n\n"
            "Bu funksiya hozircha ishlab chiqilmoqda...",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Admin panel", callback_data="admin_panel")]
            ])
        )
        await callback.answer()
    except Exception as e:
        print(f"Delete sections error: {e}")
        try:
            await callback.answer("❌ Xatolik yuz berdi", show_alert=True)
        except:
            pass

# Catch-all for other admin callbacks
@router.callback_query(F.data.startswith("admin_"))
@admin_only
async def admin_catch_all(callback: CallbackQuery):
    """Safe catch-all for admin callbacks"""
    try:
        if not callback.message:
            await callback.answer("❌ Xatolik yuz berdi", show_alert=True)
            return
            
        message = cast(Message, callback.message)
        await message.edit_text(
            "🔧 <b>Admin Panel</b>\n\n"
            "Bu funksiya hozircha ishlab chiqilmoqda...\n\n"
            "Asosiy admin funksiyalar:\n"
            "• 📊 Statistika\n"
            "• 📢 Barchaga xabar yuborish",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats")],
                [InlineKeyboardButton(text="📢 Xabar yuborish", callback_data="admin_broadcast")],
                [InlineKeyboardButton(text="🔙 Bosh menu", callback_data="main_menu")]
            ])
        )
        await callback.answer()
    except Exception as e:
        print(f"Admin catch-all error: {e}")
        try:
            await callback.answer("❌ Xatolik yuz berdi", show_alert=True)
        except:
            pass