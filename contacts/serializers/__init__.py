# Django Rest Framework Imports
from rest_framework import routers

# Local Imports
import messages
import participants
import misc
import visits

# Make Django Rest Framework Router
router = routers.DefaultRouter()
router.register(r'participant', participants.ParticipantViewSet,'participant')
router.register(r'message', messages.MessageViewSet,'message')
router.register(r'facilities', misc.FacilityViewSet)
router.register(r'visits', visits.VisitViewSet)
