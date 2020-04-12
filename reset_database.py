import json

from lib.crawler import Config
from lib.utils.mysql import DataBase


if __name__ == '__main__':
    config = Config('config.json')
    with DataBase(**config.save.database.login) as database:
        try:
            database.drop('news')
        except:
            pass
        finally:
            database.create('news',
                id          ='int primary key not null auto_increment',
                entry_time  ='datetime',
                publish_time='datetime',
                source      ='varchar(50)',
                title       ='varchar(300)',
                text        ='mediumtext',
                site        ='varchar(50)',
                url         ='varchar(1000)',
            )
        try:
            database.drop('topic')
        except:
            pass
        finally:
            database.create('topic',
                entry_time  ='datetime',
                name        ='varchar(50) primary key not null',
                keywords    ='text',
                remark      ='text'
            )
        try:
            database.drop('news_topic')
        except:
            pass
        finally:
            database.create('news_topic',
                news_id     ='int not null',
                topic_name  ='varchar(50) not null',
            )