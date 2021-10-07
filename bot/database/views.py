from sqlalchemy.sql import text


views = ['''
CREATE VIEW IF NOT EXISTS "ViewPubMedia" AS
SELECT
    BibleBook.BibleBookId,
    BibleChapter.BibleChapterId,
    SignLanguage.LangCode,
    BibleBook.BookNumber,
    BibleBook.BookName,
    BibleChapter.ChapterNumber,
    BibleChapter.Checksum,
    count(*) AS CountVideoMarkers
FROM
    VideoMarker
INNER JOIN BibleChapter ON BibleChapter.BibleChapterId = VideoMarker.BibleChapterId
INNER JOIN BibleBook ON BibleBook.BibleBookId = BibleChapter.BibleBookId
INNER JOIN SignLanguage ON SignLanguage.SignLanguageId = BibleBook.SignLanguageId
GROUP BY BibleChapter.BibleChapterId
ORDER BY
    SignLanguage.LangCode ASC,
    BibleBook.BookNumber ASC,
    BibleChapter.ChapterNumber ASC
;''',
'''
CREATE VIEW IF NOT EXISTS "ViewCountSentVersesByCitation" AS
SELECT
    SentVerse.Citation,
    count(*) AS CountSentVersesByCitation,
    BibleBook.BookNumber,
    BibleBook.BookName,
    SentVerse.ChapterNumber,
    SentVerse.RawVerseNumbers
FROM SentVerseUser
INNER JOIN SentVerse ON SentVerse.SentVerseId = SentVerseUser.SentVerseId
INNER JOIN BibleBook ON BibleBook.BibleBookId = SentVerse.BibleBookId
GROUP BY BibleBook.BookNumber, SentVerse.ChapterNumber, SentVerse.RawVerseNumbers
ORDER BY BibleBook.BookNumber ASC, SentVerse.ChapterNumber ASC, SentVerse.RawVerseNumbers ASC
;''',
'''
CREATE VIEW IF NOT EXISTS "ViewCountSentVersesByUser" AS
SELECT
    User.TelegramUserId,
    User.FullName,
    count(*) AS CountSentVersesByUser
FROM SentVerseUser
INNER JOIN User ON User.UserId = SentVerseUser.UserId
GROUP BY User.UserId
ORDER BY User.TelegramUserId ASC
;''',
'''
CREATE VIEW IF NOT EXISTS "ViewCountSentVerseByLang" AS
SELECT
    SignLanguage.LangCode,
    SignLanguage.Name,
    SignLanguage.Vernacular,
    count(*) AS CountSentVerseByLang,
    Historic.CountSentVerseHistoricByLang
FROM SentVerse
INNER JOIN BibleBook ON BibleBook.BibleBookId = SentVerse.BibleBookId
INNER JOIN SignLanguage ON SignLanguage.SignLanguageId = BibleBook.SignLanguageId
INNER JOIN (
    SELECT
        SignLanguage.SignLanguageId,
        count(*) AS CountSentVerseHistoricByLang
    FROM SentVerseUser
    INNER JOIN SentVerse ON SentVerse.SentVerseId = SentVerseUser.SentVerseId
    INNER JOIN BibleBook ON BibleBook.BibleBookId = SentVerse.BibleBookId
    INNER JOIN SignLanguage ON SignLanguage.SignLanguageId = BibleBook.SignLanguageId
    GROUP BY SignLanguage.SignLanguageId
) AS Historic ON Historic.SignLanguageId = SignLanguage.SignLanguageId
GROUP BY SignLanguage.SignLanguageId
;''',
'''
CREATE VIEW IF NOT EXISTS "ViewUser" AS
SELECT
    User.TelegramUserId,
    User.FullName,
    User.BotLanguage,
    SignLanguage.LangCode,
    SignLanguage.Vernacular
FROM User
INNER JOIN SignLanguage ON SignLanguage.SignLanguageId = User.SignLanguageId
;''',
'''
CREATE VIEW IF NOT EXISTS "ViewSentVerseUser" AS
SELECT
    SentVerseUser.SentVerseUserId,
    User.FullName,
    SentVerse.Citation,
    SignLanguage.LangCode,
    SentVerseUser.Datetime
FROM SentVerseUser
INNER JOIN SentVerse ON SentVerse.SentVerseId = SentVerseUser.SentVerseId
INNER JOIN User ON User.UserId = SentVerseUser.UserId
INNER JOIN BibleBook ON BibleBook.BibleBookId = SentVerse.BibleBookId
INNER JOIN SignLanguage ON SignLanguage.SignLanguageId = BibleBook.SignLanguageId
ORDER BY SentVerseUser.Datetime DESC
;
''',
'''
CREATE VIEW ViewSentVerse AS
SELECT
    SentVerse.SentVerseId,
    SignLanguage.LangCode,
	BibleBook.BookNumber,
	SentVerse.Citation,
	SentVerse.Quality,
	SentVerse.AddedDatetime
FROM SentVerse
INNER JOIN BibleBook ON BibleBook.BibleBookId = SentVerse.BibleBookId
INNER JOIN SignLanguage ON SignLanguage.SignLanguageId = BibleBook.SignLanguageId
ORDER BY SentVerse.SentVerseId DESC
;'''
]

views = [text(view) for view in views]
