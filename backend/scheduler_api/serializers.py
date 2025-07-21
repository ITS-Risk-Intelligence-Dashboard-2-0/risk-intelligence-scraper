from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from django_celery_beat.models import PeriodicTask, IntervalSchedule, CrontabSchedule

class IntervalScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = IntervalSchedule
        # Define fields to prevent accidentally creating duplicates with different timezones
        fields = ('every', 'period')

        validators = [
            UniqueTogetherValidator(
                queryset=IntervalSchedule.objects.all(),
                fields=['every', 'period']
            )
        ]

class CrontabScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = CrontabSchedule
        # Timezone is important for crontabs
        fields = ('minute', 'hour', 'day_of_week', 'day_of_month', 'month_of_year', 'timezone')

    def to_representation(self, instance):
        """Convert timezone from ZoneInfo object to string for JSON serialization."""
        ret = super().to_representation(instance)
        if instance.timezone:
            ret['timezone'] = str(instance.timezone)
        return ret

class PeriodicTaskSerializer(serializers.ModelSerializer):
    # Make the nested serializers writable
    interval = IntervalScheduleSerializer(required=False, allow_null=True)
    crontab = CrontabScheduleSerializer(required=False, allow_null=True)

    class Meta:
        model = PeriodicTask
        # Explicitly list fields for clarity and security
        fields = ('id', 'name', 'task', 'interval', 'crontab', 'args', 'kwargs', 'enabled', 'last_run_at')
        # args and kwargs are correctly treated as string fields by default

    def validate(self, data):
        """Ensure either an interval or a crontab is set, but not both."""
        if self.partial: # Skip validation on partial updates (PATCH)
            return data
        if not data.get('interval') and not data.get('crontab'):
            raise serializers.ValidationError("A schedule is required. Please provide either an interval or a crontab.")
        if data.get('interval') and data.get('crontab'):
            raise serializers.ValidationError("Cannot define both an interval and a crontab schedule for the same task.")
        return data

    def create(self, validated_data):
        """Handle creation of task with a nested schedule."""
        interval_data = validated_data.pop('interval', None)
        crontab_data = validated_data.pop('crontab', None)
        
        if interval_data:
            # Use get_or_create to reuse existing schedules and prevent DB clutter
            interval, _ = IntervalSchedule.objects.get_or_create(**interval_data)
            validated_data['interval'] = interval
            
        if crontab_data:
            crontab, _ = CrontabSchedule.objects.get_or_create(**crontab_data)
            validated_data['crontab'] = crontab

        return PeriodicTask.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """
        Handle updates for a task, including its nested schedule.
        This method is now robust for all update scenarios.
        """
        # Pop the schedule data out of the validated_data dictionary.
        # This prevents the super().update() method from trying to process it.
        interval_data = validated_data.pop('interval', None)
        crontab_data = validated_data.pop('crontab', None)

        # Let the parent class handle the update of all simple fields 
        # like name, task, enabled, kwargs, etc.
        instance = super().update(instance, validated_data)

        # Now, handle the schedule logic manually.
        if interval_data:
            # If interval data is provided, find or create that schedule
            # and assign it to the task.
            new_interval, _ = IntervalSchedule.objects.get_or_create(**interval_data)
            instance.interval = new_interval
            instance.crontab = None  # Ensure the other schedule type is cleared
        elif crontab_data:
            # Same logic for crontab
            new_crontab, _ = CrontabSchedule.objects.get_or_create(**crontab_data)
            instance.crontab = new_crontab
            instance.interval = None # Ensure the other schedule type is cleared
        
        # Save the instance to commit the schedule changes.
        instance.save()
        return instance