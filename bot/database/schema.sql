
CREATE TABLE "Bible" (
	"VerseId" INTEGER NOT NULL, 
	"BookNumber" INTEGER, 
	"ChapterNumber" INTEGER, 
	"VerseNumber" INTEGER, 
	"IsApocryphal" BOOLEAN, 
	PRIMARY KEY ("VerseId"), 
	UNIQUE ("BookNumber", "ChapterNumber", "VerseNumber")
)

;
CREATE TABLE "Language" (
	"LanguageId" INTEGER NOT NULL, 
	"LanguageMepsSymbol" VARCHAR NOT NULL, 
	"LanguageCode" VARCHAR NOT NULL, 
	"LanguageName" VARCHAR, 
	"LanguageVernacular" VARCHAR, 
	"RsConfigSymbol" VARCHAR, 
	"LibrarySymbol" VARCHAR, 
	"IsSignLanguage" BOOLEAN, 
	"LanguageScript" VARCHAR, 
	"IsRTL" BOOLEAN, 
	PRIMARY KEY ("LanguageId"), 
	UNIQUE ("LanguageMepsSymbol"), 
	UNIQUE ("LanguageCode")
)

;
CREATE TABLE "Edition" (
	"EditionId" INTEGER NOT NULL, 
	"LanguageId" INTEGER NOT NULL, 
	"Name" VARCHAR, 
	"SymbolEdition" VARCHAR, 
	"URL" VARCHAR, 
	PRIMARY KEY ("EditionId"), 
	FOREIGN KEY("LanguageId") REFERENCES "Language" ("LanguageId"), 
	UNIQUE ("LanguageId", "SymbolEdition")
)

;
CREATE TABLE "User" (
	"UserId" INTEGER NOT NULL, 
	"TelegramUserId" INTEGER NOT NULL, 
	"FirstName" VARCHAR, 
	"LastName" VARCHAR, 
	"UserName" VARCHAR, 
	"IsPremium" BOOLEAN, 
	"SignLanguageId" INTEGER, 
	"BotLanguageId" INTEGER, 
	"OverlayLanguageId" INTEGER, 
	"Status" INTEGER, 
	"AddedDatetime" DATETIME, 
	"LastActiveDatetime" DATETIME, 
	PRIMARY KEY ("UserId"), 
	FOREIGN KEY("SignLanguageId") REFERENCES "Language" ("LanguageId"), 
	FOREIGN KEY("BotLanguageId") REFERENCES "Language" ("LanguageId"), 
	FOREIGN KEY("OverlayLanguageId") REFERENCES "Language" ("LanguageId"), 
	UNIQUE ("TelegramUserId")
)

;
CREATE TABLE "Book" (
	"BookId" INTEGER NOT NULL, 
	"EditionId" INTEGER NOT NULL, 
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
	"RefreshedOnDate" DATETIME, 
	"BookDisplayTitle" VARCHAR, 
	"ChapterDisplayTitle" VARCHAR, 
	PRIMARY KEY ("BookId"), 
	FOREIGN KEY("EditionId") REFERENCES "Edition" ("EditionId"), 
	UNIQUE ("BookNumber", "EditionId")
)

;
CREATE TABLE "Chapter" (
	"ChapterId" INTEGER NOT NULL, 
	"BookId" INTEGER NOT NULL, 
	"ChapterNumber" INTEGER, 
	"Checksum" VARCHAR, 
	"ModifiedDatetime" DATETIME, 
	"URL" VARCHAR, 
	PRIMARY KEY ("ChapterId"), 
	FOREIGN KEY("BookId") REFERENCES "Book" ("BookId"), 
	UNIQUE ("BookId", "ChapterNumber")
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
	"IsSingleVerse" BOOLEAN, 
	"FileSize" INTEGER, 
	"AddedDatetime" DATETIME, 
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
	"VerseId" INTEGER NOT NULL, 
	"VerseNumber" INTEGER, 
	"Label" VARCHAR, 
	"Duration" VARCHAR, 
	"StartTime" VARCHAR, 
	"EndTransitionDuration" VARCHAR, 
	PRIMARY KEY ("VideoMarkerId"), 
	FOREIGN KEY("ChapterId") REFERENCES "Chapter" ("ChapterId"), 
	FOREIGN KEY("VerseId") REFERENCES "Bible" ("VerseId")
)

;
CREATE TABLE "File2User" (
	"File2UserId" INTEGER NOT NULL, 
	"FileId" INTEGER NOT NULL, 
	"UserId" INTEGER NOT NULL, 
	"Datetime" DATETIME, 
	PRIMARY KEY ("File2UserId"), 
	FOREIGN KEY("FileId") REFERENCES "File" ("FileId"), 
	FOREIGN KEY("UserId") REFERENCES "User" ("UserId")
)

;