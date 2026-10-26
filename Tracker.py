import datetime
import pandas as pd
import streamlit as st
import os

# Настройка страницы с иконкой
st.set_page_config(
    page_title="Sleep Tracker Pro", 
    page_icon="icon.png" if os.path.exists("icon.png") else "🌙", 
    layout="centered"
)

# Принудительное внедрение иконки для рабочих столов мобильных устройств
st.markdown(
    """
    <head>
        <link rel="icon" type="image/png" href="https://githubusercontent.com">
        <link rel="apple-touch-icon" href="https://githubusercontent.com">
        <meta name="mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-capable" content="yes">
    </head>
    """,
    unsafe_allow_html=True
)

if os.path.exists("icon.png"):
    st.image("icon.png", width=80)

# --- Работа с личным хранилищем пользователя ---
def load_user_logs():
    if "my_sleep_history" not in st.session_state:
        st.session_state["my_sleep_history"] = []
    return st.session_state["my_sleep_history"]

def save_user_log(date, bed_time, wake_time, duration, mood):
    if "my_sleep_history" not in st.session_state:
        st.session_state["my_sleep_history"] = []
    
    new_log = {
        "Дата": date,
        "Время сна": f"{bed_time} - {wake_time}",
        "Всего сна": f"{round(duration, 2)} ч",
        "Настроение": mood,
        "raw_duration": duration,
        "raw_date": date
    }
    st.session_state["my_sleep_history"].insert(0, new_log)

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
    return tips

st.title("🌙 Личный Трекер Сна Pro")
st.write("Ваши данные хранятся приватно в вашем браузере и не видны другим пользователям.")

tab1, tab2, tab3 = st.tabs(["📊 Записать сон", "📈 История и Аналитика", "⏰ Калькулятор циклов"])

# Получаем историю текущего пользователя
history_logs = load_user_logs()

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
        
        save_user_log(log_date.strftime("%d.%m.%Y"), bed_time.strftime("%H:%M"), wake_time.strftime("%H:%M"), duration_hours, mood)
        st.success("Данные успешно сохранены в вашу личную историю!")
        
        st.subheader("📊 Анализ этой ночи")
        c1, c2 = st.columns(2)
        c1.metric("Общее время сна", f"{round(duration_hours, 1)} ч.")
        c2.metric("Пройдено полных циклов", f"{cycles_count}")
        
        if remainder_minutes > 20 and remainder_minutes < 70:
            st.warning(f"⚠️ Вы проснулись в середине цикла. Из-за этого может быть чувство разбитости.")
        else:
            st.success("✨ Отлично! Вы проснулись на стыке циклов, это идеальное время для бодрости.")

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
    
    if not history_logs:
        st.info("Ваша история пока пуста. Запишите первую ночь на первой вкладке!")
    else:
        df_history = pd.DataFrame(history_logs)
        df_chart = df_history.head(7).copy()
        df_chart = df_chart.iloc[::-1]
        
        st.subheader("Длительность последних снов")
        st.line_chart(data=df_chart, x="Дата", y="raw_duration", use_container_width=True)
        
        st.subheader("Ваш личный журнал")
        st.dataframe(df_history[["Дата", "Время сна", "Всего сна", "Настроение"]], use_container_width=True)

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
