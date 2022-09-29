import sqlite3
import os
import shutil
import uuid
from PIL import Image
from pyffmpeg import FFmpeg
from File import File
import hashlib

def static(path):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), path)

def init(cfg):
    '''
        Copy exmaple config to ~ if not exists, init cfg
        Create database and folders if not exists
        Set global variables
    '''

    cfgFile = os.path.realpath(os.path.expanduser('~/.tagserver.cfg'))
    if not os.path.exists(cfgFile):
        shutil.copy(static('.tagserver.cfg'), cfgFile)
    cfg.read(cfgFile)

    global imgDir, thumbDir, dbFile, imgExtensions, videoExtensions, maxThumbSize, orderTags, itemsOnPage
    storage = os.path.realpath(os.path.expanduser(cfg['File System']['storage']))
    imgDir = os.path.join(storage, 'img')
    thumbDir = os.path.join(storage, 'thumb')
    dbFile = os.path.join(storage, 'main.db')
    imgExtensions = cfg['Files']['image extensions'].split()
    videoExtensions = cfg['Files']['video extensions'].split()
    maxThumbSize = tuple(map(int, cfg['Files']['thumb size'].split('x')))
    orderTags = cfg['Files']['order tags'].split()
    itemsOnPage = int(cfg['Interface']['items on page'])

    firstRun = not os.path.exists(storage)

    if firstRun:
        os.makedirs(storage)
        os.makedirs(imgDir)
        os.makedirs(thumbDir)

    with sqlite3.connect(dbFile) as con:
        if firstRun:
            with open(static('schema.sql'), 'r') as f:
                con.executescript(f.read())
            con.commit()

def isVideo(filename):
    return os.path.splitext(filename)[1].lower() in videoExtensions

def saveThumb(imgFilename, thumbFilename):
    if isVideo(imgFilename):
        FFmpeg().convert(imgFilename, thumbFilename)
    else:
        image = Image.open(imgFilename)
        image.thumbnail(maxThumbSize)
        image = image.convert('RGB')
        image.save(thumbFilename)

def saveFile(file, tags):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext in imgExtensions + videoExtensions:
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

def formWhereSection(tags):
    '''
        Returns (where section string, params tuple)
    '''

    includeTags = []
    excludeTags = []
    for tag in tags:
        if tag[0] == '-':
            excludeTags.append(tag[1:])
        else:
            includeTags.append(tag)

    query = '''
        WHERE TRUE
          AND {includeWhere}
          AND {excludeWhere}
    '''
    queryParams = ()

    # include where section
    if includeTags:
        query = query.replace('{includeWhere}', '''
            id IN(
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
        '''.format(','.join(['?'] * len(includeTags))))
        queryParams += tuple(includeTags) + (len(includeTags),)
    else:
        query = query.replace('{includeWhere}', 'TRUE')

    # exclude where section
    query = query.replace('{excludeWhere}', '''
        id NOT IN (
            SELECT fileId
            FROM fileTags
            WHERE tagId IN (
                SELECT id
                FROM tags
                WHERE name IN ({})
            )
        )
    '''.format(','.join(['?'] * len(excludeTags))));
    queryParams += tuple(excludeTags)

    return (query, queryParams)

def getFiles(tags, page=None):
    with sqlite3.connect(dbFile) as con:
        cur = con.cursor()

        query = '''
            SELECT *
            FROM files
            {whereSection}
            {order}
            {limit}
        '''
        queryParams = ()

        # where section
        whereSection, whereSectionParams = formWhereSection(tags)
        query = query.replace('{whereSection}', whereSection)
        queryParams += whereSectionParams

        # order sectinon
        query = query.replace('{order}', '''
            ORDER BY (
                CASE
                WHEN id IN (
                    SELECT DISTINCT fileId
                    FROM fileTags
                    WHERE tagId IN (
                        SELECT id
                        FROM tags
                        WHERE name in ({})
                    )
                ) THEN id
                ELSE -id
                END
            )
            '''.format(','.join(['?'] * len(orderTags))))
        queryParams += tuple(orderTags)

        # limit section
        if page is not None:
            query = query.replace('{limit}', '''
            LIMIT ?
            OFFSET ?
            ''')
            queryParams += (itemsOnPage, page * itemsOnPage)
        else:
            query = query.replace('{limit}', '')

        cur.execute(query, queryParams)

        return list(map(lambda f: File(*f), cur.fetchall()))

def countPages(tags):
    with sqlite3.connect(dbFile) as con:
        cur = con.cursor()

        whereSection, whereSectionParams = formWhereSection(tags)

        cur.execute('''
            SELECT COUNT(*)
            FROM files
            {}
        '''.format(whereSection), whereSectionParams)

        return (int(cur.fetchone()[0]) + itemsOnPage - 1) // itemsOnPage

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

            con.execute('''
                DELETE
                FROM tags
                WHERE id NOT IN (
                    SELECT DISTINCT tagId
                    FROM fileTags
                )
            ''')

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

def addUser(user, password):
    with sqlite3.connect(dbFile) as con:
        con.execute('''
            INSERT
            INTO users
            VALUES (?, ?)
        ''', (user, hashPassword(password)))

def deleteFile(idx):
    file = getFile(idx)

    os.remove(os.path.join(imgDir, file.imgFilename))
    os.remove(os.path.join(thumbDir, file.thumbFilename))

    with sqlite3.connect(dbFile) as con:
        con.execute('''
            DELETE
            FROM files
            WHERE id = ?
        ''', (file.idx,))

        con.execute('''
            DELETE
            FROM fileTags
            WHERE fileId = ?
        ''', (file.idx,))

        con.execute('''
            DELETE
            FROM tags
            WHERE id NOT IN (
                SELECT DISTINCT tagId
                FROM fileTags
            )
        ''')

def getNeighbours(tags, idx):
    files = getFiles(tags)

    for i in range(len(files)):
        if files[i].idx == idx:
            prevIdx = files[i - 1].idx if i > 0 else None
            nextIdx = files[i + 1].idx if i + 1 < len(files) else None
            return (prevIdx, nextIdx)

    return (None, None)
