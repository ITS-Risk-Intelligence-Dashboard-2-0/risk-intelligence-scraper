# Defines how Django ORM objects are converted to and from JSON (serialization/deserialization) for the Django REST Framework API

from rest_framework import serializers
from django_celery_beat.models import PeriodicTask, CrontabSchedule, IntervalSchedule
import json

class CrontabScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = CrontabSchedule
        exclude = ('id',)

class IntervalScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = IntervalSchedule
        exclude = ('id',)

class PeriodicTaskSerializer(serializers.ModelSerializer):
    crontab = CrontabScheduleSerializer(required=False, allow_null=True)
    interval = IntervalScheduleSerializer(required=False, allow_null=True)

    args = serializers.CharField(required=False, allow_blank=True, default="[]")
    kwargs = serializers.CharField(required=False, allow_blank=True, default="{}")

    class Meta:
        model = PeriodicTask
        fields = (
            'id', 'name', 'task', 'enabled', 'args', 'kwargs', 'expires',
            'one_off', 'start_time', 'priority', 'description',
            'crontab', 'interval'
        )
        read_only_fields = ('id', 'last_run_at', 'total_run_count', 'date_changed')

    def to_internal_value(self, data):
        if 'args' in data and isinstance(data['args'], str):
            try:
                data['args'] = json.loads(data['args'])
            except json.JSONDecodeError:
                raise serializers.ValidationError({'args': 'Must be a valid JSON array string.'})
        if 'kwargs' in data and isinstance(data['kwargs'], str):
            try:
                data['kwargs'] = json.loads(data['kwargs'])
            except json.JSONDecodeError:
                raise serializers.ValidationError({'kwargs': 'Must be a valid JSON object string.'})
        return super().to_internal_value(data)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if ret.get('args') is not None:
            ret['args'] = json.dumps(ret['args'])
        if ret.get('kwargs') is not None:
            ret['kwargs'] = json.dumps(ret['kwargs'])
        return ret

    def create(self, validated_data):
        crontab_data = validated_data.pop('crontab', None)
        interval_data = validated_data.pop('interval', None)

        if not crontab_data and not interval_data:
            raise serializers.ValidationError("Either crontab or interval schedule must be provided.")
        if crontab_data and interval_data:
            raise serializers.ValidationError("Only one schedule type (crontab or interval) can be provided.")

        schedule_instance = None
        if crontab_data:
            schedule_instance = CrontabSchedule.objects.create(**crontab_data)
            validated_data['crontab'] = schedule_instance
        elif interval_data:
            schedule_instance = IntervalSchedule.objects.create(**interval_data)
            validated_data['interval'] = schedule_instance

        periodic_task = PeriodicTask.objects.create(**validated_data)
        return periodic_task

    def update(self, instance, validated_data):
        crontab_data = validated_data.pop('crontab', None)
        interval_data = validated_data.pop('interval', None)

        if crontab_data:
            if instance.crontab:
                for attr, value in crontab_data.items():
                    setattr(instance.crontab, attr, value)
                instance.crontab.save()
            else:
                if instance.interval:
                    instance.interval.delete()
                instance.crontab = CrontabSchedule.objects.create(**crontab_data)
        elif interval_data:
            if instance.interval:
                for attr, value in interval_data.items():
                    setattr(instance.interval, attr, value)
                instance.interval.save()
            else:
                if instance.crontab:
                    instance.crontab.delete()
                instance.interval = IntervalSchedule.objects.create(**interval_data)
        else:
            if instance.crontab:
                instance.crontab.delete()
                instance.crontab = None
            if instance.interval:
                instance.interval.delete()
                instance.interval = None

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance