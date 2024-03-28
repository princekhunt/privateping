from .models import UserProfile
from .models import Friends

def getFriendsList(id):
    try:
        user = UserProfile.objects.get(id=id)
        friends = Friends.objects.filter(user=user)
        friend_list = []
        for i in friends:
            friend_list.append(i)
        return friend_list
    except:
        return []


def getUserId(username):
    use = UserProfile.objects.get(username=username)
    id = use.id
    return id
