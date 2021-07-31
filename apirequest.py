import json
import os
import sys
import getopt
import time
from urllib import request, error
from datetime import datetime, timedelta
from ratelimit import limits
import config
import requests


@limits(calls=5, period=1)
def api_call(request_url):
    return requests.get(request_url).json()


# Loop through result and save images in account folders
def retrieve_images_for_result(json_result, platform):
    for post_item in json_result['posts']:
        account_name = "".join([c for c in post_item['account']['name']
                                if c.isalpha() or c.isdigit() or c == ' ']).rstrip()
        account_id = post_item['account']['platformId']

        i = 0
        if post_item['type'] == 'photo':

            # Create directory for each account in photo results
            if not os.path.exists(platform + "/" + account_name + "-" + account_id):
                os.mkdir(platform + "/" + account_name + "-" + account_id)

            for media_item in post_item['media']:
                if media_item['type'] == 'photo':
                    link = ''
                    if platform == 'facebook':
                        if 'full' in media_item:
                            link = media_item['full']
                    else:
                        if 'url' in media_item:
                            link = media_item['url']

                    # Download image, filename is timestamp of post
                    filename = platform + "/" + account_name + "-" + account_id + "/" + "".join(
                        [c for c in post_item['date'] if c.isalpha() or c.isdigit() or c == ' ']).rstrip() + str(i)

                    with open(filename + ".json", "w", encoding="utf-8") as f:
                        json.dump(post_item, f, ensure_ascii=False, indent=4)

                    if link != '':
                        if not os.path.exists(filename):
                            try:
                                request.urlretrieve(link, filename + ".jpg")
                                print('Image ' + post_item['date'] + str(i) + '.jpg saved!')
                            except error.HTTPError:
                                print('Image ' + post_item['date'] + str(i) + '.jpg could not be downloaded.')
                                print(link)
                        i += 1


def paginate_request(platform, url, request_name):
    print(url)
    api_response = api_call(url)

    # Check if request was successful
    if api_response['status'] == 200:
        results = api_response["result"]

        # Loop through pages of response
        while api_response['status'] == 200 and 'nextPage' in api_response['result']['pagination']:
            api_response = api_call(api_response['result']['pagination']['nextPage'])
            results.update(api_response["result"])
            print("Waiting 10 seconds before next request...")
            time.sleep(10)

        if not os.path.exists(platform):
            os.mkdir(platform)

        with open(platform + "/" + request_name + ".json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=4)

        print("API-Response saved!")
        last_execution_date = datetime.now()
        retrieve_images_for_result(results, platform)

    else:
        print("Error: " + str(api_response['status']) +
              ". See https://github.com/CrowdTangle/API/wiki/Errors for help.")


def main():
    argv = sys.argv[1:]
    platform = 'facebook'
    token = config.facebook_token
    parameters = ''
    time_interval = 86400 * 5
    start_date = ''

    # Parse arguments
    try:
        opts, args = getopt.getopt(argv, "hfio:t:s:, [options=, timeinterval=, startdate=]")
    except getopt.GetoptError:
        print('apirequest.py -i/-f -o <parameters> -t <timeinterval in days> (4 days are safe)')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('apirequest.py -i/-f -o <parameters> -t <timeinterval in days> (4 days are safe)')
            sys.exit()
        elif opt == "-f":
            print('Facebook request')
            platform = 'facebook'
            token = config.facebook_token
        elif opt == "-i":
            print('Instagram request')
            platform = 'instagram'
            token = config.instagram_token
        elif opt in ('-o', '--options'):
            print("Parameters: " + arg)
            parameters = arg
        elif opt in ('-t', '--timeinterval'):
            print("Timeinterval: " + arg + " days")
            if time_interval == '1':
                time_interval = 2
            else:
                time_interval = arg
        elif opt in ('-s', '--startdate'):
            print("Start date: " + arg)
            start_date = arg

    last_execution_date = datetime.today() - timedelta(days=int(time_interval))

    url = "https://api.crowdtangle.com/posts"
    request_name = platform + "-request-" + datetime.now().strftime("%d-%m-%Y-%H-%M-%S")

    if start_date != '':
        end = datetime.today()
        start = end - timedelta(days=10)
        i = 0
        while datetime.strptime(start_date, '%Y-%m-%d') <= end:
            request_name = platform + "-request-" + datetime.now().strftime("%d-%m-%Y-%H-%M-%S") + start + end
            url = "https://api.crowdtangle.com/posts?token=" + token + "&sortBy=date&count=100&" + parameters + "&startDate=" + start.strftime(
                "%Y-%m-%d") + "&endDate=" + end.strftime("%Y-%m-%d")
            end = end - timedelta(days=20)
            start = start - timedelta(days=20)
            paginate_request(platform, url, request_name + str(i))
            i += 1

    else:
        request_name = platform + "-request-" + datetime.now().strftime("%d-%m-%Y-%H-%M-%S")
        # Build request url
        url = url + "?token=" + token + "&sortBy=date&count=100&" + parameters + "&startDate=" + (
                last_execution_date + timedelta(days=1)).strftime("%Y-%m-%d") + "&endDate=" + datetime.today().strftime(
            "%Y-%m-%d")

        # Perform request every 'time_interval' days
        while True:
            if not datetime.today() == last_execution_date:
                paginate_request(platform, url, request_name)
            print("Waiting until next timed request.")
            time.sleep(86400 * int(time_interval))


if __name__ == "__main__":
    main()
