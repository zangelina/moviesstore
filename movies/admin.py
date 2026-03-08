from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from django.db.models import Count
from .models import Movie, Review, Rating


class MovieAdmin(admin.ModelAdmin):
    ordering = ['name']
    search_fields = ['name']

class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'movie', 'user', 'date')
    ordering = ['-date']
    change_list_template = 'admin/movies/review/change_list.html'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'top-commenter/',
                self.admin_site.admin_view(self.top_commenter_view),
                name = 'movies_review_top_commenter',
            )
        ]
        return custom_urls + urls
    
    def top_commenter_view(self,request):
        review_counts = (
            Review.objects
            .values('user__username')
            .annotate(total_comments = Count('id'))
            .order_by('-total_comments', 'user__username')
        )
        top_commenter = review_counts.first()

        context = dict(
            self.admin_site.each_context(request),
            title = 'Top Commenter',
            top_commenter = top_commenter,
            review_counts = review_counts,
        )

        return render(request, 'admin/movies/review/top_commenter.html', context)

admin.site.register(Movie, MovieAdmin)
admin.site.register(Rating)
admin.site.register(Review, ReviewAdmin)