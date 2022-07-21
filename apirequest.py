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


@limits(calls=5, period=60, raise_on_limit=False)
def api_call(request_url):
    print(request_url)
    return requests.get(request_url).json()


# Loop through result and save images in account folders
def retrieve_images_for_result(json_result, platform):
    for post_item in json_result['posts']:
        # Since CrowdTangle never provides more than 1 image, this should be irrelevant.
        i = 0

        for media_item in post_item['media']:
            if media_item['type'] == 'photo':
                # Create directory for each account in photo results.
                account_name = "".join([c for c in post_item['account']['name']
                                        if c.isalpha() or c.isdigit() or c == ' ']).rstrip()
                account_id = post_item['account']['platformId']

                if not os.path.exists(platform + "/" + account_name + "-" + account_id):
                    os.mkdir(platform + "/" + account_name + "-" + account_id)

                link = media_item['url']

                # Download image, filename is timestamp of post
                filename = platform + "/" + account_name + "-" + account_id + "/" + "".join(
                    [c for c in post_item['date'] if c.isalpha() or c.isdigit() or c == ' ']).rstrip() + ' ' + str(i)

                # Write post
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
    api_response = api_call(url)

    # Loop through pages of response
    while api_response['status'] == 200:
        if not os.path.exists(platform):
            os.mkdir(platform)

        # This is just the last (paginated) request made and overrides the last dump for the same query.
        with open(platform + "/" + request_name + ".json", "w", encoding="utf-8") as f:
            json.dump(api_response["result"], f, ensure_ascii=False, indent=4)

        print("API-Response saved!")
        retrieve_images_for_result(api_response["result"], platform)

        if 'nextPage' not in api_response['result']['pagination']:
            break

        next_request_url = api_response['result']['pagination']['nextPage']
        api_response = api_call(next_request_url)

    if api_response['status'] != 200:
        print(
            "Error: " + str(api_response['status']) + " - See https://github.com/CrowdTangle/API/wiki/Errors for help."
        )


def main():
    argv = sys.argv[1:]
    platform = 'facebook'
    token = config.facebook_token
    parameters = ''
    time_interval = ''
    start_date = ''

    # Parse arguments
    try:
        opts, args = getopt.getopt(argv, "hfio:t:s:, [options=, time-interval=, startdate=]")
    except getopt.GetoptError:
        print('apirequest.py -i/-f -o <parameters> -t <time-interval in days> (4 days are safe)')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('apirequest.py -i/-f -o <parameters> -t <time-interval in days> (4 days are safe)')
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
        elif opt in ('-t', '--time-interval'):
            print("Time interval: " + arg + " days")
            time_interval = arg
        elif opt in ('-s', '--start-date'):
            print("Start date: " + arg)
            start_date = arg

    base_path = "https://api.crowdtangle.com/posts"

    if start_date != '':
        end = datetime.now()
        start = datetime.strptime(start_date, '%Y-%m-%d')
        i = 0
        while datetime.strptime(start_date, '%Y-%m-%d') < end:
            request_name = platform + "-request-" + datetime.now().strftime("%d-%m-%Y-%H-%M-%S") + str(start) + str(end)
            url = base_path + "?token=" + token + "&sortBy=date&count=100&" + parameters \
                  + "&startDate=" + start.strftime("%Y-%m-%dT%H:%M:%S") \
                  + "&endDate=" + end.strftime("%Y-%m-%dT%H:%M:%S")
            paginate_request(platform, url, request_name + str(i))
            end = start
            start = start - timedelta(days=1)
            i += 1

    if time_interval != '':
        time_interval = int(time_interval)
        last_execution_date = datetime.now() - timedelta(days=time_interval)

        # Perform request every 'time_interval' days
        while True:
            current_execution_date = datetime.now()
            request_name = platform + "-request-" + current_execution_date.strftime("%Y-%m-%dT%H:%M:%S")

            # Build request url
            url = base_path + "?token=" + token + "&sortBy=date&count=100&" + parameters \
                  + "&startDate=" + last_execution_date.strftime("%Y-%m-%dT%H:%M:%S") \
                  + "&endDate=" + current_execution_date.strftime("%Y-%m-%dT%H:%M:%S")

            paginate_request(platform, url, request_name)

            last_execution_date = current_execution_date

            print("Waiting until next timed request.")

            time.sleep(86_400 * time_interval)


if __name__ == "__main__":
    main()
