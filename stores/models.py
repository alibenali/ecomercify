from django.db import models
from django.conf import settings

class Store(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="stores")
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    sheet_webhook = models.CharField(max_length=255,null=True, blank=True)
    site = models.CharField(max_length=255,null=True, blank=True)
    FB_PAGE = models.CharField(max_length=255,null=True, blank=True)
    INSTA_PAGE = models.CharField(max_length=255,null=True, blank=True)
    PHONE_NUMBER = models.CharField(max_length=255,null=True, blank=True)
    EMAIL = models.CharField(max_length=255,null=True, blank=True)
    WHATSAPP = models.CharField(max_length=255,null=True, blank=True)
    THEME_COLOR = models.CharField(max_length=255,null=True, blank=True)
    LOGO = models.ImageField(upload_to='logo/',null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def default_block_settings():
        return {"block_ref": True, "block_ip": True}

    block_settings = models.JSONField(default=default_block_settings)
    def __str__(self):
        return self.name



class FacebookPixel(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="pixels")
    pixel_code = models.TextField()  # full pixel script/code
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def firt_chars_pixel_code(self):
        return self.pixel_code[:20]
    def __str__(self):
        return f"{self.store.name} - Pixel {self.id}"