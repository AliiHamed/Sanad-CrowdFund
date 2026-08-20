from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from .models import UserProfile
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from donations.models import Donation
from projects.models import Project
import re
import os
import requests
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
# ----------------- 1. دالة إنشاء الحساب وتفعيل الإيميل -----------------
def register_view(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        birth_date = request.POST.get('birth_date')
        country = request.POST.get('country')
        facebook = request.POST.get('facebook')
        profile_picture = request.FILES.get('profile_picture')

        # التأكد إن الباسورد متطابق
        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return redirect('register')
            
        # Validation for Egyptian phone number
        if phone and not re.match(r'^01[0125][0-9]{8}$', phone):
            messages.error(request, 'Invalid Egyptian phone number format.')
            return redirect('register')

        try:
            # إنشاء المستخدم مع عدم تفعيل الحساب (is_active = False)
            user, created = User.objects.get_or_create(
                username=email,
                defaults={
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                    'is_active': False
                }
            )
            
            if not created:
                user.set_password(password)
                user.first_name = first_name
                user.last_name = last_name
                user.is_active = False
                user.save()
            else:
                user.set_password(password)
                user.save()
            
            # إنشاء أو تحديث الـ UserProfile
            UserProfile.objects.update_or_create(
                user=user,
                defaults={
                    'phone_number': phone,
                    'country': country,
                    'facebook_link': facebook,
                    'profile_image': profile_picture if profile_picture else None,
                    'birth_date': birth_date if birth_date else None
                }
            )

            # Generate activation token and send email
            current_site = get_current_site(request)
            domain = current_site.domain
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            
            activation_link = f"http://{domain}/activate/{uid}/{token}/"
            subject = 'Activate Your CrowdFund Account'
            message = f'Hi {user.first_name},\n\nPlease click the link below to activate your account:\n{activation_link}\n\nThis link will expire in 24 hours.\n\nThank you!'
            
            # محاولة إرسال الإيميل (معالجة الأخطاء عشان السيرفر ميقعش)
            try:
                send_mail(subject, message, 'crowdfunding.team.eg@gmail.com', [email])
            except Exception as mail_error:
                user.delete() # نمسح الحساب لو الإيميل متبعتش عشان ميقفلش الإيميل على الفاضي
                messages.error(request, 'Failed to send activation email. Please check your network or try again later.')
                return redirect('register')

            messages.success(request, 'Account created successfully! Please check your email to activate your account.')
            return redirect('login')
            
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
            return redirect('register')

    return render(request, 'register.html')


# ----------------- 2. دالة تفعيل الحساب عبر الرابط -----------------
def activate_view(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None:
        user.is_active = True
        user.save()
        messages.success(request, 'Your account has been activated successfully! You can now log in.')
        return redirect('login')
    else:
        messages.error(request, 'The activation link is invalid or has expired!')
        return redirect('register')


# ----------------- 3. دالة تسجيل الدخول (منع الدخول بدون تفعيل) -----------------
def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    context = {}
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        # البحث عن المستخدم بالـ Email
        user_obj = User.objects.filter(email=email).first()
        
        if user_obj:
            # === التعديل هنا: منع تسجيل الدخول نهائياً وعرض رسالة لو الحساب مش متفعل ===
            if not user_obj.is_active:
                context['error'] = 'Your account is not activated. Please check your email for the activation link.'
                return render(request, 'login.html', context)

            # التحقق من صحة كلمة المرور
            user = authenticate(request, username=user_obj.username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                context['error'] = 'Incorrect password. Please try again.'
        else:
            context['error'] = 'No account found with this email address.'

    return render(request, 'login.html', context)


# ----------------- 4. دالة تسجيل الخروج -----------------
def logout_view(request):
    logout(request)
    return redirect('home')


# ----------------- 5. دالة عرض البروفايل -----------------
@login_required(login_url='login')
def profile_view(request):
    user_projects = Project.objects.filter(owner=request.user)
    user_donations = Donation.objects.filter(user=request.user).order_by('-id')

    context = {
        'user_projects': user_projects,
        'user_donations': user_donations,
    }
    return render(request, 'profile.html', context)


# ----------------- 6. دالة تعديل البروفايل -----------------
@login_required(login_url='login')
def edit_profile_view(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        request.user.first_name = request.POST.get('first_name')
        request.user.last_name = request.POST.get('last_name')
        request.user.save()

        phone = request.POST.get('phone', '').strip()
        # سيرفر سايد فاليشن للموبايل (11 رقم وبادئ بـ 01)
        if not (phone.isdigit() and len(phone) == 11 and phone.startswith('01')):
            messages.error(request, 'Please enter a valid 11-digit Egyptian phone number.')
            return redirect('edit_profile')
        
        profile.phone_number = phone
        profile.country = 'Egypt'  # ثابتة دائماً
        
        # استرجاع وتحديث رابط الفيسبوك بشكل آمن
        facebook = request.POST.get('facebook') or request.POST.get('facebook_link')
        if facebook is not None:
            profile.facebook_link = facebook.strip()
        
        birth_date = request.POST.get('birth_date')
        if birth_date:
            profile.birth_date = birth_date

        if 'profile_picture' in request.FILES:
            profile.profile_image = request.FILES['profile_picture']

        profile.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')

    context = {'profile': profile}
    return render(request, 'edit_profile.html', context)


# ----------------- 7. دالة مسح الحساب -----------------
@login_required(login_url='login')
def delete_account_view(request):
    if request.method == 'POST':
        password = request.POST.get('password')
        user = request.user
        if not user.check_password(password):
            messages.error(request, 'Incorrect password. Account deletion failed.')
            return redirect('profile')

        logout(request)
        user.delete()
        messages.success(request, 'Your account has been deleted successfully.')
        return redirect('home')
    
    return redirect('profile')


# ----------------- 8. Forgot Password View -----------------
def forgot_password_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            current_site = get_current_site(request)
            domain = current_site.domain
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            
            reset_link = f"http://{domain}/reset-password/{uid}/{token}/"
            subject = 'Reset Your CrowdFund Password'
            message = f'Hi {user.first_name},\n\nPlease click the link below to reset your password:\n{reset_link}\n\nThank you!'
            
            # محاولة إرسال البريد الإلكتروني
            send_mail(subject, message, 'crowdfunding.team.eg@gmail.com', [email])
            
            messages.success(request, 'Password reset link sent! Please check your email.')
            return redirect('forgot_password')
            
        except User.DoesNotExist:
            messages.error(request, 'No user found with this email.')
            return redirect('forgot_password')
        except Exception as e:
            messages.error(request, f'Failed to send email. Please check your SMTP settings or network.')
            return redirect('forgot_password')
            
    return render(request, 'forgot.html')


# ----------------- 9. Reset Password View -----------------
def reset_password_view(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            new_password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')
            if new_password and new_password == confirm_password:
                user.set_password(new_password)
                user.save()
                messages.success(request, 'Password reset successful! You can now log in.')
                return redirect('login')
            else:
                messages.error(request, 'Passwords do not match.')
        
        return render(request, 'reset_password.html')
    else:
        messages.error(request, 'The reset link is invalid or has expired!')
        return redirect('forgot_password')
    
    

import time

# === 1. دالة بدء عملية الدفع مع Paymob ===
@login_required(login_url='login')
def initiate_paymob_payment(request):
    if request.method == 'POST':
        amount_str = request.POST.get('amount')
        try:
            amount = float(amount_str)
            if amount <= 0:
                messages.error(request, 'Please enter a valid amount.')
                return redirect('profile')
        except (ValueError, TypeError):
            messages.error(request, 'Invalid amount entered.')
            return redirect('profile')

        amount_cents = int(amount * 100)
        api_key = settings.PAYMOB_API_KEY
        integration_id = settings.PAYMOB_INTEGRATION_ID

        if not api_key or not integration_id:
            messages.error(request, 'Payment gateway configuration is missing.')
            return redirect('profile')

        try:
            # Step 1: Authentication Token
            auth_res = requests.post(
                "https://accept.paymob.com/api/auth/tokens",
                json={"api_key": api_key}
            )
            auth_token = auth_res.json().get("token")

            # Step 2: Order Registration
            user = request.user
            merchant_order_id = f"WALLET_{user.id}_{int(time.time())}"

            order_res = requests.post(
                "https://accept.paymob.com/api/ecommerce/orders",
                json={
                    "auth_token": auth_token,
                    "delivery_needed": "false",
                    "amount_cents": str(amount_cents),
                    "currency": "EGP",
                    "merchant_order_id": merchant_order_id,
                    "items": []
                }
            )
            order_id = order_res.json().get("id")

            # Step 3: Payment Key
            billing_data = {
                "apartment": "NA",
                "email": user.email or "test@example.com",
                "floor": "NA",
                "first_name": user.first_name or "User",
                "street": "NA",
                "building": "NA",
                "phone_number": getattr(user.userprofile, 'phone_number', '01000000000'),
                "shipping_method": "NA",
                "postal_code": "NA",
                "city": "Cairo",
                "country": "EGP",
                "last_name": user.last_name or "Customer",
                "state": "Cairo"
            }

            key_res = requests.post(
                "https://accept.paymob.com/api/acceptance/payment_keys",
                json={
                    "auth_token": auth_token,
                    "amount_cents": str(amount_cents),
                    "expiration": 3600,
                    "order_id": str(order_id),
                    "billing_data": billing_data,
                    "currency": "EGP",
                    "integration_id": int(integration_id)
                }
            )
            payment_token = key_res.json().get("token")

            # Step 4: Redirection to Iframe
            iframe_id = "1069029"
            iframe_url = f"https://accept.paymob.com/api/acceptance/iframes/{iframe_id}?payment_token={payment_token}"
            return redirect(iframe_url)

        except Exception as e:
            messages.error(request, f'Error initializing payment: {str(e)}')
            return redirect('profile')

    return redirect('profile')


# === 2. دالة استقبال التأكيد وإعادة التوجيه وإضافة الرصيد ===
@csrf_exempt
def paymob_callback(request):
    data = request.GET if request.method == 'GET' else request.POST
    
    success = data.get('success')
    amount_cents = data.get('amount_cents')
    merchant_order_id = data.get('merchant_order_id') or data.get('order_id')
    
    is_success = str(success).lower() == 'true'

    if is_success and amount_cents:
        try:
            amount_egp = float(amount_cents) / 100.0

            # 1. حالة التبرع المباشر لمشروع
            if merchant_order_id and str(merchant_order_id).startswith('DONATE_'):
                parts = str(merchant_order_id).split('_')
                user_id = parts[1]
                project_id = parts[2]

                target_user = User.objects.filter(id=user_id).first()
                target_project = Project.objects.filter(id=project_id).first()

                if target_project and target_user:
                    Donation.objects.create(
                        user=target_user,
                        project=target_project,
                        amount=amount_egp
                    )
                    messages.success(request, f'Thank you! Successfully donated {amount_egp:.2f} EGP to "{target_project.title}".')
                    return redirect('project_details', project_id=target_project.id)

            # 2. حالة شحن رصيد المحفظة العادية
            target_user = None
            if request.user.is_authenticated:
                target_user = request.user
            elif merchant_order_id and str(merchant_order_id).startswith('WALLET_'):
                user_id = str(merchant_order_id).split('_')[1]
                target_user = User.objects.filter(id=user_id).first()

            if target_user:
                profile, _ = UserProfile.objects.get_or_create(user=target_user)
                profile.wallet = float(profile.wallet or 0.0) + amount_egp
                profile.save()
                messages.success(request, f'Successfully added {amount_egp:.2f} EGP to your wallet!')

        except Exception as e:
            messages.error(request, f'Error processing payment callback: {str(e)}')

        return redirect('profile')
    else:
        messages.error(request, 'Payment failed or was declined.')
        return redirect('profile')