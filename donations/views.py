from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from projects.models import Project
from .models import Donation
from accounts.models import UserProfile
from django.conf import settings
import requests
import time

@login_required(login_url='login')
def donate_view(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')  # 'wallet' أو 'paymob'
        amount_str = request.POST.get('amount')

        # التحقق من صحة المبلغ المدخل
        try:
            amount = float(amount_str)
            if amount <= 0:
                messages.error(request, 'Please enter a valid donation amount.')
                return redirect('project_details', project_id=project.id)
        except (ValueError, TypeError):
            messages.error(request, 'Invalid amount entered.')
            return redirect('project_details', project_id=project.id)

        # ----------------------------------------------------
        # 1. الخيار الأول: الدفع عن طريق رصيد المحفظة (Wallet)
        # ----------------------------------------------------
        if payment_method == 'wallet':
            profile, _ = UserProfile.objects.get_or_create(user=request.user)
            current_balance = float(profile.wallet or 0.0)

            # فحص إذا كان الرصيد غير كافٍ
            if current_balance < amount:
                messages.error(
                    request, 
                    f'Insufficient wallet balance! Your balance is {current_balance:.2f} EGP, but you tried to donate {amount:.2f} EGP.'
                )
                return redirect('project_details', project_id=project.id)

            # خصم المبلغ من المحفظة
            profile.wallet = current_balance - amount
            profile.save()

            # تسجيل التبرع
            Donation.objects.create(
                user=request.user,
                project=project,
                amount=amount
            )

            messages.success(request, f'Thank you! Successfully donated {amount:.2f} EGP from your wallet.')
            return redirect('project_details', project_id=project.id)

        # ----------------------------------------------------
        # 2. الخيار الثاني: الدفع الإلكتروني المباشر عبر Paymob
        # ----------------------------------------------------
        elif payment_method == 'paymob':
            amount_cents = int(amount * 100)
            api_key = settings.PAYMOB_API_KEY
            integration_id = settings.PAYMOB_INTEGRATION_ID

            if not api_key or not integration_id:
                messages.error(request, 'Payment gateway configuration is missing.')
                return redirect('project_details', project_id=project.id)

            try:
                # Step 1: Authentication Token
                auth_res = requests.post(
                    "https://accept.paymob.com/api/auth/tokens",
                    json={"api_key": api_key}
                )
                auth_token = auth_res.json().get("token")

                # Step 2: Order Registration مع تضمين ID التبرع والمشروع
                user = request.user
                merchant_order_id = f"DONATE_{user.id}_{project.id}_{int(time.time())}"

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
                return redirect('project_details', project_id=project.id)

        else:
            messages.error(request, 'Please select a valid payment method.')
            return redirect('project_details', project_id=project.id)

    return redirect('project_details', project_id=project.id)

# صفحة عرض رسالة الاعتذار والخيارات للمستخدم
@login_required(login_url='login')
def donate_confirm_view(request):
    pending = request.session.get('pending_donation')
    if not pending:
        return redirect('home')
    
    project = get_object_or_404(Project, id=pending['project_id'])
    context = {
        'project': project,
        'entered_amount': pending['entered_amount'],
        'remaining': pending['remaining'],
        'excess': pending['excess']
    }
    return render(request, 'donate_confirm.html', context)


# دالة تنفيذ الاختيار اللي المستخدم حدده
@login_required(login_url='login')
def complete_donation_view(request):
    pending = request.session.get('pending_donation')
    if not pending:
        return redirect('home')

    project = get_object_or_404(Project, id=pending['project_id'])
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    
    choice = request.POST.get('choice') # 'exact' أو 'full_with_wallet'
    remaining = pending['remaining']
    excess = pending['excess']

    target = float(project.target_amount) if project.target_amount else 0.0

    if choice == 'exact':
        # المتبرع اختار يتبرع بالباقي فقط للمشروع
        Donation.objects.create(
            user=request.user,
            project=project,
            amount=remaining
        )
        project.current_amount = target
        project.save()
        messages.success(request, f'Thank you! Your donation of {remaining} EGP (the exact remaining amount) was successful.')

    elif choice == 'full_with_wallet':
        # المتبرع اختار يتبرع بالباقي للمشروع والباقي الزيادة يروح محفظته
        Donation.objects.create(
            user=request.user,
            project=project,
            amount=remaining
        )
        project.current_amount = target
        project.save()

        # إضافة الزيادة للمحفظة
        profile.wallet = float(profile.wallet) + excess
        profile.save()
        messages.success(request, f'Thank you! {remaining} EGP went to the project, and {excess} EGP was securely added to your account wallet.')

    # مسح البيانات المؤقتة من الـ Session
    del request.session['pending_donation']
    return redirect('project_details', project_id=project.id)