# https://github.com/sqlalchemy/sqlalchemy/wiki/Views
# I don't have idea how implement create views by sqlalchemy. So

views = '''
CREATE VIEW IF NOT EXISTS ViewBooks AS
SELECT
    Book.BookId,
    Language.LanguageCode,
    Language.LanguageMepsSymbol,
    Book.BookNumber,
    Book.StandardName
FROM
    Book
INNER JOIN Language ON Language.LanguageCode = Edition.LanguageCode
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
INNER JOIN Language ON Language.LanguageCode = Edition.LanguageCode
GROUP BY Chapter.ChapterId
ORDER BY
    Language.LanguageCode ASC,
    Book.BookNumber ASC,
    Chapter.ChapterNumber ASC
;

CREATE VIEW IF NOT EXISTS ViewEdition AS
SELECT
	Language.LanguageCode,
	Edition.EditionId,
	Language.LanguageMepsSymbol AS MepsSymbol,
	Language.LanguageName,
	Edition.SymbolEdition AS Pub,
	Edition.Name,
	Edition.URL
FROM Language
LEFT JOIN Edition ON Language.LanguageCode = Edition.LanguageCode
;

CREATE VIEW IF NOT EXISTS "ViewCountVerseHistoricByCitation" AS
SELECT
    Book.BookNumber,
    File.Citation AS Verse,
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
    User.FirstName || " " || User.LastName AS FullName,
    count(*) AS CountSentVersesByUser
FROM File2User
INNER JOIN User ON User.UserId = File2User.UserId
GROUP BY User.UserId
ORDER BY User.TelegramUserId ASC
;

CREATE VIEW IF NOT EXISTS "ViewCountVerseHistoricByLang" AS
SELECT
	Language.LanguageCode,
	File.Citation,
	count(*) AS CountVerseHistoricByLang
FROM File2User
INNER JOIN File ON File.FileId = File2User.FileId
INNER JOIN Chapter ON Chapter.ChapterId = File.ChapterId
INNER JOIN Book ON Book.BookId = Chapter.BookId
INNER JOIN Edition ON Edition.EditionId = Book.EditionId
INNER JOIN Language ON Language.LanguageCode = Edition.LanguageCode
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
LEFT JOIN Language AS SignLanguage ON SignLanguage.LanguageCode = User.SignLanguageCode
LEFT JOIN Language AS BotLanguage ON BotLanguage.LanguageCode = User.BotLanguageCode
LEFT JOIN Language AS OverlayLanguage ON OverlayLanguage.LanguageCode = User.OverlayLanguageCode
;

CREATE VIEW IF NOT EXISTS "ViewFile2User" AS
SELECT
    File2User.File2UserId,
    File.FileId,
	User.TelegramUserId,
    User.FirstName || " " || User.LastName AS FullName,
	Language.LanguageCode,
    OverlayLanguage.LanguageCode AS OverlayLanguageCode,
	File.Citation,
    File.Duration,
    File.FileSize,
    File2User.Datetime,
    File.CountVerses
FROM File2User
INNER JOIN File ON File.FileId = File2User.FileId
INNER JOIN User ON User.UserId = File2User.UserId
INNER JOIN Chapter ON Chapter.ChapterId = File.ChapterId
INNER JOIN Book ON Book.BookId = Chapter.BookId
INNER JOIN Edition ON Edition.EditionId = Book.EditionId
INNER JOIN Language ON Language.LanguageCode = Edition.LanguageCode
LEFT JOIN Language AS OverlayLanguage ON File.OverlayLanguageCode = OverlayLanguage.LanguageCode
ORDER BY File2User.Datetime DESC
;

CREATE VIEW IF NOT EXISTS "ViewFile" AS
SELECT
    File.FileId,
    Language.LanguageCode,
	OverlayLanguage.LanguageCode AS OverlayLanguageCode,
    File.Delogo,
	Book.BookNumber,
	File.Citation,
	File.AddedDatetime,
	File.TelegramFileId,
    File.CountVerses
FROM File
INNER JOIN Chapter ON Chapter.ChapterId = File.ChapterId
INNER JOIN Book ON Book.BookId = Chapter.BookId
INNER JOIN Edition ON Edition.EditionId = Book.EditionId
INNER JOIN Language ON Language.LanguageCode = Edition.LanguageCode
LEFT JOIN Language AS OverlayLanguage ON File.OverlayLanguageCode = OverlayLanguage.LanguageCode
ORDER BY File.FileId DESC
;'''.split(';')
