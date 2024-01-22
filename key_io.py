import yaml
import time

def get_time():
    # 读取上次操作时间
    try:
        with open('./time.yml', 'r', encoding='utf-8') as f:
            time_key = yaml.load(f.read(), Loader=yaml.FullLoader)
        return time_key
    except:
        print("SQL_KEY文件损坏！")
        key_data = {
            "submit_last_time": int(time.time()), 
            "query_last_time": int(time.time()), 
            "news_last_time": int(time.time())
        }
        return key_data
    
def save_time(submit_last_time, query_last_time, news_last_time):
    # 写入当前时间
    key_data = {
        "submit_last_time": submit_last_time, 
        "query_last_time": query_last_time, 
        "news_last_time": news_last_time
    }
    with open('./time.yml', 'w', encoding='utf-8') as f:
        yaml.dump(data=key_data, stream=f, allow_unicode=True)

def get_SQL_KEY():
    # 读取数据库密钥
    try:
        with open('./SQL_KEY.yml', 'r', encoding='utf-8') as f:
            SQL_KEY = yaml.load(f.read(), Loader=yaml.FullLoader)
        return SQL_KEY
    except:
        print("SQL_KEY文件损坏！")
        return None
    
def get_WECOM_KEY():
    # 读取企业微信密钥
    try:
        with open('./WECOM_KEY.yml', 'r', encoding='utf-8') as f:
            WECOM_KEY = yaml.load(f.read(), Loader=yaml.FullLoader)
        return WECOM_KEY
    except:
        print("WECOM_KEY文件损坏！")
        return None