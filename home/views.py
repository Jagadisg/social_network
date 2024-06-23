from django.db.models import Q
from django.utils import timezone
from rest_framework import mixins, viewsets
from rest_framework.response import Response
from django.forms.models import model_to_dict
from django.utils.decorators import method_decorator
from django.contrib.auth.hashers import make_password
from rest_framework import routers, status, permissions
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import SearchFilter, OrderingFilter
from django.views.decorators.csrf import csrf_protect

from .models import Customer, FriendRequest
from .decorator import authenticate_user_session
from .serializer import (
        SignupSerializer,
        LoginSerializer,
        UserSerializer,
        SendFriendRequestSerializer,
        FriendRequestSerializer,
        AcceptedRequestSerializer
    )
from .utils.utils import (
    save_session,
    save_object_into_database
    )


class CustomPagination(PageNumberPagination):
    '''
    paginate up to 10 records per page.
    '''
    
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


@method_decorator(csrf_protect, name="dispatch")
class SignupViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin):
    '''
    Create new user by using signup api
    '''
    
    queryset = Customer.objects.all()
    serializer_class = SignupSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request):

        serializer = SignupSerializer(data=request.data)

        if serializer.is_valid():
            password = serializer.validated_data['password']
            hashed_password = make_password(password)
            serializer.validated_data['password'] = hashed_password
            serializer.save()

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_protect, name="dispatch")
class LoginViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin):
    '''
    Signup the register user using Login api 
    '''
    
    queryset = Customer.objects.all()
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request):

        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data['user']
            user.last_login = timezone.now()
            if response := save_object_into_database(query_object=user, name="last login"):
                return response
            user_dict = model_to_dict(user, fields=['username', 'id'])
            save_session(request, user_dict)
            final_response = Response(data="Login successful", status=status.HTTP_200_OK)
            final_response.set_cookie("sessionid", request.session.session_key)

            return final_response

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST) 

  
class Searchapi(viewsets.GenericViewSet, mixins.ListModelMixin):
    '''
    Search by email or name using search api
    '''
    
    queryset = Customer.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = (SearchFilter, OrderingFilter)
    pagination_class = CustomPagination
    search_fields = ('email',)

    def get_queryset(self):
        queryset = Customer.objects.all()
        search_query = self.request.query_params.get('search', None)
        if search_query:
            if '@' in search_query:  # If search query contains '@', search by email
                queryset = queryset.filter(email=search_query)
            else:  # Otherwise, search by name
                queryset = queryset.filter(Q(username__icontains=search_query))
        return queryset
    
    
    @method_decorator(authenticate_user_session)
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)            
    

class SendFriendRequestViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin):
    '''
    send friend request to other user using sendfriendrequests api
    '''
    
    queryset = FriendRequest.objects.all()
    serializer_class = SendFriendRequestSerializer
    permission_classes = [permissions.AllowAny]
    
    @method_decorator(authenticate_user_session)
    def create(self, request, *args, **kwargs):
        serializer = SendFriendRequestSerializer(data=request.data)
        from_user_id = request.session.get('id')
        
        if not from_user_id:
            return Response(data="User is not logged in.", status=status.HTTP_401_UNAUTHORIZED)

        # Check for rate limiting: max 3 requests per minute
        one_minute_ago = timezone.now() - timezone.timedelta(minutes=1)
        recent_requests_count = FriendRequest.objects.filter(
            from_user_id=from_user_id,
            created_at__gte=one_minute_ago
        ).count()
        
        if recent_requests_count >= 3:
            return Response(data="You have sent too many friend requests. Please wait a minute before trying again.", status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        if serializer.is_valid():
            from_user = Customer.objects.get(id=from_user_id)
            to_user = serializer.validated_data.get('to_user')
            
            if from_user.id == to_user.id:
                return Response(data="You cannot send a friend request to yourself.", status=status.HTTP_400_BAD_REQUEST)

            # Check if any friend request already exists
            if FriendRequest.objects.filter(from_user=from_user, to_user_id=to_user).exists():
                return Response(data="Friend request already sent.", status=status.HTTP_400_BAD_REQUEST)

            serializer.validated_data['from_user'] = from_user
            serializer.validated_data['status'] = 'pending'
            serializer.save()
            return Response(data="Friend request sent.", status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FriendRequestViewset(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin):
    '''
    Get : list all the pending friend request received from the user.
    Post : Accept or reject the pending friend request. 
    '''
    
    serializer_class = FriendRequestSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        user_id = self.request.session.get('id')
        return FriendRequest.objects.filter(to_user_id=user_id, status='pending')
    
    @method_decorator(authenticate_user_session)
    def list(self, request, *args, **kwargs):            
        return super().list(request, *args, **kwargs)
    
    @method_decorator(authenticate_user_session)
    def create(self, request, *args, **kwargs):
        try:
            id = request.session.get('id')
            from_user_id = request.data.get('from_user')
            request_status = request.data.get('status')
            user_id = Customer.objects.get(id=id)
            
            if not from_user_id or request_status.lower() not in ['accepted', 'rejected']:
                return Response(data="Invalid data provided.",status=status.HTTP_400_BAD_REQUEST)
            
            friend_request = FriendRequest.objects.get(
                from_user_id= Customer.objects.get(id=from_user_id),
                to_user_id=user_id,
                status='pending'
            )
            friend_request.status = request_status
            friend_request.save()
            return Response({"message": f"Friend request {request_status}."}, status=status.HTTP_201_CREATED)
        except FriendRequest.DoesNotExist:
            return Response({"message": "Friend request not found or already responded to."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

class AcceptedFriendRequest(viewsets.GenericViewSet, mixins.ListModelMixin):
    '''
    list all the accepted friend request.
    '''
    
    serializer_class = AcceptedRequestSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        user_id = self.request.session.get('id')
        return FriendRequest.objects.filter(from_user_id=user_id, status='accepted')
        
    @method_decorator(authenticate_user_session)
    def list(self, request, *args, **kwargs):            
        return super().list(request, *args, **kwargs)
    
    
router = routers.DefaultRouter()
router.register(r'signup', SignupViewSet, basename='signup')
router.register(r'login', LoginViewSet, basename='login')
router.register(r'searchapi', Searchapi, basename='searchapi')
router.register(r'sendfriendrequests', SendFriendRequestViewSet, basename='send friend requests')
router.register(r'friendrequest', FriendRequestViewset, basename='friendrequests')
router.register(r'acceptedrequest', AcceptedFriendRequest, basename='acceptedfriendrequest')