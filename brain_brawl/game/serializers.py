from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Group, GroupMember, Quiz, QuizQuestion, UserGroupScore
from rest_framework.validators import UniqueValidator  


class UserSerializer(serializers.ModelSerializer):

    password = serializers.CharField(write_only=True, required=True)
    email = serializers.EmailField(required=True, allow_blank=False)
    username = serializers.CharField(required=True, allow_blank=False)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']
        read_only_fields = ['id']
        extra_kwargs = {
            'username': {'validators': [UniqueValidator(queryset=User.objects.all())]},
            'email': {'validators': [UniqueValidator(queryset=User.objects.all())]}
        }
    
    def valildate_email(self, value):

        if not value:
            raise serializers.ValidationError("Email address is required")
        
        if User.objects.filter(email=value).exists():
            
            if self.instance and self.instance.email != value():
                raise serializers.ValidationError("A user with this email alreay exists")
            elif not self.instance:
                raise serializers.ValidationError("A user with this email already exists")
            return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
    
    def update(self, instance, validated_data):

        password = validated_data.pop('password')

        for attr, value in validated_data.items():

            setattr(instance, attr, value)
            if password:
                instance.set_password(password)
            instance.save()
            return instance

class GroupMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), 
        source='user', 
        write_only=True
    )

    class Meta:
        model = GroupMember
        fields = ['group', 'user', 'user_id']
        extra_kwargs = {
            'group': {'required': False}  
        }

class QuizQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizQuestion
        fields = ['id', 'quiz', 'question_text', 'options', 'correct_answer']
        extra_kwargs = {
            'quiz': {'required': False}  
        }

class QuizSerializer(serializers.ModelSerializer):
    questions = QuizQuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = ['id', 'group', 'start_time', 'questions']
        extra_kwargs = {
            'group': {'required': False}  
        }

class GroupSerializer(serializers.ModelSerializer):
    creator = UserSerializer(read_only=True)
    creator_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), 
        source='creator', 
        write_only=True
    )
    members = GroupMemberSerializer(
        many=True, 
        read_only=True
    )
    quizzes = QuizSerializer(many=True, read_only=True)

    class Meta:
        model = Group
        fields = ['id', 'group_name', 'creator', 'creator_id', 'file', 'members', 'quizzes']

    def validate_file(self, value):
        from .validators import validate_file_size_and_type
        validate_file_size_and_type(value)
        return value

class UserGroupScoreSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), 
        source='user', 
        write_only=True
    )

    class Meta:
        model = UserGroupScore
        fields = ['group', 'user', 'user_id', 'points']
        extra_kwargs = {
            'group': {'required': False}  
        }