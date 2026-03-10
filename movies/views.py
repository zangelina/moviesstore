from django.shortcuts import render, redirect, get_object_or_404
from .models import Movie, Review, Rating
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Avg, Sum, Count
from cart.models import Item
import json

def index(request):
    search_term = request.GET.get('search')
    if search_term:
        movies = Movie.objects.filter(name__icontains=search_term)
    else:
        movies = Movie.objects.all()
    template_data = {}
    template_data['title'] = 'Movies'
    template_data['movies'] = movies
    return render(request, 'movies/index.html',
                  {'template_data': template_data})

def show(request, id):
    movie = Movie.objects.get(id=id)
    movie.view_count += 1
    movie.save()
    reviews = Review.objects.filter(movie=movie)
    rating_summary = Rating.objects.filter(movie=movie).aggregate(avg_rating=Avg('value'))
    user_rating = None
    if request.user.is_authenticated:
        user_rating = Rating.objects.filter(movie=movie, user=request.user).first()
    template_data = {}
    template_data['title'] = movie.name
    template_data['movie'] = movie
    template_data['reviews'] = reviews
    template_data['average_rating'] = rating_summary['avg_rating']
    template_data['ratings_count'] = Rating.objects.filter(movie=movie).count()
    template_data['user_rating'] = user_rating
    template_data['rating_options'] = [1, 2, 3, 4, 5]
    return render(request, 'movies/show.html',
                  {'template_data': template_data})

@login_required
def create_review(request, id):
    if request.method == 'POST' and request.POST['comment'] != '':
        movie = Movie.objects.get(id=id)
        review = Review()
        review.comment = request.POST['comment']
        review.movie = movie
        review.user = request.user
        review.save()
        return redirect('movies.show', id=id)
    else:
        return redirect('movies.show', id=id)

@login_required
def edit_review(request, id, review_id):
    review = get_object_or_404(Review, id=review_id)
    if request.user != review.user:
        return redirect('movies.show', id=id)
    if request.method == 'GET':
        template_data = {}
        template_data['title'] = 'Edit Review'
        template_data['review'] = review
        return render(request, 'movies/edit_review.html', {'template_data': template_data})
    elif request.method == 'POST' and request.POST['comment'] != '':
        review = Review.objects.get(id=review_id)
        review.comment = request.POST['comment']
        review.save()
        return redirect('movies.show', id=id)
    else:
        return redirect('movies.show', id=id)

@login_required
def delete_review(request, id, review_id):
    review = get_object_or_404(Review, id=review_id,
        user=request.user)
    review.delete()
    return redirect('movies.show', id=id)

def report_review(request, id, review_id):
    review = get_object_or_404(Review, id=review_id)
    if request.method == "POST":
        review.delete()
        return redirect('movies.show', id=id)
    if request.method == 'GET':
        template_data = {}
        template_data['title'] = 'Report Review'
        template_data['review'] = review
        return render(request, 'movies/report_review.html', {'template_data': template_data})

@login_required
def create_rating(request, id):
    movie = Movie.objects.get(id=id)
    if request.method == 'POST':
        rating_value = request.POST.get('rating')
        valid_values = {'1', '2', '3', '4', '5'}
        if rating_value in valid_values:
            Rating.objects.update_or_create(
                movie=movie,
                user=request.user,
                defaults={'value': int(rating_value)}
            )
    return redirect('movies.show', id=id)

def popularity_map(request):
    REGION_COORDS = {
        'north_america': [54.5260, -105.2551],
        'south_america': [-8.7832, -55.4915],
        'europe': [54.5260, 15.2551],
        'africa': [-8.7832, 34.5085],
        'asia': [34.0479, 100.6197],
        'oceania': [-22.7359, 140.0188],
    }
    regions = ['north_america', 'south_america', 'europe', 'africa', 'asia', 'oceania']
    map_data = []
    for region in regions:
        top_movies = list(
            Item.objects
            .filter(order__region=region)
            .values('movie__name', 'movie__view_count')
            .annotate(total=Sum('quantity'))
            .order_by('-total')[:3]
        )
        map_data.append({'region': region.replace('_', ' ').title(), 'coords': REGION_COORDS[region], 'movies': list(top_movies),})
    template_data = {}
    template_data['title'] = 'Local Popularity Map'
    template_data['map_data'] = json.dumps(map_data)
    return render(request, 'movies/popularity_map.html', {'template_data': template_data})

@staff_member_required
def admin_stats(request):
    most_purchased = Item.objects.values('movie__name').annotate(
        total_purchased=Sum('quantity')
    ).order_by('-total_purchased').first()

    most_reviewed = Review.objects.values('movie__name').annotate(
        total_reviews=Count('id')
    ).order_by('-total_reviews').first()

    template_data = {}
    template_data['title'] = 'Admin Stats'
    template_data['most_purchased'] = most_purchased
    template_data['most_reviewed'] = most_reviewed
    return render(request, 'movies/admin_stats.html', {'template_data': template_data})
