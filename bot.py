from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from PIL import Image, ImageDraw
import random
import math

TOKEN = "8727862653:AAHvaAsGfaZtbNIZfzkt9TyZB3CDhc1OqeM"

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

user_data = {}

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
    total, unique_bonuses = 0, []
    for (troop, stat, value), count in bonuses.items():
        total += value
        unique_bonuses.append((troop, stat, value))
    return unique_bonuses, total

def get_all_tiles(tiles):
    all_tiles = []
    for color, cnt in tiles.items():
        all_tiles.extend([color] * cnt)
    all_tiles.extend([None] * (35 - len(all_tiles)))
    return all_tiles

def calculate_weighted_score(bonuses, priority_army):
    score = sum(value for _, _, value in bonuses)
    for troop, _, value in bonuses:
        if troop == priority_army:
            score += value * 2
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

async def start(update, context):
    user_id = update.effective_user.id
    user_data[user_id] = {"army": None, "tiles": {c:0 for c in COLOR_NAMES}}
    keyboard = [
        [InlineKeyboardButton("⚔️ Пехота", callback_data="army_Пехота")],
        [InlineKeyboardButton("🎯 Стрелки", callback_data="army_Стрелки")],
        [InlineKeyboardButton("🐎 Кавалерия", callback_data="army_Кавалерия")],
    ]
    await update.message.reply_text("🏆 **UbiHeroOptimizer**\n\nВыбери тип войск:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def set_army(update, context):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if user_id not in user_data:
        user_data[user_id] = {"army": None, "tiles": {c:0 for c in COLOR_NAMES}}
    army = query.data.split("_")[1]
    user_data[user_id]["army"] = army
    await query.edit_message_text(f"✅ Тип войск: **{army}**\n\nТеперь добавляй Случайные Элементы:", parse_mode="Markdown")
    await show_tiles(update, user_id)

async def show_tiles(update, user_id):
    if user_id not in user_data:
        user_data[user_id] = {"army": None, "tiles": {c:0 for c in COLOR_NAMES}}
    tiles = user_data[user_id]["tiles"]
    text = "📊 **Твои Случайные Элементы:**\n\n" + "\n".join(f"{EMOJI[color]} {color}: {tiles[color]}" for color in COLOR_NAMES)
    row_buttons = [InlineKeyboardButton(f"{EMOJI[color]} +1", callback_data=f"add_{color}") for color in COLOR_NAMES]
    keyboard = [row_buttons, [InlineKeyboardButton("✅ Оптимальная расстановка", callback_data="optimize")], [InlineKeyboardButton("🗑 Очистить всё", callback_data="clear")], [InlineKeyboardButton("🏠 Главное меню", callback_data="menu")]]
    try:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    except:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def menu(update, context):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_data[user_id] = {"army": None, "tiles": {c:0 for c in COLOR_NAMES}}
    keyboard = [[InlineKeyboardButton("⚔️ Пехота", callback_data="army_Пехота")], [InlineKeyboardButton("🎯 Стрелки", callback_data="army_Стрелки")], [InlineKeyboardButton("🐎 Кавалерия", callback_data="army_Кавалерия")]]
    await query.edit_message_text("🏆 **UbiHeroOptimizer**\n\nВыбери тип войск:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def add_tile(update, context):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if user_id not in user_data:
        user_data[user_id] = {"army": None, "tiles": {c:0 for c in COLOR_NAMES}}
    color = query.data.split("_")[1]
    user_data[user_id]["tiles"][color] += 1
    await show_tiles(update, user_id)

async def clear_tiles(update, context):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if user_id not in user_data:
        user_data[user_id] = {"army": None, "tiles": {c:0 for c in COLOR_NAMES}}
    for c in user_data[user_id]["tiles"]:
        user_data[user_id]["tiles"][c] = 0
    await show_tiles(update, user_id)

async def optimize_and_draw(update, context):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if user_id not in user_data:
        user_data[user_id] = {"army": None, "tiles": {c:0 for c in COLOR_NAMES}}
    tiles = user_data[user_id]["tiles"]
    army = user_data[user_id]["army"]

    if not army:
        await query.edit_message_text("❌ Сначала выбери тип войск в меню", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Меню", callback_data="menu")]]))
        return
    if sum(tiles.values()) == 0:
        await query.edit_message_text("❌ Добавь хотя бы один элемент", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("➕ Добавить", callback_data="menu")]]))
        return

    await query.edit_message_text("🧠 Запускаю ИИ... (это может занять до 15 секунд)")
    placement, bonuses = simulated_annealing(tiles, army)
    total = sum(value for _, _, value in bonuses)
    img = draw_field(placement)
    img.save("field.png")

    result = f"🎯 **{army}** | Суммарный бонус: +{total}%\n\n✨ **Полученные бонусы:**\n"
    for troop, stat, value in bonuses:
        result += f"- {BONUS_NAMES.get((troop, stat), f'{stat} {troop}')} +{value}%\n"
    if not bonuses:
        result += "- (нет активных комбинаций)\n"

    keyboard = [[InlineKeyboardButton("🏠 Главное меню", callback_data="menu")]]
    with open("field.png", "rb") as f:
        await query.message.reply_photo(f, caption=result, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(set_army, pattern="^army_"))
    app.add_handler(CallbackQueryHandler(add_tile, pattern="^add_"))
    app.add_handler(CallbackQueryHandler(clear_tiles, pattern="^clear$"))
    app.add_handler(CallbackQueryHandler(optimize_and_draw, pattern="^optimize$"))
    app.add_handler(CallbackQueryHandler(menu, pattern="^menu$"))
    print("🚀 UbiHeroOptimizer с ИИ запущен")
    app.run_polling()

if __name__ == "__main__":
    main()