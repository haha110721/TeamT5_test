from flask import Flask, render_template, request, session, redirect, url_for
import configparser
from web_form import SubscribeForm
from auth import Auth, DataAPI
from tool import URLHandle, search_all_bus, search_stops_time, DB

config = configparser.ConfigParser() 
config.read('config.ini')

app = Flask(__name__)
app.config['SECRET_KEY'] = config['Flask']['secret_key']

@app.route("/", methods = ['GET', 'POST'])
def index():
    # 找到所有 bus name 當作選項
    settings = DataAPI(config["tdxAPI"]["app_id"], config["tdxAPI"]["app_key"])
    all_bus_data = settings.get_data("https://tdx.transportdata.tw/api/basic/v2/Bus/Route/City/Taipei?%24format=JSON")
    bus_choices = search_all_bus(all_bus_data)
    return render_template('index.html', bus_choices = bus_choices)
    
@app.route("/bustime", methods = ['GET', 'POST'])
def bustime():
    settings = DataAPI(config["tdxAPI"]["app_id"], config["tdxAPI"]["app_key"])
    url = URLHandle(request.values["bus"], int(request.values["busdirection"]))
    df = search_stops_time(settings.get_data(url.bus_route_url()), settings.get_data(url.bus_time_url()), request.values["bus"])
    return render_template('bustime.html', result = df.to_html())

@app.route("/subscribe", methods = ['GET', 'POST'])
def subscribe():
    # 找到所有 bus name 當作選項
    settings = DataAPI(config["tdxAPI"]["app_id"], config["tdxAPI"]["app_key"])
    all_bus_data = settings.get_data("https://tdx.transportdata.tw/api/basic/v2/Bus/Route/City/Taipei?%24format=JSON")
    bus_choices = search_all_bus(all_bus_data)

    form = SubscribeForm()
    form.track_bus.choices = bus_choices

    if request.method == 'POST':      
        session['user_name'] = form.user_name.data
        session['user_email'] = form.user_email.data
        session['track_bus'] = form.track_bus.data
        session['bus_direction'] = form.bus_direction.data

        if 'btn1' in request.form:
            # 根據剛剛輸入的 bus、direction，找到所有 stop 當作選項
            bus_stop_url = URLHandle(session['track_bus'], int(session['bus_direction']))
            bus_stop_data = settings.get_data(bus_stop_url.bus_route_url())
            for row in bus_stop_data:
                if row['RouteName']['Zh_tw'] == session['track_bus']:
                    sorted_stops = sorted(row['Stops'], key = lambda x: x['StopSequence'])
                    stop_choices = [(stop['StopName']['Zh_tw'], stop['StopName']['Zh_tw']) for stop in sorted_stops]
            form.track_stop.choices = stop_choices
        elif 'btn2' in request.form:
            session['track_stop'] = form.track_stop.data
            return redirect(url_for('confirm'))
            
    return render_template('subscribe.html', form = form)

@app.route("/confirm")
def confirm():
    db_connect = DB(config['MySQL']['user'], config['MySQL']['password'])
    db_connect.insert_db_bus_subscribe(session['user_name'], session['user_email'], session['track_bus'], int(session['bus_direction']), session['track_stop'])
    return render_template("confirm.html")


if __name__ == '__main__':
    app.debug = True
    app.config['SECRET_KEY'] = config['Flask']['secret_key']
    app.run()


