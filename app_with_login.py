"""
Edge-TTS Tool with Login & Admin System
"""

import streamlit as st
import edge_tts
import asyncio
import os
from datetime import datetime
import base64
import json
import hashlib

st.set_page_config(
    page_title="HXT Edge-TTS",
    page_icon="🎤",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
<style>
    [data-testid="stSidebar"] {
        display: none;
    }
    
    .main {
        padding: 2rem;
    }
    
    .big-title {
        font-size: 3.5rem;
        font-weight: 800;
        text-align: center;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
    }
    
    .stTextArea textarea {
        font-size: 1.1rem;
        border-radius: 15px;
        border: 2px solid #e0e0e0;
        padding: 1rem;
    }
    
    .stTextArea textarea:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1);
    }
    
    .stButton > button {
        width: 100%;
        border-radius: 12px;
        padding: 1rem 2rem;
        font-size: 1.2rem;
        font-weight: 600;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
        transition: transform 0.2s;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
    }
    
    .stSelectbox > div > div {
        border-radius: 10px;
        border: 2px solid #e0e0e0;
    }
    
    audio {
        width: 100%;
        margin: 1rem 0;
    }
    
    .stSuccess, .stError, .stInfo {
        border-radius: 10px;
        padding: 1rem;
    }
    
    .login-box {
        max-width: 400px;
        margin: 2rem auto;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        background: white;
    }
    
    .user-info {
        position: fixed;
        top: 1rem;
        right: 1rem;
        background: white;
        padding: 0.8rem 1.5rem;
        border-radius: 25px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        display: flex;
        align-items: center;
        gap: 1rem;
        z-index: 1000;
    }
    
    .logout-btn {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        cursor: pointer;
        font-weight: 600;
        font-size: 0.9rem;
        transition: transform 0.2s;
    }
    
    .logout-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(245, 87, 108, 0.3);
    }
    
    .user-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.2);
    }
    
    .user-name {
        color: white;
        font-size: 1.2rem;
        font-weight: 600;
    }
    
    .logout-button {
        background: white;
        color: #764ba2;
        border: none;
        padding: 0.6rem 1.5rem;
        border-radius: 25px;
        font-weight: 700;
        font-size: 1rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

OUTPUT_DIR = "outputs"
USERS_FILE = "users.json"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Initialize users file if not exists
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump({"admin": {"password": "admin123", "role": "admin"}}, f, indent=2)

def load_users():
    """Load users from JSON"""
    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        default_users = {"admin": {"password": "admin123", "role": "admin"}}
        save_users(default_users)
        return default_users

def save_users(users):
    """Save users to JSON"""
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

def hash_password(password):
    """Simple password hashing"""
    return hashlib.sha256(password.encode()).hexdigest()

def check_login(username, password):
    """Check if login is valid and not expired"""
    users = load_users()
    if username in users:
        user = users[username]
        # Check password
        if user['password'] != password:
            return False, "Sai mật khẩu"
        
        # Check expiry (skip for admin)
        if username != 'admin':
            expiry_type = user.get('expiry_type', 'permanent')
            if expiry_type == 'days':
                from datetime import datetime, timedelta
                created_date = datetime.fromisoformat(user.get('created_date', datetime.now().isoformat()))
                expiry_days = user.get('expiry_days', 30)
                expiry_date = created_date + timedelta(days=expiry_days)
                
                if datetime.now() > expiry_date:
                    return False, "Tài khoản đã hết hạn"
        
        return True, "OK"
    return False, "Tài khoản không tồn tại"

def get_days_remaining(user_data):
    """Calculate days remaining for user"""
    from datetime import datetime, timedelta
    
    expiry_type = user_data.get('expiry_type', 'permanent')
    if expiry_type == 'permanent':
        return 999999  # Vĩnh viễn
    
    created_date = datetime.fromisoformat(user_data.get('created_date', datetime.now().isoformat()))
    expiry_days = user_data.get('expiry_days', 30)
    expiry_date = created_date + timedelta(days=expiry_days)
    
    days_left = (expiry_date - datetime.now()).days
    return max(0, days_left)

def cleanup_old_files(max_files=50):
    """Tự động xóa file cũ khi quá 50 file"""
    try:
        files = [os.path.join(OUTPUT_DIR, f) for f in os.listdir(OUTPUT_DIR) if f.endswith('.mp3')]
        if len(files) > max_files:
            files.sort(key=os.path.getctime)
            for f in files[:len(files) - max_files]:
                os.remove(f)
    except:
        pass

async def get_voices():
    return await edge_tts.list_voices()

async def generate_tts(text, voice, rate, volume, pitch):
    cleanup_old_files()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(OUTPUT_DIR, f"tts_{timestamp}.mp3")
    
    if rate == "+0%":
        rate = "+0%"
    if volume == "+0%":
        volume = "+0%"
    if pitch == "+0Hz":
        pitch = "+0Hz"
    
    communicate = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate=rate,
        volume=volume,
        pitch=pitch
    )
    
    await communicate.save(output_file)
    return output_file

def get_audio_download_link(file_path):
    with open(file_path, "rb") as f:
        audio_bytes = f.read()
    b64 = base64.b64encode(audio_bytes).decode()
    filename = os.path.basename(file_path)
    return f"""
    <div style="text-align: center; margin: 1rem 0;">
        <a href="data:audio/mp3;base64,{b64}" download="{filename}" 
           style="display: inline-block; padding: 0.8rem 2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                  color: white; text-decoration: none; border-radius: 10px; font-weight: 600; transition: transform 0.2s;">
            📥 Download MP3
        </a>
    </div>
    """

# CRITICAL: Check if this is a fresh page load (no query params means new visitor)
# Force logout for new sessions to prevent session sharing bug
if 'initialized' not in st.session_state:
    st.session_state.clear()
    st.session_state.initialized = True
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.is_admin = False

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False

# LOGIN PAGE
if not st.session_state.logged_in:
    st.markdown('<div class="big-title">HXT Edge-TTS</div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### 🔐 Đăng Nhập")
        
        username = st.text_input("👤 Tên đăng nhập", key="login_user")
        password = st.text_input("🔑 Mật khẩu", type="password", key="login_pass")
        
        if st.button("🚀 Đăng Nhập", type="primary"):
            success, message = check_login(username, password)
            if success:
                st.session_state.logged_in = True
                st.session_state.username = username
                users = load_users()
                st.session_state.is_admin = users[username].get('role') == 'admin'
                st.rerun()
            else:
                st.error(f"❌ {message}")
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center; color: #999; padding: 2rem 0;">
            <p>🔒 Vui lòng đăng nhập để sử dụng</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.stop()

# ADMIN PANEL
if st.session_state.is_admin:
    with st.expander("⚙️ Admin Panel - Quản lý tài khoản"):
        st.markdown("### 👥 Tạo tài khoản mới")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            new_username = st.text_input("Tên đăng nhập mới", key="new_user")
        with col2:
            new_password = st.text_input("Mật khẩu", type="password", key="new_pass")
        with col3:
            expiry_type = st.selectbox(
                "Thời hạn",
                ["permanent", "days"],
                format_func=lambda x: "🔓 Vĩnh viễn" if x == "permanent" else "⏰ Theo ngày"
            )
        
        expiry_days = None
        if expiry_type == "days":
            expiry_days = st.number_input("Số ngày sử dụng", min_value=1, max_value=365, value=30)
        
        if st.button("➕ Tạo Tài Khoản"):
            if new_username and new_password:
                users = load_users()
                if new_username in users:
                    st.error("❌ Tài khoản đã tồn tại!")
                else:
                    from datetime import datetime
                    user_data = {
                        "password": new_password,
                        "role": "user",
                        "created_date": datetime.now().isoformat(),
                        "expiry_type": expiry_type
                    }
                    if expiry_type == "days":
                        user_data["expiry_days"] = expiry_days
                    
                    users[new_username] = user_data
                    save_users(users)
                    
                    expiry_text = "vĩnh viễn" if expiry_type == "permanent" else f"{expiry_days} ngày"
                    st.success(f"✅ Đã tạo tài khoản: {new_username} (Thời hạn: {expiry_text})")
            else:
                st.error("❌ Vui lòng nhập đầy đủ thông tin!")
        
        st.markdown("---")
        st.markdown("### 📋 Danh sách người dùng")
        users = load_users()
        for username, info in users.items():
            col1, col2, col3, col4 = st.columns([2, 1, 2, 1])
            with col1:
                st.text(f"👤 {username}")
            with col2:
                role = "🔑 Admin" if info.get('role') == 'admin' else "👥 User"
                st.text(role)
            with col3:
                if username != "admin":
                    expiry_type = info.get('expiry_type', 'permanent')
                    if expiry_type == 'permanent':
                        st.text("🔓 Vĩnh viễn")
                    else:
                        days_left = get_days_remaining(info)
                        if days_left > 0:
                            st.text(f"⏰ Còn {days_left} ngày")
                        else:
                            st.text("⛔ Hết hạn")
                else:
                    st.text("-")
            with col4:
                if username != "admin" and username != st.session_state.username:
                    if st.button("🗑️", key=f"del_{username}"):
                        del users[username]
                        save_users(users)
                        st.rerun()

# Beautiful user header with logout button
st.markdown(f"""
<div class="user-header">
    <div class="user-name">👤 {st.session_state.username}</div>
</div>
""", unsafe_allow_html=True)

# Logout button below header
col1, col2, col3 = st.columns([7, 2.5, 1])
with col2:
    if st.button("🚪 Đăng xuất", key="logout_btn", type="primary", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.is_admin = False
        st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# Header
st.markdown('<div class="big-title">HXT Edge-TTS</div>', unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# Main content (same as before)
st.markdown("### 📝 Văn bản của bạn")
text_input = st.text_area(
    "",
    height=180,
    placeholder="Nhập văn bản cần chuyển thành giọng nói...\n\nHỗ trợ: Tiếng Việt, English, 中文, 日本語, và nhiều ngôn ngữ khác",
    label_visibility="collapsed"
)

if text_input:
    char_count = len(text_input)
    st.caption(f"✍️ {char_count} ký tự")

st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🎙️ Chọn giọng")
    
    if 'voices' not in st.session_state:
        with st.spinner("Đang tải..."):
            st.session_state.voices = asyncio.run(get_voices())
    
    voices = st.session_state.voices
    
    languages = {
        "vi": "🇻🇳 Tiếng Việt",
        "en": "🇬🇧 English",
        "zh": "🇨🇳 中文",
        "ja": "🇯🇵 日本語",
        "ko": "🇰🇷 한국어",
        "fr": "🇫🇷 Français",
        "de": "🇩🇪 Deutsch",
        "es": "🇪🇸 Español"
    }
    
    selected_lang = st.selectbox(
        "Ngôn ngữ",
        ["All"] + list(languages.keys()),
        format_func=lambda x: "🌍 Tất cả" if x == "All" else languages.get(x, x)
    )
    
    if selected_lang != "All":
        filtered_voices = [v for v in voices if v['Locale'].startswith(selected_lang)]
    else:
        filtered_voices = voices
    
    voice_options = {
        f"{v['ShortName'].split('-')[-1]} ({v['Gender']})": v['ShortName'] 
        for v in filtered_voices
    }
    
    selected_voice_display = st.selectbox(
        "Giọng nói",
        list(voice_options.keys())
    )
    selected_voice = voice_options[selected_voice_display]

with col2:
    st.markdown("### ⚙️ Tùy chỉnh")
    
    rate_val = st.slider(
        "🎚️ Tốc độ",
        min_value=-10,
        max_value=10,
        value=0,
        step=1,
        format="%d",
        help="Mỗi bước tăng/giảm 5%"
    )
    rate = f"{rate_val*5:+d}%" if rate_val != 0 else "+0%"
    
    volume_val = st.slider(
        "🔊 Âm lượng",
        min_value=-10,
        max_value=10,
        value=0,
        step=1,
        format="%d",
        help="Mỗi bước tăng/giảm 5%"
    )
    volume = f"{volume_val*5:+d}%" if volume_val != 0 else "+0%"
    
    pitch_val = st.slider(
        "🎵 Cao độ",
        min_value=-10,
        max_value=10,
        value=0,
        step=1,
        format="%d",
        help="Mỗi bước tăng/giảm 5Hz"
    )
    pitch = f"{pitch_val*5:+d}Hz" if pitch_val != 0 else "+0Hz"

st.markdown("---")

st.markdown("<br>", unsafe_allow_html=True)
generate_btn = st.button("🎵 TẠO AUDIO", type="primary")

if generate_btn:
    if not text_input.strip():
        st.error("❌ Vui lòng nhập văn bản!")
    else:
        with st.spinner("🎨 Đang tạo audio..."):
            try:
                output_file = asyncio.run(generate_tts(
                    text=text_input,
                    voice=selected_voice,
                    rate=rate,
                    volume=volume,
                    pitch=pitch
                ))
                
                st.success("✅ Hoàn thành!")
                
                st.audio(output_file, format='audio/mp3')
                
                st.markdown(get_audio_download_link(output_file), unsafe_allow_html=True)
                
                file_size = os.path.getsize(output_file) / 1024
                st.caption(f"📁 {os.path.basename(output_file)} • 💾 {file_size:.1f} KB")
                
            except Exception as e:
                st.error(f"❌ Lỗi: {str(e)}")

st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #999; padding: 2rem 0;">
        <p>🎤 <strong>HXT Edge-TTS</strong></p>
        <p>Powered by Microsoft Edge • 100+ AI Voices</p>
    </div>
    """,
    unsafe_allow_html=True
)
