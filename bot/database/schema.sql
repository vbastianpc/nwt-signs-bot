
CREATE TABLE "Language" (
	"LanguageId" INTEGER NOT NULL, 
	"LanguageCode" VARCHAR NOT NULL, 
	"LanguageLocale" VARCHAR NOT NULL, 
	"LanguageName" VARCHAR, 
	"LanguageVernacular" VARCHAR, 
	"RsConfigSymbol" VARCHAR, 
	"LibrarySymbol" VARCHAR, 
	"IsSignLanguage" BOOLEAN, 
	PRIMARY KEY ("LanguageId"), 
	UNIQUE ("LanguageCode"), 
	UNIQUE ("LanguageLocale")
)

;
CREATE TABLE "Bible" (
	"BibleId" INTEGER NOT NULL, 
	"LanguageId" INTEGER NOT NULL, 
	"BookCount" INTEGER, 
	"Name" VARCHAR, 
	"Abbreviation" VARCHAR, 
	"URL" VARCHAR, 
	PRIMARY KEY ("BibleId"), 
	FOREIGN KEY("LanguageId") REFERENCES "Language" ("LanguageId"), 
	UNIQUE ("LanguageId")
)

;
CREATE TABLE "User" (
	"UserId" INTEGER NOT NULL, 
	"TelegramUserId" INTEGER, 
	"FullName" VARCHAR, 
	"SignLanguageId" INTEGER, 
	"BotLanguageId" INTEGER, 
	"OverlayLanguageId" INTEGER, 
	"Status" INTEGER, 
	"AddedDatetime" VARCHAR, 
	PRIMARY KEY ("UserId"), 
	FOREIGN KEY("SignLanguageId") REFERENCES "Language" ("LanguageId"), 
	FOREIGN KEY("BotLanguageId") REFERENCES "Language" ("LanguageId"), 
	FOREIGN KEY("OverlayLanguageId") REFERENCES "Language" ("LanguageId"), 
	UNIQUE ("TelegramUserId")
)

;
CREATE TABLE "Book" (
	"BookId" INTEGER NOT NULL, 
	"BibleId" INTEGER NOT NULL, 
	"BookNumber" INTEGER, 
	"ChapterCount" INTEGER, 
	"StandardName" VARCHAR, 
	"StandardAbbreviation" VARCHAR, 
	"OfficialAbbreviation" VARCHAR, 
	"StandardSingularBookName" VARCHAR, 
	"StandardSingularAbbreviation" VARCHAR, 
	"OfficialSingularAbbreviation" VARCHAR, 
	"StandardPluralBookName" VARCHAR, 
	"StandardPluralAbbreviation" VARCHAR, 
	"OfficialPluralAbbreviation" VARCHAR, 
	"BookDisplayTitle" VARCHAR, 
	"ChapterDisplayTitle" VARCHAR, 
	PRIMARY KEY ("BookId"), 
	FOREIGN KEY("BibleId") REFERENCES "Bible" ("BibleId"), 
	UNIQUE ("BookNumber", "BibleId")
)

;
CREATE TABLE "Chapter" (
	"ChapterId" INTEGER NOT NULL, 
	"BookId" INTEGER NOT NULL, 
	"ChapterNumber" INTEGER, 
	"Checksum" VARCHAR, 
	"ModifiedDatetime" VARCHAR, 
	"URL" VARCHAR, 
	"Title" VARCHAR, 
	PRIMARY KEY ("ChapterId"), 
	FOREIGN KEY("BookId") REFERENCES "Book" ("BookId"), 
	UNIQUE ("BookId", "ChapterNumber", "Checksum")
)

;
CREATE TABLE "File" (
	"FileId" INTEGER NOT NULL, 
	"ChapterId" INTEGER NOT NULL, 
	"TelegramFileId" VARCHAR, 
	"TelegramFileUniqueId" VARCHAR, 
	"Duration" INTEGER, 
	"FileName" VARCHAR, 
	"RawVerseNumbers" VARCHAR, 
	"FileSize" INTEGER, 
	"AddedDatetime" VARCHAR, 
	"OverlayLanguageId" INTEGER, 
	PRIMARY KEY ("FileId"), 
	FOREIGN KEY("ChapterId") REFERENCES "Chapter" ("ChapterId"), 
	FOREIGN KEY("OverlayLanguageId") REFERENCES "Language" ("LanguageId"), 
	UNIQUE ("TelegramFileId"), 
	UNIQUE ("TelegramFileUniqueId")
)

;
CREATE TABLE "VideoMarker" (
	"VideoMarkerId" INTEGER NOT NULL, 
	"ChapterId" INTEGER NOT NULL, 
	"Label" VARCHAR, 
	"StartTime" VARCHAR, 
	"Duration" VARCHAR, 
	"VerseNumber" INTEGER, 
	"EndTransitionDuration" VARCHAR, 
	PRIMARY KEY ("VideoMarkerId"), 
	FOREIGN KEY("ChapterId") REFERENCES "Chapter" ("ChapterId")
)

;
CREATE TABLE "File2User" (
	"File2UserId" INTEGER NOT NULL, 
	"FileId" INTEGER NOT NULL, 
	"UserId" INTEGER NOT NULL, 
	"Datetime" VARCHAR, 
	PRIMARY KEY ("File2UserId"), 
	FOREIGN KEY("FileId") REFERENCES "File" ("FileId"), 
	FOREIGN KEY("UserId") REFERENCES "User" ("UserId")
)

;