import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from projects.models import Project
from .services import chat_with_sanad, improve_campaign, predict_funding_potential
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from .models import ChatLog
from .services import generate_ai_analytics
@csrf_exempt
def chat_api_view(request):
    """المسار الأساسي للمحادثة العامة مع دعم الصور والذاكرة"""
    if request.method != "POST": return JsonResponse({"error": "POST required"}, status=405)
    try:
        data = json.loads(request.body)
        user_message = data.get("message", "")
        history = data.get("history", [])
        image_data = data.get("image", None) # <-- استقبال الصورة
        
        if not user_message and not image_data:
            return JsonResponse({"error": "Message or image cannot be empty."}, status=400)
            
        answer = chat_with_sanad(user_message, history, image_data) # <-- تمرير الصورة للدالة
        return JsonResponse({"answer": answer})
    except Exception as e:
        print(f"Gemini API Error: {str(e)}")
        return JsonResponse({"error": "Sorry, I am currently experiencing high demand. Please try again in a few moments ⏳."}, status=500)

@csrf_exempt
def improve_campaign_view(request):
    if request.method != "POST": return JsonResponse({"error": "POST required"}, status=405)
    try:
        data = json.loads(request.body)
        result = improve_campaign(data.get("title", ""), data.get("description", ""), data.get("story", ""))
        return JsonResponse({"result": result})
    except Exception as e:
        print(f"Gemini API Error: {str(e)}")
        return JsonResponse({"error": "Sorry, I am currently experiencing high demand. Please try again in a few moments ⏳."}, status=500)

@csrf_exempt
def funding_prediction_view(request):
    if request.method != "POST": return JsonResponse({"error": "POST required"}, status=405)
    try:
        data = json.loads(request.body)
        result = predict_funding_potential(data.get("title", ""), data.get("description", ""), data.get("category", ""), data.get("target_amount", ""), data.get("start_date", ""), data.get("end_date", ""))
        return JsonResponse({"result": result})
    except Exception as e:
        print(f"Gemini API Error: {str(e)}")
        return JsonResponse({"error": "Sorry, I am currently experiencing high demand. Please try again in a few moments ⏳."}, status=500)


@staff_member_required
def analytics_dashboard_view(request):
    total_queries = ChatLog.objects.count()
    # توليد التقرير الذكي لحظياً
    ai_report = generate_ai_analytics() 
    return render(request, 'analytics_dashboard.html', {
        'total_queries': total_queries,
        'ai_report': ai_report
    })