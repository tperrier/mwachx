# Django Rest Framework Imports
from rest_framework import routers

# Local Imports
import messages
import participants
import misc

# Make Django Rest Framework Router
router = routers.DefaultRouter()
router.register(r'participant', participants.ParticipantViewSet,'participant')
router.register(r'message', messages.MessageViewSet,'message')
router.register(r'facility', misc.FacilityViewSet)
