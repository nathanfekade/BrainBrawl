from django.db import IntegrityError
from rest_framework.views import APIView
from django.contrib.auth.models import User
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers
from django.http import Http404
from .serializers import UserSerializer
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Group, GroupMember, Quiz, QuizQuestion, UserGroupScore
from .serializers import UserSerializer, GroupSerializer, GroupMemberSerializer, QuizSerializer, QuizQuestionSerializer, UserGroupScoreSerializer, EmailInputSerializer
import time
from pypdf import PdfReader
import os
from django.core.cache import cache
from google import genai
import google.generativeai as generativeai
import logging
import json
from pydantic import BaseModel




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


def under_token_limit(prompt, model_name="gemini-2.0-flash", max_tokens=1048000):
        try:
            generativeai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
            
            model = generativeai.GenerativeModel(model_name)
            input_tokens = model.count_tokens(prompt).total_tokens
            if input_tokens > max_tokens:
                return False, input_tokens
            else:
                return True, input_tokens

        except Exception as e:
            logging.error(f"An error occured during token limit check: {e}")
            return False, 0


class question_schema(BaseModel):
    question_text: str
    options: list[str]
    correct_answer: str

def question_generator(prompt):
    client = genai.Client(api_key=os.environ.get('GEMINI_API_KEY'))
    
    while True:

        last_request_time = cache.get('last_gemini_request_time', 0)
        now = time.time()
        delay = 4

        if now - last_request_time >= delay:
                
            response = client.models.generate_content(
                model="gemini-2.0-flash", contents=prompt,
                    config={
                    "response_mime_type": "application/json",
                    "response_schema": list[question_schema],
                }
            )
            cache.set('last_gemini_request_time', time.time())
            return response.text
        else:
                time.sleep(delay - (now - last_request_time))



def question_detail_level(path, page_count):
        
        reader = PdfReader(path)
        num_of_pages = len(reader.pages)
        question = "Generate 5 multiple-choice questions based on the text below. Each question should have exactly 4 options. Output the questions as a JSON array, where each element is an object with the following fields: 'question' (string), 'options' (array of 4 strings), and 'correct_answer' (string, exactly matching one of the options). Ensure that the correct_answer is identical to one of the strings in the options array. Provide only the JSON array as the output, without any additional text or explanations."
        prompt = question 
        question_answer = ""
        count = page_count - 1
        all_questions = []


        if num_of_pages <= count:
            for i in range(num_of_pages):
                page = reader.pages[i]
                text = page.extract_text()
                prompt = prompt + " " + text

            if prompt.strip() == question.strip():
                return "sorry i was unable to generate questions"

            # question_answer = question_answer 
            questions_response = json.loads(question_generator(prompt=prompt))
            all_questions.extend(questions_response)
            return all_questions

        for i in range(num_of_pages):
            
            page = reader.pages[i]
            text = page.extract_text()
            prompt = prompt + " " + text

            if i == count:
                if under_token_limit(prompt=prompt)[0] == False:
                        raise serializers.ValidationError("Token limit exceeded")
                        break
                # question_answer = question_answer + question_generator(prompt=prompt)
                questions_response = json.loads(question_generator(prompt=prompt))
                all_questions.extend(questions_response)
                
                prompt = question
                
                count += page_count

            elif num_of_pages-1 == i and i < count:
                if under_token_limit(prompt=prompt)[0] == False:
                        raise serializers.ValidationError("Token limit exceeded")
                        break
                
                # question_answer = question_answer + question_generator(prompt=prompt)
                questions_response = json.loads(question_generator(prompt=prompt))
                all_questions.extend(questions_response)
                prompt = question

                
        return all_questions




def call_gemini_api(quiz):
    group = quiz.group
    file_path = None
    if group.file:
        file_path = group.file.path 
        value = question_detail_level(file_path, 9)
        return value




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
                questions_data = call_gemini_api(quiz)
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
    

    def post(self, request, pk, format=None):
        """Update the user's score in the group based on total points from the frontend."""
        quiz = self.get_object(pk)
        total_points = request.data.get('total_points')

        if total_points is None:
            return Response(
                {"detail": "total_points is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            total_points = int(total_points)
            if total_points < 0:
                raise ValueError("Points cannot be negative.")
        except ValueError:
            return Response(
                {"detail": "total_points must be a non-negative integer."},
                status=status.HTTP_400_BAD_REQUEST
            )

        score, created = UserGroupScore.objects.get_or_create(
            group=quiz.group,
            user=request.user,
            defaults={'points': total_points}
        )
        if not created:
            score.points += total_points
            score.save()

        return Response(
            {"message": "Score updated successfully", "total_points_added": total_points},
            status=status.HTTP_200_OK
        )

class UserGroupScoreList(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, format=None):
        group_id = request.query_params.get('group')
        user_id = request.query_params.get('user')
        scores = UserGroupScore.objects.all()
        if group_id:
            try:
                group = Group.objects.get(pk=group_id)
                scores = scores.filter(group=group)
            except Group.DoesNotExist:
                return Response({"detail": "Group not found."}, status=status.HTTP_404_NOT_FOUND)
        if user_id:
            try:
                user = User.objects.get(pk=user_id)
                scores = scores.filter(user=user)
            except User.DoesNotExist:
                return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = UserGroupScoreSerializer(scores, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class UserIdByEmail(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, format=None):
        """Retrieve user_id by email."""
        serializer = EmailInputSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email=email)
                return Response({"user_id": user.id}, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response({"detail": "User with this email not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)