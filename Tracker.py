import sqlite3
import datetime
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Sleep Tracker Pro", page_icon="🌙", layout="centered")

def init_db():
    conn = sqlite3.connect("sleep_tracker_cloud.db")
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

def save_log(date, bed_time, wake_time, duration, mood):
    conn = sqlite3.connect("sleep_tracker_cloud.db")
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO sleep_logs (date, bed_time, wake_time, duration, mood)
        VALUES (?, ?, ?, ?, ?)
    ''', (date, bed_time, wake_time, duration, mood))
    conn.commit()
    conn.close()

def get_logs():
    conn = sqlite3.connect("sleep_tracker_cloud.db")
    df = pd.read_sql_query("SELECT date, bed_time, wake_time, duration, mood FROM sleep_logs ORDER BY date DESC", conn)
    conn.close()
    return df

init_db()

def calculate_sleep_phases(duration_hours):
    deep = duration_hours * 0.20
    rem = duration_hours * 0.25
    light = duration_hours * 0.55
    return round(deep, 1), round(rem, 1), round(light, 1)

def get_sleep_tips(duration_hours, mood):
    tips = []
    if duration_hours < 6:
        tips.append("⚠️ **Недостаток сна:** Вы спали меньше 6 часов. Постарайтесь сегодня лечь пораньше.")
    elif duration_hours > 9:
        tips.append("💤 **Избыток сна:** Сон более 9 часов может вызывать вялость. Старайтесь соблюдать режим.")
    else:
        tips.append("✅ **Отличная длительность:** Вы уложились в здоровую норму (7–9 часов).")
    
    if mood in ["Усталое", "Разбитое"]:
        tips.append("💡 **Совет:** Попробуйте отказаться от гаджетов за 1 час до сна и проветрить комнату.")
    return tips

st.title("🌙 Умный Трекер Сна Pro")
st.write("Отслеживайте циклы сна, ведите историю и делитесь результатами.")

tab1, tab2, tab3 = st.tabs(["📊 Записать сон", "📈 История и Аналитика", "⏰ Калькулятор циклов"])

with tab1:
    st.header("📋 Новая запись")
    col1, col2 = st.columns(2)
    with col1:
        log_date = st.date_input("Дата ночи", datetime.date.today())
        bed_time = st.time_input("Время отхода ко сну", datetime.time(23, 0))
    with col2:
        st.write("") 
        wake_time = st.time_input("Время пробуждения", datetime.time(7, 30))
        
    mood = st.selectbox(
        "Настроение после пробуждения?",
        ["Энергичное", "Хорошее", "Нормальное", "Усталое", "Разбитое"]
    )
    
    if st.button("Рассчитать и сохранить"):
        dt_bed = datetime.datetime.combine(log_date, bed_time)
        dt_wake = datetime.datetime.combine(log_date, wake_time)
        if dt_wake <= dt_bed:
            dt_wake += datetime.timedelta(days=1)
            
        duration_hours = (dt_wake - dt_bed).total_seconds() / 3600
        
        total_minutes = duration_hours * 60
        cycles_count = int(total_minutes // 90)
        remainder_minutes = int(total_minutes % 90)
        
        save_log(log_date.strftime("%Y-%m-%d"), bed_time.strftime("%H:%M"), wake_time.strftime("%H:%M"), round(duration_hours, 2), mood)
        st.success("Данные успешно сохранены в историю!")
        
        st.subheader("📊 Анализ этой ночи")
        c1, c2 = st.columns(2)
        c1.metric("Общее время сна", f"{round(duration_hours, 1)} ч.")
        c2.metric("Пройдено полных циклов", f"{cycles_count}")
        
        if remainder_minutes > 20 and remainder_minutes < 70:
            st.warning(f"⚠️ Вы проснулись в середине цикла (остаток {remainder_minutes} мин). Из-за этого может быть чувство разбитости.")
        else:
            st.success("✨ Отлично! Вы проснулись близко к концу цикла, это идеальное время для бодрости.")

        deep_s, rem_s, light_s = calculate_sleep_phases(duration_hours)
        df_phases = pd.DataFrame({
            "Фаза сна": ["Глубокий сон", "Быстрый сон (REM)", "Легкий сон"],
            "Длительность (ч)": [deep_s, rem_s, light_s],
            "Норма (%)": ["~20%", "~25%", "~55%"]
        })
        st.table(df_phases)
        
        for tip in get_sleep_tips(duration_hours, mood):
            st.info(tip)

with tab2:
    st.header("📈 Ваша статистика")
    df_history = get_logs()
    
    if df_history.empty:
        st.info("История пуста. Добавьте первую запись во вкладке 'Записать сон'.")
    else:
        df_chart = df_history.head(7).copy()
        df_chart = df_chart.sort_values(by="date")
        
        st.subheader("Длительность сна за последние 7 дней")
        st.line_chart(data=df_chart, x="date", y="duration", use_container_width=True)
        
        st.subheader("Все сохраненные записи")
        st.dataframe(df_history, use_container_width=True)

with tab3:
    st.header("⏰ Калькулятор идеального пробуждения")
    st.write("Сон человека состоит из циклов по 90 минут. Чтобы проснуться легко, нужно вставать на стыке этих циклов.")
    
    plan_bed = st.time_input("Если вы ляжете спать в:", datetime.time(23, 0))
    st.write("Учитывается среднее время на засыпание — 15 минут.")
    
    now_date = datetime.date.today()
    dt_plan_bed = datetime.datetime.combine(now_date, plan_bed) + datetime.timedelta(minutes=15)
    
    st.subheader("⏰ Лучшее время для будильника:")
    
    times = []
    for cycles in [4,5,6]:
        wake_t = dt_plan_bed + datetime.timedelta(minutes=cycles * 90)
        label = "⚠️ Маловато" if cycles == 4 else ("👌 Хорошо" if cycles == 5 else "🌟 Идеально")
        times.append({"Циклы": f"{cycles} циклов", "Время сна": f"{cycles * 1.5} ч.", "Будильник": wake_t.strftime("%H:%M"), "Статус": label})
        
    st.table(pd.DataFrame(times))
