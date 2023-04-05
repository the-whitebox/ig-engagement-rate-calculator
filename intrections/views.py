import requests
from django.utils import timezone
from django.contrib.auth import authenticate
from datetime import timedelta
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework.authtoken.models import Token
from instagram_calculater.settings import env
from intrections.models import CustomUser
from rest_framework import status


def format_number(num):
    if num >= 1000000:
        return f"{num / 1000000:.1f}M"
    elif num >= 1000:
        return f"{num / 1000:.2f}k"
    else:
        return f"{num:.0f}"


@api_view(['GET'])
@permission_classes((IsAuthenticated, ))
def user_info(request, username):
    user = request.user

    user_request, created = CustomUser.objects.get_or_create(email=user)

    # Check timestamp of last request
    # if user_request.last_request_time is not None and \
    #         user_request.last_request_time + timedelta(minutes=1) > timezone.now():
    #     message = {
    #         "error": "You can only make one request per minute."
    #     }
    #     return Response(message, status=status.HTTP_202_ACCEPTED)
    if user_request.calculation_count >= 3:
        message = {
            "error": "You have exceeded the limit of 3 calculations."
        }
        return Response(message, status=status.HTTP_202_ACCEPTED)

    user_request.calculation_count += 1
    user_request.last_request_time = timezone.now() # Update timestamp
    user_request.save()





    # Get user information
    user_info_url = env('USER_INFO')
    user_info_querystring = {"user_name": username}
    user_info_headers = {
        "X-RapidAPI-Key": env('API_KEY'),
        "X-RapidAPI-Host": env('API_HOST')
    }
    try:
        user_info_response = requests.get(user_info_url, headers=user_info_headers, params=user_info_querystring).json()
    except KeyError:
        message = {
            "error": f"The user {username} is not available or invalid. Please add correct username."
        }
        return Response(message, status=status.HTTP_202_ACCEPTED)

    if user_info_response.get('data') is None:
        # Return a message if the data key is not present in the response
        message = {
            "error": f"The user {username} is not available or invalid. Please add correct username."
        }
        return Response(message, status=status.HTTP_202_ACCEPTED)

    if user_info_response['data']['user']["is_private"]:
        # Return a message if the user is private
        message = {
            "error": f"The user {username} is private and you cannot access the data."
        }
        return Response(message, status=status.HTTP_202_ACCEPTED)

    user_id = user_info_response['data']['user']["pk_id"]

    # Get media information
    media_url = env('MEDIA_API')
    media_params = {"user_id": user_info_response['data']['user']["pk_id"], "batch_size": 20}
    media_response = requests.get(media_url, headers=user_info_headers, params=media_params).json()

    # Parse user information
    user_data = {
        "username": user_info_response['data']['user']["username"],
        "profile_picture": user_info_response['data']['user']["profile_pic_url_hd"],
        "follower_count": format_number(user_info_response['data']['user']["edge_followed_by"]['count']),
        "following_count": format_number(user_info_response['data']['user']["edge_follow"]['count']),
        "post_count": format_number(user_info_response['data']['user']["edge_owner_to_timeline_media"]["count"])

    }

    # Parse media information
    posts = media_response['data']['user']["edge_owner_to_timeline_media"]["edges"]
    avg_likes =sum([post["node"]["edge_media_preview_like"]["count"] for post in posts]) / len(posts)
    avg_comments = sum([post["node"]["edge_media_to_comment"]["count"] for post in posts]) / len(posts)
    avg_engagement_rate = round(((avg_likes + avg_comments) / user_info_response['data']['user']["edge_followed_by"][
        'count']) * 100, 2)

    # Format average likes and comments
    avg_likes_formatted = format_number(avg_likes)
    avg_comments_formatted = format_number(avg_comments)

    # Get recent 8 posts
    recent_posts = []
    for post in posts[:8]:
        post_data = {
            "media_url": post["node"]["display_url"],
            "likes": format_number(post["node"]["edge_media_preview_like"]["count"]),
            "comments": format_number(post["node"]["edge_media_to_comment"]["count"]),
            "engagement_rate": round((post["node"]["edge_media_preview_like"]["count"] +
                                      post["node"]["edge_media_to_comment"]["count"]) /
                                     user_info_response['data']['user']["edge_followed_by"]['count'] * 100, 2),
            "post_link": f"https://www.instagram.com/p/{post['node']['shortcode']}/"
        }
        if post['node']["is_video"]:
            post_data["views"] = format_number(post['node']["video_view_count"])

        recent_posts.append(post_data)




    # Return the data as a JSON response
    data = {
        "user_data": user_data,

               "average_likes":format_number( avg_likes),
               "average_comments":format_number( avg_comments),
               "average_engagement_rate": avg_engagement_rate,
                "recent_posts": recent_posts
    }


    return Response(data, status=status.HTTP_200_OK)





class CustomUserLogin(APIView):
    def post(self, request):
        email = request.data.get('email')
        role = request.data.get('role')
        User = get_user_model()
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user = User.objects.create_user(email=email, role=role)
        try:
            token = Token.objects.get(user=user)
            return Response({'access_token': str(token.key)})
        except Token.DoesNotExist:
            token = Token.objects.create(user=user)
            return Response({'access_token': str(token.key)})

