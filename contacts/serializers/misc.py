# Rest Framework Imports
from rest_framework import serializers
from rest_framework import viewsets
from rest_framework.decorators import detail_route
from rest_framework.response import Response

#Local Imports
import contacts.models as cont


##############################################
# Facility Serializer and Viewset
##############################################

class FacilitySerializer(serializers.ModelSerializer):

    name = serializers.SerializerMethodField()

    class Meta:
        model = cont.Facility

    def get_name(self,obj):
        return ''.join(word.capitalize() for word in obj.name.split())

class FacilityViewSet(viewsets.ModelViewSet):

    queryset = cont.Facility.objects.all()
    serializer_class = FacilitySerializer
