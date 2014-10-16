import traceback
import time
from urllib2 import urlopen

__author__ = 'user'
from TwitterAPI import TwitterAPI


class TweetsParser():
    number_of_requests = 0  # number of completed requests
    location_id = None  # id of location
    bounding_boxes = None  # bounding boxes of location
    full_location = None  # full response with all probable locations
    api = None  # token with 2 keys
    api_user_context = None  # token with all 4 keys
    area = ""  # name of area
    area_type = ""  # area type
    time = None  # time of reset of request_per_15_min
    requests_for_15_min = 0  # number of request from last 15 min (after last reset)
    current_acc = 0  # number of current account
    accounts = [["b2maesFw1ia0xBmFB5f4R3boE",
                "Lz0yub93OqdpCXKkTSogPvmKNj8yJRcMj4qQwC1mgUXn5f7KFU",
                "2821415422-FgEdHvNhd2KCxsfTTwnShhWS7VIWrXmQJoJOunY",
                "jhFO3LwwnPn5QiMgrcwOuDP2KflHz6U1dMkEKcphOvHho"],

               ["7wFNLRFnhJsmr8JtcybY9Lfke",
                "JFqe97mkjW5zqj0vxZ2dhZOFazrgoAUjYYPVICWjBpRvFrvKko",
                "2827937368-4VpBfTEZDVHV6Dm5LKc1ElpoxJobxTpP1xGU2o3",
                "wsHqxuW253vcTBmezyMC9Lku4035rGdMbX6SffanIjiA4"],

               ["d1v4bQwyI89SqEpZMtmO9zIme"
                "Z4WPjStN6aRBvXH9jfGLzKtHjyebSddnbCO2a6AdAqgShDSPq3"
                "2827892277-EQJtR247FPLueYO7e9mgiVqbBn17Jkk4UCn1Ekf"
                "gvAhA55ZhHul6yXQmygYsV9tkktcTvIGHvdnKWnX75qQB"]]  # accounts of twitter: consumer key,
                # consumer secret, access token, access token secret

    def __init__(self, area, area_type):
        """
        initialize initial data, get both types of tokens and set location
        :param area: name of country/state/city for example Mexico
        :param area_type: type of area for example: state
        :return:
        """
        # load accounts from file - TODO
        self.area = area
        self.area_type = area_type
        self.register_api()  # get token from 4 keys
        self.register_api(user_context=False)  # get token from 2 keys
        self.get_location()
        self.time = time.time()  # save time

    def register_api(self, user_context=True):
        """
        get token with or without user context
        :return:
        """

        self.wait_an_internet()  # wait until internet appeared

        if user_context:  # get token with user context
            api = TwitterAPI(self.accounts[self.current_acc][0],
                             self.accounts[self.current_acc][1],
                             self.accounts[self.current_acc][2],
                             self.accounts[self.current_acc][3],)
            self.api_user_context = api

        else:  # get token without user auth.
            api = TwitterAPI(self.accounts[self.current_acc][0],
                             self.accounts[self.current_acc][1],
                             auth_type='oAuth2')
            self.api = api

    def get_next_tweets(self, api_type, science_id=0):
        """

        :param science_id: science id
        :param api_type: 0 - is streaming, 1 - is rest
        :return: iterator over tweets
        """
        flag = True

        self.wait_an_internet()  # wait until internet appeared

        self.check_time(api_type)  # check, may be it should change account
        number_of_attempts = 0
        while flag:  # try until success
            self.is_many_attempts(number_of_attempts)  # check number of attempts and do smth

            try:
                number_of_attempts += 1  # inc number of attempts
                if api_type == 0:  # use steaming api
                    r = self.api_user_context.request('statuses/filter', {'locations': self.bounding_boxes})
                else:  # use rest api
                    r = self.api.request('search/tweets',
                                         {'count': '100', 'q': 'place:' + self.location_id, 'since_id': science_id,
                                          'result_type': 'recent'})
                flag = False  # if success
                print("getting_response")
                self.number_of_requests += 1  # inc number of requests
            except Exception:
                traceback.print_exc()
                flag = True  # continue trying

        return r

    def parse_current(self, apy_type=0):
        """
        print all current tweets
        :param apy_type: 0 - is streaming, 1 - is rest; default is streaming
        :return:
        """
        i = 0  # global number of record
        r = self.get_next_tweets(apy_type)  # get first request of records
        prev_max_id = 0  # previous max id
        max_id = 0  # max id
        bad = 0  # number of id that less than we need

        while True:
            try:
                j = 0  # number of record in request
                for item in r.get_iterator():  # look over all records in request
                    if "errors" in item:  # check for errors
                        print("we decided to change acc, because get an error #"+str(item['error']) +
                              "at"+str(time.time()))
                        self.change_account()
                    j += 1  # number of record in request
                    if j == 1:  # if first record
                        max_id = max(prev_max_id, item['id'])  # save its' id
                        print(i, item['id'])  # print its' id and global number

                    if item['id'] > prev_max_id:  # if current id > previous max id
                        print(i, item['created_at'], item['id'], prev_max_id)  # print it date and id
                        print(item['text'])
                        i += 1  # inc global number
                    else:  # if id less than we need
                        bad += 1
            except Exception:
                traceback.print_exc()
                print('=========================================')

            prev_max_id = max_id  # change value of previous max id
            r = self.get_next_tweets(apy_type, max_id)  # get next set of records
            print("====================", self.number_of_requests, "======================")

    def get_location(self):
        """
        extract location_id and bounding box of area
        :return:
        """

        self.wait_an_internet()

        flag = True
        number_of_attempts = 0
        while flag:
            self.is_many_attempts(number_of_attempts)  # check number of attempts and do smth

            try:
                number_of_attempts += 1
                r = self.api_user_context.request('geo/search', {'query': self.area, 'granularity': self.area_type})
                self.full_location = r  # save full location
                for i in r.get_iterator():
                    self.location_id = i['result']['places'][0]['id']

                    # bounding boxes
                    bounding_boxes = i['result']['places'][0]['bounding_box']['coordinates'][0]
                    x2 = -999
                    x1 = 999
                    y2 = -999
                    y1 = 999
                    for k in bounding_boxes:  # compute bounding boxes
                        if k[0] < x1:
                            x1 = k[0]
                        if k[0] > x2:
                            x2 = k[0]
                        if k[1] < y1:
                            y1 = k[1]
                        if k[1] > y2:
                            y2 = k[1]
                    self.bounding_boxes = str(x1)+','+str(y1)+','+str(x2)+','+str(y2)
                    flag = False
            except Exception:
                flag = True

    def check_time(self, api_type):
        """
        make changing account if it necessary
        :param api_type: 0 - is streaming, 1 - is rest
        :return:
        """
        if time.time()-self.time >= 15*60:  # if 15 min left since last requests_for_15_min reset
            self.requests_for_15_min = 0  # reset requests_for_15_min
            self.time = time.time()  # save time
        if self.requests_for_15_min > api_type * 430 + 18:  # if there is over limit requests
            self.change_account()  # change account
            self.requests_for_15_min = 0  # reset requests_for_15_min
            self.time = time.time()  # save time

    def change_account(self):
        """
        get new tokens
        :return:
        """
        flag = True
        while flag:  # while no success
            try:
                self.current_acc = (self.current_acc + 1) % len(self.accounts)  # inc account id
                self.register_api(user_context=True)  # get new token with user_context
                self.register_api(user_context=False)  # get new token without user_context
                flag = False
            except Exception:
                flag = True
                print("some troubles during getting token, we decided to sleep a min and change acc"+
                      str(time.time()))  # may be we should do smth another -TODO
                time.sleep(60)
        print("account have been changed at "+' '+str(time.time()))

    @staticmethod
    def is_internet_on():
        """

        :return: True if there is internet connection, else False
        """
        try:
            urlopen('http://twitter.com', timeout=5)
        except Exception:
            return False
        return True

    @staticmethod
    def wait_an_internet():
        while not TweetsParser.is_internet_on():  # while there is no the internet connection
            print("there is no internet connection, so we decided to sleep a min"+' '+str(time.time()))
            time.sleep(60)  # sleep a minute

    def is_many_attempts(self, number_of_attempts):
        if number_of_attempts > 10:  # if there is many attempts
                print("some troubles during getting next tweets, we have decided to change an acc")
                self.change_account()  # change acc
                if number_of_attempts > 20:  # if there too many attempts
                    print("some troubles during getting next tweets, we have decided to sleep a minute")
                    time.sleep(60)  # sleep a min


def main():
    parser = TweetsParser("Ukraine", "country")
    parser.parse_current(1)
main()
