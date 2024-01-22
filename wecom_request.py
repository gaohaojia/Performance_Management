import requests

# 获取access_token
def get_access_token(corpid, corpsecret):
    url = "https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={}&corpsecret={}".format(corpid, corpsecret)
    response = requests.get(url)
    data = response.json()
    access_token = data['access_token']
    return access_token

# 获取所有审批id
def get_sp_no_list(access_token, template_id, last_time, now_time, new_cursor):
    url = "https://qyapi.weixin.qq.com/cgi-bin/oa/getapprovalinfo?access_token={}".format(access_token)
    sp_no_list = []
    while True:
        data = {
            "starttime" : last_time,
            "endtime" : now_time,
            "new_cursor" : new_cursor,
            "size" : 100 ,
            "filters" : [
                {
                    "key": "template_id",
                    "value": template_id
                } 
            ]
        }
        response = requests.post(url, json=data)
        data = response.json()
        sp_no_list.extend(data['sp_no_list'])
        try:
            new_cursor = data['new_next_cursor']
        except:
            break
    return sp_no_list

# 根据审批id获取具体内容
def get_approval_data(access_token, sp_no):
    url = "https://qyapi.weixin.qq.com/cgi-bin/oa/getapprovaldetail?access_token={}".format(access_token)
    data = {
        "sp_no" : sp_no
    }
    response = requests.post(url, json=data)
    data = response.json()
    return data['info']

# 获取所有user_id
def get_all_user_id(access_token):
    url = "https://qyapi.weixin.qq.com/cgi-bin/user/list_id?access_token={}".format(access_token)
    response = requests.get(url)
    user_id = response.json()
    return user_id['dept_user']

# 根据user_id获取员工姓名
def get_name(access_token, user_id):
    url = "https://qyapi.weixin.qq.com/cgi-bin/user/get?access_token={}&userid={}".format(access_token, user_id)
    response = requests.get(url)
    name = response.json()['name']
    return name

# 设置应用在工作台展示的模版
def set_template(access_token, agentid):
    url = "https://qyapi.weixin.qq.com/cgi-bin/agent/set_workbench_template?access_token={}".format(access_token)
    data = {
        "agentid":agentid,
        "type":"keydata"
    }
    response = requests.post(url, json=data)
    data = response.json()
    return data

# 添加数据
def push_data(access_token, agentid, user_id, items):
    url = "https://qyapi.weixin.qq.com/cgi-bin/agent/set_workbench_data?access_token={}".format(access_token)
    data = {
        "agentid": agentid,
        "userid": user_id,
        "type":"keydata",
        "keydata":{
            "items": items
        }
    }
    response = requests.post(url, json=data)
    data = response.json()
    return data

# 发送自定义消息
def send_message(access_token, user_id, agent_id, msg):
    url = "https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={}&debug=1".format(access_token)
    data = {
        "touser" : str(user_id),
        "msgtype": "markdown",
        "agentid" : agent_id,
        "markdown": {
            "content": msg
        }
    }
    response = requests.post(url, json=data)
    return response.json()