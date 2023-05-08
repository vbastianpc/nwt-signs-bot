from sqlalchemy.sql import text


views = ['''
CREATE VIEW IF NOT EXISTS "ViewPubMedia" AS
SELECT
    BibleBook.BibleBookId,
    Chapter.BibleChapterId,
    Language.LanguageCode,
    BibleBook.BookNumber,
    BibleBook.BookName,
    Chapter.ChapterNumber,
    Chapter.Checksum,
    count(*) AS CountVideoMarkers
FROM
    VideoMarker
INNER JOIN Chapter ON Chapter.BibleChapterId = VideoMarker.BibleChapterId
INNER JOIN BibleBook ON BibleBook.BibleBookId = Chapter.BibleBookId
INNER JOIN Language ON Language.LanguageId = BibleBook.LanguageId
GROUP BY Chapter.BibleChapterId
ORDER BY
    Language.LanguageCode ASC,
    BibleBook.BookNumber ASC,
    Chapter.ChapterNumber ASC
;''',
'''
CREATE VIEW IF NOT EXISTS "ViewCountSentVersesByCitation" AS
SELECT
    count(*) AS CountSentVersesByCitation,
    BibleBook.BookNumber,
    BibleBook.BookName,
    File.ChapterNumber,
    File.RawVerseNumbers
FROM File2User
INNER JOIN File ON File.FileId = File2User.FileId
INNER JOIN BibleBook ON BibleBook.BibleBookId = File.BibleBookId
GROUP BY BibleBook.BookNumber, File.ChapterNumber, File.RawVerseNumbers
ORDER BY BibleBook.BookNumber ASC, File.ChapterNumber ASC, File.RawVerseNumbers ASC
;''',
'''
CREATE VIEW IF NOT EXISTS "ViewCountSentVersesByUser" AS
SELECT
    User.TelegramUserId,
    User.FullName,
    count(*) AS CountSentVersesByUser
FROM File2User
INNER JOIN User ON User.UserId = File2User.UserId
GROUP BY User.UserId
ORDER BY User.TelegramUserId ASC
;''',
'''
CREATE VIEW IF NOT EXISTS "ViewCountSentVerseByLang" AS
SELECT
    Language.LanguageCode,
    Language.LanguageName,
    Language.LanguageVernacular,
    count(*) AS CountSentVerseByLang,
    Historic.CountSentVerseHistoricByLang
FROM File
INNER JOIN BibleBook ON BibleBook.BibleBookId = File.BibleBookId
INNER JOIN Language ON Language.LanguageId = BibleBook.LanguageId
INNER JOIN (
    SELECT
        Language.LanguageId,
        count(*) AS CountSentVerseHistoricByLang
    FROM File2User
    INNER JOIN File ON File.FileId = File2User.FileId
    INNER JOIN BibleBook ON BibleBook.BibleBookId = File.BibleBookId
    INNER JOIN Language ON Language.LanguageId = BibleBook.LanguageId
    GROUP BY Language.LanguageId
) AS Historic ON Historic.LanguageId = Language.LanguageId
GROUP BY Language.LanguageId
;''',
'''
CREATE VIEW IF NOT EXISTS "ViewUser" AS
SELECT
    User.TelegramUserId,
    User.FullName,
    User.BotLanguageId,
    Language.LanguageCode,
    Language.LanguageVernacular
FROM User
INNER JOIN Language ON Language.LanguageId = User.LanguageId
;''',
'''
CREATE VIEW IF NOT EXISTS "ViewSentVerseUser" AS
SELECT
    File2User.File2UserId,
    User.FullName,
    Language.LanguageCode,
    File2User.Datetime
FROM File2User
INNER JOIN File ON File.FileId = File2User.FileId
INNER JOIN User ON User.UserId = File2User.UserId
INNER JOIN BibleBook ON BibleBook.BibleBookId = File.BibleBookId
INNER JOIN Language ON Language.LanguageId = BibleBook.LanguageId
ORDER BY File2User.Datetime DESC
;
''',
'''
CREATE VIEW IF NOT EXISTS "ViewSentVerse" AS
SELECT
    File.FileId,
    Language.LanguageCode,
	BibleBook.BookNumber,
	File.Quality,
	File.AddedDatetime
FROM File
INNER JOIN BibleBook ON BibleBook.BibleBookId = File.BibleBookId
INNER JOIN Language ON Language.LanguageId = BibleBook.LanguageId
ORDER BY File.FileId DESC
;'''
]

views = [text(view) for view in views]
