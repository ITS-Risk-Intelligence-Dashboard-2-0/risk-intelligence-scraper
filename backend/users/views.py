from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import User
from django.http import HttpResponse

def test_view(request):
    return HttpResponse("Users URL is working!")

@api_view(['GET'])
def get_all_users(request):
    users = User.objects.all().values()
    return Response(list(users))

@api_view(['POST'])
def create_user(request):
    username = request.data.get("username")
    email = request.data.get("email")

    if not username:
        return Response({"error": "username is required"}, status=400)

    user = User.objects.create(username=username, email=email)
    return Response({"user added": user.username})

@api_view(['PUT'])
def update_user(request, id):
    new_username = request.GET.get("new_username", "")
    new_email = request.GET.get("new_email", "")
    try:
        user = User.objects.get(pk=id)
        if new_username:
            user.username = new_username
        if new_email:
            user.email = new_email
        user.save()
        return Response({"message": f"User {user.username} updated successfully"})
    except User.DoesNotExist:
        return Response({"error": "User not found"})

@api_view(['DELETE'])
def delete_user(request, id):
    try:
        user = User.objects.get(pk=id)
        username = user.username
        user.delete()
        return Response({"user deleted": username})
    except User.DoesNotExist:
        return Response({"error": "User not found"})
