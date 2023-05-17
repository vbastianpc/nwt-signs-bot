# https://github.com/sqlalchemy/sqlalchemy/wiki/Views
# I don't have idea how implement create views by sqlalchemy. So

views = '''
CREATE VIEW IF NOT EXISTS ViewBooks AS
SELECT
    Book.BookId,
    Language.LanguageId,
    Language.LanguageCode,
    Language.LanguageMepsSymbol,
    Book.BookNumber,
    Book.StandardName
FROM
    Book
INNER JOIN Language ON Language.LanguageId = Edition.LanguageId
INNER JOIN Edition ON Edition.EditionId = Book.EditionId
;

CREATE VIEW IF NOT EXISTS "ViewPubMedia" AS
SELECT
    Chapter.ChapterId,
    Language.LanguageMepsSymbol,
    Language.LanguageCode,
    Edition.SymbolEdition,
    Book.BookNumber,
    Book.StandardName || " " || Chapter.ChapterNumber AS Chapter,
    Chapter.URL,
    count(VideoMarker.VideoMarkerId) AS CountVideoMarkers,
    Chapter.Checksum
FROM
    Chapter
LEFT JOIN VideoMarker ON VideoMarker.ChapterId = Chapter.ChapterId
INNER JOIN Book ON Book.BookId = Chapter.BookId
INNER JOIN Edition ON Edition.EditionId = Book.EditionId
INNER JOIN Language ON Language.LanguageId = Edition.LanguageId
GROUP BY Chapter.ChapterId
ORDER BY
    Language.LanguageCode ASC,
    Book.BookNumber ASC,
    Chapter.ChapterNumber ASC
;

CREATE VIEW IF NOT EXISTS ViewEdition AS
SELECT
	Language.LanguageId,
	Edition.EditionId,
	Language.LanguageCode,
	Language.LanguageMepsSymbol AS MepsSymbol,
	Language.LanguageName,
	Edition.SymbolEdition AS Pub,
	Edition.Name,
	Edition.URL
FROM Language
LEFT JOIN Edition ON Language.LanguageId = Edition.LanguageId
;

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
;

CREATE VIEW IF NOT EXISTS "ViewCountVerseHistoricByUser" AS
SELECT
    User.TelegramUserId,
    User.FullName,
    count(*) AS CountSentVersesByUser
FROM File2User
INNER JOIN User ON User.UserId = File2User.UserId
GROUP BY User.UserId
ORDER BY User.TelegramUserId ASC
;

CREATE VIEW IF NOT EXISTS "ViewCountVerseHistoricByLang" AS
SELECT
	Language.LanguageCode,
	Book.StandardName || " " || Chapter.ChapterNumber || ":" || File.RawVerseNumbers AS Verse,
	count(*) AS CountVerseHistoricByLang
FROM File2User
INNER JOIN File ON File.FileId = File2User.FileId
INNER JOIN Chapter ON Chapter.ChapterId = File.ChapterId
INNER JOIN Book ON Book.BookId = Chapter.BookId
INNER JOIN Edition ON Edition.EditionId = Book.EditionId
INNER JOIN Language ON Language.LanguageId = Edition.LanguageId
GROUP BY Language.LanguageCode, Book.BookNumber, Chapter.ChapterNumber , File.RawVerseNumbers
ORDER BY Book.BookNumber ASC, Chapter.ChapterNumber ASC, File.RawVerseNumbers ASC
;

CREATE VIEW IF NOT EXISTS "ViewUser" AS
SELECT
    User.TelegramUserId,
	(CASE
		WHEN User.Status = 1 THEN "Allowed"
		WHEN User.Status = 0 THEN "Waiting"
		WHEN User.Status = -1 THEN "Banned"
		ELSE "Unknown" END
	) AS Status,
    User.FirstName,
    User.LastName,
    User.UserName,
    SignLanguage.LanguageCode AS SignLanguageCode,
	BotLanguage.LanguageCode AS BotLanguageCode,
	OverlayLanguage.LanguageCode AS OverlayLanguageCode
FROM User
LEFT JOIN Language AS SignLanguage ON SignLanguage.LanguageId = User.SignLanguageId
LEFT JOIN Language AS BotLanguage ON BotLanguage.LanguageId = User.BotLanguageId
LEFT JOIN Language AS OverlayLanguage ON OverlayLanguage.LanguageId = User.OverlayLanguageId
;

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
INNER JOIN Edition ON Edition.EditionId = Book.EditionId
INNER JOIN Language ON Language.LanguageId = Edition.LanguageId
LEFT JOIN Language AS OverlayLanguage ON File.OverlayLanguageId = OverlayLanguage.LanguageId
ORDER BY File2User.Datetime DESC
;

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
INNER JOIN Edition ON Edition.EditionId = Book.EditionId
INNER JOIN Language ON Language.LanguageId = Edition.LanguageId
LEFT JOIN Language AS OverlayLanguage ON File.OverlayLanguageId = OverlayLanguage.LanguageId
ORDER BY File.FileId DESC
;'''.split(';')
