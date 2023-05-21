import pandas as pd
from urllib import parse
import mysql.connector
import smtplib
from email.mime.multipart import MIMEMultipart 
from email.mime.text import MIMEText

class URLHandle():
    '''
    根據傳入參數處理 url
    '''
    
    def __init__(self, bus: str, direction: int):
        self.bus = parse.quote(bus)
        self.direction = direction
    
    def bus_route_url(self) -> str:
        '''
        根據公車、行經方向，取得公車行經站牌資料
        '''
        
        url = "https://tdx.transportdata.tw/api/basic/v2/Bus/StopOfRoute/City/Taipei/{0}?%24filter=direction%20eq%20{1}&%24format=JSON".format(self.bus, self.direction)
        return url
    
    def bus_time_url(self) -> str:
        '''
        根據公車、行經方向，取得公車到各站牌之預估時間資料
        '''

        url = "https://tdx.transportdata.tw/api/basic/v2/Bus/EstimatedTimeOfArrival/City/Taipei/{0}?%24filter=direction%20eq%20{1}&%24format=JSON".format(self.bus, self.direction)
        return url
    
    def bus_stop_time_url(self, stop: str) -> str:
        '''
        根據公車、行經方向、特定站牌，取得公車到此站牌之預估時間
        '''
        
        url = "https://tdx.transportdata.tw/api/basic/v2/Bus/EstimatedTimeOfArrival/City/Taipei/{0}?%24select=EstimateTime&%24filter=StopName%2FZh_tw%20eq%20%27{2}%27%20and%20Direction%20eq%20{1}&%24format=JSON".format(self.bus, self.direction, parse.quote(stop))
        return url


def search_all_bus(all_bus_data: pd.DataFrame) -> list:
    '''
    找到所有 bus name
    '''

    all_bus = set()
    for bus in all_bus_data:
        all_bus.add(bus['RouteName']['Zh_tw'])
    bus_choices = [(bus, bus) for bus in sorted(all_bus)]
    return bus_choices


def search_stops_time(route_data: pd.DataFrame, time_data: pd.DataFrame, bus: str) -> pd.DataFrame:
    '''
    查詢特定公車到每站的時間
    '''

    # 整理公車行徑路線
    for row in route_data:
        if row['RouteName']['Zh_tw'] == bus: # 再次確認公車名稱
            sorted_stops = sorted(row['Stops'], key = lambda x: x['StopSequence'])
            stops_name = [stop['StopName']['Zh_tw'] for stop in sorted_stops]
            route_df = pd.DataFrame(stops_name, columns = ['停靠站'])

    # 加上各站點的預估時間
    time_df_row = []

    for row in time_data:
        remark = ''
        if row['RouteName']['Zh_tw'] == bus:
            stop = row['StopName']['Zh_tw']
            try:
                estimate_time = 99999 if pd.isna(row['EstimateTime']) else round(row['EstimateTime']/60, 2)
            except:
                estimate_time = 99999
            if row['StopStatus'] == 1:  
                remark = '尚未發車'
            elif row['StopStatus'] == 2:
                remark = '不停靠'
            elif row['StopStatus'] == 3:
                remark = '末班車已過'
            elif row['StopStatus'] == 4:
                remark = '今日未營運'
            time_df_row.append([stop, estimate_time, remark])

    time_df = pd.DataFrame(time_df_row, columns = ['停靠站', '到站時間(分鐘)', '備註'])

    all_stops_df = pd.merge(route_df, time_df, left_on = "停靠站", right_on = "停靠站")
    return all_stops_df


class DB():
    def __init__(self, user: str, password: str):
        self.dbconnect = mysql.connector.connect(
            host = "localhost",
            user = user,
            password = password,
            database = "teamt5"
        )

    def insert_db_bus_subscribe(self, user_name: str, user_email: str, track_bus: str, bus_direction: int, track_stop: str) -> None:   
        '''
        將使用者提供資料寫入 db
        '''
        
        cursor = self.dbconnect.cursor()
        _sql = "INSERT INTO bus_subscribe (USER_NAME, USER_EMAIL, BUS_NAME, BUS_DIRECTION, STOP) VALUES (%s, %s, %s, %s, %s)"
        val = (user_name, user_email, track_bus, bus_direction, track_stop)
        cursor.execute(_sql, val)
        self.dbconnect.commit()

        cursor.close()
        self.dbconnect.close()

    def select_db_bus_monitor(self) -> list:
        '''
        從 db 取得使用者所提供的資料
        '''
        
        cursor = self.dbconnect.cursor()
        _sql = "SELECT USER_EMAIL, BUS_NAME, BUS_DIRECTION, STOP FROM bus_subscribe"
        cursor.execute(_sql)
        user_data = cursor.fetchall()
        
        cursor.close()
        self.dbconnect.close()
        return user_data


class SendMail(object):
    '''
    以 email 提醒使用者，追蹤的公車即將到站
    '''
    
    def __init__(self, from_gmail_address, from_gmail_password):
        self.from_gmail_address = from_gmail_address
        self.from_gmail_password = from_gmail_password

    def email_content(self, bus: str, estimate_time: int) -> str:
        '''
        提醒之信件內容
        '''

        html = ""
        html += "<h1>提醒！您追蹤的公車{}".format(bus)
        html += "即將在{}分鐘後到站！</h1>".format(estimate_time)

        mime = MIMEMultipart()
        mime["From"] = self.from_gmail_address
        mime["Subject"] = "[通知!!] {}公車到站提醒".format(bus)
        content_to_send = MIMEText(html, "html", "utf-8") 
        mime.attach(content_to_send)
        msg = mime.as_string()
        return msg

    def send_email(self, to_gmail_address: str, bus: str, estimate_time: int) -> str:
        '''
        將信件寄出
        '''

        try:
            server = smtplib.SMTP("smtp.gmail.com", port = 587)
            server.starttls() # 加密文件，避免私密訊息被截取
            server.login(self.from_gmail_address, self.from_gmail_password) # 登入帳號
            server.sendmail(self.from_gmail_address, to_gmail_address, self.email_content(bus, estimate_time))
            # server.quit()
            print("Email sent successfully")
        except Exception as e:
            print("Error sending email")
    