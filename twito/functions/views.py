
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
    #HttpResponseRedirect
from django.contrib import messages

#from django.core.urlresolvers import reverse

from .models import (
    TwitterApp,
    TasksList,
    TaskLike,
    TaskFollow,
    TaskreTweet,
    AppAccess,
)

from .tweepyfunc import (
    getAPI,
    appendTaskList,
    followUser,
    likeTweet,
    reTweetTweet,
    searchTweets,
    searchUsers,
)


from .forms import (
    TwitterApp_Form,
    SearchLocation_Form,
    PerformTask_Form,
    SearchUser_Form,
    SerachKeyword_Form,
)

import tweepy

login_url = '/'


def index(request):
    return render(request, 'index.html')

@login_required(login_url=login_url)
def appCallback(request, app_id):

    print("in callback url")

    app = get_object_or_404(TwitterApp, id=app_id, user=request.user)

    auth = tweepy.OAuthHandler(app.ConsumerKey, app.ConsumerToken)

    oauth_token = request.GET.get('oauth_token', '')
    oauth_verifier = request.GET.get('oauth_verifier', '')

    auth.request_token = {'oauth_token': oauth_token,
                          'oauth_token_secret': oauth_verifier}

    try:
        auth.get_access_token(verifier=oauth_verifier)
        appAcc = AppAccess(user=request.user, AppName=app)
        appAcc.access_key = auth.access_token_secret
        appAcc.access_token = auth.access_token
        appAcc.save()
        # print("access key:",appAcc.access_key," access token:",appAcc.access_token)

        return redirect('/dashboard/')

    except Exception as e:
        # log this error
        print(str(e))
        messages.warning(request, 'Could not connect to twitter! Please try again.')
        return redirect('/dashboard/')




@login_required(login_url=login_url)
def dashboard(request):

    if request.method == 'POST':

        form = TwitterApp_Form(request.POST)

        # log form details here

        if form.is_valid():

            _consumerKey = request.POST['ConsumerKey'].strip()
            _consumerToken = request.POST['ConsumerToken'].strip()
            # _access_token = request.POST['access_token'].strip()
            # _access_key = request.POST['access_key'].strip()

            try:
                # callback_url = 'http://127.0.0.1:8000/dashboard/callback'

                auth = tweepy.OAuthHandler(_consumerKey, _consumerToken)
                auth.get_authorization_url()

                #if consumer keys and tokens will be valid then..

                app = form.save(commit=False)
                app.user = request.user
                app.save()

                appendTaskList(request.user, appObj=app, taskName="Application Created")

                # print("consumer key:", app.ConsumerKey, "\nconsumer token:", app.ConsumerToken)

                return redirect('/dashboard/connect/'+str(app.id))


            except Exception as e:

                print(e)

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
def appConnect(request, app_id):

    print("Connecting........")
    TwitoApp = get_object_or_404(TwitterApp, id=app_id, user=request.user)

    try:

        auth = tweepy.OAuthHandler(TwitoApp.ConsumerKey, TwitoApp.ConsumerToken)

        callbackURL = 'http://45.76.44.38:8000/dashboard/connect/' + str(app_id) + '/callback/'

        # print("in auth")

        auth = tweepy.OAuthHandler(TwitoApp.ConsumerKey, TwitoApp.ConsumerToken, callbackURL)

        return redirect(auth.get_authorization_url())


    except Exception as e:
        print(e)

        messages.warning(request, "Error occurred while connecting...")
        return redirect('/dashboard/')



@login_required(login_url=login_url)
def appPage(request, app_id):


    if request.method == 'POST':

        if 'locationsearch' in request.POST:

            print("searchlocation")

            form = SearchLocation_Form(request.POST)

            if form.is_valid():
                _keyword = request.POST['keyword'] or None
                _lang = request.POST['lang'] or None
                _latitude = request.POST['latitude'] or None
                _longitude = request.POST['longitude'] or None
                _radius = request.POST['radius'] or None
                _radiusUnit = request.POST['radiusUnit'] or None

                try:
                    request.session['keyword'] = _keyword
                    request.session['lang'] = _lang
                    request.session['latitude'] = _latitude
                    request.session['longitude'] = _longitude
                    request.session['radius'] = _radius
                    request.session['radiusUnit'] = _radiusUnit

                    print("form is valid")

                    return redirect('/dashboard/' + app_id + '/search/')


                except Exception as e:

                    print(e)
                    return redirect('/dashboard/' + app_id + '/')

            else:
                print(form.errors)
                return redirect('/dashboard/' + app_id + '/')

        if 'keywordsearch' in request.POST:

            print("seachkeyword")

            form = SerachKeyword_Form(request.POST)

            if form.is_valid():

                _keyword = request.POST['keyword'] or None
                _lang = request.POST['lang'] or None

                try:
                    request.session['keyword'] = _keyword
                    request.session['lang'] = _lang
                    request.session['radiusUnit'] = None

                    print("form is valid")


                    return redirect('/dashboard/' + app_id + '/search/')


                except Exception as e:

                    print(e)
                    return redirect('/dashboard/' + app_id + '/')

            else:
                print(form.errors)
                return redirect('/dashboard/' + app_id + '/')


            #return searchTweet(location=True, app_id=app_id, request=request)

            #return redirect(reverse('Search', kwargs={'location':True}))

            #return redirect('Search', kwargs={'location':'True'})

            #return HttpResponseRedirect(reverse('Search', kwargs={'location': 'True'}))

            #return redirect('SearchByLocation', app_id)



        if 'usersearch' in request.POST:

            print("usersearch")

            form =SearchUser_Form(request.POST)

            if form.is_valid():

                _username = request.POST['username']

                request.session['username'] = _username

                return redirect('/dashboard/' + app_id + '/searchuser/')

            else:
                print(form.errors)
                return redirect('/dashboard/' + app_id + '/')


    else:

        TwitoApp = get_object_or_404(TwitterApp, id=app_id, user=request.user)

        try:

            appAcc = get_object_or_404(AppAccess, user=request.user, AppName=TwitoApp)

            print("direct to function..")
            api = getAPI(TwitoApp.ConsumerKey, TwitoApp.ConsumerToken, appAcc.access_token, appAcc.access_key)

            if api:
                username = (api.me()).screen_name

                print("Tokens are correct")
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
                likeTasks = TaskLike.objects.filter(AppName=TwitoApp)
                followTasks = TaskFollow.objects.filter(AppName=TwitoApp)
                reTweetTasks = TaskreTweet.objects.filter(AppName=TwitoApp)


                return render(request, 'app.html', {'app': TwitoApp, 'followers':followers,
                                                          'friends':friends,'tweets':tweets,'likes':likes,
                                                          'generalTasks':tasks,
                                                    'likeTasks':likeTasks,'followTasks':followTasks,'reTweetTasks':reTweetTasks
                                                    })
            else:
                messages.warning(request, "Error Occurred, Invalid Tokens..")

                return redirect('/dashboard/')


        except Exception as e:

            print(e)

            messages.warning(request,"Error Occurred, Try Again...")

            return redirect('/dashboard/')



@login_required(login_url=login_url)
def Search(request, app_id):

    print("search.................")
    TwitoApp = get_object_or_404(TwitterApp, id=app_id, user=request.user)
    appAcc = get_object_or_404(AppAccess, user=request.user, AppName=TwitoApp)

    api = getAPI(TwitoApp.ConsumerKey, TwitoApp.ConsumerToken, appAcc.access_token, appAcc.access_key)

    #SearchId = {}  # ["userId":"MessageId"]

    total_search_result = 10
    perform_task_on_tweets = 10

    if request.method != 'POST':

        try:

            # t = TasksList(user=request.user, AppName=app, TaskName="Search by User")
            # t.save()

            arg_geo = request.session.get('radiusUnit')

            arg_key = request.session.get('keyword')
            arg_lang = request.session.get('lang')


            #if location search is made then it will pass location query otherwise it will pass none value

            if arg_geo:
                arg_geo = str(request.session.get('latitude')) + "," +\
                      str(request.session.get('longitude')) + "," +\
                      (str(request.session.get('radius')))+\
                      (request.session.get('radiusUnit'))


            searchResult, taskResult = searchTweets(api, arg_key, arg_lang, arg_geo, True, total_search_result, perform_task_on_tweets)

            request.session['taskIDs'] = taskResult


            return render(request, 'search.html', {'status': searchResult,'app':TwitoApp})

        except Exception as e:

            print(e)
            return redirect('/dashboard/'+app_id+'/')

    else:

        try:

            form = PerformTask_Form(request.POST)

            if form.is_valid():

                username = api.me().screen_name

                _like = request.POST.get('likeTweets', None)
                _follow = request.POST.get('followUsers', None)
                _retweet = request.POST.get('retweetTweets', None)


                taskIDs = request.session.get('taskIDs')

                if _like:

                    taskObj = appendTaskList(request.user, TwitoApp, "Like "+str(perform_task_on_tweets)+" Tweets", True)
                    for i in taskIDs.values():
                        likeTweet(request.user, TwitoApp, api, i, taskObj)

                if _follow:

                    taskObj = appendTaskList(request.user, TwitoApp, "Follow " + str(perform_task_on_tweets)+" Users", True)
                    for i in taskIDs.keys():
                        followUser(request.user, TwitoApp, api, username, i, taskObj)

                if _retweet:


                    taskObj = appendTaskList(request.user, TwitoApp, "Retweet " + str(perform_task_on_tweets)+" Tweets", True)
                    for i in taskIDs.values():
                        reTweetTweet(request.user, TwitoApp, api, i, taskObj)


                #print("Task completed")
                return redirect('/dashboard/'+app_id+'/')


        except Exception as e:

            print(e)
            return redirect('/dashboard/'+app_id+'/')




@login_required(login_url=login_url)
def searchUser(request, app_id):

    TwitoApp = get_object_or_404(TwitterApp, id=app_id, user=request.user)
    appAcc = get_object_or_404(AppAccess, user=request.user, AppName=TwitoApp)

    api = getAPI(TwitoApp.ConsumerKey, TwitoApp.ConsumerToken, appAcc.access_token, appAcc.access_key)

    total_search_result = 10
    perform_task_on_tweets = 10

    if request.method != 'POST':

        try:

            arg_user = request.session.get('username')

            #here taskIDs will be list of user ids
            searchResult, taskIDs = searchUsers(api, arg_user, uniqueUser=True,
                                                    total_search_result=total_search_result,
                                                    total_task_result=perform_task_on_tweets)

            request.session['userIDs'] = taskIDs

            return render(request, 'searchUser.html', {'users': searchResult, 'app': TwitoApp})

        except Exception as e:

            print(e)
            return redirect('/dashboard/' + app_id + '/')

    else:

        try:

            form = PerformTask_Form(request.POST)

            if form.is_valid():

                username = api.me().screen_name

                _follow = request.POST.get('followUsers', None)

                taskIDs = request.session.get('userIDs')

                # print(len(taskIDs))

                if _follow:

                    taskObj = appendTaskList(request.user, TwitoApp, "Follow " + str(perform_task_on_tweets) + " Users", True)
                    for i in taskIDs:
                        followUser(request.user, TwitoApp, api, username, i, taskObj)


                return redirect('/dashboard/' + app_id + '/')

        except Exception as e:

            print(e)
            return redirect('/dashboard/' + app_id + '/')


@login_required(login_url=login_url)
def deleteTwitterApp(request, app_id):


    app = get_object_or_404(TwitterApp, id=app_id, user=request.user)

    # t = TasksList(user=request.user, AppName=app, TaskName="Application Deleted")
    # t.save()

    appendTaskList(request.user, app, "Application Deleted")

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
# NOTE THAT IF USER MANUALLY DISLIKE OR UNFOLLOW OR UNRETWEET WHICH IS PERFORMED BY
# TWITO TASK THEN IT WILL NOT DELETE RECORD FROM TASK MODELS#######################################


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
