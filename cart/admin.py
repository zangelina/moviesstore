from urllib import request

from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from django.db.models import Sum, Count, Value
from django.db.models.functions import Coalesce
from django.contrib.auth.models import User
from .models import Order, Item

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user')
    change_list_template = 'admin/cart/order/change_list.html'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'top-purchaser/',
                self.admin_site.admin_view(self.top_purchaser_view),
                name = 'cart_order_top_purchaser',
            )
        ]
        return custom_urls + urls
    
    
    def top_purchaser_view(self, request):
        top_user = (
            User.objects
            .annotate(total_movies=Coalesce(Sum('order__item__quantity'), Value(0)))
            .order_by('-total_movies')
            .first())
        
        ranked_users = (
            User.objects
            .annotate(total_movies=Coalesce(Sum('order__item__quantity'), Value(0)))
            .order_by('-total_movies', 'username')
        )
        ranked_by_order = (
            User.objects
            .annotate(total_orders=Coalesce(Count('order', distinct=True), Value(0)))
            .order_by('-total_orders', 'username')
        )
        purchase_items = []
        if top_user:
            purchase_items = (
                Item.objects
                .filter(order__user=top_user)
                .select_related('movie', 'order')
                .order_by('order__id', 'id')
            )
        context = {
            **self.admin_site.each_context(request),
            "top_user": top_user,
            "purchase_items": purchase_items,
            'ranked_users': ranked_users,
            'ranked_by_order': ranked_by_order,
            
    }
        return render(request, "accounts/admin_top_purchaser.html", context)
#     if top_user and top_user.total_movies > 0:
#         messages.info(request, f"Top Purchaser: {top_user.username} with {top_user.total_movies} movies purchased.")
#     else:
#         messages.info(request, "no purchases found.")
        
# show_top_purchaser.short_description = "Show Top Purchaser"


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'movie', 'quantity', 'order')
    
# class CustomUserAdmin(UserAdmin):
#     list_display = UserAdmin.list_display + ('total_movies_purchased',)
    
#     def get_queryset(self, request):
#         qs = super().get_queryset(request)
#         return qs.annotate(total_movies_bought = Coalesce(Sum('order__item__quantity'), 0))
        
#     def total_movies_purchased(self, obj):
#         return obj.total_movies_bought
    
#     total_movies_purchased.short_description = 'Total Movies Purchased'
#     total_movies_purchased.admin_order_field = 'total_movies_bought'
            

# admin.site.unregister(User)
# admin.site.register(User, CustomUserAdmin)