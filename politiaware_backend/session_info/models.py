from django.db import models
from django.core.exceptions import ValidationError

class SessionDetails(models.Model):
    SEASON_CHOICES = [
        ("monsoon", "monsoon"),
        ("winter", "winter"),
        ("budget", "budget"),
    ]

    HOUSE_CHOICES = [
        ("loksabha", "loksabha"),
        ("rajyasabha", "rajyasabha"),
        ("both", "both")
    ]
    season = models.CharField(max_length=10, choices=SEASON_CHOICES)
    house = models.CharField(max_length=12, choices=HOUSE_CHOICES)
    year = models.PositiveSmallIntegerField()
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["season", "house", "year"],
                name="unique_session_season_house_year"
            )
        ]

class SessionPhase(models.Model):
    session = models.ForeignKey(SessionDetails, related_name="phases", on_delete=models.CASCADE)
    number = models.PositiveSmallIntegerField()
    start_date = models.DateField()
    end_date = models.DateField()   

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["session", "number"],
                name="unique_phase_number_per_session"
            )
        ]

    def clean(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError("start_date must be on or before end_date")


