from django.db import IntegrityError
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


class GroupMemberList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        group_id = request.query_params.get('group')
        if group_id:
            try:
                group = Group.objects.get(pk=group_id)
                members = GroupMember.objects.filter(group=group)
            except Group.DoesNotExist:
                return Response({"detail": "Group not found."}, status=status.HTTP_404_NOT_FOUND)
        else:
            members = GroupMember.objects.all()
        serializer = GroupMemberSerializer(members, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, format=None):
           
        serializer = GroupMemberSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            group = serializer.validated_data['group']
            if group.creator != request.user:
                return Response({"detail": "Only the group creator can add members."}, status=status.HTTP_403_FORBIDDEN)
            try:
                serializer.save()
            except IntegrityError: 
                return Response({"detail": "This user is already a member of the group."}, status=status.HTTP_400_BAD_REQUEST)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GroupMemberDetail(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, group_id, user_id):
        try:
            return GroupMember.objects.get(group_id=group_id, user_id=user_id)
        except GroupMember.DoesNotExist:
            raise Http404

    # def delete(self, request, group_id, user_id, format=None):
    #     member = self.get_object(group_id, user_id)
    #     if member.group.creator != request.user:
    #         return Response({"detail": "Only the group creator can remove members."}, status=status.HTTP_403_FORBIDDEN)
    #     member.delete()
    #     return Response(status=status.HTTP_204_NO_CONTENT)



def call_gemini_api(quiz):
    # Replace this with actual Gemini API integration
    # Example: response = requests.post('https://api.gemini.com/generate', data={'topic': quiz.group.group_name})
    # return response.json()['questions']
    return [
        {
            "question_text": "What is the capital of France?",
            "options": ["Paris", "London", "Berlin", "Madrid"],
            "correct_answer": "Paris"
        },
        {
            "question_text": "What is 2 + 2?",
            "options": ["3", "4", "5", "6"],
            "correct_answer": "4"
        }
    ]

class QuizList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        """List all quizzes."""
        quizzes = Quiz.objects.all()
        serializer = QuizSerializer(quizzes, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, format=None):
        """Create a new quiz and generate questions via Gemini."""
        serializer = QuizSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            quiz = serializer.save()
            try:
                # Generate questions from Gemini API
                questions_data = call_gemini_api(quiz)
                # Create QuizQuestion instances
                for question in questions_data:
                    QuizQuestion.objects.create(
                        quiz=quiz,
                        question_text=question['question_text'],
                        options=question['options'],
                        correct_answer=question['correct_answer']
                    )
            except Exception as e:
                return Response(
                    {"detail": "Failed to generate questions", "error": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            # Return the quiz with generated questions
            serializer = QuizSerializer(quiz, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class QuizDetail(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        """Retrieve a quiz by ID or raise 404."""
        try:
            return Quiz.objects.get(pk=pk)
        except Quiz.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        """Retrieve a specific quiz."""
        quiz = self.get_object(pk)
        serializer = QuizSerializer(quiz, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)