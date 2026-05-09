import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import datetime
import requests
from streamlit_lottie import st_lottie
from streamlit_option_menu import option_menu
import plotly.express as px
import google.generativeai as genai

# ==========================================
# ⚙️ תצורה, עיצוב ופונקציות בסיס (Features 7, 8, 13)
# ==========================================
st.set_page_config(page_title="Zeev's Budapest Pro", page_icon="🇭🇺", layout="centered", initial_sidebar_state="collapsed")

# (13) Aggressive Caching - שמירת נתונים בזיכרון המטמון לחיסכון ברשת
@st.cache_data
def load_lottieurl(url: str):
    try:
        r = requests.get(url)
        return r.json() if r.status_code == 200 else None
    except:
        return None

@st.cache_data
def get_places_data():
    return pd.DataFrame({
        'name': ['בניין הפרלמנט', 'טירת בודה', 'מרחצאות סצ\'ני', 'שוק האוכל המרכזי', 'Szimpla Kert', 'Champs Sport Pub'],
        'lat': [47.5071, 47.4962, 47.5181, 47.4871, 47.4979, 47.4950],
        'lon': [19.0456, 19.0396, 19.0814, 19.0585, 19.0633, 19.0610],
        'type': ['אטרקציה', 'אטרקציה', 'פנאי', 'קולינריה', 'חיי לילה', 'ספורט-בר'] # (12) מציאת שידורי ספורט
    })

# (7, 8) Custom Fonts & Dynamic Time Theme
current_hour = datetime.datetime.now().hour
greeting = "לילה טוב" if current_hour >= 19 or current_hour <= 5 else "בוקר טוב"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Heebo:wght@400;700&display=swap');
html, body, [class*="css"] {{
    font-family: 'Heebo', sans-serif;
    direction: rtl;
    text-align: right;
}}
.stTextInput > div > div > input, .stNumberInput > div > div > input {{ text-align: right; }}
#MainMenu, footer {{visibility: hidden;}}
/* (4) Cards CSS */
.place-card {{
    background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); margin-bottom: 15px; border-right: 5px solid #ff4b4b;
}}
</style>
""", unsafe_allow_html=True)

# (5) Toast Notifications
if 'toast_shown' not in st.session_state:
    st.toast(f"{greeting}! אל תשכח לקחת דרכון וארנק.", icon="🎒")
    st.session_state.toast_shown = True

# ==========================================
# 💾 ניהול מצב (State Management)
# ==========================================
if 'huf_rate' not in st.session_state: st.session_state.huf_rate = 97.5 
if 'expenses' not in st.session_state: st.session_state.expenses = pd.DataFrame(columns=["תאריך", "קטגוריה", "סכום_HUF", "סכום_ILS", "תיאור"])
if 'packing_list' not in st.session_state: # (20) Smart Packing List
    st.session_state.packing_list = {
        "מסמכים": {"דרכון": False, "ביטוח": False, "מזומן": False},
        "אלקטרוניקה": {"Galaxy S25 Ultra": False, "מטען": False, "Powerbank": False},
        "לבוש": {"נעלי הליכה": False, "ז'קט": False, "כפכפים למרחצאות": False}
    }

# ==========================================
# 🧭 תפריט ניווט תחתון (Feature 1)
# ==========================================
selected = option_menu(
    menu_title=None, 
    options=["בית", "מפה", "כסף", 'לו"ז'],
    icons=["house", "map", "wallet2", "calendar-check"], 
    default_index=0, orientation="horizontal",
    styles={"container": {"padding": "0!important"}, "nav-link": {"font-size": "13px"}}
)

# ==========================================
# 🏠 מסך הבית (Features 2, 9, 15, 17, 18)
# ==========================================
if selected == "בית":
    # (2) Lottie Animations
    lottie_flight = load_lottieurl("https://assets3.lottiefiles.com/packages/lf20_jmejybvu.json")
    if lottie_flight: st_lottie(lottie_flight, height=120)
    
    st.title("הדשבורד של זאב 🇭🇺")
    st.write(f"**{greeting}!** מזג האוויר כרגע: 22°C ☀️")

    # (17) Flight Tracker Placeholder
    with st.expander("✈️ סטטוס טיסה WizzAir W6 2326"):
        st.success("הטיסה בזמן. שער עליה למטוס טרם נקבע.")
        
    # (18) Emergency Hub
    with st.expander("🚨 חירום ושגרירות"):
        st.error("**משטרה/אמבולנס:** 112")
        st.info("**שגרירות ישראל בבודפשט:**\nכתובת: Fullánk u. 8\nטלפון: +36 1 392 6200")

    # (9) Progress Bar for Packing
    total_items = sum(len(i) for i in st.session_state.packing_list.values())
    packed_items = sum(sum(i.values()) for i in st.session_state.packing_list.values())
    progress = int((packed_items / total_items) * 100)
    st.caption(f"התקדמות אריזה למזוודה: {progress}%")
    st.progress(progress / 100.0)

   # (15) AI Assistant Interface
    st.divider()
    st.subheader("🤖 בוט הטיול (Gemini)")
    ai_query = st.text_input("שאל את המדריך המקומי שלך (למשל: איפה כדאי לאכול קיורטוש?):")
    
    if ai_query:
        if "GEMINI_API_KEY" not in st.secrets:
            st.error("חסר מפתח API בהגדרות השרת!")
        else:
            with st.spinner("המדריך חושב..."):
                try:
                    # הגדרת המפתח והמודל
                    genai.configure(api_key=st.secrets["AIzaSyCB9woyAf3xCamAY3TJUvYs8jgoYZYCHaE"])
                    
                    # הוספנו "הוראות מערכת" כדי שהבוט יענה כמו מדריך תיירים קצר ולעניין
                    model = genai.GenerativeModel(
                        'gemini-1.5-flash',
                        system_instruction="אתה מדריך תיירים מקומי ומומחה לבודפשט. ענה תמיד בעברית. התשובות שלך צריכות להיות קצרות, מדויקות ופרקטיות, כי המשתמש קורא אותן ממסך של טלפון סלולרי תוך כדי הליכה ברחוב. אל תכתוב מגילות."
                    )
                    
                    response = model.generate_content(ai_query)
                    st.info(response.text)
                except Exception as e:
                    st.error(f"הייתה בעיה בתקשורת: {e}")
# ==========================================
# 💱 מסך כסף והוצאות (Features 6, 11, 14)
# ==========================================
elif selected == "כסף":
    tab_calc, tab_track = st.tabs(["מחשבונים 🧮", "מעקב הוצאות 📊"])
    
    with tab_calc:
        huf_input = st.number_input("סכום בפורינט (HUF)", min_value=0, value=1000, step=100)
        ils_calc = huf_input / st.session_state.huf_rate
        st.success(f"שווה ל- **{ils_calc:.2f} ₪**")
        
        # (14) Tax-Free Calculator
        st.divider()
        st.subheader("🛍️ מחשבון החזר מס (Tax-Free)")
        st.caption("בהונגריה, קניות מעל 74,001 HUF באותה חנות מזכות בהחזר מע\"מ.")
        if huf_input > 74000:
            refund = huf_input * 0.13 # ממוצע החזר לאחר עמלות
            st.success(f"זכאי! החזר משוער: {refund:.0f} HUF (כ-{refund/st.session_state.huf_rate:.0f} ₪)")
        else:
            st.warning(f"חסר עוד {74001 - huf_input} HUF לזכאות באותה קבלה.")

    with tab_track:
        # (11) Expense Tracker Form
        with st.form("expense_form"):
            col1, col2 = st.columns(2)
            cat = col1.selectbox("קטגוריה", ["אוכל", "תחבורה", "קניות", "אטרקציות", "אחר"])
            amount = col2.number_input("סכום (HUF)", min_value=0, step=500)
            desc = st.text_input("תיאור קצר (למשל: בירה בסימפלה)")
            if st.form_submit_button("➕ הוסף הוצאה"):
                new_row = {"תאריך": datetime.date.today().strftime("%d/%m"), "קטגוריה": cat, "סכום_HUF": amount, "סכום_ILS": round(amount/st.session_state.huf_rate, 1), "תיאור": desc}
                st.session_state.expenses = pd.concat([st.session_state.expenses, pd.DataFrame([new_row])], ignore_index=True)
                st.success("הוצאה נרשמה!")

        # (6) Pandas Styler & DataViz
        if not st.session_state.expenses.empty:
            total_ils = st.session_state.expenses['סכום_ILS'].sum()
            st.metric("סה\"כ הוצאות עד כה", f"₪ {total_ils:.2f}")
            
            fig = px.pie(st.session_state.expenses, values='סכום_ILS', names='קטגוריה', hole=0.4, title="פילוג הוצאות")
            st.plotly_chart(fig, use_container_width=True)
            
            st.write("פירוט מלא:")
            st.dataframe(st.session_state.expenses.style.highlight_max(subset=['סכום_ILS'], color='#ff4b4b'), hide_index=True)

# ==========================================
# 🎒 מסך לו"ז ואריזה (Feature 3, 20)
# ==========================================
elif selected == 'לו"ז':
    st.title("ניהול הטיול 📝")
    
    # (3, 20) Expander Packing List
    st.subheader("רשימת אריזה למזוודה")
    for category, items in st.session_state.packing_list.items():
        with st.expander(f"{category} ({sum(items.values())}/{len(items)})"):
            for item, is_packed in items.items():
                st.session_state.packing_list[category][item] = st.checkbox(item, value=is_packed, key=f"pack_{category}_{item}")
    
    if st.button("🔄 איפוס רשימה", use_container_width=True):
        for c in st.session_state.packing_list:
            for i in st.session_state.packing_list[c]: st.session_state.packing_list[c][i] = False
        st.rerun()
