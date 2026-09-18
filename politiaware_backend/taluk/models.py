from django.db import models
from django.contrib.gis.db import models as geomodels
from django.db.models import JSONField
from district.models import DistrictForeign

# ==============================================================================
# Indian Sub-District Administrative System (Taluk / Tehsil / Mandal / CD Block)
# In India, the administrative level directly below the District (or Revenue Division)
# is designated differently across states:
# - Tehsil / Tahsil: North & Central India (UP, MP, RJ, HR, PB, HP, UK, CG, DL, JK, etc.)
# - Taluk / Taluka: South & West India (Karnataka, Maharashtra, Gujarat, Goa, TN, Kerala)
# - Mandal: Andhra Pradesh, Telangana (introduced in 1985 to replace taluks)
# - Community Development Block (CD Block): WB, Bihar, Jharkhand, Odisha
# - Sub-Division / Revenue Circle: Assam, Arunachal Pradesh, Northeast States
# - Anchal: Bihar (Revenue Circle)
#
# Standard National Identifiers:
# - LGD Code: Local Government Directory unique code (Ministry of Panchayati Raj)
# - Census 2011 Sub-District Code: Office of the Registrar General & Census Commissioner
# ==============================================================================

class Taluk(DistrictForeign):
    """
    Core Model representing a Sub-District administrative unit in India
    (Taluk, Tehsil, Mandal, CD Block, Revenue Circle, etc.)
    Inherits `state` and `district` foreign keys from `DistrictForeign`.
    """

    SUBDISTRICT_TYPE_CHOICES = [
        ('TALUK', 'Taluk'),
        ('TALUKA', 'Taluka'),
        ('TEHSIL', 'Tehsil / Tahsil'),
        ('MANDAL', 'Mandal'),
        ('CD_BLOCK', 'Community Development (CD) Block'),
        ('SUB_DIVISION', 'Sub-Division'),
        ('REVENUE_CIRCLE', 'Revenue Circle / Circle'),
        ('ANCHAL', 'Anchal'),
        ('OTHER', 'Other'),
    ]

    CATEGORY_CHOICES = [
        ('RURAL', 'Rural'),
        ('URBAN', 'Urban'),
        ('SEMI_URBAN', 'Semi-Urban'),
        ('TRIBAL', 'Tribal'),
        ('METROPOLITAN', 'Metropolitan'),
        ('COASTAL', 'Coastal'),
        ('HILLY', 'Hilly / Mountainous'),
    ]

    # --- Basic Identification & Nomenclature ---
    talukName = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Official English name (e.g. Anekal, Haveli, Varanasi, Gannavaram)"
    )
    local_name = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        help_text="Name in local / regional state script (e.g. ಆನೇಕಲ್, हवेली, గన్నవరం)"
    )
    subdistrict_type = models.CharField(
        max_length=30,
        choices=SUBDISTRICT_TYPE_CHOICES,
        default='TALUK',
        help_text="State-specific sub-district designation"
    )
    abbreviation = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        help_text="Short code / official abbreviation"
    )

    # --- Administrative Hierarchy & Headquarters ---
    revenue_division = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Sub-division or Revenue Division within the district"
    )
    headquarters = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Administrative headquarters town or village"
    )


    # --- Governance & Regional Characteristics ---
    category = models.CharField(
        max_length=30,
        choices=CATEGORY_CHOICES,
        default='RURAL'
    )
   

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['district', 'talukName', 'subdistrict_type'],
                name='unique_subdistrict_per_district'
            )
        ]
        indexes = [
            models.Index(fields=['subdistrict_type']),
            models.Index(fields=['talukName']),
        ]
        verbose_name = 'Taluk / Sub-District'
        verbose_name_plural = 'Taluks / Sub-Districts'
        ordering = ['district', 'talukName']



# ==============================================================================
# Model Aliases for multi-state naming consistency
# ==============================================================================
SubDistrict = Taluk
Tehsil = Taluk
Taluka = Taluk
Mandal = Taluk
Block = Taluk
CDBlock = Taluk


class TalukMap(geomodels.Model):
    """
    Used for representing Taluk / Sub-District boundary maps.
    """
    feature_properties = JSONField(blank=True, null=True)
    boundary = geomodels.MultiPolygonField()
    taluk = models.ForeignKey(Taluk, on_delete=models.CASCADE, null=True, related_name='maps')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['taluk'],
                name='unique_boundary_per_taluk'
            )
        ]
        verbose_name = 'Taluk Map'
        verbose_name_plural = 'Taluk Maps'

    def __str__(self):
        return f"Map of {self.taluk}" if self.taluk else "TalukMap"


SubDistrictMap = TalukMap
