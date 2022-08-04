import sqlite3
import os
import shutil
import uuid
from PIL import Image
from File import File
import hashlib

def init(cfg):
    '''
        Copy exmaple config to ~ if not exists, init cfg
        Create database and folders if not exists
        Set global variables
    '''

    cfgFile = os.path.realpath(os.path.expanduser('~/.tagserver.cfg'))
    if not os.path.exists(cfgFile):
        shutil.copy(os.path.realpath('.tagserver.cfg'), cfgFile)
    cfg.read(cfgFile)

    global imgDir, thumbDir, dbFile, imgExtensions, maxThumbSize
    storage = os.path.realpath(os.path.expanduser(cfg['File System']['storage']))
    imgDir = os.path.join(storage, 'img')
    thumbDir = os.path.join(storage, 'thumb')
    dbFile = os.path.join(storage, 'main.db')
    imgExtensions = cfg['Image']['image extensions'].split()
    maxThumbSize = tuple(map(int, cfg['Image']['thumb size'].split('x')))

    firstRun = not os.path.exists(storage)

    if firstRun:
        os.makedirs(storage)
        os.makedirs(imgDir)
        os.makedirs(thumbDir)

    with sqlite3.connect(dbFile) as con:
        if firstRun:
            with open('schema.sql', 'r') as f:
                con.executescript(f.read())
            con.commit()

def saveThumb(imgFilename, thumbFilename):
    image = Image.open(imgFilename)
    image.thumbnail(maxThumbSize)
    image = image.convert('RGB')
    image.save(thumbFilename)

def saveFile(file, tags):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext in imgExtensions:

        # Upload and save
        noExtName = uuid.uuid4().hex
        imgFilename = noExtName + ext
        thumbFilename = noExtName + '.jpg'

        fullImgFilename = os.path.join(imgDir, imgFilename)
        fullThumbFilename = os.path.join(thumbDir, thumbFilename)

        file.save(fullImgFilename)
        saveThumb(fullImgFilename, fullThumbFilename)

        with sqlite3.connect(dbFile) as con:
            cur = con.cursor()

            cur.execute('''
                INSERT INTO files(imgFilename, thumbFilename)
                VALUES (?, ?)
            ''', (imgFilename, thumbFilename))
            fileIdx = cur.lastrowid
            con.commit()

            updateTags(fileIdx, tags)

def getFiles(tags):
    with sqlite3.connect(dbFile) as con:
        cur = con.cursor()

        if tags:
            cur.execute('''
                SELECT *
                FROM files
                WHERE id IN (
                    SELECT fileId
                    FROM fileTags
                    WHERE tagId IN (
                        SELECT id
                        FROM tags
                        WHERE name IN ({})
                    )
                    GROUP BY fileId
                    HAVING COUNT(*) = ?
                )
                '''.format(','.join(['?'] * len(tags))),
                tuple(tags) + (len(tags),))
        else:
            cur.execute('''
                SELECT *
                FROM files;
            ''')

        return list(map(lambda f: File(*f), cur.fetchall()))

def getFile(idx):
    with sqlite3.connect(dbFile) as con:
        cur = con.cursor()

        cur.execute('''
            SELECT *
            FROM files
            WHERE id = ?
        ''', (idx,))

        fileTuple = cur.fetchone()

        return File(*fileTuple)\
            if fileTuple\
            else None

def getTags(idx):
    with sqlite3.connect(dbFile) as con:
        cur = con.cursor()

        cur.execute('''
            SELECT tags.name
            FROM tags, fileTags
            WHERE fileTags.fileId = ?
              AND fileTags.tagId = tags.id
            ORDER BY tags.name
        ''', (idx,))

        return list(map(lambda t: t[0], cur.fetchall()))

def updateTags(idx, tags):
    with sqlite3.connect(dbFile) as con:
        cur = con.cursor()

        con.execute('''
            DELETE
            FROM fileTags
            WHERE fileId = ?
        ''', (idx,))

        for tag in tags:
            try:
                con.execute('''
                    INSERT INTO tags(name)
                    VALUES (?)
                ''', (tag,))
            except sqlite3.IntegrityError: # if tag already exists
                pass

            con.execute('''
                INSERT INTO fileTags(tagId, fileId)
                    SELECT tags.id, files.id
                    FROM tags, files
                    WHERE tags.name = ?
                      AND files.id = ?
            ''', (tag, idx))

def getAllTags():
    with sqlite3.connect(dbFile) as con:
        cur = con.cursor()

        cur.execute('''
            SELECT name
            FROM tags
            ORDER BY name
        ''')

        return list(map(lambda t: t[0], cur.fetchall()))

def checkUser(user, password):
    with sqlite3.connect(dbFile) as con:
        cur = con.cursor()

        cur.execute('''
            SELECT 1
            FROM users
            WHERE user = ?
              AND password = ?
        ''', (user, password))

        return bool(cur.fetchone())

def hashPassword(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()
