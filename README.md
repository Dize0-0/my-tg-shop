Простой Telegram-бот для продажи товаров (номеров/аккаунтов) — демонстрационный пример.

Требования:
- Python 3.8+
- Установите зависимости:

```bash
pip install -r requirements.txt
```

Переменные окружения:
- `TG_BOT_TOKEN` — токен бота
- `ADMIN_ID` — ваш Telegram user id (админ). По умолчанию поставлен `8594771951`.

Запуск:

```bash
set TG_BOT_TOKEN=ваш_токен
set ADMIN_ID=ваш_id
python bot.py
```

- Использование:
- Админ добавляет товар командой (цена фиксирована 100 руб):
  `/addproduct category|title|credentials|description(optional)`
  Категории: `proxy`, `numbers`, `tg`, `email`

## Загрузка на GitHub
Чтобы вы могли разместить этот код на своём хостинге, создайте репозиторий и запушьте файлы:

```powershell
# в папке проекта
git init
git add -A
git commit -m "Initial commit"
# замените <username> и tg-shop на своё имя/название репозитория
git remote add origin https://github.com/<username>/tg-shop.git
# либо используйте токен в URL: https://<token>@github.com/<username>/tg-shop.git
git branch -M main
git push -u origin main
```

Если у вас ещё нет репозитория, создайте его через веб‑интерфейс или API. Убедитесь, что `git` установлен и доступен в окружении.

- Пользователь стартует `/start`, выбирает товар и создаётся заказ.
- Админ проверяет оплату и подтверждает доставку:
  `/deliver <order_id>` — бот автоматически отправит `credentials` покупателю.

Важно: это пример. Интеграция реальных платёжных шлюзов требует отдельной реализации. Убедитесь, что вы действуете в рамках закона и имеете право продавать содержимое.