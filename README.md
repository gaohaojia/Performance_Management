# 北工大PIP战队队员工作量量化管理系统
高颢嘉
## 简介
本代码用Python实现，需配合企业微信使用。实现队员工作量的自动化管理与分析。\
## 功能
连接云端MySQL数据库，实现自动化管理\
队员工作量自动记录\
管理层自主查看所有队员工作量\
队员自主查看自己工作量细则\
队员自主查看工作量队内排名
## 使用方式
克隆代码
```bash
git clone https://github.com/gaohaojia/performance_management.git
cd performance_management
```
创建SQL_KEY.yml文件，将下面信息补全
```
host:
port:
user:
passwd:
db:
charset: 'utf8mb4'
```
创建WECOM_KEY.yml文件，将下面信息补全
```
corpid: 
corpsecret: 
AppSecret:
AddressSecret: 
AgentId: 
submit_template_id:
query_template_id:
news_template_id:
```
安装所需包文件
```
pip3 install -r requirements.txt
```
运行
```
nohup python3 -u main.py > main.log 2>&1 &
```