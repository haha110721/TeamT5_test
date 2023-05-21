from flask_wtf import FlaskForm
from wtforms import StringField, RadioField, SelectField, SubmitField
from wtforms.fields import EmailField
from wtforms.validators import DataRequired, Email # 引入驗證

class SubscribeForm(FlaskForm):
    user_name = StringField('使用者名稱', validators = [DataRequired(message = '必填')])
    user_email = EmailField('接收通知信箱', 
                            validators = [DataRequired(message = '必填'),
                                          Email(message = '請輸入有效信箱，比如：username@gmail.com')])
    track_bus = SelectField('欲追蹤公車',
                            choices = [],
                            validators = [DataRequired(message = '請選擇')])
    
    bus_direction = RadioField('去返程', choices = [('0', '去程'), ('1', '返程')], validators = [DataRequired(message = '請選擇')])
    submit = SubmitField('確認')
    track_stop = SelectField('欲追蹤站點',
                            choices = [],
                            validators = [DataRequired(message = '請選擇')])
    
