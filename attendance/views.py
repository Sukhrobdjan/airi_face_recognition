from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.auth import login
from .models import Employee, AttendanceRecord, Schedule
from .face_recognition import FaceRecognitionSystem
import json
from datetime import datetime, date
import base64
from django.core.files.base import ContentFile

def dashboard(request):
    """Dashboard view"""
    employees = Employee.objects.all()
    recent_attendance = AttendanceRecord.objects.all()[:10]
    
    # Today's statistics
    today = timezone.now().date()
    today_checkins = AttendanceRecord.objects.filter(
        timestamp__date=today,
        attendance_type='IN'
    ).count()
    
    today_checkouts = AttendanceRecord.objects.filter(
        timestamp__date=today,
        attendance_type='OUT'
    ).count()
    
    context = {
        'employees': employees,
        'recent_attendance': recent_attendance,
        'today_checkins': today_checkins,
        'today_checkouts': today_checkouts,
        'total_employees': employees.count(),
    }
    
    return render(request, 'attendance/dashboard.html', context)

def register_employee(request):
    """Employee registration view"""
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        position = request.POST.get('position')
        face_data = request.POST.get('face_data')
        
        if not all([first_name, last_name, position, face_data]):
            messages.error(request, 'All fields are required including face capture.')
            return render(request, 'attendance/register.html')
        
        try:
            # Create user
            username = f"{first_name.lower()}.{last_name.lower()}"
            user = User.objects.create_user(
                username=username,
                first_name=first_name,
                last_name=last_name
            )
            
            # Process face data
            face_system = FaceRecognitionSystem()
            face_encoding = face_system.encode_face_from_base64(face_data)
            
            if face_encoding is None:
                user.delete()
                messages.error(request, 'Could not process face data. Please try again.')
                return render(request, 'attendance/register.html')
            
            # Save face image
            format, imgstr = face_data.split(';base64,')
            ext = format.split('/')[-1]
            face_image_file = ContentFile(
                base64.b64decode(imgstr),
                name=f'{username}_face.{ext}'
            )
            
            # Create employee
            employee = Employee.objects.create(
                user=user,
                first_name=first_name,
                last_name=last_name,
                position=position,
                face_encoding=face_system.save_face_encoding(face_encoding),
                face_image=face_image_file
            )
            
            messages.success(request, f'Employee {first_name} {last_name} registered successfully!')
            return redirect('dashboard')
            
        except Exception as e:
            messages.error(request, f'Error registering employee: {str(e)}')
    
    return render(request, 'attendance/register.html')

def checkin_checkout(request):
    """Check-in/Check-out view"""
    if request.method == 'POST':
        action = request.POST.get('action')
        face_data = request.POST.get('face_data')
        
        if not face_data:
            return JsonResponse({'success': False, 'message': 'Face data required'})
        
        try:
            # Load all employees for recognition
            employees = Employee.objects.filter(face_encoding__isnull=False)
            face_system = FaceRecognitionSystem()
            face_system.load_known_faces(employees)
            
            # Recognize face
            recognized_name, confidence = face_system.recognize_face(face_data)
            
            if not recognized_name or confidence < 0.7:
                return JsonResponse({
                    'success': False, 
                    'message': 'Face not recognized or confidence too low'
                })
            
            # Find employee
            name_parts = recognized_name.split(' ')
            first_name, last_name = name_parts[0], ' '.join(name_parts[1:])
            
            try:
                employee = Employee.objects.get(
                    first_name=first_name,
                    last_name=last_name
                )
            except Employee.DoesNotExist:
                return JsonResponse({
                    'success': False, 
                    'message': 'Employee not found'
                })
            
            # Record attendance
            attendance_type = 'IN' if action == 'checkin' else 'OUT'
            
            AttendanceRecord.objects.create(
                employee=employee,
                attendance_type=attendance_type,
                confidence=confidence
            )
            
            return JsonResponse({
                'success': True,
                'message': f'{employee.first_name} {employee.last_name} checked {action.replace("check", "")} successfully!',
                'employee': f'{employee.first_name} {employee.last_name}',
                'confidence': f'{confidence:.2%}'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})
    
    return render(request, 'attendance/checkin_checkout.html')

def schedule_view(request):
    """Schedule management view"""
    if request.method == 'POST':
        employee_id = request.POST.get('employee_id')
        schedule_date = request.POST.get('date')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        
        try:
            employee = Employee.objects.get(id=employee_id)
            Schedule.objects.create(
                employee=employee,
                date=schedule_date,
                start_time=start_time,
                end_time=end_time
            )
            messages.success(request, 'Schedule created successfully!')
        except Exception as e:
            messages.error(request, f'Error creating schedule: {str(e)}')
    
    employees = Employee.objects.all()
    schedules = Schedule.objects.filter(date__gte=date.today()).order_by('date', 'start_time')
    
    context = {
        'employees': employees,
        'schedules': schedules,
    }
    
    return render(request, 'attendance/schedule.html', context)

def train_system(request):
    """Train face recognition system"""
    if request.method == 'POST':
        try:
            employees = Employee.objects.filter(face_encoding__isnull=False)
            face_system = FaceRecognitionSystem()
            face_system.load_known_faces(employees)
            
            messages.success(request, f'System trained with {len(employees)} employees!')
        except Exception as e:
            messages.error(request, f'Training error: {str(e)}')
    
    employees = Employee.objects.all()
    trained_employees = employees.filter(face_encoding__isnull=False).count()
    untrained_employees = employees.filter(face_encoding__isnull=True).count()
    
    context = {
        'total_employees': employees.count(),
        'trained_employees': trained_employees,
        'untrained_employees': untrained_employees,
    }
    
    return render(request, 'attendance/train.html', context)