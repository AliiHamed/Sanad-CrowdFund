import json
from google import genai
from google.genai import types
from django.conf import settings
from projects.models import Project
import base64 
from .models import ChatLog # 📌 تم استدعاء الموديل هنا

def get_gemini_client():
    return genai.Client(api_key=settings.GEMINI_API_KEY)

# =========================================================
# 1. RAG System (Smart Project Retrieval)
# =========================================================
def get_relevant_projects_context():
    """يسحب أحدث 5 مشاريع نشطة فقط لتقليل استهلاك التوكنز وزيادة السرعة"""
    projects = Project.objects.filter(status='Active').order_by('-id')[:5]
    context = ""
    for p in projects:
        context += f"- Project ID: {p.id} | Title: '{p.title}' | Category: {p.category} | Target: {p.target_amount} EGP | Raised: {p.current_amount} EGP\n  Description: {p.description[:150]}...\n"
    return context

# =========================================================
# 2. Main Chatbot with Memory & Guardrails
# =========================================================
def chat_with_sanad(user_message: str, history: list, image_data: str = None) -> str:
    client = get_gemini_client()
    projects_context = get_relevant_projects_context()

    sys_instruct = f"""
    You are 'Sanad AI', the official AI assistant for the Sanad CrowdFund platform in Egypt.
    STRICT RULES:
    1. Answer questions related to crowdfunding, Sanad projects, donations.
    2. If the user uploads an image, analyze it creatively to help them create a crowdfunding campaign based on it, or answer their specific question about it.
    3. Use these ACTIVE projects as context: {projects_context}
    """

    formatted_contents = []
    # 📌 التعديل الجذري: فلترة الـ history وتأمينها لتجنب أي بطء أو أخطاء في الـ parts
    for msg in history:
        role = "user" if msg.get('role') == 'user' else "model"
        content_text = msg.get('content', '')
        if content_text:
            formatted_contents.append(
                types.Content(role=role, parts=[types.Part.from_text(text=content_text)])
            )
    
    # تجهيز محتوى المستخدم (نص + صورة إن وجدت)
    user_parts = []
    if user_message:
        user_parts.append(types.Part.from_text(text=user_message))
        
    if image_data:
        # فك تشفير الصورة من Base64
        mime_type = image_data.split(';')[0].split(':')[1]
        base64_str = image_data.split(',')[1]
        image_bytes = base64.b64decode(base64_str)
        user_parts.append(types.Part.from_bytes(data=image_bytes, mime_type=mime_type))

    if user_parts:
        formatted_contents.append(types.Content(role="user", parts=user_parts))

    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=formatted_contents,
        config=types.GenerateContentConfig(
            system_instruction=sys_instruct,
            temperature=0.7,
        )
    )
    
    answer = response.text
    
    # 📌 حفظ السؤال والرد في قاعدة البيانات للتحليلات (للنصوص فقط)
    if user_message:
        ChatLog.objects.create(user_message=user_message, bot_response=answer)
        
    return answer

# =========================================================
# 3. Campaign Assistant (Improve)
# =========================================================
def improve_campaign(title: str, description: str, story: str) -> str:
    client = get_gemini_client()
    prompt = f"""
    Improve this crowdfunding campaign to be more engaging and convincing:
    Title: {title}
    Description: {description}
    Story: {story}
    
    Return in this exact format:
    Improved Title: ...
    Improved Description: ...
    Improved Story: ...
    """
    response = client.models.generate_content(model="gemini-3.5-flash", contents=prompt)
    return response.text

# =========================================================
# 4. AI Funding Predictor
# =========================================================
def predict_funding_potential(title, description, category, target_amount, start_date, end_date) -> str:
    client = get_gemini_client()
    prompt = f"""
    Analyze this campaign and estimate its funding potential (High/Medium/Low):
    Title: {title} | Category: {category} | Target: {target_amount} | Dates: {start_date} to {end_date}
    Description: {description}
    
    Return in this format:
    Funding Potential: [Result]
    Reasons:
    - ...
    Suggestions to improve:
    - ...
    """
    response = client.models.generate_content(model="gemini-3.5-flash", contents=prompt)
    return response.text

# =========================================================
# 5. AI Analytics Generator (المحلل الذكي)
# =========================================================
def generate_ai_analytics():
    client = get_gemini_client()
    # جلب أحدث 50 سؤال تم طرحهم على البوت
    logs = ChatLog.objects.all().order_by('-created_at')[:50]
    if not logs:
        return "<p>No data available yet. Please interact with the chatbot first.</p>"

    context = "\n".join([f"Q: {log.user_message}" for log in logs])

    prompt = f"""
    You are a Data Analyst for 'Sanad CrowdFund'. Analyze these recent user queries asked to our AI:
    {context}
    
    Provide a professional analytics report containing:
    1. Top 3 Topics (with estimated percentages).
    2. General User Intent (Donation, creation, support, etc.).
    3. One Key Recommendation to improve the platform based on these queries.
    
    Output strictly in clean HTML format (use <h3>, <ul>, <li>, <strong>, <p>) suitable to be embedded directly in a webpage. DO NOT use markdown formatting like ```html.
    """
    response = client.models.generate_content(model="gemini-3.5-flash", contents=prompt)
    return response.text