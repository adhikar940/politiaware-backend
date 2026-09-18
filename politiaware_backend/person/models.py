from django.db import models
from state.models import State
from district.models import Districts
from city.models import City
import os
from .enums import CasteCategoryEnum, GenderEnum, ReligionEnum, enum_to_choices
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError
import subprocess
import tempfile
import shutil

def get_upload_path(instance, filename, filetype):
    class_name = instance.__class__.__name__.lower()
    name = instance.name.replace(" ", "_") if instance.name else "unknown"
    
    ext = os.path.splitext(filename)[1]
    
    if filetype == "father":
        final_filename = f"{name}_father{ext}"
    elif filetype == "spouse":
        final_filename = f"{name}_spouse{ext}"
    elif filetype == "voice":
        final_filename = f"{name}_voice{ext}"
    else:
        final_filename = f"{name}{ext}"
    
    return os.path.join("adhikar", "person", class_name, name, final_filename)

def upload_person_photo(instance, filename):
    return get_upload_path(instance, filename, "person")

def upload_father_photo(instance, filename):
    return get_upload_path(instance, filename, "father")

def upload_spouse_photo(instance, filename):
    return get_upload_path(instance, filename, "spouse")

def upload_voice_sample(instance, filename):
    return get_upload_path(instance, filename, "voice")


class person(models.Model):
    name = models.CharField(max_length=100, unique=True)
    dob = models.DateTimeField(null=True, blank=True)
    death_date = models.DateTimeField(null=True, blank=True)
    religion = models.CharField(max_length=100, choices=enum_to_choices(ReligionEnum), null=True, blank=True)
    caste = models.CharField(max_length=100, null=True, blank=True)
    caste_category = models.CharField(max_length=10, choices=enum_to_choices(CasteCategoryEnum), null=True, blank=True)
    gender = models.CharField(max_length=10, choices=enum_to_choices(GenderEnum), default=GenderEnum.MALE.value, null=True, blank=True)
    fathers_Name = models.CharField(max_length=100, default='', null=True, blank=True)
    Spouse_Name = models.CharField(max_length=100, default='', null=True, blank=True)
    Highest_Education = models.CharField(max_length=100, default='', null=True, blank=True)
    University = models.CharField(max_length=100, default='', null=True, blank=True)
    presentaddress = models.TextField(max_length=600, default='', null=True, blank=True)
    premanentaddress = models.TextField(max_length=600, default='', null=True, blank=True)
    Email_address = models.EmailField(max_length=100, default='', null=True, blank=True)
    Mobile = models.CharField(max_length=20, default='', null=True, blank=True)
    children = models.CharField(max_length=100, null=True, blank=True)    
    birth_city = models.ForeignKey(City, related_name="%(app_label)s_%(class)s_birth_city", on_delete=models.SET_NULL, null=True, blank=True)
    extra_info = models.TextField(null=True, blank=True)
    person_photo = models.ImageField(upload_to=upload_person_photo, null=True, blank=True)
    fathers_image = models.ImageField(upload_to=upload_father_photo, null=True, blank=True)
    spouse_image = models.ImageField(upload_to=upload_spouse_photo, null=True, blank=True)
    voice_sample = models.FileField(upload_to=upload_voice_sample, null=True, blank=True)
   
    class Meta:
        abstract = True

    def _ensure_ffmpeg_exists(self):
        if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
            raise ValidationError("ffmpeg/ffprobe not found on system. Required for audio processing.")

    def _ffprobe_duration(self, path):
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            path
        ]
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        return float(out.strip())

    def save(self, *args, **kwargs):
        # If voice_sample provided, ensure ffmpeg present, probe duration, convert to WAV PCM 16kHz mono,
        # and trim to 60s if longer (print a message instead of raising).
        if self.voice_sample and getattr(self.voice_sample, "file", None):
            self._ensure_ffmpeg_exists()

            tmp_in = tempfile.NamedTemporaryFile(delete=False)
            tmp_out = None
            try:
                uploaded = self.voice_sample.file
                uploaded.seek(0)
                tmp_in.write(uploaded.read())
                tmp_in.flush()
                tmp_in.close()

                # probe duration
                try:
                    duration = self._ffprobe_duration(tmp_in.name)
                except subprocess.CalledProcessError as e:
                    raise ValidationError(f"Could not determine audio duration: {e}")

                # Prepare ffmpeg command:
                # - always resample/convert to WAV PCM s16 16kHz mono
                # - if duration > 60, add -t 60 to trim
                tmp_out = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
                tmp_out.close()

                ffmpeg_cmd = [
                    "ffmpeg", "-y", "-i", tmp_in.name,
                ]
                if duration > 60.0 + 1e-6:
                    ffmpeg_cmd += ["-t", "60"]
                ffmpeg_cmd += [
                    "-ar", "16000", "-ac", "1", "-sample_fmt", "s16",
                    "-loglevel", "error",
                    tmp_out.name
                ]

                subprocess.check_call(ffmpeg_cmd, stderr=subprocess.STDOUT)

                if duration > 60.0 + 1e-6:
                    # inform that trimming happened
                    print("Voice sample trimmed to 60 sec")

                # read converted file and save into FileField (avoid recursion/save inside save by save=False)
                with open(tmp_out.name, "rb") as f:
                    data = f.read()

                original_name = getattr(self.voice_sample, "name", "voice_sample")
                base, _ = os.path.splitext(os.path.basename(original_name))
                new_filename = f"{base}.wav"

                self.voice_sample.save(new_filename, ContentFile(data), save=False)
            finally:
                # cleanup temp files
                try:
                    os.unlink(tmp_in.name)
                except Exception:
                    pass
                if tmp_out:
                    try:
                        os.unlink(tmp_out.name)
                    except Exception:
                        pass

        super().save(*args, **kwargs)
    
   
class ruling_period(models.Model):
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
