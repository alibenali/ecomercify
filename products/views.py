from django.views.generic import ListView
from .models import Product, ProductVariant, VariantOption
from stores.models import Store  # Assuming user selects or owns store
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect

# Create your views here.
class ProductListView(ListView):
    model = Product
    template_name = "dashboard/products/products_list.html"
    context_object_name = "products"
    paginate_by = 10  # Adjust pagination as needed
    
    def get_queryset(self):
        return Product.objects.all().order_by("-created_at")
    

def add_product(request):
    if request.method == 'POST':
        # === Base Product Fields ===
        name = request.POST.get('name')
        sku = request.POST.get('SKU')
        price = request.POST.get('price')
        description = request.POST.get('description')
        stock_quantity = request.POST.get('stock_quantity') or 0
        image = request.FILES.get('image')
        
        # You may need to retrieve store from user/session
        store = Store.objects.first()  # Replace with actual logic

        if not all([name, sku, price]):
            messages.error(request, "Name, SKU, and price are required.")
            return redirect('add_product')

        # === Save Product ===
        product = Product.objects.create(
            store=store,
            name=name,
            SKU=sku,
            price=price,
            description=description,
            stock_quantity=stock_quantity,
            image=image
        )

        # === Save Variants ===
        variants_data = {}
        for key in request.POST:
            if key.startswith("variants["):
                parts = key.replace("variants[", "").replace("]", "").split("[")
                idx = int(parts[0])
                field = parts[1]
                if idx not in variants_data:
                    variants_data[idx] = {}
                variants_data[idx][field] = request.POST[key]

        # Add image files to the variant data
        for file_key in request.FILES:
            if file_key.startswith("variants["):
                parts = file_key.replace("variants[", "").replace("]", "").split("][")
                idx = int(parts[0])
                field = parts[1]
                if idx not in variants_data:
                    variants_data[idx] = {}
                variants_data[idx][field] = request.FILES[file_key]

        for idx, data in variants_data.items():
            variant = ProductVariant.objects.create(
                product=product,
                SKU=data.get('SKU'),
                price=data.get('price') or 0,
                stock_quantity=data.get('stock_quantity') or 0,
                image=data.get('image')
            )

            # === Save Options ===
            options_prefix = f"variants[{idx}][options][]"
            option_keys = [key for key in request.POST if key.startswith(f"variants[{idx}][options]")]
            names = request.POST.getlist(f"variants[{idx}][options][][name]")
            values = request.POST.getlist(f"variants[{idx}][options][][value]")
            for name, value in zip(names, values):
                if name and value:
                    VariantOption.objects.create(
                        variant=variant,
                        name=name,
                        value=value
                    )

        messages.success(request, "Product and variants added successfully.")
        return redirect('products:products_list')  # Or any view you like

    return render(request, 'dashboard/products/add_product.html')



def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, "dashboard/products/product_detail.html", {"product": product})

def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if request.method == "POST":
        # === 1. Update main product ===
        product.name = request.POST.get("name")
        product.SKU = request.POST.get("SKU")
        product.price = request.POST.get("price")
        product.stock_quantity = request.POST.get("stock_quantity")
        product.description = request.POST.get("description")

        if request.FILES.get("image"):
            product.image = request.FILES["image"]
        product.save()

        # === 2. Update existing variants ===
        variant_ids = request.POST.getlist("variant_ids[]")
        for idx, variant_id in enumerate(variant_ids):
            variant = ProductVariant.objects.get(pk=variant_id)
            variant.SKU = request.POST.getlist("variant_SKUs[]")[idx]
            variant.price = request.POST.getlist("variant_prices[]")[idx]
            variant.stock_quantity = request.POST.getlist("variant_stocks[]")[idx]
            if f"variant_images" in request.FILES:
                variant.image = request.FILES.getlist("variant_images")[idx]
            variant.save()

            # === Update options ===
            option_ids = request.POST.getlist(f"option_ids_{variant_id}[]")
            option_names = request.POST.getlist(f"option_names_{variant_id}[]")
            option_values = request.POST.getlist(f"option_values_{variant_id}[]")

            # Delete removed options (if any)
            existing_option_ids = [str(opt.id) for opt in variant.options.all()]
            to_delete = set(existing_option_ids) - set(option_ids)
            VariantOption.objects.filter(pk__in=to_delete).delete()

            # Update or create each option
            for i in range(len(option_names)):
                if i < len(option_ids) and option_ids[i]:
                    # Update existing option
                    option = VariantOption.objects.get(pk=option_ids[i])
                    option.name = option_names[i]
                    option.value = option_values[i]
                    option.save()
                else:
                    # New option added
                    VariantOption.objects.create(
                        variant=variant,
                        name=option_names[i],
                        value=option_values[i]
                    )

        # === 3. Handle newly added variants ===
        new_variants = []
        for key in request.POST:
            if key.startswith("new_variants"):
                new_variants.append(key.split("[")[1].split("]")[0])
        new_variants = sorted(set(new_variants), key=int)

        for index in new_variants:
            sku = request.POST.get(f"new_variants[{index}][SKU]")
            price = request.POST.get(f"new_variants[{index}][price]")
            stock_quantity = request.POST.get(f"new_variants[{index}][stock_quantity]")
            image = request.FILES.get(f"new_variants[{index}][image]")

            if not sku or not price:
                continue  # skip invalid variants

            new_variant = ProductVariant.objects.create(
                product=product,
                SKU=sku,
                price=price,
                stock_quantity=stock_quantity or 0,
                image=image if image else None,
            )

            # Handle new options
            option_names = request.POST.getlist(f"new_variants[{index}][options][][name]")
            option_values = request.POST.getlist(f"new_variants[{index}][options][][value]")
            for name, value in zip(option_names, option_values):
                if name.strip() and value.strip():
                    VariantOption.objects.create(
                        variant=new_variant,
                        name=name.strip(),
                        value=value.strip()
                    )

        return redirect("products:product_detail", pk=product.pk)

    return render(request, "dashboard/products/product_edit.html", {"product": product})

