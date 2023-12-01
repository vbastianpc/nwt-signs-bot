
CREATE TABLE "Bible" (
	"VerseId" INTEGER NOT NULL, 
	"BookNumber" INTEGER, 
	"ChapterNumber" INTEGER, 
	"VerseNumber" INTEGER, 
	"IsOmitted" BOOLEAN, 
	PRIMARY KEY ("VerseId"), 
	UNIQUE ("BookNumber", "ChapterNumber", "VerseNumber")
)

;
CREATE TABLE "Language" (
	"LanguageCode" VARCHAR NOT NULL, 
	"LanguageMepsSymbol" VARCHAR NOT NULL, 
	"LanguageName" VARCHAR, 
	"LanguageVernacular" VARCHAR, 
	"RsConfigSymbol" VARCHAR, 
	"LibrarySymbol" VARCHAR, 
	"IsSignLanguage" BOOLEAN, 
	"LanguageScript" VARCHAR, 
	"IsRTL" BOOLEAN, 
	"HasWebContent" BOOLEAN, 
	"IsCounted" BOOLEAN, 
	PRIMARY KEY ("LanguageCode"), 
	UNIQUE ("LanguageMepsSymbol")
)

;
CREATE TABLE "Edition" (
	"EditionId" INTEGER NOT NULL, 
	"LanguageCode" INTEGER NOT NULL, 
	"Name" VARCHAR, 
	"SymbolEdition" VARCHAR, 
	"URL" VARCHAR, 
	PRIMARY KEY ("EditionId"), 
	FOREIGN KEY("LanguageCode") REFERENCES "Language" ("LanguageCode"), 
	UNIQUE ("LanguageCode", "SymbolEdition")
)

;
CREATE TABLE "User" (
	"UserId" INTEGER NOT NULL, 
	"TelegramUserId" INTEGER NOT NULL, 
	"FirstName" VARCHAR, 
	"LastName" VARCHAR, 
	"UserName" VARCHAR, 
	"IsPremium" BOOLEAN, 
	"SignLanguageCode" INTEGER, 
	"SignLanguageCode2" INTEGER, 
	"SignLanguageCode3" INTEGER, 
	"BotLanguageCode" INTEGER, 
	"OverlayLanguageCode" INTEGER, 
	"SignLanguageName" VARCHAR, 
	"Status" INTEGER, 
	"AddedDatetime" DATETIME, 
	"LastActiveDatetime" DATETIME, 
	"Delogo" BOOLEAN, 
	PRIMARY KEY ("UserId"), 
	FOREIGN KEY("SignLanguageCode") REFERENCES "Language" ("LanguageCode"), 
	FOREIGN KEY("SignLanguageCode2") REFERENCES "Language" ("LanguageCode"), 
	FOREIGN KEY("SignLanguageCode3") REFERENCES "Language" ("LanguageCode"), 
	FOREIGN KEY("BotLanguageCode") REFERENCES "Language" ("LanguageCode"), 
	FOREIGN KEY("OverlayLanguageCode") REFERENCES "Language" ("LanguageCode"), 
	UNIQUE ("TelegramUserId")
)

;
CREATE TABLE "Book" (
	"BookId" INTEGER NOT NULL, 
	"EditionId" INTEGER NOT NULL, 
	"BookNumber" INTEGER, 
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
	"FileSize" INTEGER, 
	"Duration" INTEGER, 
	"Citation" VARCHAR, 
	"RawVerseNumbers" VARCHAR, 
	"CountVerses" INTEGER, 
	"AddedDatetime" DATETIME, 
	"OverlayLanguageCode" INTEGER, 
	"IsDeprecated" BOOLEAN, 
	"Delogo" BOOLEAN, 
	PRIMARY KEY ("FileId"), 
	FOREIGN KEY("ChapterId") REFERENCES "Chapter" ("ChapterId"), 
	FOREIGN KEY("OverlayLanguageCode") REFERENCES "Language" ("LanguageCode"), 
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