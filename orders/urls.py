from django.urls import path
from . import views as orders

app_name = "orders"

urlpatterns = [
    path("", orders.OrderListView.as_view(), name="orders_list"),
    
    
    path("<int:order_id>/details/", orders.order_detail_partial, name="order_detail_partial"),
    path("<int:order_id>/update/", orders.update_order, name="update_order"),
    path("<int:order_id>/order_client_info/", orders.order_client_info, name="order_client_info"),
    path("<int:order_id>/edit_client_info/", orders.edit_client_info, name="edit_client_info"),
    
    path("order_item/update/<int:item_id>/", orders.update_order_item, name="update_order_item"), 
    path("order_item/delete/<int:item_id>/", orders.delete_order_item, name="delete_order_item"),

    path("order/archive/<int:order_id>/", orders.archive_order, name="archive_order"),
    path("order/move_to_in_progress/<int:order_id>/", orders.move_to_in_progress, name="move_to_in_progress"),
    path("order/send_to_sheet/<int:order_id>/", orders.send_to_sheet, name="send_to_sheet"),

    path("status/", orders.order_status, name="order_status"),
]