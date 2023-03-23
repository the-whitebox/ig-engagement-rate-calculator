import requests
from rest_framework.response import Response
from rest_framework.decorators import api_view


@api_view(['GET'])
def user_info(request, username):

    # Get user information
    user_info_url = "https://instagram28.p.rapidapi.com/user_info"
    user_info_querystring = {"user_name": username}
    user_info_headers = {
        "X-RapidAPI-Key": "931d8a0ceemsh125bfc3153f6387p1ace1fjsn6f8dfdcf9e37",
        "X-RapidAPI-Host": "instagram28.p.rapidapi.com"
    }
    user_info_response = requests.get(user_info_url, headers=user_info_headers, params=user_info_querystring).json()

    user_id=user_info_response['data']['user']["pk_id"]
    print(user_id)
    # Get media information
    media_url = "https://instagram28.p.rapidapi.com/medias"
    media_params = {"user_id": user_info_response['data']['user']["pk_id"], "batch_size": 20}
    media_response = requests.get(media_url, headers=user_info_headers, params=media_params).json()

    # Parse user information
    user_data = {
        "username": user_info_response['data']['user']["username"],
        "profile_picture": user_info_response['data']['user']["profile_pic_url_hd"],
        "follower_count": user_info_response['data']['user']["edge_followed_by"]['count'],
        "following_count": user_info_response['data']['user']["edge_follow"]['count'],
        "post_count": user_info_response['data']['user']["edge_owner_to_timeline_media"]["count"]

    }


    # Parse media information
    posts = media_response['data']['user']["edge_owner_to_timeline_media"]["edges"]
    avg_likes = sum([post["node"]["edge_media_preview_like"]["count"] for post in posts]) / len(posts)
    avg_comments = sum([post["node"]["edge_media_to_comment"]["count"] for post in posts]) / len(posts)
    avg_engagement_rate = round(((avg_likes + avg_comments) / user_data["follower_count"]) * 100,2)

    # Get recent 8 posts
    recent_posts = []
    for post in posts[:8]:
        post_data = {
            "media_url": post["node"]["display_url"],
            "likes": post["node"]["edge_media_preview_like"]["count"],
            "comments": post["node"]["edge_media_to_comment"]["count"],
            "engagement_rate": (post["node"]["edge_media_preview_like"]["count"] +
                                post["node"]["edge_media_to_comment"]["count"]) / user_data["follower_count"] * 100
        }
        if post['node']["is_video"]:
            post_data["views"] = post['node']["video_view_count"]
        recent_posts.append(post_data)

    # Return the data as a JSON response
    data = {
        "user_data": user_data,

               "average_likes": avg_likes,
               "average_comments": avg_comments,
               "average_engagement_rate": avg_engagement_rate,
                "recent_posts": recent_posts
    }
    return Response(data)
