# crowdtangle-datacollection

Simple python script to download posts containing images received by the CrowdTangle API (Facebook or Instagram).

## Requirements

- Tested on Python 3.8
- `pip3 install -r requirements.txt`
- CrowdTangle API keys for Facebook and/or Twitter (to be entered in `apirequest.py`)

## Usage

Either `-f` (Facebook) or `-i` (Instagram) must be provided as command line argument.

The targeted lists have to be provided with `-o "listIds=<ID_1,ID_2[,ID_I]>"`.

Two modes are supported:

- Obtaining images from a given starting date until now (`-s`)
- Obtaining images periodically in time intervals every N days (`-t`)

### Download images and posts since some specified date

`python3 apirequest.py [-f|-i] -o "listIds="<someListID>" -s "<start date>"`

Example: `python3 apirequest.py -f -o "listIds=1568443,1568444" -s "2021-12-31"`

This request would download images and posts since the 31st of December, 2021.

### Download images and posts in time intervals every N days

`python3 apirequest.py [-f|-i] -o "listIds="<someListID>" -t <time_interval_days>`

Example: `python3 apirequest.py -f -o "listIds=1568443,1568444" -t 3`

This request would download new posts every 3 days until the script is stopped.  
The first interval is executed immediately, meaning that the first posts and images obtained are up to N days old.
