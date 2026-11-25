from rest_framework.routers import DefaultRouter

from .views import AttemptViewSet, StudentViewSet, TestViewSet

router = DefaultRouter()
router.register("tests", TestViewSet, basename="test")
router.register("attempts", AttemptViewSet, basename="attempt")
router.register("students", StudentViewSet, basename="student")

urlpatterns = router.urls
