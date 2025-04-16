# Family Home Panel

Status: In Progress

This is a simple webapp used to get the household on the same page for the day. The panel includes two widgets: weather and events. 

## Weather
- show the current weather
- show 24-hour forecast at 3-hour increments
- sourced from OpenWeatherAPI

## Events
- show Google calendar events for today and tomorrow
- also includes meals planned in a "Food" calendar


## Installation
- clone repo
- create a `config.yaml` file using the template

## How to Run Locally
- run `flask run --debug`

## How to Create and Run Docker Container
- build docker image
    `docker build -t home-panel .`
- run docker image
    `docker run --name home-panel -p 5000:5000 home-panel`