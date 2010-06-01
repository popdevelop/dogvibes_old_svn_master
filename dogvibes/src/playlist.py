from database import Database
from track import Track
import logging

class Playlist():
    version = 0

    def __init__(self, id, name, db):
        self.id = int(id)
        self.name = name
        self.db = db

    def to_dict(self):
        return dict(name = self.name, id = self.id)

    @classmethod
    def get(self, id):
        db = Database()
        db.commit_statement('''select * from playlists where id = ?''', [int(id)])
        row = db.fetchone()
        if row == None:
            raise ValueError('Could not get playlist with id=' + str(id))
        return Playlist(id, row['name'], db)

    @classmethod
    def get_by_name(self, name):
        db = Database()
        db.commit_statement('''select * from playlists where name = ?''', [name])
        row = db.fetchone()
        if row == None:
            raise ValueError('Could not get playlist with id=' + str(id))
        return Playlist(row['id'], row['name'], db)

    @classmethod
    def name_exists(self, name):
        db = Database()
        db.commit_statement('''select * from playlists where name = ?''', [name])
        row = db.fetchone()
        if row == None:
            return False
        else:
            return True

    @classmethod
    def get_all(self):
        db = Database()
        db.commit_statement('''select * from playlists''')
        row = db.fetchone()
        playlists = []
        while row != None:
            playlists.append(Playlist(row['id'], row['name'], db))
            row = db.fetchone()
        return playlists

    @classmethod
    def create(self, name):
        db = Database()
        db.commit_statement('''insert into playlists (name) values (?)''', [name])
        logging.debug ("Adding playlist '" + name + "'")
        return Playlist(db.inserted_id(), name, db)

    @classmethod
    def remove(self, id):
        self.tick_version()
        db = Database()
        db.commit_statement('''select * from playlists where id = ?''', [int(id)])
        row = db.fetchone()
        if row == None:
            raise ValueError('Could not get playlist with id=' + id)

        db.add_statement('''delete from playlist_tracks where playlist_id = ?''', [int(id)])
        db.add_statement('''delete from playlists where id = ?''', [int(id)])
        db.commit()

    @classmethod
    def rename(self, playlist_id, name):
        self.tick_version()
        db = Database()
        db.commit_statement('''select * from playlists where id = ?''', [int(playlist_id)])
        row = db.fetchone()
        if row == None:
            raise ValueError('Could not get playlist with id=' + playlist_id)

        db.add_statement('''update playlists set name = ? where id = ?''', [name, int(playlist_id)])
        db.commit()

    @classmethod
    def tick_version(self):
        self.version = self.version + 1

    @classmethod
    def get_version(self):
        return self.version

    # returns: the id so client don't have to look it up right after add
    def add_track(self, track, request):
        self.tick_version()
        track_id = track.store()
        self.db.commit_statement('''select max(position) from playlist_tracks where playlist_id = ?''', [self.id])
        row = self.db.fetchone()

        # Do not assume that user is set always
        user = request.user
        if user == None:
            user = ""
        
        if row['max(position)'] == None:
            position = 1
        else:
            position = row['max(position)'] + 1

        self.db.commit_statement('''insert into playlist_tracks (playlist_id, track_id, position, user) values (?, ?, ?, ?)''', [self.id, track_id, position, user])
        return self.db.inserted_id()
        
     # returns: the id so client don't have to look it up right after add
    def add_tracks(self, tracks, request, position):
        first = True
        tid = 0
        
        self.db.commit_statement('''select max(position) from playlist_tracks where playlist_id = ?''', [self.id])
        row = self.db.fetchone()
        
        if row['max(position)'] == None:
            # no tracks in queue, put it first
            position = 1
        else:
            # sanity check index
            if int(position) > int(row['max(position)']) + 1 or int(position) < 0:
                position = int(row['max(position)']) + 1
            else:
                self.db.commit_statement('''update playlist_tracks set position = position + ? where playlist_id = ? and position >= ?''', [str(len(tracks)), self.id, position])
            
        # add new tracks    
        for track in tracks:
            track_id = track.store()
        
            # Do not assume that user is set always
            user = request.user
            if user == None:
                user = ""

            self.db.commit_statement('''insert into playlist_tracks (playlist_id, track_id, position, user) values (?, ?, ?, ?)''', [self.id, track_id, position, user])
            position = int(position) + 1    
            
            if first:
                first = False
                tid = self.db.inserted_id()

        self.tick_version()
        return tid

    # returns: an array of Track objects
    def get_all_tracks(self):
        self.db.commit_statement('''select * from playlist_tracks where playlist_id = ? order by position''', [int(self.id)])
        row = self.db.fetchone()
        tracks = []
        while row != None:
            tracks.append((str(row['id']), row['track_id'])) # FIXME: broken!
            row = self.db.fetchone()

        ret_tracks = []
        for track in tracks:
            # TODO: replace with an SQL statement that instantly creates a Track object
            self.db.commit_statement('''select * from tracks where id = ?''', [track[1]])
            row = self.db.fetchone()
            del row['id']
            t = Track(**row)
            t.id = track[0]
            ret_tracks.append(t)

        return ret_tracks

    def get_track_nbr(self, nbr):
        self.db.commit_statement('''select * from playlist_tracks where playlist_id = ? order by position limit ?,1''', [int(self.id), nbr])
        return self.get_track_row()

    def get_track_id(self, id):
        self.db.commit_statement('''select * from playlist_tracks where id = ?''', [id])
        return self.get_track_row()

    def get_track_row(self):
        row = self.db.fetchone()
        tid = row['track_id']
        position = row['position']
        ptid = row['id']

        self.db.commit_statement('''select * from tracks where id = ?''', [row['track_id']])
        row = self.db.fetchone()
        del row['id']
        t = Track(**row)
        t.id = tid
        t.position = position
        t.ptid = ptid
        return t

    def move_track(self, id, position):
        self.tick_version()
        self.db.commit_statement('''select position from playlist_tracks where playlist_id = ? and id = ?''', [self.id, id])
        row = self.db.fetchone()
        if row == None:
            raise ValueError('Could not find track with id=%d in playlist with id=%d' % (id, self.id))
        old_position = row['position']
        logging.debug("Move track from %s to %s" % (old_position,position))

        self.db.commit_statement('''select max(position) from playlist_tracks where playlist_id = ?''', [self.id])
        row = self.db.fetchone()

        if position > row['max(position)'] or position < 1:
            raise ValueError('Position %d is out of bounds (%d, %d)' % (position, 1, row['max(position)']))

        if position > old_position:
            self.db.commit_statement('''update playlist_tracks set position = position - 1 where playlist_id = ? and position > ? and position <= ?''', [self.id, old_position, position])
            self.db.commit_statement('''update playlist_tracks set position = ? where playlist_id = ? and id = ?''', [position, self.id, id])
        else:
            self.db.commit_statement('''update playlist_tracks set position = position + 1 where playlist_id = ? and position >= ?''', [self.id, position])
            self.db.commit_statement('''update playlist_tracks set position = ? where playlist_id = ? and id = ?''', [position, self.id, id])
            self.db.commit_statement('''update playlist_tracks set position = position - 1 where playlist_id = ? and position > ?''', [self.id, old_position])

    def remove_track_id(self, id):
        self.tick_version()
        self.db.commit_statement('''select * from playlist_tracks where id = ?''', [id])

        row = self.db.fetchone()
        if row == None:
            raise ValueError('Could not find track with id=%s' % (int(id)))

        id = row['id']
        self.db.commit_statement('''delete from playlist_tracks where id = ?''', [row['id']])
        self.db.commit_statement('''update playlist_tracks set position = position - 1 where playlist_id = ? and position > ?''', [self.id, row['position']])

    def length(self):
        # FIXME this is insane we need to do a real sql count here
        i = 0
        self.db.commit_statement('''select * from playlist_tracks where playlist_id = ?''', [int(self.id)])

        row = self.db.fetchone()

        while row != None:
            i = i + 1
            row = self.db.fetchone()

        return i

if __name__ == '__main__':

    from dogvibes import Dogvibes
    global dogvibes
    dogvibes = Dogvibes()
    