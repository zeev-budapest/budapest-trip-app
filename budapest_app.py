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
# ⚙️ תצורה, עיצוב ופונקציות בסיס
# ==========================================
st.set_page_config(page_title="Zeev's Budapest Pro", page_icon="🇭🇺", layout="centered", initial_sidebar_state="collapsed")

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
        'type': ['אטרקציה', 'אטרקציה', 'פנאי', 'קולינריה', 'חיי לילה', 'ספורט-בר']
    })

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
.place-card {{
    background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); margin-bottom: 15px; border-right: 5px solid #ff4b4b;
}}
</style>
""", unsafe_allow_html=True)

if 'toast_shown' not in st.session_state:
    st.toast(f"{greeting}! אל תשכח לקחת דרכון וארנק.", icon="🎒")
    st.session_state.toast_shown = True

# ==========================================
# 💾 ניהול מצב (State Management)
# ==========================================
if 'huf_rate' not in st.session_state: st.session_state.huf_rate = 97.5 
if 'expenses' not in st.session_state: st.session_state.expenses = pd.DataFrame(columns=["תאריך", "קטגוריה", "סכום_HUF", "סכום_ILS", "תיאור"])
if 'packing_list' not in st.session_state:
    st.session_state.packing_list = {
        "מסמכים": {"דרכון": False, "ביטוח": False, "מזומן": False},
        "אלקטרוניקה": {"Galaxy S25 Ultra": False, "מטען": False, "Powerbank": False},
        "לבוש": {"נעלי הליכה": False, "ז'קט": False, "כפכפים למרחצאות": False}
    }

# ==========================================
# 🧭 תפריט ניווט תחתון
# ==========================================
selected = option_menu(
    menu_title=None, 
    options=["בית", "מפה", "כסף", 'לו"ז'],
    icons=["house", "map", "wallet2", "calendar-check"], 
    default_index=0, orientation="horizontal",
    styles={"container": {"padding": "0!important"}, "nav-link": {"font-size": "13px"}}
)

# ==========================================
# 🏠 מסך הבית
# ==========================================
if selected == "בית":
    lottie_flight = load_lottieurl("https://assets3.lottiefiles.com/packages/lf20_jmejybvu.json")
    if lottie_flight: st_lottie(lottie_flight, height=120)
    
    st.title("הדשבורד של זאב 🇭🇺")
    st.write(f"**{greeting}!** מזג האוויר כרגע: 22°C ☀️")

    with st.expander("✈️ סטטוס טיסה WizzAir W6 2326"):
        st.success("הטיסה בזמן. שער עליה למטוס טרם נקבע.")
        
    with st.expander("🚨 חירום ושגרירות"):
        st.error("**משטרה/אמבולנס:** 112")
        st.info("**שגרירות ישראל בבודפשט:**\nכתובת: Fullánk u. 8\nטלפון: +36 1 392 6200")

    total_items = sum(len(i) for i in st.session_state.packing_list.values())
    packed_items = sum(sum(i.values()) for i in st.session_state.packing_list.values())
    progress = int((packed_items / total_items) * 100)
    st.caption(f"התקדמות אריזה למזוודה: {progress}%")
    st.progress(progress / 100.0)

    # מודול ה-AI המשוחזר והתקין
    st.divider()
    st.subheader("🤖 בוט הטיול (Gemini)")
    ai_query = st.text_input("שאל את המדריך המקומי שלך (למשל: איפה כדאי לאכול קיורטוש?):")
    
    if ai_query:
        if "GEMINI_API_KEY" not in st.secrets:
            st.error("⚠️ לא הוזן מפתח API. אנא הוסף את ה-GEMINI_API_KEY להגדרות ה-Secrets ב-Streamlit Cloud כפי שהוסבר.")
        else:
            with st.spinner("המדריך חושב..."):
                try:
                    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
                    model = genai.GenerativeModel(
                        'gemini-1.5-flash',
                        system_instruction="אתה מדריך תיירים מקומי ומומחה לבודפשט. ענה תמיד בעברית. התשובות שלך צריכות להיות קצרות, מדויקות ופרקטיות, כי המשתמש קורא אותן ממסך של טלפון סלולרי תוך כדי הליכה ברחוב."
                    )
                    response = model.generate_content(ai_query)
                    st.info(response.text)
                except Exception as e:
                    st.error(f"הייתה בעיה בתקשורת: {e}")

# ==========================================
# 🗺️ מסך מפה ואטרקציות (שוחזר!)
# ==========================================
elif selected == "מפה":
    tab1, tab2, tab3 = st.tabs(["מפה מרוכזת 🗺️", "אטרקציות 🏰", "שיחון קולי 🗣️"])
    
    with tab1:
        places = get_places_data()
        m = folium.Map(location=[47.4979, 19.0402], zoom_start=13, tiles="CartoDB positron")
        for i, row in places.iterrows():
            color = 'blue' if row['type'] == 'אטרקציה' else 'green' if row['type'] == 'קולינריה' else 'orange' if row['type'] == 'ספורט-בר' else 'red'
            folium.Marker([row['lat'], row['lon']], popup=row['name'], icon=folium.Icon(color=color)).add_to(m)
        st_folium(m, height=400, use_container_width=True)
        st.info("💡 המלצת אלגוריתם מסלול: התחל בבניין הפרלמנט (צפון), רד לטירת בודה, וסיים בערב ב-Szimpla Kert.")

    with tab2:
        st.markdown("""
        <div class="place-card">
            <h4>🟢 בניין הפרלמנט ההונגרי</h4>
            <p>פתוח עכשיו עד 18:00. חובה להביא דרכון לבידוק בטחוני.</p>
        </div>
        <div class="place-card" style="border-right-color: #28a745;">
            <h4>🔴 Hungarikum Bisztró</h4>
            <p>נסגר בקרוב. מסעדה מסורתית, מומלץ להזמין מקום.</p>
        </div>
        <div class="place-card" style="border-right-color: #ffc107;">
            <h4>⚽ Champs Sport Pub</h4>
            <p>ממוקם באזור הרובע היהודי. משדר את כל משחקי ליגת האלופות.</p>
        </div>
        """, unsafe_allow_html=True)

    with tab3:
        st.write("לחץ על המשפט כדי לשמוע איך הונגרי אומר את זה:")
        phrases = {"תודה רבה": "Köszönöm szépen", "כמה זה עולה?": "Mennyibe kerül?", "חשבון בבקשה": "A számlát kérem"}
        for heb, hun in phrases.items():
            st.markdown(f"**{heb}:** {hun}")
            html_audio = f"""<button onclick="let msg = new SpeechSynthesisUtterance('{hun}'); msg.lang='hu-HU'; window.speechSynthesis.speak(msg);" style="background:#ff4b4b; color:white; border:none; padding:5px 10px; border-radius:5px;">🔊 השמע</button>"""
            st.components.v1.html(html_audio, height=40)

# ==========================================
# 💱 מסך כסף והוצאות
# ==========================================
elif selected == "כסף":
    tab_calc, tab_track = st.tabs(["מחשבונים 🧮", "מעקב הוצאות 📊"])
    
    with tab_calc:
        huf_input = st.number_input("סכום בפורינט (HUF)", min_value=0, value=1000, step=100)
        ils_calc = huf_input / st.session_state.huf_rate
        st.success(f"שווה ל- **{ils_calc:.2f} ₪**")
        
        st.divider()
        st.subheader("🛍️ מחשבון החזר מס (Tax-Free)")
        st.caption("בהונגריה, קניות מעל 74,001 HUF באותה חנות מזכות בהחזר מע\"מ.")
        if huf_input > 74000:
            refund = huf_input * 0.13
            st.success(f"זכאי! החזר משוער: {refund:.0f} HUF (כ-{refund/st.session_state.huf_rate:.0f} ₪)")
        else:
            st.warning(f"חסר עוד {74001 - huf_input} HUF לזכאות באותה קבלה.")

    with tab_track:
        with st.form("expense_form"):
            col1, col2 = st.columns(2)
            cat = col1.selectbox("קטגוריה", ["אוכל", "תחבורה", "קניות", "אטרקציות", "אחר"])
            amount = col2.number_input("סכום (HUF)", min_value=0, step=500)
            desc = st.text_input("תיאור קצר (למשל: בירה בסימפלה)")
            if st.form_submit_button("➕ הוסף הוצאה"):
                new_row = {"תאריך": datetime.date.today().strftime("%d/%m"), "קטגוריה": cat, "סכום_HUF": amount, "סכום_ILS": round(amount/st.session_state.huf_rate, 1), "תיאור": desc}
                st.session_state.expenses = pd.concat([st.session_state.expenses, pd.DataFrame([new_row])], ignore_index=True)
                st.success("הוצאה נרשמה!")

        if not st.session_state.expenses.empty:
            total_ils = st.session_state.expenses['סכום_ILS'].sum()
            st.metric("סה\"כ הוצאות עד כה", f"₪ {total_ils:.2f}")
            
            fig = px.pie(st.session_state.expenses, values='סכום_ILS', names='קטגוריה', hole=0.4, title="פילוג הוצאות")
            st.plotly_chart(fig, use_container_width=True)
            
            st.write("פירוט מלא:")
            st.dataframe(st.session_state.expenses.style.highlight_max(subset=['סכום_ILS'], color='#ff4b4b'), hide_index=True)

# ==========================================
# 🎒 מסך לו"ז ואריזה
# ==========================================
elif selected == 'לו"ז':
    st.title("ניהול הטיול 📝")
    
    st.subheader("רשימת אריזה למזוודה")
    for category, items in st.session_state.packing_list.items():
        with st.expander(f"{category} ({sum(items.values())}/{len(items)})"):
            for item, is_packed in items.items():
                st.session_state.packing_list[category][item] = st.checkbox(item, value=is_packed, key=f"pack_{category}_{item}")
    
    if st.button("🔄 איפוס רשימה", use_container_width=True):
        for c in st.session_state.packing_list:
            for i in st.session_state.packing_list[c]: st.session_state.packing_list[c][i] = False
        st.rerun()
