import logging
import os
import requests
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from db import init_db, list_products, get_product, create_order, add_product, get_order, set_order_status
from db import set_payment_link, confirm_order_paid

logging.basicConfig(level=logging.INFO)

# bot token can be provided via environment or hardcoded default below
# WARNING: hardcoding the token is insecure. Prefer setting TG_BOT_TOKEN in env.
API_TOKEN = os.getenv('TG_BOT_TOKEN', '8706625605:AAG3IF-ODZ4-FsqVVtkaDuKtP0LcjqsDpLI')
# default admin id set to provided value if env not set
ADMIN_ID = int(os.getenv('ADMIN_ID', '8594771951'))  # ваш ID как админа

if not API_TOKEN:
    raise SystemExit('Set TG_BOT_TOKEN env var')

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

init_db()

# seed database with some example items when a specific category is empty
# ensures that restarting the bot won't wipe out already existing products
try:
    if not list_products('proxy'):
        add_product('🇩🇪 Германия 3 дня', '8.8', 'DEFAULT_CREDENTIALS', 'proxy', 'доступ на 3 дня')
        add_product('🇩🇪 Германия 7 дней', '20', 'DEFAULT_CREDENTIALS', 'proxy', 'доступ на 7 дней')
    if not list_products('numbers'):
        add_product('🇷🇺 Россия 1 номер', '50', 'NUMBER123', 'numbers', 'мобильный номер')
    if not list_products('email'):
        add_product('📧 Email VIP', '30', 'mail:pass', 'email', 'быстрый email')
    if not list_products('tg'):
        add_product('🤖 TG аккаунт', '100', 'tguser:pass', 'tg', 'телеграм-аккаунт')
except Exception:
    pass  # ignore if something goes wrong during seeding
# to force reseed in future delete products.db or remove specific rows manually

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    # send welcome image from provided Imgur album
    try:
        await bot.send_photo(message.from_user.id,
                             photo='https://i.imgur.com/UhLPRl2.jpg',
                             caption='Добро пожаловать в магазин!')
    except Exception:
        pass
    # layout: catalog left, profile right; top-up full-width below; support bottom left, agreement bottom right
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(InlineKeyboardButton('📦 Каталог', callback_data='menu:catalog'),
           InlineKeyboardButton('👤 Профиль', callback_data='menu:profile'))
    kb.row(InlineKeyboardButton('💰 Пополнить баланс', callback_data='menu:topup'))
    kb.add(InlineKeyboardButton('📩 Техподдержка', callback_data='menu:support'),
           InlineKeyboardButton('📄 Польз. соглашение', callback_data='menu:agreement'))
    await message.answer('Главное меню:', reply_markup=kb)


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('cat:'))
async def process_category(cb: types.CallbackQuery):
    # remove the previous message with buttons
    try:
        await cb.message.delete()
    except Exception:
        pass
    category = cb.data.split(':', 1)[1]
    # fetch products for category
    prods = list_products(category)
    if not prods:
        await bot.send_message(cb.from_user.id, 'В этом разделе пока нет товаров.')
        await cb.answer()
        return
    kb = InlineKeyboardMarkup()
    for pid, title, desc, price in prods:
        kb.add(InlineKeyboardButton(f"{title} — {price}", callback_data=f"buy:{pid}"))
    # back button
    kb.add(InlineKeyboardButton('🔙 Назад', callback_data='menu:catalog'))
    await bot.send_message(cb.from_user.id, f'Товары в разделе {category}:', reply_markup=kb)
    await cb.answer()

@dp.callback_query_handler(lambda c: c.data and c.data.startswith('buy:'))
async def process_buy(cb: types.CallbackQuery):
    try:
        await cb.message.delete()
    except Exception:
        pass
    pid = int(cb.data.split(':', 1)[1])
    prod = get_product(pid)
    if not prod:
        await cb.answer('Товар не найден', show_alert=True)
        return
    _, title, desc, price, _, category = prod
    kb = InlineKeyboardMarkup(row_width=5)
    for i in range(1, 11):
        kb.insert(InlineKeyboardButton(str(i), callback_data=f'qty:{pid}:{i}'))
    kb.add(InlineKeyboardButton('Свое количество', callback_data=f'qty_custom:{pid}'))
    # back to category button
    kb.add(InlineKeyboardButton('🔙 Назад', callback_data=f'cat:{category}'))
    await bot.send_message(cb.from_user.id, f"Вы выбрали: <b>{title}</b>\nЦена за единицу: <b>{price} руб</b>\n{desc}\nВыберите количество:", parse_mode=ParseMode.HTML, reply_markup=kb)
    await cb.answer()


# new menu callback handler
def handle_menu(cb: types.CallbackQuery):
    return cb.data and cb.data.startswith('menu:')

@dp.callback_query_handler(handle_menu)
async def process_menu(cb: types.CallbackQuery):
    try:
        await cb.message.delete()
    except Exception:
        pass
    choice = cb.data.split(':',1)[1]
    if choice == 'catalog':
        # reuse start logic to show category buttons
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton('Прокси', callback_data='cat:proxy'))
        kb.add(InlineKeyboardButton('Номера', callback_data='cat:numbers'))
        kb.add(InlineKeyboardButton('TG аккаунты', callback_data='cat:tg'))
        kb.add(InlineKeyboardButton('Почты', callback_data='cat:email'))
        await bot.send_message(cb.from_user.id, 'Выберите раздел:', reply_markup=kb)
    elif choice == 'profile':
        await bot.send_message(cb.from_user.id, f'Ваш ID: {cb.from_user.id}\nБаланс: 0 руб (пока не реализовано)')
    elif choice == 'topup':
        await bot.send_message(cb.from_user.id, 'Чтобы пополнить баланс, обратитесь к администратору.')
    elif choice == 'support':
        await bot.send_message(cb.from_user.id, 'Техподдержка: @your_support_username')
    elif choice == 'agreement':
        await bot.send_message(cb.from_user.id, 'Пользовательское соглашение: https://example.com/agreement')
    await cb.answer()

@dp.message_handler(commands=['addproduct'])
async def cmd_addproduct(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.reply('Только админ может добавлять товары')
        return
    # Expect format: /addproduct category|title|credentials|description(optional)
    # price is forced to 100
    parts = message.get_args().split('|')
    if len(parts) < 3:
        await message.reply('Использование:\n/addproduct category|title|credentials|description(optional)\nКатегории: proxy,numbers,tg,email')
        return
    category = parts[0].strip()
    title = parts[1].strip()
    credentials = parts[2].strip()
    description = parts[3].strip() if len(parts) >= 4 else ''
    price = '100'
    if category not in ('proxy', 'numbers', 'tg', 'email'):
        await message.reply('Неверная категория. Используйте: proxy,numbers,tg,email')
        return
    pid = add_product(title, price, credentials, category, description)
    await message.reply(f'Товар добавлен, id={pid} (цена зафиксирована 100 руб)')


# existing handlers remain unchanged below

@dp.callback_query_handler(lambda c: c.data and c.data.startswith('qty:'))
async def process_qty(cb: types.CallbackQuery):
    try:
        await cb.message.delete()
    except Exception:
        pass
    _, pid_str, qty_str = cb.data.split(':')
    pid = int(pid_str)
    qty = int(qty_str)
    prod = get_product(pid)
    if not prod:
        await cb.answer('Товар не найден', show_alert=True)
        return
    _, title, desc, price, _, category = prod
    total = float(price) * qty
    oid = create_order(cb.from_user.id, pid, qty, total)
    await bot.send_message(cb.from_user.id, f"Создан заказ #{oid}\nТовар: {title}\nКол-во: {qty}\nСумма: {total} руб\nПеред покупкой пополните баланс. Админ пришлёт ссылку для оплаты.")
    await cb.answer('Заказ создан')


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('qty_custom:'))
async def process_qty_custom(cb: types.CallbackQuery):
    try:
        await cb.message.delete()
    except Exception:
        pass
    pid = int(cb.data.split(':', 1)[1])
    await bot.send_message(cb.from_user.id, 'Отправьте желаемое количество (число).')
    await cb.answer()


@dp.message_handler(lambda m: m.text and m.text.isdigit())
async def handle_custom_qty(message: types.Message):
    # This will be a basic heuristic: if user recently received prompt, create order
    # For simplicity, require format: /buy_custom <product_id> <qty>
    if message.text.startswith('/buy_custom'):
        parts = message.text.split()
        if len(parts) != 3:
            await message.reply('Использование: /buy_custom <product_id> <qty>')
            return
    else:
        return

@dp.message_handler(commands=['requestpay'])
async def cmd_requestpay(message: types.Message):
    # user asks admin to send payment link for order: /requestpay <order_id>
    args = message.get_args().strip()
    if not args:
        await message.reply('Использование: /requestpay <order_id>')
        return
    try:
        oid = int(args)
    except ValueError:
        await message.reply('Неверный id')
        return
    order = get_order(oid)
    if not order:
        await message.reply('Заказ не найден')
        return
    _, user_id, product_id, quantity, total_price, payment_link, status, created_at = order
    # forward request to admin
    await bot.send_message(ADMIN_ID, f'Пользователь {message.from_user.id} запрашивает ссылку для оплаты заказа #{oid} (сумма {total_price} руб). Используйте /sendlink {oid} <link>')
    await message.reply('Запрос отправлен администратору. Ожидайте ссылку.')


@dp.message_handler(commands=['sendlink'])
async def cmd_sendlink(message: types.Message):
    # admin command: /sendlink <order_id> <link>
    if message.from_user.id != ADMIN_ID:
        await message.reply('Только админ')
        return
    parts = message.get_args().split(None, 1)
    if len(parts) != 2:
        await message.reply('Использование: /sendlink <order_id> <link>')
        return
    try:
        oid = int(parts[0])
    except ValueError:
        await message.reply('Неверный id')
        return
    link = parts[1].strip()
    order = get_order(oid)
    if not order:
        await message.reply('Заказ не найден')
        return
    # save link and send to buyer
    set_payment_link(oid, link)
    _, user_id, product_id, quantity, total_price, payment_link, status, created_at = order
    await bot.send_message(user_id, f'Ссылка для оплаты заказа #{oid}: {link}\nПосле оплаты отправьте чек/ссылку администратору или дождитесь автоматического подтверждения.')
    await message.reply('Ссылка отправлена покупателю')

# admin can trigger the CI webhook to auto-deploy
@dp.message_handler(commands=['update'])
async def cmd_update(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    url = 'http://agent.bothost.ru/api/webhooks/github'
    try:
        resp = requests.get(url, timeout=10)
        await message.reply(f'Webhook triggered, status {resp.status_code}')
    except Exception as e:
        await message.reply(f'Ошибка при запуске webhook: {e}')


@dp.message_handler(commands=['confirm'])
async def cmd_confirm(message: types.Message):
    # admin confirms payment and optionally delivers
    if message.from_user.id != ADMIN_ID:
        await message.reply('Только админ')
        return
    args = message.get_args().strip()
    if not args:
        await message.reply('Использование: /confirm <order_id>')
        return
    try:
        oid = int(args)
    except ValueError:
        await message.reply('Неверный id')
        return
    order = get_order(oid)
    if not order:
        await message.reply('Заказ не найден')
        return
    _, user_id, product_id, quantity, total_price, payment_link, status, created_at = order
    prod = get_product(product_id)
    if not prod:
        await message.reply('Товар не найден')
        return
    _, title, desc, price, credentials, category = prod
    # mark paid
    confirm_order_paid(oid)
    if category in ('numbers', 'proxy'):
        await message.reply(f'Заказ #{oid} отмечен как оплаченный. Выдача данных для {category} производится вручную — используйте /deliver {oid} когда будете готовы.')
        await bot.send_message(user_id, f'Оплата заказа #{oid} подтверждена. Админ скоро вручную вышлет данные.')
    else:
        # automatic delivery for email / tg
        try:
            await bot.send_message(user_id, f'Оплата заказа #{oid} подтверждена. Данные: {credentials}')
            set_order_status(oid, 'delivered')
            await message.reply(f'Заказ #{oid} доставлен автоматически.')
        except Exception as e:
            await message.reply(f'Не удалось отправить данные пользователю: {e}')

@dp.message_handler(commands=['listorders'])
async def cmd_listorders(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.reply('Только админ')
        return
    # List recent pending orders
    # Simple implementation: fetch from sqlite directly
    import sqlite3
    conn = sqlite3.connect('products.db')
    cur = conn.cursor()
    cur.execute("SELECT id, user_id, product_id, status, created_at FROM orders ORDER BY created_at DESC LIMIT 50")
    rows = cur.fetchall()
    conn.close()
    if not rows:
        await message.reply('Заказов нет')
        return
    lines = []
    for r in rows:
        lines.append(f"#{r[0]} user={r[1]} product={r[2]} status={r[3]} created={r[4]}")
    await message.reply('\n'.join(lines))

@dp.message_handler(commands=['deliver'])
async def cmd_deliver(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.reply('Только админ')
        return
    args = message.get_args().strip()
    if not args:
        await message.reply('Использование: /deliver <order_id>')
        return
    try:
        oid = int(args)
    except ValueError:
        await message.reply('Неверный id')
        return
    order = get_order(oid)
    if not order:
        await message.reply('Заказ не найден')
        return
    _, user_id, product_id, status, _ = order
    if status == 'delivered':
        await message.reply('Уже доставлен')
        return
    prod = get_product(product_id)
    if not prod:
        await message.reply('Товар не найден')
        return
    _, title, desc, price, credentials = prod
    # Send credentials to user and mark delivered
    try:
        await bot.send_message(user_id, f"Данные для товара <b>{title}</b>:\n{credentials}", parse_mode=ParseMode.HTML)
    except Exception as e:
        await message.reply(f'Не удалось отправить пользователю: {e}')
        return
    set_order_status(oid, 'delivered')
    await message.reply('Данные отправлены и статус обновлён')

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
