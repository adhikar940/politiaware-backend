from django.db import models
from django.forms import ValidationError
from politiaware_backend.loksabha.models import LokSabhaMP
from politiaware_backend.session_info.models import SessionPhase

class VideoLoksabha(models.Model):
    session = models.ForeignKey(SessionPhase, on_delete=models.SET_NULL, null=True)
    date = models.DateField()
    youtube_url = models.URLField() 

class SpeakerSegment(models.Model):
    video = models.ForeignKey(VideoLoksabha, related_name='segments', on_delete=models.CASCADE)
    mp = models.ForeignKey(LokSabhaMP, on_delete=models.SET_NULL, null=True, blank=True)
    other_mp = models.CharField(max_length=255, null=True, blank=True,
                                help_text="Use when the MP is not in LokSabhaMP table")
    start_time_sec = models.PositiveIntegerField() # video time in seconds
    end_time_sec = models.PositiveIntegerField()
    start_time = models.TimeField(null=True, blank=True, help_text="Only time (HH:MM:SS)") # that date's start time
    end_time = models.TimeField(null=True, blank=True, help_text="Only time (HH:MM:SS)")

    def clean(self):
        if not self.mp and not (self.other_mp and self.other_mp.strip()):
            raise ValidationError("Either 'mp' (ForeignKey) or 'other_mp' (text) must be provided.")
        if self.start_time_sec >= self.end_time_sec:
            raise ValidationError("start_time_sec must be less than end_time_sec")



