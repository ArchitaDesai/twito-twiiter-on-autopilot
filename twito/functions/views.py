
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from .models import (
    TwitterApp,
    TasksList,

)


from .forms import (
    TwitterApp_Form,
    SearchLocation_Form,
    PerformTask_Form
)

from tweepy import(
    OAuthHandler,
	API,
	Cursor,
)


login_url = '/'


def index(request):
    return render(request, 'index.html')


@login_required(login_url=login_url)
def dashboard(request):

    if request.method == 'POST':

        form = TwitterApp_Form(request.POST)

        # log form details here

        if form.is_valid():

            _consumerKey = request.POST['ConsumerKey'].strip()
            _consumerToken = request.POST['ConsumerToken'].strip()
            _access_token = request.POST['access_token'].strip()
            _access_key = request.POST['access_key'].strip()

            try:
                auth = OAuthHandler(_consumerKey, _consumerToken)
                auth.get_authorization_url()

                auth.set_access_token(_access_token,_access_key)

                api = API(auth)
                twitterName = (api.me()).name

                # if consumer token and Access Tokens are valid then only would go further

                app = form.save(commit=False)
                app.user = request.user
                app.save()

                t = TasksList(user=request.user, AppName=app, TaskName="Application Created")
                t.save()

                return redirect('/dashboard/')

            except Exception as e:
                # log exception
                print(str(e))

                messages.warning(
                    request,
                    '''Error in Consumer Key/Token!
                    Please try again with correct Twitter App Credentials!''')

                return redirect('/dashboard/')
        else:
            print(form.errors)
            return redirect('/dashboard/')

    else:

        form = TwitterApp_Form()

        apps = TwitterApp.objects.filter(
            user=request.user).order_by('-created_at')

        return render(request, 'dashboard.html', {'apps': apps, 'form': form})


@login_required(login_url=login_url)
def appPage(request, app_id):


    if request.method == 'POST':

        form = SearchLocation_Form(request.POST)


        if form.is_valid():

            _keyword = request.POST['keyword']
            _lang = request.POST['lang']
            _latitude = request.POST['latitude']
            _longitude = request.POST['longitude']
            _radius = request.POST['radius']
            _radiusUnit = request.POST['radiusUnit']

            try:

                request.session['keyword'] = _keyword
                request.session['lang'] = _lang
                request.session['latitude'] = _latitude
                request.session['longitude'] = _longitude
                request.session['radius'] = _radius
                request.session['radiusUnit'] = _radiusUnit


                return redirect('/dashboard/' + app_id + '/search/')



            except Exception as e:

                print(e)
                return redirect('/dashboard/'+app_id+'/')
        else:
            print(form.errors)
            return redirect('/dashboard/'+app_id+'/')

    else:

        TwitoApp = get_object_or_404(TwitterApp, id=app_id, user=request.user)

        auth = OAuthHandler(TwitoApp.ConsumerKey, TwitoApp.ConsumerToken)
        auth.get_authorization_url()

        auth.set_access_token(TwitoApp.access_token, TwitoApp.access_key)

        api = API(auth)

        username = (api.me()).screen_name

######objects to pass to html
        #to get all followers or friends use cursor
        #trends = api.trends_available()
        followers = api.followers(username)  #returns user object
        #followers_ids = api.followers_ids(username)
        friends = api.friends(username)      #returns user object

        tweets = api.user_timeline()             #returns status object

        #lists =
        likes = api.favorites(username)          #returns status object

        #messages = api.direct_messages()
        tasks = TasksList.objects.filter(AppName=TwitoApp)      #returns TaskList objects as Queryset


        #request.session['followers_ids'] = followers_ids
        # request.session['friends_sname'] = friends_sname
        # request.session['tweets_ids'] = tweets_id
        # request.session['likes_ids'] = likes_ids


        return render(request, 'app.html', {'app': TwitoApp, 'followers':followers,
                                                  'friends':friends,'tweets':tweets,'likes':likes,
                                                  'tasks':tasks})






@login_required(login_url=login_url)
def searchLocationwise(request, app_id):

    app = get_object_or_404(TwitterApp, id=app_id, user=request.user)

    auth = OAuthHandler(app.ConsumerKey, app.ConsumerToken)
    auth.get_authorization_url()

    auth.set_access_token(app.access_token, app.access_key)

    api = API(auth)

    SearchId = {}  # ["userId":"MessageId"]

    total_search_result = 10
    perform_task_on_tweets = 10

    if request.method != 'POST':

        try:



            t = TasksList(user=request.user, AppName=app, TaskName="Search by User")
            t.save()


            arg_key = request.session.get('keyword')
            arg_lang = request.session.get('lang')
            arg_geo = str(request.session.get('latitude')) + "," +\
                  str(request.session.get('longitude')) + "," +\
                  (str(request.session.get('radius')))+\
                  (request.session.get('radiusUnit'))

            StatusObjects = []

            for StatusObject in Cursor(api.search,q=arg_key,lang=arg_lang,geocode=arg_geo).items(total_search_result):
                StatusObjects.append(StatusObject)

                if StatusObject.user.id_str not in SearchId.keys() and len(SearchId.keys()) < perform_task_on_tweets:

                    SearchId[StatusObject.user.id_str] = str(StatusObject.id_str)


            request.session['SearchId'] = SearchId


            return render(request, 'searchlocation.html', {'status': StatusObjects,'app':app})

        except Exception as e:

            print(e)
            return redirect('/dashboard/'+app_id+'/')

    else:

        try:

            form = PerformTask_Form(request.POST)

            username = api.me().screen_name

            _like = request.POST.get('likeTweets', None)
            _follow = request.POST.get('followUsers', None)
            _retweet = request.POST.get('retweetTweets', None)


            SearchId = request.session.get('SearchId')

            print("Search ..", SearchId.values())

            # friends_sname = request.session.get('friends_sname')
            # tweets_ids = request.session.get('tweets_ids')
            # likes_ids = request.session.get('likes_ids')

            # likes_ids = []
            # likes = api.favorites(username)
            #
            # for i in likes:
            #     likes_ids.append(i.id_str)
            #
            # print("favorites...",likes_ids)

            for i in SearchId.keys():
                #print(i)
                if _like:

                    # if SearchId[i] not in likes_ids:
                    #
                    #     print("like", SearchId[i], end=" - ")
                    #     print((api.create_favorite(SearchId[i])).id_str)  # create_favorite method returns status
                    #     likes_ids.append(SearchId[i])
                    #
                    # else:
                    #     print("already like", SearchId[i])
                    # print("favorites...", likes_ids)

                    try:
                        print("like", SearchId[i], end=" - ")
                        print((api.create_favorite(SearchId[i])).id_str)  # create_favorite method returns status

                    except Exception as e:
                        print("Already like")
                        pass

                if _follow:

                    # if i not in friends_ids:
                    #     print("follow", i, end=" - ")
                    #     print(api.create_friendship(i).screen_name)  #follow specific user
                    #     friends_ids.append(i)
                    # else:
                    #     print("already follow", i)

                    if (api.show_friendship(source_screen_name=username, target_id=i))[1].followed_by:
                        print("Already follow ", i)
                    else:
                        print("follow", i, end=" - ")
                        print(api.create_friendship(i).screen_name)  #follow specific user

                    #it doesn't return error if user is already following to destination user
                        #and it works same without error whether user is following or not
                        #so we don't require to change, can remove upper feature
                    # try:
                    #     print("follow", i, end=" - ")
                    #     print(api.create_friendship(i).screen_name)  #follow specific user
                    # except Exception as e:
                    #     print("Already follow")
                    #     pass


                if _retweet:

                    try:
                        print("retweet", end=" - ")
                        print((api.retweet(SearchId[i])).id)  # retweet specific tweet

                    except Exception as e:
                        print("Already retweeted")
                        pass

            if _like:
                t = TasksList(user=request.user, AppName=app, TaskName="Like top 10 tweets")
                t.save()

            if _follow:
                t = TasksList(user=request.user, AppName=app, TaskName="Follow top 10 Users")
                t.save()

            if _retweet:
                t = TasksList(user=request.user, AppName=app, TaskName="Retweet top 10 tweets")
                t.save()

            #print("Task completed")
            return redirect('/dashboard/'+app_id+'/')

        except Exception as e:

            print(e)
            return redirect('/dashboard/'+app_id+'/')



@login_required(login_url=login_url)
def deleteTwitterApp(request, app_id):


    app = get_object_or_404(TwitterApp, id=app_id, user=request.user)

    t = TasksList(user=request.user, AppName=app, TaskName="Application Deleted")
    t.save()

    app.delete()

    return redirect('/dashboard/')


    # https://twitter.com/narendramodi/status/891865991503806464
    # https://twitter.com/Devchan39963044

#####################MAKE USER AWARE OF ERROR SHOW ERROR MESSAGE BY POP UP MENU ####################
#DONE ###################ADD CHOOSE FIELD in radius Unit(km or mi)#############################
########################PAGINATION IN RESULT TWEETS#################################
#DONE #########################CLEAR PROFILE PHOTO#################################
############################ALL AUTH#############################################
#DONE ##############MAKE SPECIFIC FIELD OF FORM AS REQUIRED##########################
#CANCEL ##################PROVIDE CHECKBOX FOR KEYWORD AND LANG QUERY#####################
######################EVEN USER AND APP IS DELETED TASK TABLE SHOULD CONTAIN THEIR RECORDS###################
#################FOR LOOP IS REPEATED IN APP.HTML FOR SAME STATUS OR SAME USER OBJECT REMOVE IT####################
#################IF TAB HAVE NONE RESULT IT SHOULD SHOW SOME SPECIFIC PAGE#######################
#DONE #################FOR URL IN SEARCHLOCATION.HTML ADD ALSO FOR IPHONE######################
###################SOME TWEETS ARE NOT RETRIEVE WHOLE TEXT MESSAGE########################

#####################BEFORE RETWEETING  ################
#DONE ################### LIKEING ANY TWEETS CHECK IF IT ALREADY LIKE OR NOT######################

##########################THINGS TO DISPLAY##############################
    #authenticated user's profile #me()
    #User of Application(More than one user possible for one application)
    #followers    #followers_ids
    # #when particular user is clicked #get_user (returns user all info)
    #friends       #friends_ids
    #User of Their App (they might or might not be either followers or friends)
    #list of tasks (our Task database objects )
    #search by location  #search
    #search by tag/message/username/tweet and specific language #search_user  #search
    #Direct Messages (Sent by me && Sent to me) #direct_messages #sent_direct_messages
