from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import sessionmaker

Base = declarative_base()
toutiao_engine = create_engine('mysql://huanghai:huanghai_password@dev3.zhangyupai.net/toutiao?charset=utf8mb4')
toutiaoSession = sessionmaker(bind=toutiao_engine)
media_engine = create_engine('mysql://julai01:Sh51785136@sh@120.26.106.222/jijin?charset=utf8mb4')
mediaSession = sessionmaker(bind=media_engine)


class User(Base):
    __tablename__ = 'toutiao_users'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    user_name = Column(String)
    user_type = Column(Integer)

    def __repr__(self):
        return f"<User(name={self.user_name}, user_type={self.user_type})>"


class UserData(Base):
    __tablename__ = 'toutiao_users_data'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    publish_count = Column(Integer)
    followers_count = Column(Integer)
    digg_count = Column(Integer)

    def __repr__(self):
        return f"<UserData(user_id={self.user_id}, publish_count={self.publish_count}, followers_count={self.followers_count}, digg_count={self.digg_count})>"


class News(Base):
    __tablename__ = 'toutiao_news'
    id = Column(Integer, primary_key=True)
    post_type = Column(Integer)
    url = Column(String, unique=True)
    uniform_url = Column(String, unique=True)
    title = Column(String)
    abstract = Column(String)
    user_id = Column(Integer)
    user_name = Column(String)
    media_orig = Column(String)
    str_date = Column(Integer)
    datestamp = Column(Integer)
    read_count = Column(Integer)
    digg_count = Column(Integer)
    comment_count = Column(Integer)
    forward_count = Column(Integer)
    video_watch_count = Column(Integer)

    def __repr__(self):
        return f"<News(post_type={self.post_type}, title={self.title}, link={self.link}, date={self.str_date})>"


class NewsContent(Base):
    __tablename__ = 'toutiao_news_content'
    id = Column(Integer, primary_key=True)
    news_id = Column(Integer)
    content = Column(String)

    def __repr__(self):
        return f"<Content(news_id={self.news_id}, content={self.content})>"


class Media(Base):
    __tablename__ = 'media'
    id = Column(Integer, primary_key=True)
    media = Column(String)
    post_type = Column(Integer)
    link = Column(String)

    def __repr__(self):
        return f"<Media(media={self.media}, post_type={self.post_type}, link={self.link})>"
