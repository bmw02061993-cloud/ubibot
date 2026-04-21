from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from PIL import Image, ImageDraw
import random
import math
import re

TOKEN = "8727862653:AAHvaAsGfaZtbNIZfzkt9TyZB3CDhc1OqeM"

# ==================== ЯЗЫКИ ====================
LANG = {
    "ru": {
        "choose_troop": "🏆 **UbiHeroOptimizer**\n\nВыбери тип войск:",
        "infantry": "⚔️ Пехота",
        "shooters": "🎯 Стрелки",
        "cavalry": "🐎 Кавалерия",
        "army_set": "✅ Тип войск: **{}**\n\nТеперь добавляй Случайные Элементы:",
        "your_tiles": "📊 **Твои Случайные Элементы:**",
        "optimal": "✅ Оптимальная расстановка",
        "clear": "🗑 Очистить всё",
        "menu": "🏠 Главное меню",
        "no_army": "❌ Сначала выбери тип войск в меню",
        "no_tiles": "❌ Добавь хотя бы один элемент",
        "ai_start": "🧠 Запускаю ИИ... (это может занять до 15 секунд)",
        "total_bonus": "🎯 **{}** | Суммарный бонус: +{}%",
        "bonuses": "✨ **Полученные бонусы:**",
        "no_bonuses": "- (нет активных комбинаций)",
        "war_calc": "📊 **Калькулятор войны**\n\nОтправь количество юнитов в формате:\n`T11 200000, T14 50000`\nИли по одному: `T2 300000`\n\nПоддерживаются любые числа: `T11 999`, `T14 231500`",
        "war_result": "🎯 **Очки:** {}\n🏆 **Стадий:** {}\n📈 **До {}:** {} / {}\n⚡ **Бонус восстановления:** +300% (мощь: {} → {})",
        "invalid": "❌ Неверный формат. Пример: `T11 200000`",
    },
    "en": {
        "choose_troop": "🏆 **UbiHeroOptimizer**\n\nChoose troop type:",
        "infantry": "⚔️ Infantry",
        "shooters": "🎯 Shooters",
        "cavalry": "🐎 Cavalry",
        "army_set": "✅ Troop type: **{}**\n\nNow add Random Elements:",
        "your_tiles": "📊 **Your Random Elements:**",
        "optimal": "✅ Optimal placement",
        "clear": "🗑 Clear all",
        "menu": "🏠 Main menu",
        "no_army": "❌ First select troop type in menu",
        "no_tiles": "❌ Add at least one element",
        "ai_start": "🧠 Starting AI... (may take up to 15 seconds)",
        "total_bonus": "🎯 **{}** | Total bonus: +{}%",
        "bonuses": "✨ **Bonuses received:**",
        "no_bonuses": "- (no active combinations)",
        "war_calc": "📊 **War Calculator**\n\nSend unit count in format:\n`T11 200000, T14 50000`\nOr one by one: `T2 300000`\n\nAny number supported: `T11 999`, `T14 231500`",
        "war_result": "🎯 **Points:** {}\n🏆 **Stages:** {}\n📈 **To {}:** {} / {}\n⚡ **Recovery bonus:** +300% (power: {} → {})",
        "invalid": "❌ Invalid format. Example: `T11 200000`",
    }
}

# ==================== ДАННЫЕ ====================
COLOR_NAMES = ["зелёный", "синий", "фиолетовый", "жёлтый", "красный"]
COLORS_RGB = {
    "зелёный": (80, 255, 80),
    "синий": (80, 80, 255),
    "фиолетовый": (200, 80, 255),
    "жёлтый": (255, 255, 80),
    "красный": (255, 80, 80)
}
EMOJI = {"зелёный":"🟢", "синий":"🔵", "фиолетовый":"🟣", "жёлтый":"🟡", "красный":"🔴"}

COMBOS = {
    "Г4_зелёный": ("Пехота", "атака", 20), "В4_зелёный": ("Пехота", "атака", 20),
    "Г4_синий": ("Кавалерия", "атака", 20), "В4_синий": ("Кавалерия", "атака", 20),
    "Г4_фиолетовый": ("Отряд", "защита", 20), "В4_фиолетовый": ("Отряд", "защита", 20),
    "Г4_жёлтый": ("Отряд", "оз", 20), "В4_жёлтый": ("Отряд", "оз", 20),
    "Г4_красный": ("Стрелки", "атака", 20), "В4_красный": ("Стрелки", "атака", 20),
    "Г3_кжф": ("Стрелки", "здоровье", 10), "В3_кжф": ("Стрелки", "защита", 10),
    "Г3_зжф": ("Пехота", "здоровье", 10), "В3_зжф": ("Пехота", "защита", 10),
    "Г3_сжф": ("Кавалерия", "здоровье", 10), "В3_сжф": ("Кавалерия", "защита", 10),
    "Г3_кзс": ("Отряд", "защита", 5), "В3_кзс": ("Отряд", "защита", 5),
    "Г3_скз": ("Отряд", "оз", 5), "В3_скз": ("Отряд", "оз", 5),
}
BONUS_NAMES = {
    ("Стрелки", "атака"): "Атака Стрелков", ("Стрелки", "здоровье"): "Здоровье Стрелков", ("Стрелки", "защита"): "Защита Стрелков",
    ("Пехота", "атака"): "Атака Пехоты", ("Пехота", "здоровье"): "Здоровье Пехоты", ("Пехота", "защита"): "Защита Пехоты",
    ("Кавалерия", "атака"): "Атака Кавалерии", ("Кавалерия", "здоровье"): "Здоровье Кавалерии", ("Кавалерия", "защита"): "Защита Кавалерии",
    ("Отряд", "защита"): "ЗАЩ. Отряда", ("Отряд", "оз"): "ОЗ Отряда",
}

# Калькулятор войны
POINTS = {1:0, 2:2, 3:4, 4:6, 5:8, 6:12, 7:16, 8:20, 9:30, 10:40, 11:80, 12:100, 13:125, 14:150}
POWER = {1:4, 2:6, 3:8, 4:12, 5:15, 6:20, 7:25, 8:33, 9:45, 10:60, 11:80, 12:100, 13:125, 14:150}
STAGES = {1:300, 2:600, 3:1500, 4:2000, 5:3000, 6:4000, 7:5000, 8:6000, 9:7000, 10:8000, 11:9000, 12:10000}

user_data = {}

# ==================== ФУНКЦИИ ====================
def get_stage(points):
    stage = 0
    for s, t in STAGES.items():
        if points >= t:
            stage = s
        else:
            return stage, t
    return stage, STAGES[12]

def parse_war_input(text):
    counts = {i: 0 for i in range(1, 15)}
    # Ищем T1, T2, ... T14 с пробелом и любым числом
    pattern = r'T(\d{1,2})\s+(\d+)'
    matches = re.findall(pattern, text, re.IGNORECASE)
    for lvl, cnt in matches:
        lvl = int(lvl)
        if 1 <= lvl <= 14:
            counts[lvl] += int(cnt)
    return counts

def draw_field(placement):
    img = Image.new('RGB', (750, 550), (240, 240, 240))
    draw = ImageDraw.Draw(img)
    cell_w, cell_h = 90, 90
    start_x, start_y = 60, 60
    for row in range(5):
        for col in range(7):
            x, y = start_x + col * cell_w, start_y + row * cell_h
            if (row + col) % 2 == 0:
                bg = (200, 200, 200)
            else:
                bg = (100, 100, 100)
            draw.rectangle([x, y, x+cell_w, y+cell_h], fill=bg, outline=(50,50,50), width=2)
            color = placement.get((row, col))
            if color and color in COLORS_RGB:
                draw.ellipse([x+10, y+10, x+cell_w-10, y+cell_h-10], fill=COLORS_RGB[color])
    return img

def check_line_horizontal(line):
    if len(line) == 4 and all(c == line[0] for c in line):
        return COMBOS.get(f"Г4_{line[0]}")
    if len(line) == 3:
        key_map = {("красный","жёлтый","фиолетовый"): "Г3_кжф", ("зелёный","жёлтый","фиолетовый"): "Г3_зжф",
                   ("синий","жёлтый","фиолетовый"): "Г3_сжф", ("красный","зелёный","синий"): "Г3_кзс",
                   ("синий","зелёный","красный"): "Г3_скз"}
        return COMBOS.get(key_map.get(tuple(line)))
    return None

def check_line_vertical(line):
    if len(line) == 4 and all(c == line[0] for c in line):
        return COMBOS.get(f"В4_{line[0]}")
    if len(line) == 3:
        key_map = {("красный","жёлтый","фиолетовый"): "В3_кжф", ("зелёный","жёлтый","фиолетовый"): "В3_зжф",
                   ("синий","жёлтый","фиолетовый"): "В3_сжф", ("красный","зелёный","синий"): "В3_кзс",
                   ("синий","зелёный","красный"): "В3_скз"}
        return COMBOS.get(key_map.get(tuple(line)))
    return None

def check_all_combinations(placement):
    bonuses = {}
    for row in range(5):
        for col in range(4):
            res = check_line_horizontal([placement.get((row, col+i)) for i in range(4)])
            if res: bonuses[res] = bonuses.get(res, 0) + 1
        for col in range(5):
            res = check_line_horizontal([placement.get((row, col+i)) for i in range(3)])
            if res: bonuses[res] = bonuses.get(res, 0) + 1
    for col in range(7):
        for row in range(2):
            res = check_line_vertical([placement.get((row+i, col)) for i in range(4)])
            if res: bonuses[res] = bonuses.get(res, 0) + 1
        for row in range(3):
            res = check_line_vertical([placement.get((row+i, col)) for i in range(3)])
            if res: bonuses[res] = bonuses.get(res, 0) + 1
    total, unique = 0, []
    for (troop, stat, val), cnt in bonuses.items():
        total += val
        unique.append((troop, stat, val))
    return unique, total

def get_all_tiles(tiles):
    all_tiles = []
    for color, cnt in tiles.items():
        all_tiles.extend([color] * cnt)
    all_tiles.extend([None] * (35 - len(all_tiles)))
    return all_tiles

def calculate_weighted_score(bonuses, priority_army):
    score = sum(val for _, _, val in bonuses)
    for troop, _, val in bonuses:
        if troop == priority_army:
            score += val * 2
    return score

def simulated_annealing(tiles, priority_army, initial_temp=100, cooling_rate=0.999, iterations_per_temp=100):
    current_tiles = get_all_tiles(tiles)
    random.shuffle(current_tiles)
    current_placement = {(r,c): current_tiles[r*7 + c] for r in range(5) for c in range(7)}
    current_bonuses, _ = check_all_combinations(current_placement)
    current_score = calculate_weighted_score(current_bonuses, priority_army)

    best_placement = current_placement.copy()
    best_bonuses = current_bonuses.copy()
    best_score = current_score

    temp = initial_temp
    while temp > 1:
        for _ in range(iterations_per_temp):
            new_placement = {k: v for k, v in current_placement.items()}
            pos1, pos2 = random.sample(list(new_placement.keys()), 2)
            new_placement[pos1], new_placement[pos2] = new_placement[pos2], new_placement[pos1]
            new_bonuses, _ = check_all_combinations(new_placement)
            new_score = calculate_weighted_score(new_bonuses, priority_army)
            if new_score > current_score:
                accept = True
            else:
                delta = new_score - current_score
                probability = math.exp(delta / temp)
                accept = random.random() < probability
            if accept:
                current_placement, current_bonuses, current_score = new_placement, new_bonuses, new_score
                if current_score > best_score:
                    best_placement, best_bonuses, best_score = current_placement.copy(), current_bonuses.copy(), current_score
        temp *= cooling_rate
    return best_placement, best_bonuses

# ==================== ОБРАБОТЧИКИ ====================
async def start(update, context):
    uid = update.effective_user.id
    user_data[uid] = {"lang": "ru", "army": None, "tiles": {c:0 for c in COLOR_NAMES}}
    kb = [
        [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")]
    ]
    await update.message.reply_text("Выбери язык / Choose language:", reply_markup=InlineKeyboardMarkup(kb))

async def set_lang(update, context):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    lang = q.data.split("_")[1]
    user_data[uid]["lang"] = lang
    await show_main_menu(update, uid)

async def show_main_menu(update, uid):
    lang = user_data[uid].get("lang", "ru")
    t = LANG[lang]
    kb = [
        [InlineKeyboardButton(t["infantry"], callback_data="army_Пехота")],
        [InlineKeyboardButton(t["shooters"], callback_data="army_Стрелки")],
        [InlineKeyboardButton(t["cavalry"], callback_data="army_Кавалерия")],
        [InlineKeyboardButton("📊 Калькулятор войны", callback_data="war_calc")]
    ]
    try:
        await update.callback_query.edit_message_text(t["choose_troop"], reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
    except:
        await update.message.reply_text(t["choose_troop"], reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

async def set_army(update, context):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    army = q.data.split("_")[1]
    user_data[uid]["army"] = army
    lang = user_data[uid].get("lang", "ru")
    t = LANG[lang]
    await q.edit_message_text(t["army_set"].format(army), parse_mode="Markdown")
    await show_tiles(update, uid)

async def show_tiles(update, uid):
    lang = user_data[uid].get("lang", "ru")
    t = LANG[lang]
    tiles = user_data[uid]["tiles"]
    text = f"{t['your_tiles']}\n\n" + "\n".join(f"{EMOJI[c]} {c}: {tiles[c]}" for c in COLOR_NAMES)
    rb = [InlineKeyboardButton(f"{EMOJI[c]} +1", callback_data=f"add_{c}") for c in COLOR_NAMES]
    kb = [rb, [InlineKeyboardButton(t["optimal"], callback_data="optimize")],
          [InlineKeyboardButton(t["clear"], callback_data="clear")],
          [InlineKeyboardButton(t["menu"], callback_data="menu")]]
    try:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
    except:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

async def menu(update, context):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    user_data[uid] = {"lang": user_data[uid].get("lang", "ru"), "army": None, "tiles": {c:0 for c in COLOR_NAMES}}
    await show_main_menu(update, uid)

async def add_tile(update, context):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    color = q.data.split("_")[1]
    user_data[uid]["tiles"][color] += 1
    await show_tiles(update, uid)

async def clear_tiles(update, context):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    for c in user_data[uid]["tiles"]:
        user_data[uid]["tiles"][c] = 0
    await show_tiles(update, uid)

async def optimize_and_draw(update, context):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    lang = user_data[uid].get("lang", "ru")
    t = LANG[lang]
    tiles = user_data[uid]["tiles"]
    army = user_data[uid]["army"]
    if not army:
        await q.edit_message_text(t["no_army"], reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(t["menu"], callback_data="menu")]]))
        return
    if sum(tiles.values()) == 0:
        await q.edit_message_text(t["no_tiles"], reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(t["menu"], callback_data="menu")]]))
        return
    await q.edit_message_text(t["ai_start"])
    placement, bonuses = simulated_annealing(tiles, army)
    total = sum(val for _, _, val in bonuses)
    img = draw_field(placement)
    img.save("field.png")
    res = f"{t['total_bonus'].format(army, total)}\n\n{t['bonuses']}\n"
    for troop, stat, val in bonuses:
        name = BONUS_NAMES.get((troop, stat), f"{stat} {troop}")
        res += f"- {name} +{val}%\n"
    if not bonuses:
        res += t['no_bonuses']
    kb = [[InlineKeyboardButton(t["menu"], callback_data="menu")]]
    with open("field.png", "rb") as f:
        await q.message.reply_photo(f, caption=res, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

async def war_calc(update, context):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    lang = user_data[uid].get("lang", "ru")
    t = LANG[lang]
    await q.edit_message_text(t["war_calc"], parse_mode="Markdown")

async def handle_war_input(update, context):
    uid = update.effective_user.id
    lang = user_data.get(uid, {}).get("lang", "ru")
    t = LANG[lang]
    text = update.message.text.strip()
    
    # Проверяем, что сообщение похоже на ввод для калькулятора
    if not re.search(r'T\d+\s+\d+', text, re.IGNORECASE):
        # Если не похоже — игнорируем (не отвечаем)
        return
    
    counts = parse_war_input(text)
    if sum(counts.values()) == 0:
        await update.message.reply_text(t["war_calc"], parse_mode="Markdown")
        return
    
    points = sum(POINTS[l] * counts[l] for l in range(1, 15))
    power = sum(POWER[l] * counts[l] for l in range(1, 15))
    stage, nxt = get_stage(points)
    res = t["war_result"].format(points, stage, stage+1, points, nxt, power, power*4)
    await update.message.reply_text(res, parse_mode="Markdown")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(set_lang, pattern="^lang_"))
    app.add_handler(CallbackQueryHandler(set_army, pattern="^army_"))
    app.add_handler(CallbackQueryHandler(add_tile, pattern="^add_"))
    app.add_handler(CallbackQueryHandler(clear_tiles, pattern="^clear$"))
    app.add_handler(CallbackQueryHandler(optimize_and_draw, pattern="^optimize$"))
    app.add_handler(CallbackQueryHandler(menu, pattern="^menu$"))
    app.add_handler(CallbackQueryHandler(war_calc, pattern="^war_calc$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_war_input))
    print("✅ UbiHeroOptimizer запущен")
    app.run_polling()

if __name__ == "__main__":
    main()