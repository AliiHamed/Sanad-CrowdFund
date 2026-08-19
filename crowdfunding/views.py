from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
import re

from projects.models import Project, Category
from accounts.models import UserProfile


def home_view(request):
    projects = Project.objects.all()
    categories = Category.objects.all()
    return render(request, 'index.html', {'projects': projects, 'categories': categories})


def login_view(request):
    # لو المستخدم عامل سشن وعمل تسجيل دخول، حوّله للـ home فوراً
    if request.user.is_authenticated:
        return redirect('home')

    context = {}
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        # 1. البحث الآمن عن المستخدم بالإيميل لجلب الـ username الصحيح
        user_obj = User.objects.filter(email=email).first()
        
        if user_obj:
            # 2. التحقق باستخدام الـ username الفعلي والباسورد الصحيح
            user = authenticate(request, username=user_obj.username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')

        # 3. استخدام متغير محلّي للـ error لمنع تراكم الرسائل في الـ session وعرضها في صفحة اللوجين فقط
        context['error'] = 'Invalid email or password. Please try again.'

    return render(request, 'login.html', context)


def logout_view(request):
    logout(request)
    return redirect('login')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        first_name    = request.POST.get('first_name', '').strip()
        last_name     = request.POST.get('last_name', '').strip()
        email         = request.POST.get('email', '').strip()
        phone         = request.POST.get('phone', '').strip()
        password      = request.POST.get('password', '')
        confirm_pass  = request.POST.get('confirm_password', '')
        country       = request.POST.get('country', '').strip()
        facebook      = request.POST.get('facebook', '').strip() # تم إرجاع استقبال الفيسبوك
        profile_pic   = request.FILES.get('profile_picture')

        # Validate required fields
        if not all([first_name, last_name, email, phone, password, confirm_pass]):
            messages.error(request, 'Please fill in all required fields.')
            return render(request, 'register.html')

        # Password match
        if password != confirm_pass:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'register.html')

        # Password length
        if len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
            return render(request, 'register.html')

        # Egyptian phone validation
        egypt_phone = re.compile(r'^01[0125][0-9]{8}$')
        if not egypt_phone.match(phone):
            messages.error(request, 'Please enter a valid Egyptian phone number (e.g. 01012345678).')
            return render(request, 'register.html')

        # Email uniqueness
        if User.objects.filter(email=email).exists():
            messages.error(request, 'This email address is already registered.')
            return render(request, 'register.html')

        # Create user — use email as username base
        username = email.split('@')[0]
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        # Update UserProfile (created automatically by signal)
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.phone_number = phone
        profile.country = country
        if facebook: # حفظ رابط الفيسبوك لو المستخدم كتبه
            profile.facebook_link = facebook
        if profile_pic:
            profile.profile_image = profile_pic
        profile.save()

        messages.success(request, 'تم إنشاء حسابك بنجاح! يمكنك تسحيل الدخول الآن.')
        return redirect('login')

    return render(request, 'register.html')


def projects_view(request):
    all_projects = Project.objects.all()
    return render(request, 'projects.html', {'projects': all_projects})


def project_details_view(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if project.target_amount and project.target_amount > 0:
        progress = min(int((project.current_amount / project.target_amount) * 100), 100)
    else:
        progress = 0
    return render(request, 'project-details.html', {'project': project, 'progress': progress})


@login_required(login_url='/login/')
def profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    user_projects = request.user.projects.all()
    user_donations = request.user.donations.select_related('project').order_by('-date')[:10]
    return render(request, 'profile.html', {
        'profile': profile,
        'user_projects': user_projects,
        'user_donations': user_donations,
    })