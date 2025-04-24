from django.shortcuts import render, get_object_or_404, redirect
from .models import Project
from django.contrib.auth.decorators import login_required
from .forms import ProjectForm

# Create your views here.

def projects_list_view(request):

    projects = Project.objects.all()

    return render(request,'content/projects_list.html', {'projects': projects})

# @login_required
# def project_detail_view(request, pk):
#     project = get_object_or_404(Project, pk=pk)

#     if request.method == 'POST':
#         project.delete()
#         return redirect('projects_list')
        
#     return render(request, 'content/project_detail.html', {'project': project})


def project_new_view(request):

    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES)
        if form.is_valid():
            project = form.save()
            return redirect('projects_list') #urls.py pattern of the project section
    else:
        form = ProjectForm()

    return render(request, "content/project_new.html", {"form":form})