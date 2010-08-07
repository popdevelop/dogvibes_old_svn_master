from database import Database
import logging
import time


class User:
    all_votes = []

    def __init__(self, username, avatar_url="http://dogvibes.com"):
        if username == None:
            self.username = "dogvibes"
        else:
            self.username = username
        self.avatar_url = avatar_url
        self.id = -1
    def __str__(self):
        return "username: " + self.username + " id:" + str(self.id) + " avatar: " + self.avatar_url

    # Store user, if not already added
    def store(self):
        db = Database()
        db.commit_statement('''select * from users where username = ?''', [self.username])
        u = db.fetchone()
        if  u == None:
            db.commit_statement('''insert into users (username, avatar_url, votes) VALUES(?, ?, ?)''', [self.username, self.avatar_url, 5])
            db.commit_statement('''select * from users where username = ?''', [self.username])
            u = db.fetchone()
            logging.debug("Added user=%s" % self.username)

        self.id = u['id']
        return u['id']
    def votes_left(self):
        db = Database()
        db.commit_statement('''select * from users where username = ?''', [self.username])
        u = db.fetchone()
        return u['votes']

    def voteup(self, track_id):
        if self.votes_left() < 1:
            logging.warning("No votes left for %s" % self.username)
            return

        db = Database()
        db.commit_statement('''select * from tracks where id=?''', [track_id])
        row = db.fetchone()

        now = time.time()

        self.all_votes.append({"id":track_id,"title":row['title'], "artist":row['artist'], "album": row['album'], "user":self.username, "time":now, "votes":1, "duration":row['duration'], "votes":3})

        db.commit_statement('''insert into votes (track_id, user_id) values (?, ?)''', [track_id, self.id])
        # take vote from user
        db.commit_statement('''update users set votes = votes - 1 where id = ?''', [self.id])
        logging.debug("Update number of votes and track votes for user = %s" % self.username)

    def votedown(self, track_id):
        db = Database()
        db.commit_statement('''delete from votes where track_id = ? and user_id = ?''', [track_id, self.id])
        # give vote back to user
        db.commit_statement('''update users set votes = votes + 1 where id = ?''', [self.id])
        logging.debug("Update number of votes and track votes for user = %s" % self.username)

    @classmethod
    def remove_all_voting_users(self, track_id):
        db = Database()
        db.commit_statement('''select * from votes where track_id = ?''', [track_id])
        
        logging.debug("Give votes back to all users who voted for removed track")

        row = db.fetchone()
        while row != None:
            # give vote back to user
            db.commit_statement('''update users set votes = votes + 1 where id = ?''', [row['user_id']])
            row = db.fetchone()

        db.commit_statement('''delete from votes where track_id = ?''', [track_id])
            
    @classmethod
    def get_activity(self):
        return self.all_votes
