from django.contrib import admin
from .models import Category, Tag, Project, ProjectImage

# 1. تسجيل الأقسام والتاجز 
# (تسجيل الـ Tag هنا هو اللي هيظهرلك علامة الـ '+' الخضراء في صفحة المشروع)
admin.site.register(Category)
admin.site.register(Tag)

# 2. عمل كلاس للصور الإضافية (عشان نعرضهم جوا صفحة المشروع نفسه)
class ProjectImageInline(admin.TabularInline):
    model = ProjectImage
    extra = 3  # هيعرضلك 3 خانات فاضيين لرفع الصور الإضافية (تقدر تغير الرقم براحتك)

# 3. إعدادات لوحة تحكم المشروع
class ProjectAdmin(admin.ModelAdmin):
    # دمج الصور الإضافية مع المشروع
    inlines = [ProjectImageInline]
    
    # تحسينات إضافية عشان شكل الجدول بتاع المشاريع من بره يبقى احترافي ومنظم
    list_display = ('title', 'owner', 'category', 'current_amount', 'target_amount', 'status', 'is_featured')
    list_filter = ('status', 'category', 'is_featured', 'start_date')
    search_fields = ('title', 'description')

# 4. تسجيل المشروع مع إعداداته الجديدة
admin.site.register(Project, ProjectAdmin)