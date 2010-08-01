from database import Database

class Track:
    # Set all attributes as parateters to be able to initialize with a **dict
    def __init__(self, uri, title = 'Name', artist = 'Artist', album = 'Album',
                 duration = 0, album_uri = ''):
        self.title = title
        self.artist = artist
        self.album = album
        self.album_uri = album_uri
        self.uri = uri
        self.duration = duration
        self.id = -1
        self.votes = -1
    def __str__(self):
        return self.artist + ' - ' + self.title

    # Store track for the future
    def store(self):
        db = Database()
        # TODO: don't search on uri, do a comparison on more metadata
        db.commit_statement('''select * from tracks where uri = ?''', [self.uri])
        row = db.fetchone()
        if row == None:
            db.commit_statement('''insert into tracks (title, artist, album, album_uri, uri, duration) values (?, ?, ?, ?, ?, ?)''',
                                (self.title, self.artist, self.album, self.album_uri, self.uri, self.duration))
            self.id = db.inserted_id()
        else:
            self.id = row['id']
        return self.id

    def has_vote_from(self, user_id):
        db = Database()

        db.commit_statement('''select * from votes where track_id = ? AND user_id = ?''', [self.id, user_id])
        row = db.fetchone()
        return row != None
    
