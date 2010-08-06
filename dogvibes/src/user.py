from database import Database
import logging


class User:
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

    def vote(self, track_id):
        if self.votes_left() < 1:
            logging.warning("No votes left for %s" % self.username)
            return

        db = Database()
        db.commit_statement('''insert into votes (track_id, user_id) values (?, ?)''', [track_id, self.id])
        db.commit_statement('''update users set votes = votes - 1 where id = ?''', [self.id])
        logging.debug("Update number of votes and track votes for user = %s" % self.username)


    def current_votes(self):
        db = Database()
        db.commit_statement('''select * from votes where user_id = ?''', [self.id])
        u = db.fetchall()
        logging.debug("Get votes for user %s" % u)
        return u
