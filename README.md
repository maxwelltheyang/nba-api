# NBA Metrics
A RESTful API that takes NBA historic and current data and presents it in an organized manner

## Inspiration
Using sports data for machine learning or software engineering has always been finnicky and not streamlined. I find myself downloading csv files or using out-of-date modules, an API allows for seamless connection and organization of data all in one area.

## How it works
1) The user enters a query with thie desired NBA data they want to obtain
2) Information is scraped from basketballreference.com and stored in MongoDB Atlas Database (cached for repeat use)
3) Data is returned to the user in JSON format to use for their application

## API structure
nbametrics.com/team/{team abbreviation}/stats/{statistic type}/{time period}/{aggregation type}<br /><br />
team abbreviation- abbreviation of the NBA (e.g. BOS, GSW, LAC, LAL)<br /><br />
time period- start and end (inclusive) of statistics the user wants to obtain (e.g. 2000-2018 goes from 2000-2001 NBA season to 2017-2018 NBA season)<br /><br />
statistic type- the type of statistic the user wants to use (per season, per game, opponent per season, opponent per game, per season rank, per game rank, opponent per season rank, opponent per game rank, per season year-over-year, per game year-over-year, opponent per season year-over-year, opponent per game year-over-year<br /><br />
aggregation type- how the data should be presented (total, average)<br /><br />
Currently, only team statistics are supported but I am currently working on supporting player statistics as well.<br /><br />

## File descriptions
nba_api.py- Local (Flask) version of the API<br /><br />
nba_api_gcloud.py- Cloud version of the API to be invoked by custom domain<br /><br />

## Experience gained
I learned how to obtain a DNS certificate for secure HTTPS connections, as well as JSON formatting in Python and domain redirection from cloud function domain to my own custom domain (nbametrics.com)



