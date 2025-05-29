from rest_framework.views import APIView
from django.contrib.auth.models import User
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.http import Http404
from .serializers import UserSerializer


class UserList(APIView):

# TO GET ALL USERS
    # def get(self, request, format=None):
    #     users = User.objects.all()
    #     serializer = UserSerializer(users, many=True)
    #     return Response(serializer.data, status=status.HTTP_200_OK)
    
    
    def post(self, request, format=None):

        serializer = UserSerializer(data= request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status= status.HTTP_201_CREATED)
        return Response(serializer.errors, status= status.HTTP_400_BAD_REQUEST)


class UserDetail(APIView):
    
    permission_classes = [IsAuthenticated]


    def get(self, request, format=None):

        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
