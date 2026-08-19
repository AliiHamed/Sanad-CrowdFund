from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg, Q
from .models import Project, Category, Tag, ProjectImage
from interactions.models import Rating
from django.http import JsonResponse

def home_view(request):
    query = request.GET.get('q', '')
    
    if query:
        # إضافة prefetch_related('tags') لتحسين الأداء
        projects = Project.objects.filter(
            Q(title__icontains=query) | 
            Q(tags__name__icontains=query) | 
            Q(category__name__icontains=query)
        ).distinct().prefetch_related('tags').annotate(
            avg_rating=Avg('interaction_project_ratings__rate'),
            avg_rate=Avg('interaction_project_ratings__rate')
        ).order_by('-id')
    else:
        projects = None

    # إضافة prefetch_related('tags') هنا أيضاً
    top_rated_running = Project.objects.filter(status='Active').prefetch_related('tags').annotate(
        avg_rating=Avg('interaction_project_ratings__rate'),
        avg_rate=Avg('interaction_project_ratings__rate')
    ).order_by('-avg_rate', '-id')[:5]

    latest_projects = Project.objects.filter(status='Active').prefetch_related('tags').annotate(
        avg_rating=Avg('interaction_project_ratings__rate'),
        avg_rate=Avg('interaction_project_ratings__rate')
    ).order_by('-id')[:5]

    featured_projects = Project.objects.filter(is_featured=True, status='Active').prefetch_related('tags').annotate(
        avg_rating=Avg('interaction_project_ratings__rate'),
        avg_rate=Avg('interaction_project_ratings__rate')
    ).order_by('-id')[:5]

    categories = Category.objects.all()

    context = {
        'query': query,
        'projects': projects,
        'top_rated_running': top_rated_running,
        'latest_projects': latest_projects,
        'featured_projects': featured_projects,
        'categories': categories,
    }
    return render(request, 'index.html', context)


def projects_view(request):
    # إضافة prefetch_related('tags') لصفحة كل المشاريع
    projects = Project.objects.all().prefetch_related('tags').annotate(
        avg_rating=Avg('interaction_project_ratings__rate'),
        avg_rate=Avg('interaction_project_ratings__rate')
    ).order_by('-id')
    
    context = {
        'projects': projects,
    }
    return render(request, 'projects.html', context)


def project_details_view(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    comments = project.interaction_comments_project.all().order_by('-date')
    
    progress = 0
    if project.target_amount and project.target_amount > 0:
        progress = int((project.current_amount / project.target_amount) * 100)

    avg_rating = project.interaction_project_ratings.aggregate(Avg('rate'))['rate__avg']
    avg_rating = round(avg_rating, 1) if avg_rating else 0.0

    # إضافة prefetch_related('tags') أيضاً للمشاريع المشابهة
    similar_projects = Project.objects.filter(tags__in=project.tags.all()).exclude(id=project.id).distinct().prefetch_related('tags')[:4]

    context = {
        'project': project,
        'comments': comments,
        'progress': progress,
        'avg_rating': avg_rating,
        'similar_projects': similar_projects,
    }
    return render(request, 'project-details.html', context)


@login_required(login_url='login')
def create_project_view(request):
    categories = Category.objects.all()
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        story = request.POST.get('story')
        category_id = request.POST.get('category')
        target_amount = request.POST.get('target_amount')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        tags_input = request.POST.get('tags', '')
        
        raw_current_amount = request.POST.get('current_amount', 0.00)
        is_featured = request.POST.get('is_featured') == 'on' if request.user.is_staff else False
        main_image = request.FILES.get('image')
        additional_images = request.FILES.getlist('images')

        if title and target_amount and start_date and end_date:
            try:
                category_obj = Category.objects.filter(id=category_id).first() if category_id else None
                target_val = float(target_amount)
                if target_val <= 0:
                    messages.error(request, 'Target amount must be greater than zero.')
                    return redirect('create_project')

                if request.user.is_staff:
                    final_current_amount = max(0.00, float(raw_current_amount))
                else:
                    final_current_amount = 0.00

                project_status = 'Completed' if final_current_amount >= target_val else 'Active'
                project = Project.objects.create(
                    owner=request.user, title=title, description=description, story=story,
                    category=category_obj, target_amount=target_val, current_amount=final_current_amount,
                    is_featured=is_featured, start_date=start_date, end_date=end_date,
                    image=main_image, status=project_status
                )

                if tags_input:
                    tag_names = [t.strip() for t in tags_input.split(',')]
                    for t_name in tag_names:
                        if t_name:
                            tag_obj, created = Tag.objects.get_or_create(name=t_name)
                            project.tags.add(tag_obj)

                for img in additional_images:
                    ProjectImage.objects.create(project=project, image=img)

                messages.success(request, 'Campaign created successfully!')
                return redirect('project_details', project_id=project.id)
            except Exception as e:
                messages.error(request, f'An error occurred: {str(e)}')
        else:
            messages.error(request, 'Please fill in all required fields.')

    context = {'categories': categories}
    return render(request, 'create_project.html', context)


@login_required(login_url='login')
def rate_project_view(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if request.method == 'POST':
        score = request.POST.get('score')
        if score:
            Rating.objects.update_or_create(project=project, user=request.user, defaults={'rate': score})
            messages.success(request, 'Your rating has been submitted successfully!')
    return redirect('project_details', project_id=project.id)


@login_required(login_url='login')
def cancel_project_view(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    is_admin = request.user.is_superuser or request.user.is_staff
    is_owner = (project.owner == request.user)

    if not is_admin and not is_owner:
        messages.error(request, "You are not authorized to cancel this project.")
        return redirect('project_details', project_id=project.id)

    if is_admin:
        project.delete()
        messages.success(request, "Project has been cancelled successfully by Admin.")
        return redirect('projects')

    threshold_25_percent = float(project.target_amount) * 0.25
    if float(project.current_amount) < threshold_25_percent:
        project.delete()
        messages.success(request, "Project has been cancelled successfully.")
        return redirect('projects')
    else:
        messages.error(request, "Cannot cancel project! Raised amount exceeds 25% of target.")
        return redirect('project_details', project_id=project.id)


def add_category_view(request):
    if request.method == 'POST' and request.user.is_staff:
        name = request.POST.get('name')
        if name:
            cat = Category.objects.create(name=name)
            return JsonResponse({'success': True, 'id': cat.id, 'name': cat.name})
    return JsonResponse({'success': False})