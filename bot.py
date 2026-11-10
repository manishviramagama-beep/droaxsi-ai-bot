import os
import fal_client
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

TELEGRAM_BOT_TOKEN = "9093825289:AAF4dhLi75jzz9DszfIYSh0F9NjrG2bjbsQ"
os.environ["FAL_KEY"] = "fal_sk_1b9edfd02bc74f8e9a75016a40937b99:2c86f4b0a3fa229f87b089ebf38a3229"
ADMIN_USER_ID = 9017537176

def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_USER_ID

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 Access Denied!")
        return

    welcome_text = (
        "👋 **Droaxsi AI Bot માં સ્વાગત છે!**\n\n"
        "1. **ટેક્સ્ટ મોકલો:** AI ફોટો કે વિડીયો બનાવવા માટે.\n"
        "2. **ફોટો મોકલો:** 4K Upscale અથવા ફોટોમાંથી વિડીયો બનાવવા માટે."
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    context.user_data["type"] = "text"
    context.user_data["prompt"] = update.message.text

    keyboard = [
        [InlineKeyboardButton("🎨 Create 4K AI Photo", callback_data="action_photo")],
        [InlineKeyboardButton("📱 Trending Reel (9:16)", callback_data="action_video_916")],
        [InlineKeyboardButton("🖥️ YouTube Video (16:9)", callback_data="action_video_169")]
    ]
    await update.message.reply_text(
        "આ પ્રોમ્પ્ટમાંથી શું બનાવવું છે?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    photo = await update.message.photo[-1].get_file()
    caption = update.message.caption or "Smooth cinematic motion"

    context.user_data["type"] = "image"
    context.user_data["image_url"] = photo.file_path
    context.user_data["prompt"] = caption

    keyboard = [
        [InlineKeyboardButton("✨ Enhance / Upscale to 4K", callback_data="action_upscale")],
        [InlineKeyboardButton("🎬 Turn into Reel (9:16)", callback_data="action_img_video_916")],
        [InlineKeyboardButton("🖥️ Turn into Video (16:9)", callback_data="action_img_video_169")]
    ]
    await update.message.reply_text(
        "આ ફોટા સાથે શું કરવું છે?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        return

    action = query.data
    prompt = context.user_data.get("prompt", "")
    chat_id = query.message.chat_id

    if action == "action_photo":
        await query.edit_message_text("⏳ 4K AI ફોટો બની રહ્યો છે...")
        try:
            handler = fal_client.submit("fal-ai/flux/schnell", arguments={"prompt": prompt, "image_size": "landscape_16_9"})
            result = handler.get()
            img_url = result["images"][0]["url"]
            await context.bot.send_photo(chat_id=chat_id, photo=img_url, caption=f"🎨 **Prompt:** {prompt}")
            await query.delete_message()
        except Exception as e:
            await query.edit_message_text(f"⚠️ એરર: {e}")

    elif action == "action_upscale":
        await query.edit_message_text("⏳ ફોટો 4K ક્લીન થઈ રહ્યો છે...")
        try:
            img_url = context.user_data.get("image_url")
            handler = fal_client.submit("fal-ai/esrgan", arguments={"image_url": img_url})
            result = handler.get()
            enhanced_url = result["image"]["url"]
            await context.bot.send_photo(chat_id=chat_id, photo=enhanced_url, caption="✨ 4K Enhanced Photo!")
            await query.delete_message()
        except Exception as e:
            await query.edit_message_text(f"⚠️ એરર: {e}")

    elif "video" in action:
        ratio = "9:16" if "916" in action else "16:9"
        await query.edit_message_text(f"⏳ {ratio} વિડીયો બની રહ્યો છે (૧ થી ૨ મિનિટ)...")
        try:
            args = {"prompt": prompt, "aspect_ratio": ratio}
            if context.user_data.get("type") == "image":
                args["image_url"] = context.user_data.get("image_url")

            handler = fal_client.submit("fal-ai/luma-dream-machine", arguments=args)
            result = handler.get()
            video_url = result.get("video", {}).get("url")

            if video_url:
                await context.bot.send_video(chat_id=chat_id, video=video_url, caption=f"🎬 **Video Ready!**\nRatio: {ratio}\nPrompt: {prompt}")
                await query.delete_message()
            else:
                await query.edit_message_text("❌ વિડીયો જનરેટ ન થઈ શક્યો.")
        except Exception as e:
            await query.edit_message_text(f"⚠️ એરર: {e}")

if __name__ == '__main__':
    print("AI Droaxsi Bot Started...")
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.run_polling()
