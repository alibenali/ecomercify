from django.db import models
from stores.models import Store, FacebookPixel
from products.models import Product
from django.db.models.signals import post_save
from django.dispatch import receiver


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

    default_html = """<div class="container" dir="rtl">
        <div class="success-icon" style="text-align:center"><strong><span style="color:#2ecc71"><span style="font-family:Verdana,Geneva,sans-serif"><span dir="rtl"><span style="font-size:26px">تم الطلب بنجاح!</span></span></span></span></strong></div>

        <p style="text-align:center"><span style="color:#ffffff"><span style="font-family:Verdana,Geneva,sans-serif"><span dir="rtl"><span style="font-size:26px"><span style="background-color:#27ae60">شكراً لشرائك من متجرنا. تم تأكيد طلبك وهو الآن في طريقه إليك!</span></span></span></span></span></p>
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
