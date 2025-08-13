from django.db import models
from django.conf import settings
from django.db.models import Sum

class Store(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="stores")
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    sheet_webhook = models.CharField(max_length=255,null=True)
    site = models.CharField(max_length=255,null=True)
    FB_PIXEL = models.TextField(null=True)
    FB_PAGE = models.CharField(max_length=255,null=True)
    INSTA_PAGE = models.CharField(max_length=255,null=True)
    INSTA_PAGE = models.CharField(max_length=255,null=True)
    PHONE_NUMBER = models.CharField(max_length=255,null=True)
    EMAIL = models.CharField(max_length=255,null=True)
    WHATSAPP = models.CharField(max_length=255,null=True)
    THEME_COLOR = models.CharField(max_length=255,null=True)
    LOGO = models.ImageField(upload_to='logo/',null=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class City(models.Model):
    CITY_CHOICES = (
        ("أدرار", "أدرار"),
        (" الشلف", " الشلف"),
        ("الأغواط", "الأغواط"),
        ("أم البواقي", "أم البواقي"),
        ("باتنة", "باتنة"),
        (" بجاية", " بجاية"),
        ("بسكرة", "بسكرة"),
        ("بشار", "بشار"),
        ("البليدة", "البليدة"),
        ("البويرة", "البويرة"),
        ("تمنراست", "تمنراست"),
        ("تبسة", "تبسة"),
        ("تلمسان", "تلمسان"),
        ("تيارت", "تيارت"),
        ("تيزي وزو", "تيزي وزو"),
        ("الجزائر", "الجزائر"),
        ("الجلفة", "الجلفة"),
        ("جيجل", "جيجل"),
        ("سطيف", "سطيف"),
        ("سعيدة", "سعيدة"),
        ("سكيكدة", "سكيكدة"),
        ("سيدي بلعباس", "سيدي بلعباس"),
        ("عنابة", "عنابة"),
        ("قالمة", "قالمة"),
        ("قسنطينة", "قسنطينة"),
        ("المدية", "المدية"),
        ("مستغانم", "مستغانم"),
        ("المسيلة", "المسيلة"),
        ("معسكر", "معسكر"),
        ("ورقلة", "ورقلة"),
        ("وهران", "وهران"),
        ("البيض", "البيض"),
        ("إليزي", "إليزي"),
        ("برج بوعريريج", "برج بوعريريج"),
        ("بومرداس", "بومرداس"),
        ("الطارف", "الطارف"),
        ("تندوف", "تندوف"),
        ("تيسمسيلت", "تيسمسيلت"),
        ("الوادي", "الوادي"),
        ("خنشلة", "خنشلة"),
        ("سوق أهراس", "سوق أهراس"),
        ("تيبازة", "تيبازة"),
        ("ميلة", "ميلة"),
        ("عين الدفلة", "عين الدفلة"),
        ("النعامة", "النعامة"),
        ("عين تيموشنت", "عين تيموشنت"),
        ("غرداية", "غرداية"),
        ("غليزان", "غليزان"),
        ("تيميمون", "تيميمون"),
        ("برج باجي مختار", "برج باجي مختار"),
        ("أولاد جلال", "أولاد جلال"),
        ("بني عباس", "بني عباس"),
        ("عين صالح", "عين صالح"),
        ("عين قزام", "عين قزام"),
        ("تقرت", "تقرت"),
        ("جانت", "جانت"),
        ("المغير", "المغير"),
        ("المنيعة", "المنيعة"),

    )
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="cities")
    name = models.CharField(max_length=255, unique=True, choices=CITY_CHOICES,)
    delivery_cost = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name
