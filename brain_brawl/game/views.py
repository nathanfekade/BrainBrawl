from rest_framework.views import APIView
from django.contrib.auth.models import User
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.http import Http404
from .serializers import UserSerializer
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Group, GroupMember, Quiz, QuizQuestion, UserGroupScore
from .serializers import UserSerializer, GroupSerializer, GroupMemberSerializer, QuizSerializer, QuizQuestionSerializer, UserGroupScoreSerializer


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

class GroupList(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request, format=None):
        groups = Group.objects.all()
        serializer = GroupSerializer(groups, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, format=None):
        data = request.data.copy()
        data['creator_id'] = request.user.id
        serializer = GroupSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class GroupDetail(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_object(self, pk):
        try:
            return Group.objects.get(pk=pk)
        except Group.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        group = self.get_object(pk)
        serializer = GroupSerializer(group, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    # def put(self, request, pk, format=None):
    #     group = self.get_object(pk)
    #     if group.creator != request.user:
    #         return Response({"detail": "You are not authorized to update this group."}, status=status.HTTP_403_FORBIDDEN)
    #     data = request.data.copy()
    #     data['creator_id'] = request.user.id
    #     serializer = GroupSerializer(group, data=data, partial=True, context={'request': request})
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data, status=status.HTTP_200_OK)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # def delete(self, request, pk, format=None):
    #     group = self.get_object(pk)
    #     if group.creator != request.user:
    #         return Response({"detail": "You are not authorized to delete this group."}, status=status.HTTP_403_FORBIDDEN)
    #     group.delete()
    #     return Response(status=status.HTTP_204_NO_CONTENT)





