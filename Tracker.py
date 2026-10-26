import sqlite3
import datetime
import tkinter as tk
from tkinter import messagebox, ttk

# --- Инициализация Базы Данных ---
def init_db():
    conn = sqlite3.connect("sleep_tracker_v3.db") # Новое имя БД, чтобы очистить старые ошибки
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sleep_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            bed_time TEXT,
            wake_time TEXT,
            duration REAL,
            mood TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- Логика приложения ---
def calculate_sleep():
    try:
        bed_str = entry_bed.get()
        wake_str = entry_wake.get()
        mood = combo_mood.get()
        
        t_bed = datetime.datetime.strptime(bed_str, "%H:%M").time()
        t_wake = datetime.datetime.strptime(wake_str, "%H:%M").time()
        
        today = datetime.date.today()
        dt_bed = datetime.datetime.combine(today, t_bed)
        dt_wake = datetime.datetime.combine(today, t_wake)
        
        if dt_wake <= dt_bed:
            dt_wake += datetime.timedelta(days=1)
            
        duration_hours = (dt_wake - dt_bed).total_seconds() / 3600
        cycles = int((duration_hours * 60) // 90)
        
        deep = round(duration_hours * 0.20, 1)
        rem = round(duration_hours * 0.25, 1)
        light = round(duration_hours * 0.55, 1)
        
        conn = sqlite3.connect("sleep_tracker_v3.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO sleep_logs (date, bed_time, wake_time, duration, mood) VALUES (?, ?, ?, ?, ?)",
                       (today.strftime("%d.%m.%Y"), bed_str, wake_str, round(duration_hours, 2), mood))
        conn.commit()
        conn.close()
        
        result_text = f"Сон: {round(duration_hours, 1)} ч. ({cycles} циклов)\n" \
                      f"Глубокий: {deep} ч. | Быстрый: {rem} ч.\n" \
                      f"Легкий: {light} ч.\n\n"
                      
        if duration_hours < 6:
            result_text += "Мало сна! Постарайтесь лечь раньше."
        elif duration_hours > 9:
            result_text += "Избыток сна может вызвать вялость."
        else:
            result_text += "Отличная норма сна! Вы выспитесь."
            
        label_result.config(text=result_text)
        update_history()
        
    except ValueError:
        messagebox.showerror("Ошибка", "Формат ЧЧ:ММ (например, 23:00)")

def update_history():
    for item in tree.get_children():
        tree.delete(item)
    conn = sqlite3.connect("sleep_tracker_v3.db")
    cursor = conn.cursor()
    cursor.execute("SELECT date, bed_time, wake_time, duration, mood FROM sleep_logs ORDER BY id DESC LIMIT 5")
    for row in cursor.fetchall():
        # Правильное отображение времени и настроения без багов кодировки
        time_period = f"{row[1]}-{row[2]}"
        tree.insert("", "end", values=(row[0], time_period, f"{row[3]} ч", row[4]))
    conn.close()

# --- Стилизация Интерфейса (Dark Cosmic Mode) ---
root = tk.Tk()
root.title(" Трекер сна Pro")
root.geometry("450x750")
root.configure(bg="#12101a") 

# Стили для таблиц элементов
style = ttk.Style()
style.theme_use("clam")
style.configure("TCombobox", fieldbackground="#1f1a30", background="#383054", foreground="white")
style.configure("Treeview", background="#1f1a30", fieldbackground="#1f1a30", foreground="white", rowheight=32)
style.configure("Treeview.Heading", background="#383054", foreground="white", font=("Arial", 10, "bold"))

# Заголовок
lbl_title = tk.Label(root, text=" SLEEP TRACKER", font=("Arial", 18, "bold"), fg="#bb86fc", bg="#12101a")
lbl_title.pack(pady=15)

# Карточка ввода
card_input = tk.Frame(root, bg="#1f1a30", highlightbackground="#383054", highlightthickness=1)
card_input.pack(fill="x", padx=20, pady=5, ipady=10)

tk.Label(card_input, text="Время отхода ко сну:", fg="#a5a0bc", bg="#1f1a30", font=("Arial", 11)).pack(anchor="w", padx=15, pady=(10,0))
entry_bed = tk.Entry(card_input, bg="#12101a", fg="white", insertbackground="white", bd=0, font=("Arial", 12))
entry_bed.insert(0, "23:00")
entry_bed.pack(fill="x", padx=15, pady=5, ipady=8)

tk.Label(card_input, text="Время пробуждения:", fg="#a5a0bc", bg="#1f1a30", font=("Arial", 11)).pack(anchor="w", padx=15, pady=(5,0))
entry_wake = tk.Entry(card_input, bg="#12101a", fg="white", insertbackground="white", bd=0, font=("Arial", 12))
entry_wake.insert(0, "07:30")
entry_wake.pack(fill="x", padx=15, pady=5, ipady=8)

tk.Label(card_input, text="Настроение:", fg="#a5a0bc", bg="#1f1a30", font=("Arial", 11)).pack(anchor="w", padx=15, pady=(5,0))
combo_mood = ttk.Combobox(card_input, values=["Энергичное", "Хорошее", "Нормальное", "Усталое", "Разбитое"], state="readonly")
combo_mood.current(1)
combo_mood.pack(fill="x", padx=15, pady=5, ipady=5)

# Кнопка
btn_calc = tk.Button(root, text="Рассчитать и сохранить", command=calculate_sleep, bg="#6200ee", fg="white", font=("Arial", 12, "bold"), bd=0, activebackground="#3700b3", activeforeground="white")
btn_calc.pack(fill="x", padx=20, pady=10, ipady=12)

# Результаты
label_result = tk.Label(root, text="Здесь появятся фазы вашего сна...", justify="center", font=("Arial", 11), fg="white", bg="#383054", padx=15, pady=15, wraplength=380)
label_result.pack(fill="x", padx=20, pady=5)

# Таблица истории
lbl_hist = tk.Label(root, text="ИСТОРИЯ СНА", font=("Arial", 11, "bold"), fg="#a5a0bc", bg="#12101a")
lbl_hist.pack(anchor="w", padx=25, pady=(15, 5))

columns = ("date", "time", "dur", "mood")
tree = ttk.Treeview(root, columns=columns, show="headings", height=5)
tree.heading("date", text="Дата")
tree.heading("time", text="Время")
tree.heading("dur", text="Сон")
tree.heading("mood", text="Настрой")
tree.column("date", width=85, anchor="center")
tree.column("time", width=110, anchor="center")
tree.column("dur", width=70, anchor="center")
tree.column("mood", width=105, anchor="center")
tree.pack(fill="both", expand=True, padx=20, pady=(0, 15))

update_history()
root.mainloop()
