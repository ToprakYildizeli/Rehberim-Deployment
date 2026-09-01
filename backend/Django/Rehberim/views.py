from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from accounts.models import Student

@login_required
def dashboard(request):
    return render(request, "rehber/index.html")

def students(request):
    all_students = Student.objects.all()
    return render(request, "rehber/studentlist.html", {
        "students" : all_students
    })

def studentID(request, id):
    student = get_object_or_404(Student, id = id)
    return render(request, "rehber/studentID.html", {
        "student": student
    })

def settings(request):
    return render(request, "rehber/settings.html")
    