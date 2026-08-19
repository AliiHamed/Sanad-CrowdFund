from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from donations.views import donate_view, donate_confirm_view, complete_donation_view
from projects.views import (
    projects_view, 
    project_details_view, 
    create_project_view, 
    rate_project_view,
    home_view,
    cancel_project_view,
    add_category_view
)
from interactions.views import (
    add_comment_view, 
    add_reply_view, 
    report_project_view, 
    report_comment_view
)
from accounts.views import (
    register_view, 
    login_view, 
    logout_view, 
    profile_view, 
    edit_profile_view,
    delete_account_view,
    activate_view,
    forgot_password_view,
    reset_password_view,
    initiate_paymob_payment,  # تم نقلها من myapp إلى accounts.views
    paymob_callback,          # تم نقلها من myapp إلى accounts.views
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # ---------------- مسارات الصفحات الأساسية ----------------
    path('', home_view, name='home'),
    path('projects/', projects_view, name='projects'),
    path('projects/<int:project_id>/', project_details_view, name='project_details'),
    
    # ---------------- مسارات نظام الحسابات والدفع ----------------
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('register/', register_view, name='register'),
    path('profile/', profile_view, name='profile'),
    path('edit-profile/', edit_profile_view, name='edit_profile'),
    path('delete-account/', delete_account_view, name='delete_account'),
    path('activate/<uidb64>/<token>/', activate_view, name='activate'),
    path('forgot-password/', forgot_password_view, name='forgot_password'),
    path('reset-password/<uidb64>/<token>/', reset_password_view, name='reset_password'),
    path('paymob/pay/', initiate_paymob_payment, name='initiate_paymob_payment'),
    path('paymob/callback/', paymob_callback, name='paymob_callback'),
    
    # ---------------- مسارات المشاريع والتفاعل ----------------
    path('projects/new/', create_project_view, name='create_project'),
    path('add-category/', add_category_view, name='add_category'),
    path('projects/<int:project_id>/donate/', donate_view, name='donate'),
    path('projects/<int:project_id>/comment/', add_comment_view, name='add_comment'),
    path('comment/<int:comment_id>/reply/', add_reply_view, name='add_reply'), # <--- مسار الردود
    path('project/<int:project_id>/rate/', rate_project_view, name='rate_project'),
    path('project/<int:project_id>/cancel/', cancel_project_view, name='cancel_project'),
    
    # ---------------- مسارات الإبلاغ ----------------
    path('project/<int:project_id>/report/', report_project_view, name='report_project'),
    path('comment/<int:comment_id>/report/', report_comment_view, name='report_comment'),
    
    # ---------------- مسارات التبرعات الإضافية ----------------
    path('donate/confirm/', donate_confirm_view, name='donate_confirm'),
    path('donate/complete/', complete_donation_view, name='complete_donation'),

    # ---------------- مسارات الشات بوت (الذكاء الاصطناعي) ----------------
    path('api/chatbot/', include('chatbot.urls')),
]

# لعرض الصور المرفوعة (Media) في وضع التطوير (Development)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)