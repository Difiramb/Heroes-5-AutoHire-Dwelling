import pyautogui
import keyboard
import time
import os
import configparser

pyautogui.FAILSAFE = False 

bot_enabled = False      
stop_requested = False   

CONFIG_FILE = 'settings.ini'

CONFIG_TEMPLATE = """[СКОРОСТЬ_И_КООРДИНАТЫ]
; Задержка после клика по существу (в секундах). 
; Если бот кликает, но не выделяет существо - увеличьте (например, до 0.15)
delay_after_click = 0.1

; Задержка после нажатия Пробела (покупка).
; Если игра не успевает купить и кликает дальше - увеличьте (например, до 0.3)
delay_after_space = 0.2

; Пауза после прокрутки колесика, чтобы список успел обновиться
delay_after_scroll = 1.0

; Насколько пикселей влево от пустой ячейки кликать, чтобы попасть в существо
offset_x = -100
offset_y = 20

; Сила прокрутки колесика (чем больше минус, тем сильнее крутит)
scroll_amount = -330

[КЛАВИШИ]
; Впишите английские буквы, на которые будут реагировать кнопки.
; Если хотите отключить какую-то функцию, оставьте поле пустым (например: scroll_3 = )

; Вкл/Выкл бота
toggle_bot = o

; Экстренная остановка
stop_action = i

; Скупить видимые
buy_visible = j

; Прокрутить 1 раз и скупить
scroll_1 = k

; Прокрутить 2 раза и скупить
scroll_2 = l

; Прокрутить 3 раза (пусто = выкл)
scroll_3 = 

; Прокрутить 4 раза (пусто = выкл)
scroll_4 = 

; Выход из программы (теперь это знак равно)
exit_bot = =
"""

def load_config():
    config = configparser.ConfigParser()
    
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            f.write(CONFIG_TEMPLATE)
    else:
        config.read(CONFIG_FILE, encoding='utf-8')
    
    settings = {}
    keys = {}
    
    try:
        for key in ['delay_after_click', 'delay_after_space', 'delay_after_scroll', 'offset_x', 'offset_y', 'scroll_amount']:
            settings[key.upper()] = float(config.get('СКОРОСТЬ_И_КООРДИНАТЫ', key, fallback=0))
        
        for key in ['toggle_bot', 'stop_action', 'buy_visible', 'scroll_1', 'scroll_2', 'scroll_3', 'scroll_4', 'exit_bot']:
            val = config.get('КЛАВИШИ', key, fallback='').strip()
            val = val.split(';')[0].strip() 
            
            if val.lower() == 'пусто' or val == '':
                keys[key] = ''
            else:
                keys[key] = val
    except Exception as e:
        print(f"Ошибка чтения настроек: {e}")
        settings = {'DELAY_AFTER_CLICK': 0.1, 'DELAY_AFTER_SPACE': 0.2, 'DELAY_AFTER_SCROLL': 1.0, 'OFFSET_X': -100, 'OFFSET_Y': 20, 'SCROLL_AMOUNT': -330}
        keys = {'toggle_bot': 'o', 'stop_action': 'i', 'buy_visible': 'j', 'scroll_1': 'k', 'scroll_2': 'l', 'scroll_3': '', 'scroll_4': '', 'exit_bot': '='}

    return settings, keys

def find_and_buy(settings, action_name=""):
    global stop_requested 
    
    print(f"--- Запуск: {action_name} ---")
    
    screen_width, screen_height = pyautogui.size()
    pyautogui.moveTo(screen_width - 50, 50)
    time.sleep(0.1)

    try:
        empty_slots = list(pyautogui.locateAllOnScreen('empty_slot.png', confidence=0.95))
    except Exception as e:
        print(f"Ошибка вижна: {e}")
        return

    if not empty_slots:
        print("Пустые ячейки не найдены.")
        return
        
    filtered_slots = [s for s in empty_slots if s.top < (screen_height * 0.85)]
    
    rows = {}
    for slot in filtered_slots:
        found_row = False
        for y_coord in rows.keys():
            if abs(slot.top - y_coord) < 20:
                rows[y_coord].append(slot)
                found_row = True
                break
        if not found_row:
            rows[slot.top] = [slot]

    valid_rows = []
    for y_coord, slots_in_row in rows.items():
        if len(slots_in_row) >= 2:
            slots_in_row.sort(key=lambda box: box.left)
            valid_rows.append(slots_in_row[0])

    valid_rows.sort(key=lambda box: box.top)
    print(f"Найдено строк: {len(valid_rows)}")

    for index, slot in enumerate(valid_rows):
        if stop_requested:
            print("🛑 СКУПКА ПРЕРВАНА КЛАВИШЕЙ I!")
            return

        center_x, center_y = pyautogui.center(slot)
        click_x = center_x + settings['OFFSET_X']
        click_y = center_y + settings['OFFSET_Y']
        
        pyautogui.click(click_x, click_y)
        time.sleep(settings['DELAY_AFTER_CLICK'])
        
        if stop_requested:
            print("🛑 СКУПКА ПРЕРВАНА КЛАВИШЕЙ I!")
            return

        keyboard.press_and_release('space')
        time.sleep(settings['DELAY_AFTER_SPACE'])
        
    print("Скупка видимых существ завершена!")

def scroll_game(settings, times=1):
    global stop_requested 
    
    print(f"--- Умная прокрутка вниз ({times} раз) ---")
    
    try:
        empty_slots = list(pyautogui.locateAllOnScreen('empty_slot.png', confidence=0.95))
        if empty_slots:
            first_slot = empty_slots[0]
            center_x, center_y = pyautogui.center(first_slot)
            pyautogui.moveTo(center_x, center_y)
            print(f"  Мышь наведена на список: ({center_x}, {center_y})")
        else:
            pyautogui.moveTo(350, 500)
    except:
        pyautogui.moveTo(350, 500)
        
    time.sleep(0.1)
    
    for _ in range(times):
        if stop_requested:
            print("🛑 ПРОКРУТКА ПРЕРВАНА КЛАВИШЕЙ I!")
            return
        
        pyautogui.scroll(int(settings['SCROLL_AMOUNT'])) 
        time.sleep(settings['DELAY_AFTER_SCROLL'])

# --- ФУНКЦИИ ДЛЯ ГОРЯЧИХ КЛАВИШ ---

def toggle_bot_state():
    global bot_enabled
    bot_enabled = not bot_enabled
    if bot_enabled:
        print("\n🟢 БОТ ВКЛЮЧЕН\n")
    else:
        print("\n🔴 БОТ ВЫКЛЮЧЕН\n")

def emergency_stop():
    global stop_requested
    stop_requested = True
    print("\n⚠️ Получен сигнал СТОП (I). Прерываю действия...\n")

def create_scroll_callback(times):
    def callback():
        global stop_requested
        if bot_enabled:
            stop_requested = False 
            cfg, _ = load_config()
            scroll_game(cfg, times) 
            if not stop_requested: 
                find_and_buy(cfg, f"Скупка после прокрута ({times})")
    return callback

def create_buy_callback():
    def callback():
        global stop_requested
        if bot_enabled:
            stop_requested = False 
            cfg, _ = load_config()
            find_and_buy(cfg, "Скупка видимых")
    return callback

# --- ГЛАВНЫЙ ЦИКЛ ---
if __name__ == "__main__":
    current_settings, current_keys = load_config() 
    
    print("\n=== БОТ ЗАПУЩЕН ===")
    print(f"O - Включить/Выключить бота (сейчас ВЫКЛЮЧЕН)")
    print(f"J - Скупить видимые")
    print(f"K - Прокрутить 1 раз и скупить")
    print(f"L - Прокрутить 2 раза и скупить")
    print(f"I - ЭКСТРЕННАЯ ОСТАНОВКА")
    print(f"= - Выход из программы")
    print("Все настройки можно изменить в файле settings.ini\n")
    
    if current_keys['toggle_bot']: keyboard.add_hotkey(current_keys['toggle_bot'], toggle_bot_state)
    if current_keys['stop_action']: keyboard.add_hotkey(current_keys['stop_action'], emergency_stop)
    if current_keys['buy_visible']: keyboard.add_hotkey(current_keys['buy_visible'], create_buy_callback())
    
    if current_keys['scroll_1']: keyboard.add_hotkey(current_keys['scroll_1'], create_scroll_callback(1))
    if current_keys['scroll_2']: keyboard.add_hotkey(current_keys['scroll_2'], create_scroll_callback(2))
    if current_keys['scroll_3']: keyboard.add_hotkey(current_keys['scroll_3'], create_scroll_callback(3))
    if current_keys['scroll_4']: keyboard.add_hotkey(current_keys['scroll_4'], create_scroll_callback(4))
    
    keyboard.wait(current_keys['exit_bot'])
