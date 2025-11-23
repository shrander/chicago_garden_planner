"""
Tests for the garden notification system.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from datetime import date, timedelta

from gardens.models import Garden, Plant, PlantInstance
from gardens.notifications import calculate_garden_notifications

User = get_user_model()


class NotificationCalculatorTest(TestCase):
    """Test the notification calculator functionality."""

    def setUp(self):
        """Create test user, garden, and plants."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        self.garden = Garden.objects.create(
            name='Test Garden',
            owner=self.user,
            width=4,
            height=4
        )

        self.tomato = Plant.objects.create(
            name='Tomato',
            days_to_harvest=70,
            spacing_inches=24,
            is_default=True
        )

    def test_harvest_ready_notification(self):
        """Test notification for plant ready to harvest today."""
        today = date.today()
        planted_date = today - timedelta(days=70)

        instance = PlantInstance.objects.create(
            garden=self.garden,
            plant=self.tomato,
            row=0,
            col=0,
            planted_date=planted_date
        )

        notifications = calculate_garden_notifications(self.garden, self.user)

        self.assertEqual(len(notifications['harvest_ready']), 1)
        self.assertEqual(notifications['harvest_ready'][0]['plant_name'], 'Tomato')
        self.assertEqual(notifications['harvest_ready'][0]['row'], 0)
        self.assertEqual(notifications['harvest_ready'][0]['col'], 0)

    def test_harvest_soon_notification(self):
        """Test notification for plant approaching harvest."""
        today = date.today()
        planted_date = today - timedelta(days=65)  # 5 days until harvest

        instance = PlantInstance.objects.create(
            garden=self.garden,
            plant=self.tomato,
            row=1,
            col=1,
            planted_date=planted_date
        )

        notifications = calculate_garden_notifications(self.garden, self.user)

        self.assertEqual(len(notifications['harvest_soon']), 1)
        self.assertEqual(notifications['harvest_soon'][0]['plant_name'], 'Tomato')
        self.assertEqual(notifications['harvest_soon'][0]['days_until'], 5)

    def test_harvest_overdue_notification(self):
        """Test notification for overdue harvest."""
        today = date.today()
        planted_date = today - timedelta(days=75)  # 5 days overdue

        instance = PlantInstance.objects.create(
            garden=self.garden,
            plant=self.tomato,
            row=2,
            col=2,
            planted_date=planted_date
        )

        notifications = calculate_garden_notifications(self.garden, self.user)

        self.assertEqual(len(notifications['harvest_overdue']), 1)
        self.assertEqual(notifications['harvest_overdue'][0]['plant_name'], 'Tomato')
        self.assertEqual(notifications['harvest_overdue'][0]['days_overdue'], 5)

    def test_no_notification_for_harvested_plant(self):
        """Test that harvested plants don't generate notifications."""
        today = date.today()
        planted_date = today - timedelta(days=70)

        instance = PlantInstance.objects.create(
            garden=self.garden,
            plant=self.tomato,
            row=3,
            col=3,
            planted_date=planted_date,
            actual_harvest_date=today  # Already harvested
        )

        notifications = calculate_garden_notifications(self.garden, self.user)

        self.assertEqual(len(notifications['harvest_ready']), 0)
        self.assertEqual(len(notifications['harvest_soon']), 0)
        self.assertEqual(len(notifications['harvest_overdue']), 0)

    def test_no_notification_without_planted_date(self):
        """Test that plants without planted dates don't generate notifications."""
        instance = PlantInstance.objects.create(
            garden=self.garden,
            plant=self.tomato,
            row=0,
            col=1,
            # No planted_date
        )

        notifications = calculate_garden_notifications(self.garden, self.user)

        self.assertEqual(len(notifications['harvest_ready']), 0)
        self.assertEqual(len(notifications['harvest_soon']), 0)
        self.assertEqual(len(notifications['harvest_overdue']), 0)

    def test_multiple_notifications(self):
        """Test multiple plants with different notification states."""
        today = date.today()

        # One ready
        PlantInstance.objects.create(
            garden=self.garden,
            plant=self.tomato,
            row=0,
            col=0,
            planted_date=today - timedelta(days=70)
        )

        # One soon
        PlantInstance.objects.create(
            garden=self.garden,
            plant=self.tomato,
            row=1,
            col=1,
            planted_date=today - timedelta(days=65)
        )

        # One overdue
        PlantInstance.objects.create(
            garden=self.garden,
            plant=self.tomato,
            row=2,
            col=2,
            planted_date=today - timedelta(days=75)
        )

        notifications = calculate_garden_notifications(self.garden, self.user)

        self.assertEqual(len(notifications['harvest_ready']), 1)
        self.assertEqual(len(notifications['harvest_soon']), 1)
        self.assertEqual(len(notifications['harvest_overdue']), 1)
