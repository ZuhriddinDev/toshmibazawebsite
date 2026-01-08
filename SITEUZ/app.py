import streamlit as st
import os
import shutil
import json
import base64
from datetime import datetime, timedelta, timezone

# 1. Konfiguratsiya va Papka yaratish
# Fayllar saqlanadigan papka nomi
UPLOAD_FOLDER = 'yuklangan_fayllar'

# Agar papka mavjud bo'lmasa, uni yaratamiz
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Reklama ma'lumotlarini saqlash uchun fayl
AD_FILE = 'reklama.json'
SECRETS_FILE = 'admin_secrets.json'
METADATA_FILE = 'file_metadata.json'
STATS_FILE = 'download_stats.json'

# Sahifa sozlamalari
st.set_page_config(page_title="Toshmi Baza Websayt", layout="wide", initial_sidebar_state="auto")

# 2. Yordamchi funksiyalar
def save_uploaded_file(uploaded_file, path):
    """Yuklangan faylni papkaga saqlash funksiyasi"""
    try:
        file_path = os.path.join(path, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return True
    except Exception as e:
        return False

def get_content(path):
    """Papkadagi fayl va papkalarni olish"""
    try:
        items = os.listdir(path)
        folders = [f for f in items if os.path.isdir(os.path.join(path, f))]
        files = [f for f in items if os.path.isfile(os.path.join(path, f))]
        return folders, files
    except:
        return [], []

def get_file_size(file_path):
    """Fayl hajmini MB da olish"""
    try:
        size = os.path.getsize(file_path)
        return f"{size / (1024 * 1024):.2f} MB"
    except:
        return "0.00 MB"

def count_files_in_folder(folder_path):
    """Papkadagi fayllar sonini olish"""
    try:
        return len([f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))])
    except:
        return 0

def delete_item(path, name):
    """Faylni o'chirish funksiyasi"""
    file_path = os.path.join(path, name)
    if os.path.exists(file_path):
        if os.path.isdir(file_path):
            shutil.rmtree(file_path)
        else:
            os.remove(file_path)
        return True
    return False

def create_folder(path, name):
    """Papka yaratish"""
    try:
        new_path = os.path.join(path, name)
        if not os.path.exists(new_path):
            os.makedirs(new_path)
            return True
    except:
        pass
    return False

def load_metadata():
    """Fayl ma'lumotlarini (izohlarni) o'qish"""
    if os.path.exists(METADATA_FILE):
        try:
            with open(METADATA_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}

def save_metadata_to_file(data):
    """Fayl ma'lumotlarini saqlash"""
    with open(METADATA_FILE, 'w') as f:
        json.dump(data, f)

def get_comment(file_path):
    """Fayl izohini olish"""
    data = load_metadata()
    try:
        key = os.path.relpath(file_path, UPLOAD_FOLDER)
        return data.get(key, "")
    except:
        return ""

def save_comment(file_path, comment):
    """Fayl izohini saqlash"""
    data = load_metadata()
    try:
        key = os.path.relpath(file_path, UPLOAD_FOLDER)
        if comment:
            data[key] = comment
        else:
            if key in data:
                del data[key]
        save_metadata_to_file(data)
    except:
        pass

def load_stats():
    """Yuklashlar statistikasini o'qish"""
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}

def save_stats(data):
    """Yuklashlar statistikasini saqlash"""
    with open(STATS_FILE, 'w') as f:
        json.dump(data, f)

def register_download(file_path):
    """Yuklashlar sonini oshirish"""
    stats = load_stats()
    try:
        key = os.path.relpath(file_path, UPLOAD_FOLDER)
        stats[key] = stats.get(key, 0) + 1
        save_stats(stats)
    except:
        pass

def get_top_downloads(limit=5):
    """Eng ko'p yuklangan fayllarni olish"""
    stats = load_stats()
    sorted_stats = sorted(stats.items(), key=lambda item: item[1], reverse=True)
    return sorted_stats[:limit]

def clear_search_state():
    """Qidiruvni tozalash"""
    if 'search_input' in st.session_state:
        st.session_state.search_input = ""

def rename_item(path, old_name, new_name):
    """Fayl yoki papka nomini o'zgartirish"""
    try:
        old_path = os.path.join(path, old_name)
        new_path = os.path.join(path, new_name)
        os.rename(old_path, new_path)
        
        # Metadata (izoh) ni ham yangilash
        data = load_metadata()
        try:
            old_key = os.path.relpath(old_path, UPLOAD_FOLDER)
            new_key = os.path.relpath(new_path, UPLOAD_FOLDER)
            if old_key in data:
                data[new_key] = data.pop(old_key)
                save_metadata_to_file(data)
        except:
            pass

        # Stats (yuklashlar soni) ni ham yangilash
        stats = load_stats()
        try:
            old_key = os.path.relpath(old_path, UPLOAD_FOLDER)
            new_key = os.path.relpath(new_path, UPLOAD_FOLDER)
            if old_key in stats:
                stats[new_key] = stats.pop(old_key)
                save_stats(stats)
        except:
            pass
            
        return True
    except:
        return False

def search_files(query, file_type=None):
    """Fayllarni qidirish (rekursiv)"""
    results = []
    for root, dirs, files in os.walk(UPLOAD_FOLDER):
        for file in files:
            if query.lower() in file.lower():
                if file_type and file_type != "Barchasi":
                    if not file.lower().endswith(file_type.lower()):
                        continue
                full_path = os.path.join(root, file)
                results.append((file, full_path))
    return results

def get_all_folders(base_path):
    """Barcha papkalarni olish (rekursiv)"""
    folders = []
    for root, dirs, files in os.walk(base_path):
        folders.append(root)
    return sorted(folders)

def load_ad():
    """Reklamani o'qish"""
    if os.path.exists(AD_FILE):
        try:
            with open(AD_FILE, 'r') as f:
                data = json.load(f)
            
            # Muddatni tekshirish
            if data.get('active') and data.get('expires_at'):
                expires_at = datetime.fromisoformat(data['expires_at'])
                if datetime.now() > expires_at:
                    data['active'] = False
                    with open(AD_FILE, 'w') as f:
                        json.dump(data, f)
            return data
        except:
            pass
    return {"text": "", "active": False}

def save_ad(text, active, hours=0):
    """Reklamani saqlash"""
    data = {"text": text, "active": active}
    if active and hours > 0:
        data["expires_at"] = (datetime.now() + timedelta(hours=hours)).isoformat()
    
    with open(AD_FILE, 'w') as f:
        json.dump(data, f)

def load_admin_credentials():
    """Admin login va parolini o'qish"""
    if os.path.exists(SECRETS_FILE):
        try:
            with open(SECRETS_FILE, 'r') as f:
                data = json.load(f)
                return data.get('username', 'admin'), data.get('password', 'admin123')
        except:
            pass
    return 'admin', 'admin123'

def save_admin_credentials(username, password):
    """Admin login va parolini saqlash"""
    with open(SECRETS_FILE, 'w') as f:
        json.dump({'username': username, 'password': password}, f)

# Tarjimalar lug'ati
TRANSLATIONS = {
    "uz": {
        "title": "🏛️ Toshmi Baza Websayt",
        "menu_user": "Asosiy Sahifa",
        "menu_admin": "Admin Paneli",
        "ad_label": "📢 E'LON",
        "dl_header": "📥 Fayllarni Yuklab Olish",
        "no_files": "Hozircha fayllar mavjud emas.",
        "admin_header": "Asosiy Sahifa",
        "login_user": "Foydalanuvchi nomi",
        "login_pass": "Parol",
        "login_btn": "Kirish",
        "logout_btn": "Chiqish",
        "ad_settings": "📢 Reklama Sozlamalari",
        "ad_text": "Reklama matni",
        "ad_active": "Reklamani yoqish",
        "ad_save": "Reklamani Saqlash",
        "ad_hours": "Reklama muddati (soat)",
        "ad_hours_help": "0 kiritilsa, reklama o'chirilmaguncha turadi.",
        "upload_header": "📤 Admin orqali fayl yuklash",
        "upload_label": "Fayl yuklash",
        "upload_btn": "Admin sifatida yuklash",
        "files_list": "### Fayllar va Papkalar",
        "delete_btn": "O'chirish",
        "dl_btn": "Yuklab olish",
        "settings": "⚙️ Sozlamalar",
        "change_pass": "Parolni o'zgartirish",
        "new_pass": "Yangi parol",
        "save_pass": "Parolni saqlash",
        "success_pass": "Parol muvaffaqiyatli yangilandi!",
        "success_ad": "Reklama muvaffaqiyatli yangilandi!",
        "success_upload": "saqlandi!",
        "error_upload": "Xatolik yuz berdi.",
        "login_success": "Tizimga kirdingiz!",
        "login_fail": "Login yoki parol noto'g'ri",
        "welcome": "Siz Admin sifatida tizimdasiz",
        "dark_mode": "Tungi rejim",
        "search_ph": "Fayllarni qidirish...",
        "create_folder": "📂 Yangi papka yaratish",
        "folder_name": "Papka nomi",
        "create": "Yaratish",
        "rename": "✏️ Tahrirlash",
        "new_name": "Yangi nom",
        "save": "Saqlash",
        "back": "⬅️ Orqaga",
        "current_path": "Joriy papka",
        "select_folder": "Qaysi papkaga yuklansin?",
        "comment": "Izoh",
        "write_comment": "Izoh yozing...",
        "save_comment": "Izohni saqlash",
        "del_comment": "Izohni o'chirish",
        "top_5": "🔥 Eng ko'p yuklanganlar (Top 5)",
        "downloads": "marta yuklandi",
        "pass_empty_warning": "Parol bo'sh bo'lmasligi kerak",
        "root_folder": "Asosiy papka (Root)",
        "admin_stats": "📊 Yuklashlar Statistikasi",
        "stat_file": "Fayl nomi",
        "stat_count": "Yuklashlar soni"
    },
    "ru": {
        "title": "🏛️ Веб-сайт базы Тошми",
        "menu_user": "Главная страница",
        "menu_admin": "Панель администратора",
        "ad_label": "📢 ОБЪЯВЛЕНИЕ",
        "dl_header": "📥 Скачать файлы",
        "no_files": "Файлов пока нет.",
        "admin_header": "Главная страница",
        "login_user": "Имя пользователя",
        "login_pass": "Пароль",
        "login_btn": "Войти",
        "logout_btn": "Выйти",
        "ad_settings": "📢 Настройки рекламы",
        "ad_text": "Текст рекламы",
        "ad_active": "Включить рекламу",
        "ad_save": "Сохранить рекламу",
        "ad_hours": "Длительность рекламы (часы)",
        "ad_hours_help": "Если 0, реклама будет висеть пока не отключите.",
        "upload_header": "📤 Загрузка файлов (Админ)",
        "upload_label": "Загрузить файл",
        "upload_btn": "Загрузить как админ",
        "files_list": "### Файлы и папки",
        "delete_btn": "Удалить",
        "dl_btn": "Скачать",
        "settings": "⚙️ Настройки",
        "change_pass": "Изменить пароль",
        "new_pass": "Новый пароль",
        "save_pass": "Сохранить пароль",
        "success_pass": "Пароль успешно обновлен!",
        "success_ad": "Реклама успешно обновлена!",
        "success_upload": "сохранен!",
        "error_upload": "Произошла ошибка.",
        "login_success": "Вы вошли в систему!",
        "login_fail": "Неверный логин или пароль",
        "welcome": "Вы вошли как администратор",
        "dark_mode": "Ночной режим",
        "search_ph": "Поиск файлов...",
        "create_folder": "📂 Создать новую папку",
        "folder_name": "Имя папки",
        "create": "Создать",
        "rename": "✏️ Редактировать",
        "new_name": "Новое имя",
        "save": "Сохранить",
        "back": "⬅️ Назад",
        "current_path": "Текущий путь",
        "select_folder": "В какую папку загрузить?",
        "comment": "Комментарий",
        "write_comment": "Напишите комментарий...",
        "save_comment": "Сохранить коммент.",
        "del_comment": "Удалить коммент.",
        "top_5": "🔥 Топ 5 скачиваний",
        "downloads": "скачиваний",
        "pass_empty_warning": "Пароль не должен быть пустым",
        "root_folder": "Главная папка (Root)",
        "admin_stats": "📊 Статистика скачиваний",
        "stat_file": "Имя файла",
        "stat_count": "Количество скачиваний"
    }
}

# 3. Asosiy Ilova Logikasi
def main():
    # Session State initsializatsiyasi
    if 'lang' not in st.session_state:
        st.session_state.lang = 'uz'
    if 'dark_mode' not in st.session_state:
        st.session_state.dark_mode = False
    if 'current_path' not in st.session_state:
        st.session_state.current_path = UPLOAD_FOLDER
    if 'current_view' not in st.session_state:
        st.session_state.current_view = 'user'

    txt = TRANSLATIONS[st.session_state.lang]

    # Til va Rejim tugmalari (Asosiy sahifada - Tepada)
    col_l1, col_l2, col_d, col_a, col_sp = st.columns([0.5, 0.5, 0.8, 2, 4])
    with col_l1:
        if st.button("UZ"):
            st.session_state.lang = 'uz'
            st.rerun()
    with col_l2:
        if st.button("RU"):
            st.session_state.lang = 'ru'
            st.rerun()
    with col_d:
        if st.button("☀️ | 🌙"):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.rerun()
    with col_a:
        if st.session_state.current_view == 'user':
            if st.button(txt['menu_admin']):
                st.session_state.current_view = 'admin'
                st.rerun()
        else:
            if st.button(txt['menu_user']):
                st.session_state.current_view = 'user'
                st.session_state['admin_logged_in'] = False
                st.rerun()

    # Tungi rejim (Dark Mode)
    if st.session_state.dark_mode:
        st.markdown("""
            <style>
            /* Medical Dark Theme */
            .stApp {
                background-color: #1a202c;
                color: #e2e8f0;
            }
            [data-testid="stSidebar"] {
                background-color: #2d3748;
                color: #e2e8f0;
            }
            h1, h2, h3, h4, h5, h6 {
                color: #63b3ed !important;
            }
            .stButton>button {
                background-color: #3182ce;
                color: white;
                border-radius: 8px;
                border: none;
            }
            </style>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <style>
            /* Medical Light Theme */
            .stApp {
                background-color: #f0f9ff;
                color: #2d3748;
            }
            [data-testid="stSidebar"] {
                background-color: #e6fffa;
                color: #2d3748;
            }
            h1, h2, h3, h4, h5, h6 {
                color: #0056b3 !important;
            }
            .stButton>button {
                background-color: #007bff;
                color: white;
                border-radius: 8px;
                border: none;
            }
            .stButton>button:hover {
                background-color: #0056b3;
            }
            </style>
            """, unsafe_allow_html=True)

    st.title(txt['title'])

    # Soat (O'zbekiston vaqti)
    uz_time = datetime.now(timezone.utc) + timedelta(hours=5)
    st.markdown(f"##### 🕒 {uz_time.strftime('%H:%M | %d.%m.%Y')}")

    # Reklama qismi (Barcha sahifalarda ko'rinadi)
    ad_data = load_ad()
    if ad_data.get('active') and ad_data.get('text'):
        st.warning(f"{txt['ad_label']}: {ad_data['text']}")

    # --- FOYDALANUVCHI QISMI ---
    if st.session_state.current_view == 'user':
        # Top 5 qismi
        top_files = get_top_downloads()
        if top_files:
            with st.expander(txt['top_5'], expanded=False):
                for rel_path, count in top_files:
                    full_path = os.path.join(UPLOAD_FOLDER, rel_path)
                    if os.path.exists(full_path):
                        filename = os.path.basename(full_path)
                        f_size = get_file_size(full_path)
                        col_t1, col_t2 = st.columns([4, 1])
                        with col_t1:
                            st.write(f"🏆 **{filename}** - {count} {txt['downloads']} ({f_size})")
                        with col_t2:
                            with open(full_path, "rb") as f:
                                file_data = f.read()
                            st.download_button(
                                label="⬇️",
                                data=file_data,
                                file_name=filename,
                                mime="application/octet-stream",
                                key=f"dl_top_{rel_path}",
                                on_click=register_download,
                                args=(full_path,)
                            )

        # Qidiruv tizimi
        search_query = st.text_input("🔍", placeholder=txt['search_ph'], key="search_input")
        
        if search_query:
            st.button(txt['back'], key="back_from_search", on_click=clear_search_state)

            st.subheader(f"🔍 {search_query}")
            results = search_files(search_query)
            if not results:
                st.info(txt['no_files'])
            else:
                for filename, full_path in results:
                    comment = get_comment(full_path)
                    file_size = get_file_size(full_path)
                    col_info, col_dl = st.columns([4, 1])
                    with col_info:
                        st.markdown(f"📄 **{filename}** ({file_size})")
                        if comment:
                            st.caption(f"📝 {comment}")
                    with col_dl:
                        with open(full_path, "rb") as f:
                            file_data = f.read()
                        st.download_button(
                            label="⬇️",
                            data=file_data,
                            file_name=filename,
                            mime="application/octet-stream",
                            key=f"dl_search_{filename}",
                            on_click=register_download,
                            args=(full_path,)
                        )
                    st.divider()
        else:
            # Papkalar bo'ylab navigatsiya
            current_display_path = st.session_state.current_path
            
            # Orqaga qaytish tugmasi
            if current_display_path != UPLOAD_FOLDER:
                if st.button(txt['back']):
                    st.session_state.current_path = os.path.dirname(current_display_path)
                    st.rerun()
                st.write(f"📂 {txt['current_path']}: `{os.path.relpath(current_display_path, UPLOAD_FOLDER)}`")

            folders, files = get_content(current_display_path)

            if not folders and not files:
                st.info(txt['no_files'])

            # Papkalarni ko'rsatish
            for folder in folders:
                if st.button(f"📁 {folder}", key=f"dir_{folder}"):
                    st.session_state.current_path = os.path.join(current_display_path, folder)
                    st.rerun()

            # Fayllarni ko'rsatish
            for filename in files:
                file_path = os.path.join(current_display_path, filename)
                comment = get_comment(file_path)
                file_size = get_file_size(file_path)
                
                col_info, col_dl = st.columns([4, 1])
                with col_info:
                    st.markdown(f"📄 **{filename}** ({file_size})")
                    if comment:
                        st.info(f"📝 {comment}")
                with col_dl:
                    with open(file_path, "rb") as f:
                        file_data = f.read()
                    st.download_button(
                        label="⬇️",
                        data=file_data,
                        file_name=filename,
                        mime="application/octet-stream",
                        key=f"dl_user_{filename}",
                        on_click=register_download,
                        args=(file_path,)
                    )
                st.divider()

    # --- ADMIN PANELI QISMI ---
    elif st.session_state.current_view == 'admin':
        st.subheader(txt['admin_header'])

        # Session State orqali login holatini tekshirish
        if 'admin_logged_in' not in st.session_state:
            st.session_state['admin_logged_in'] = False

        if not st.session_state['admin_logged_in']:
            # Login formasi
            username = st.text_input(txt['login_user'])
            password = st.text_input(txt['login_pass'], type='password')

            if st.button(txt['login_btn']):
                stored_user, stored_pass = load_admin_credentials()
                if username == stored_user and password == stored_pass:
                    st.session_state['admin_logged_in'] = True
                    st.success(txt['login_success'])
                    st.rerun() # Sahifani yangilash
                else:
                    st.error(txt['login_fail'])
        else:
            # Admin tizimga kirgandan keyingi ko'rinish
            st.success(txt['welcome'])
            
            if st.button(txt['logout_btn']):
                st.session_state['admin_logged_in'] = False
                st.rerun()

            # Admin navigatsiyasi
            current_admin_path = st.session_state.current_path
            if current_admin_path != UPLOAD_FOLDER:
                if st.button(txt['back'], key='admin_back'):
                    st.session_state.current_path = os.path.dirname(current_admin_path)
                    st.rerun()
            
            st.info(f"📂 {txt['current_path']}: `{os.path.relpath(current_admin_path, UPLOAD_FOLDER)}`")

            st.divider()
            st.subheader(txt['admin_stats'])
            
            admin_top_files = get_top_downloads(10)
            if admin_top_files:
                stats_data = [
                    {txt['stat_file']: f_name, txt['stat_count']: f_count}
                    for f_name, f_count in admin_top_files
                ]
                st.dataframe(stats_data, use_container_width=True, hide_index=True)
            else:
                st.info(txt['no_files'])

            st.divider()
            st.subheader(txt['ad_settings'])
            
            new_ad_text = st.text_area(txt['ad_text'], value=ad_data.get('text', ''))
            new_ad_active = st.checkbox(txt['ad_active'], value=ad_data.get('active', False))
            new_ad_hours = st.number_input(txt['ad_hours'], min_value=0, value=0, help=txt['ad_hours_help'])
            
            if st.button(txt['ad_save']):
                save_ad(new_ad_text, new_ad_active, new_ad_hours)
                st.success(txt['success_ad'])
                st.rerun()

            st.divider()
            st.subheader(txt['settings'])
            with st.expander(txt['change_pass']):
                current_user, _ = load_admin_credentials()
                new_username = st.text_input(txt['login_user'], value=current_user)
                new_password = st.text_input(txt['new_pass'], type='password')
                if st.button(txt['save_pass']):
                    if new_username and new_password:
                        save_admin_credentials(new_username, new_password)
                        st.success(txt['success_pass'])
                    else:
                        st.warning(txt['pass_empty_warning'])

            st.divider()
            st.subheader(txt['upload_header'])
            
            # Papka tanlash
            all_folders = get_all_folders(UPLOAD_FOLDER)
            folder_map = {}
            for f in all_folders:
                rel = os.path.relpath(f, UPLOAD_FOLDER)
                display = txt['root_folder'] if rel == "." else rel
                folder_map[display] = f
            
            current_rel = os.path.relpath(current_admin_path, UPLOAD_FOLDER)
            default_val = txt['root_folder'] if current_rel == "." else current_rel
            
            if default_val not in folder_map:
                default_val = list(folder_map.keys())[0]

            selected_folder = st.selectbox(txt['select_folder'], list(folder_map.keys()), index=list(folder_map.keys()).index(default_val))
            target_path = folder_map[selected_folder]

            admin_upload = st.file_uploader(txt['upload_label'], key="admin_uploader", accept_multiple_files=True)
            if admin_upload:
                if st.button(txt['upload_btn']):
                    saved_count = 0
                    for file in admin_upload:
                        if save_uploaded_file(file, target_path):
                            saved_count += 1
                    if saved_count > 0:
                        st.success(f"{saved_count} {txt['success_upload']}")
                        st.rerun()

            st.divider()
            st.write(txt['files_list'])

            # Papka yaratish
            with st.expander(txt['create_folder']):
                new_folder_name = st.text_input(txt['folder_name'])
                if st.button(txt['create']):
                    if new_folder_name:
                        if create_folder(current_admin_path, new_folder_name):
                            st.success(txt['success_upload'])
                            st.rerun()
                        else:
                            st.error(txt['error_upload'])

            folders, files = get_content(current_admin_path)
            
            if not folders and not files:
                st.warning(txt['no_files'])
            
            # Papkalarni boshqarish
            for folder in folders:
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    f_count = count_files_in_folder(os.path.join(current_admin_path, folder))
                    if st.button(f"📁 {folder} ({f_count})", key=f"adm_dir_{folder}"):
                        st.session_state.current_path = os.path.join(current_admin_path, folder)
                        st.rerun()
                with col2:
                    with st.popover(txt['rename']):
                        new_name = st.text_input(txt['new_name'], value=folder, key=f"ren_d_{folder}")
                        if st.button(txt['save'], key=f"save_d_{folder}"):
                            rename_item(current_admin_path, folder, new_name)
                            st.rerun()
                with col3:
                    if st.button(txt['delete_btn'], key=f"del_dir_{folder}"):
                        delete_item(current_admin_path, folder)
                        st.rerun()

            # Fayllarni boshqarish
            for filename in files:
                file_path = os.path.join(current_admin_path, filename)
                file_size = get_file_size(file_path)
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.text(f"📄 {filename} ({file_size})")
                    
                    # Izoh yozish qismi
                    current_comment = get_comment(file_path)
                    if current_comment:
                        st.caption(f"📝 {current_comment}")
                    
                    with st.popover(f"💬 {txt['comment']}"):
                        new_comment = st.text_input(txt['write_comment'], value=current_comment, key=f"c_in_{filename}")
                        c_col1, c_col2 = st.columns(2)
                        with c_col1:
                            if st.button(txt['save'], key=f"c_save_{filename}"):
                                save_comment(file_path, new_comment)
                                st.rerun()
                        with c_col2:
                            if st.button(txt['delete_btn'], key=f"c_del_{filename}"):
                                save_comment(file_path, "")
                                st.rerun()

                with col2:
                    with st.popover(txt['rename']):
                        new_name = st.text_input(txt['new_name'], value=filename, key=f"ren_f_{filename}")
                        if st.button(txt['save'], key=f"save_f_{filename}"):
                            rename_item(current_admin_path, filename, new_name)
                            st.rerun()
                with col3:
                    if st.button(txt['delete_btn'], key=f"del_file_{filename}"):
                        delete_item(current_admin_path, filename)
                        st.rerun()

if __name__ == '__main__':
    main()
