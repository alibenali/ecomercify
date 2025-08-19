from django.db import models
from stores.models import Store, FacebookPixel
from products.models import Product
from django.db.models.signals import post_save
from django.dispatch import receiver

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
    name = models.CharField(max_length=255, choices=CITY_CHOICES,)
    delivery_cost = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ("store", "name")  # ✅ uniqueness per store

        # OR the modern way (recommended since Django 2.2+):
        constraints = [
            models.UniqueConstraint(fields=["store", "name"], name="unique_store_city")
        ]

    def __str__(self):
        return f"{self.store.name} - {self.name}"


class LandingPage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="landingpages")
    code = models.CharField(max_length=255, unique=True)
    # Override-able fields (optional, user can leave blank to fallback to Product)
    custom_name = models.CharField(max_length=255, null=True, blank=True)
    custom_description = models.TextField(null=True, blank=True)
    custom_image = models.ImageField(upload_to="landing_page_images/", null=True, blank=True)
    custom_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    custom_fake_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    # Extra fields only for landing pages
    pixels = models.ManyToManyField(FacebookPixel, blank=True, related_name="landing_pages")
    custom_webhook = models.CharField(max_length=255, null=True, blank=True)

    default_html = """<div class="container">
        <div class="success-icon">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 52 52">
            <path d="M26 0C11.664 0 0 11.664 0 26s11.664 26 26 26 26-11.664 26-26S40.336 0 26 0zm0 48C13.215 48 4 38.785 4 26S13.215 4 26 4s22 9.215 22 22-9.215 22-22 22zm-3.172-14.828l-7.778-7.778-2.828 2.828 10.606 10.606L39.778 17.778l-2.828-2.828-14.122 14.122z"></path>
        </svg>
        </div>
        <h1>تم الطلب بنجاح!</h1>
        <p>شكراً لشرائك من متجرنا. تم تأكيد طلبك وهو الآن في طريقه إليك!</p>
    </div>"""
    
    thank_you_html = models.TextField(null=True, blank=True, default=default_html)

    show_state = models.BooleanField(default=True)
    show_city = models.BooleanField(default=True)
    show_address = models.BooleanField(default=True)
    show_final_cost = models.BooleanField(default=True)


    def __str__(self):
        return f"Landing Page for {self.product.name}"

    # 👇 Helper methods to fallback to product values if override not set
    @property
    def name(self):
        return self.custom_name or self.product.name

    @property
    def description(self):
        return self.custom_description or self.product.description
    
    @property
    def image(self):
        return self.custom_image or self.product.image

    @property
    def price(self):
        return self.custom_price if self.custom_price is not None else self.product.price
    
    @property
    def fake_price(self):
        return self.custom_fake_price if self.custom_fake_price is not None else self.product.fake_price
    
    @property
    def webhook(self):
        return self.custom_webhook or self.product.store.sheet_webhook
    

    

# ✅ Create all cities automatically when a Store is created
@receiver(post_save, sender=Store)
def create_cities_for_store(sender, instance, created, **kwargs):
    if created:
        for city_name, _ in City.CITY_CHOICES:
            City.objects.get_or_create(store=instance, name=city_name, defaults={"delivery_cost": 0})

