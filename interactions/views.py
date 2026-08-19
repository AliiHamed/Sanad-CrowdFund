from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Comment, Reply, Report
from projects.models import Project

@login_required(login_url='login')
def add_comment_view(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if request.method == 'POST':
        comment_text = request.POST.get('comment')
        if comment_text:
            Comment.objects.create(
                project=project,
                user=request.user,
                comment=comment_text
            )
            messages.success(request, "Comment added successfully!")
    return redirect('project_details', project_id=project.id)


@login_required(login_url='login')
def add_reply_view(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if request.method == 'POST':
        reply_text = request.POST.get('reply')
        if reply_text:
            Reply.objects.create(
                comment=comment,
                user=request.user,
                reply=reply_text
            )
            messages.success(request, "Reply added successfully!")
    return redirect('project_details', project_id=comment.project.id)


@login_required(login_url='login')
def report_project_view(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if request.method == 'POST':
        reason = request.POST.get('reason')
        if reason:
            Report.objects.create(user=request.user, project=project, reason=reason)
            messages.success(request, "Report submitted successfully to admins.")
    return redirect('project_details', project_id=project.id)


@login_required(login_url='login')
def report_comment_view(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if request.method == 'POST':
        reason = request.POST.get('reason')
        if reason:
            Report.objects.create(user=request.user, project=comment.project, comment=comment, reason=reason)
            messages.success(request, "Comment reported successfully.")
    return redirect('project_details', project_id=comment.project.id)