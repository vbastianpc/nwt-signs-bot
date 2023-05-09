from sqlalchemy.sql import text


views = ['''
CREATE VIEW IF NOT EXISTS "ViewPubMedia" AS
SELECT
    Language.LanguageMepsSymbol,
    Language.LanguageCode,
    Bible.SymbolEdition,
    Book.BookNumber,
    Book.StandardName || " " || Chapter.ChapterNumber AS Chapter,
    count(*) AS CountVideoMarkers,
    Chapter.Checksum
FROM
    VideoMarker
INNER JOIN Chapter ON Chapter.ChapterId = VideoMarker.ChapterId
INNER JOIN Book ON Book.BookId = Chapter.BookId
INNER JOIN Bible ON Bible.BibleId = Book.BibleId
INNER JOIN Language ON Language.LanguageId = Bible.LanguageId
GROUP BY Chapter.ChapterId
ORDER BY
    Language.LanguageCode ASC,
    Book.BookNumber ASC,
    Chapter.ChapterNumber ASC
;''',
'''
CREATE VIEW IF NOT EXISTS "ViewCountVerseHistoricByCitation" AS
SELECT
    Book.BookNumber,
    Book.StandardName || " " || Chapter.ChapterNumber || ":" || File.RawVerseNumbers AS Verse,
    count(*) AS CountVerseHistoricByCitation
FROM File2User
INNER JOIN File ON File.FileId = File2User.FileId
INNER JOIN Chapter ON Chapter.ChapterId = File.ChapterId
INNER JOIN Book ON Book.BookId = Chapter.BookId
GROUP BY Book.BookNumber, Chapter.ChapterNumber, File.RawVerseNumbers
ORDER BY Book.BookNumber ASC, Chapter.ChapterNumber ASC, File.RawVerseNumbers ASC
;''',
'''
CREATE VIEW IF NOT EXISTS "ViewCountVerseHistoricByUser" AS
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
CREATE VIEW IF NOT EXISTS "ViewCountVerseHistoricByLang" AS
SELECT
	Language.LanguageCode,
	Book.StandardName || " " || Chapter.ChapterNumber || ":" || File.RawVerseNumbers AS Verse,
	count(*) AS CountVerseHistoricByLang
FROM File2User
INNER JOIN File ON File.FileId = File2User.FileId
INNER JOIN Chapter ON Chapter.ChapterId = File.ChapterId
INNER JOIN Book ON Book.BookId = Chapter.BookId
INNER JOIN Bible ON Bible.BibleId = Book.BibleId
INNER JOIN Language ON Language.LanguageId = Bible.LanguageId
GROUP BY Language.LanguageCode, Book.BookNumber, Chapter.ChapterNumber , File.RawVerseNumbers
ORDER BY Book.BookNumber ASC, Chapter.ChapterNumber ASC, File.RawVerseNumbers ASC
;''',
'''
CREATE VIEW IF NOT EXISTS "ViewUser" AS
SELECT
    User.TelegramUserId,
	(CASE
		WHEN User.Status = 1 THEN "Allowed"
		WHEN User.Status = 0 THEN "Waiting"
		WHEN User.Status = -1 THEN "Banned"
		ELSE "Unknown" END
	) AS Status,
    User.FullName,
    SignLanguage.LanguageCode AS SignLanguageCode,
	BotLanguage.LanguageCode AS BotLanguageCode,
	OverlayLanguage.LanguageCode AS OverlayLanguageCode
FROM User
LEFT JOIN Language AS SignLanguage ON SignLanguage.LanguageId = User.SignLanguageId
LEFT JOIN Language AS BotLanguage ON BotLanguage.LanguageId = User.BotLanguageId
LEFT JOIN Language AS OverlayLanguage ON OverlayLanguage.LanguageId = User.OverlayLanguageId
;''',
'''
CREATE VIEW IF NOT EXISTS "ViewSentVerseUser" AS
SELECT
	User.TelegramUserId,
    User.FullName,
	Language.LanguageCode,
    OverlayLanguage.LanguageCode AS OverlayLanguageCode,
	Book.StandardName || " " || Chapter.ChapterNumber || ":" || File.RawVerseNumbers AS Verse,
    File2User.Datetime,
    File.FileId
FROM File2User
INNER JOIN File ON File.FileId = File2User.FileId
INNER JOIN User ON User.UserId = File2User.UserId
INNER JOIN Chapter ON Chapter.ChapterId = File.ChapterId
INNER JOIN Book ON Book.BookId = Chapter.BookId
INNER JOIN Bible ON Bible.BibleId = Book.BibleId
INNER JOIN Language ON Language.LanguageId = Bible.LanguageId
LEFT JOIN Language AS OverlayLanguage ON File.OverlayLanguageId = OverlayLanguage.LanguageId
ORDER BY File2User.Datetime DESC
;
''',
'''
CREATE VIEW IF NOT EXISTS "ViewSentVerse" AS
SELECT
    Language.LanguageCode,
	OverlayLanguage.LanguageCode AS OverlayLanguageCode,
	Book.BookNumber,
	Book.StandardName || " " || Chapter.ChapterNumber || ":" || File.RawVerseNumbers AS Verse,
	File.AddedDatetime,
	File.TelegramFileId,
    File.FileId
FROM File
INNER JOIN Chapter ON Chapter.ChapterId = File.ChapterId
INNER JOIN Book ON Book.BookId = Chapter.BookId
INNER JOIN Bible ON Bible.BibleId = Book.BibleId
INNER JOIN Language ON Language.LanguageId = Bible.LanguageId
LEFT JOIN Language AS OverlayLanguage ON File.OverlayLanguageId = OverlayLanguage.LanguageId
ORDER BY File.FileId DESC
;'''
]

views = [text(view) for view in views]
