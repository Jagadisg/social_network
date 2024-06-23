from rest_framework import serializers
from django.contrib.auth.hashers import check_password

from .models import Customer, Address, FriendRequest
from .validator import unique_username


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['address_line1', 'address_line2', 'city']


class To_user(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['id','username', 'email', 'phone', 'profile_picture']
        extra_kwargs = {
            'username': {'read_only': True},
            'email': {'read_only': True},
            'phone': {'read_only': True},
            'profile_picture': {'read_only': True},
        }
        
        
class SignupSerializer(serializers.ModelSerializer):
    username = serializers.CharField(validators=[unique_username])
    email = serializers.EmailField(validators=[unique_username])
    phone = serializers.CharField(validators=[unique_username])
    profile_picture = serializers.ImageField(required=False)

    address = AddressSerializer()
    
    class Meta:
        model = Customer
        fields = ['username', 'email', 'password', 'phone', 'address', 'profile_picture', 'joined_on', 'last_login']
        extra_kwargs = {
            'password': {'write_only': True},
            'joined_on' : {'read_only': True},
            'last_login' : {'read_only': True},
            }

    def create(self, validated_data):
        address_data = validated_data.pop('address')
        address = Address.objects.create(**address_data)
        validated_data['email'] = validated_data['email'].lower()
        profile_picture = validated_data.pop('profile_picture', None)
        user = Customer.objects.create(address=address, **validated_data)
        if profile_picture:
            user.profile_picture = profile_picture
            user.save()
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.CharField(max_length=120)
    password = serializers.CharField(max_length=254, write_only=True)

    def validate(self,data):
        email = data.get('email')
        password = data.get('password')

        if email and password:
            try:
                user = Customer.objects.get(email=email.lower())
            except Customer.DoesNotExist:
                raise serializers.ValidationError("Invalid username or password")

            if not check_password(password,user.password):
                raise serializers.ValidationError("Invalid username or password")
        else:
            raise serializers.ValidationError("Must include 'username' and 'password'")

        data['user'] = user
        return data
    
    
class UserSerializer(serializers.ModelSerializer):
    
    address = AddressSerializer()
    
    class Meta:
        model = Customer
        fields = ['id','username', 'email', 'phone', 'address', 'joined_on', 'last_login', 'phone']
        
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['address'] = {
            'address_line1': instance.address.address_line1,
            'address_line2': instance.address.address_line2,
            'city': instance.address.city
        }
        return representation
    
    
class SendFriendRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = FriendRequest
        fields = ['to_user']
        
        
class FriendRequestSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    profile_picture = serializers.SerializerMethodField()
    
    class Meta:
        model = FriendRequest
        fields = ['status','from_user','username','email','profile_picture']
        
    def get_username(self, obj):
        return obj.from_user.username if obj.from_user else None
    
    def get_email(self, obj):
        return obj.from_user.email if obj.from_user else None
    
    def get_profile_picture(self, obj):
        return obj.from_user.profile_picture.url if obj.from_user.profile_picture else None
    
    
class AcceptedRequestSerializer(serializers.ModelSerializer):
    to_user = To_user()
    class Meta:
        model = FriendRequest
        fields = ['status','to_user']
        