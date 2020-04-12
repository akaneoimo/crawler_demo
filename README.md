# 环境配置

### 1 MySQL

1. 安装MySQL5.7或更高版本

2. 在MySQL shell中输入

> create database your_database_name;

新建数据库 `your_database_name`

3. 在 `config.json` 中修改相应的 `password` 和 `database` 项

### 2 Python

1. 安装Python3.6或更高版本

2. 输入

> pip install -r requirements.txt

安装脚本依赖

# 使用步骤

1. 在 crawler_demo 目录下输入

> python reset_database.py

初始化/重置 `your_database_name` 数据库。该操作会创建/重置数据库下 `news` , `topic` 和 `news_topic` 三张表

2. 修改 topical_crawler_main.py 源码中的话题和关键词配置，在 crawler_demo 目录下输入

> python topical_crawler_main.py

# 注意事项

- 该爬虫的工作过程是：给定主题，根据给定的关键词，使用百度搜索引擎搜索指定网站的新闻网页，解析网页中的正文文本存入数据库的 `news` 表内，主题存入数据库的 `topic` 表内，新闻的所属主题存入 `news_topic` 表内

- 网页链接爬自百度的搜索结果，有时候因为网络（也可能是百度的反爬机制）导致脚本会中断。再输入 python topical_crawler_main.py 即可，脚本会根据tmp目录下的文件执行断点续爬。也可通过ctrl+c手动中断程序。若不想续爬（例如配置不理想等），需要删除或清空tmp目录

- 日志输出在终端和log目录下的文件中，报ERROR的条目是网页解析出错（毕竟咱制定的解析规则不能覆盖任意网页...），忽略即可，INFO 和 ERROR 分流在两个文件中，便于以后完善解析规则
