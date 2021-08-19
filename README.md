# crowdtangle-datacollection

Simple python script to download images received by the Crowdtangle API (Facebook or Instagram).

## Requirements
pip install -r requirements.txt

## Usage

### Download images since some specified date
`python apirequest.py -f/-i (Facebook or Instagram) -o "listIds="<someListID>" -s "<start date>"`

e.g. `python apirequest.py -f -o "listIds=1568443,1568444" -s "2015-01-01"`

### Run script continuously every specified timeinterval
`python apirequest.py -f/-i (Facebook or Instagram) -o "listIds="<someListID>" -t <time_interval>`

e.g. `python apirequest.py -f -o "listIds=1568443,1568444" -t 4`
