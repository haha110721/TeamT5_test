from apscheduler.schedulers.blocking import BlockingScheduler
# from apscheduler.schedulers.background import BackgroundScheduler
import configparser
from auth import Auth, DataAPI
from tool import URLHandle, search_stops_time, DB, SendMail

config = configparser.ConfigParser() 
config.read('config.ini')

def bus_monitor():
    '''
    定時查看 db 中的 user 資訊，即將到站時提醒
    '''
    
    db_connect = DB(config['MySQL']['user'], config['MySQL']['password'])
    user_track_data = db_connect.select_db_bus_monitor()

    settings = DataAPI(config["tdxAPI"]["app_id"], config["tdxAPI"]["app_key"])
    for i in range(len(user_track_data)):
        url = URLHandle(user_track_data[i][1], user_track_data[i][2])
        estimate_time_now = settings.get_data(url.bus_stop_time_url(user_track_data[i][3]))
        if estimate_time_now[0]['EstimateTime'] <= 300:
            mail = SendMail(config['gmail']['account'], config['gmail']['password'])
            mail.send_email(user_track_data[i][0], user_track_data[i][1], int(estimate_time_now[0]['EstimateTime']/60))


if __name__ == '__main__':
    scheduler = BlockingScheduler()
    scheduler.add_job(bus_monitor, "cron", hour = '7-23', second = '*/10', id = "bus_monitor")
    scheduler.start()

