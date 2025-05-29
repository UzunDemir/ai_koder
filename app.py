import streamlit as st
from PIL import Image
import pytesseract
import PyPDF2
from io import BytesIO
import httpx
import asyncio

# Настройки страницы
st.set_page_config(page_title="DeepSeek Coder", layout="wide")

# Подключение tesseract
#pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"  # Для Streamlit Cloud

# Кастомный стиль для тёмной темы (неофициальный способ)
st.markdown("""
    <style>
        body {
            background-color: #1e1e1e;
            color: #000000;
        }
        .stChatMessage {
            background-color: #2c2c2c;
            border-radius: 8px;
            padding: 10px;
            margin-bottom: 10px;
        }
        .stTextInput, .stTextArea, .stButton {
            background-color: #333333;
            color: black;
        }
    </style>
""", unsafe_allow_html=True)

# Инициализация истории чата
if "messages" not in st.session_state:
    st.session_state.messages = []

# Функции извлечения текста
def extract_text_from_pdf(file):
    pdf_reader = PyPDF2.PdfReader(file)
    text = "\n".join([page.extract_text() for page in pdf_reader.pages if page.extract_text()])
    return text

def extract_text_from_image(file):
    image = Image.open(file)
    text = pytesseract.image_to_string(image, lang="eng+rus")
    return text

# Заголовок
st.title("🤖 DeepSeek Coding Agent")

# Боковая панель — история чата
st.sidebar.header("📜 История")
for i, msg in enumerate(st.session_state.messages):
    role = "👤 Пользователь" if msg["role"] == "user" else "🤖 DeepSeek"
    with st.sidebar.expander(f"{role} №{i+1}", expanded=False):
        st.markdown(msg["content"])

# Загрузка файла
uploaded_file = st.file_uploader(
    "Загрузите PDF или изображение с кодом:",
    type=["pdf", "png", "jpg", "jpeg"]
)

# Обработка файла
if uploaded_file:
    file_type = uploaded_file.type
    try:
        if "pdf" in file_type:
            text = extract_text_from_pdf(BytesIO(uploaded_file.read()))
        elif "image" in file_type:
            text = extract_text_from_image(uploaded_file)
        else:
            text = uploaded_file.read().decode("utf-8")
        
        st.session_state.messages.append({
            "role": "user", 
            "content": f"📎 Файл '{uploaded_file.name}':\n{text}"
        })
    except Exception as e:
        st.error(f"Ошибка при обработке файла: {e}")

# Отображение сообщений в основной части
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Асинхронный вызов API
async def get_deepseek_response(prompt):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {st.secrets['DEEPSEEK_API_KEY']}"
                },
                json={
                    "model": "deepseek-coder",
                    "messages": st.session_state.messages + [
                        {"role": "user", "content": prompt}
                    ],
                },
                timeout=30.0,
            )
            return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"❌ Ошибка API: {e}"

# Ввод запроса
if prompt := st.chat_input("Введите ваш запрос..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    response = asyncio.run(get_deepseek_response(prompt))
    st.session_state.messages.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.markdown(response)
