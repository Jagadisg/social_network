from rest_framework.validators import UniqueValidator

from .models import Customer

unique_username = UniqueValidator(queryset=Customer.objects.all())