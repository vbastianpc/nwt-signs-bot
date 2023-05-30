CREATE TABLE "BibleBook" (
	"BibleBookId" INTEGER NOT NULL, 
	"LanguageId" INTEGER NOT NULL, 
	"BookNumber" INTEGER, 
	"BookName" VARCHAR, 
	PRIMARY KEY ("BibleBookId"), 
	UNIQUE ("BookNumber", "LanguageId"), 
	FOREIGN KEY("LanguageId") REFERENCES "Language" ("LanguageId")
);

CREATE TABLE "BibleChapter" (
	"BibleChapterId" INTEGER NOT NULL, 
	"BibleBookId" INTEGER NOT NULL, 
	"ChapterNumber" INTEGER, 
	"Checksum" VARCHAR, 
	PRIMARY KEY ("BibleChapterId"), 
	UNIQUE ("BibleBookId", "ChapterNumber", "Checksum"), 
	FOREIGN KEY("BibleBookId") REFERENCES "BibleBook" ("BibleBookId")
);

CREATE TABLE "BookNamesAbbreviation" (
	"BookNamesAbbreviationId" INTEGER NOT NULL, 
	"LangLocale" VARCHAR, 
	"BookNumber" INTEGER, 
	"BookFullName" VARCHAR, 
	"BookLongAbbreviationName" VARCHAR, 
	"BookAbbreviationName" VARCHAR, 
	PRIMARY KEY ("BookNamesAbbreviationId"), 
	UNIQUE ("LangLocale", "BookNumber")
);

CREATE TABLE "Language" (
	"LanguageId" INTEGER NOT NULL, 
	"LanguageCode" VARCHAR NOT NULL, 
	"LanguageLocale" VARCHAR, 
	"LanguageName" VARCHAR, 
	"LanguageVernacular" VARCHAR, 
	"RsConfigSymbol" VARCHAR, 
	"LibrarySymbol" VARCHAR, IsSignLanguage BOOLEAN, 
	PRIMARY KEY ("LanguageId"), 
	UNIQUE ("LanguageCode"), 
	UNIQUE ("LanguageLocale")
);

CREATE TABLE "SentVerse" (
	"SentVerseId" INTEGER NOT NULL, 
	"BibleBookId" INTEGER NOT NULL, 
	"Checksum" VARCHAR, 
	"ChapterNumber" INTEGER, 
	"RawVerseNumbers" VARCHAR, 
	"Citation" VARCHAR, 
	"Quality" VARCHAR, 
	"TelegramFileId" VARCHAR, 
	"Size" INTEGER, 
	"AddedDatetime" VARCHAR, 
	PRIMARY KEY ("SentVerseId"), 
	FOREIGN KEY("BibleBookId") REFERENCES "BibleBook" ("BibleBookId"), 
	UNIQUE ("TelegramFileId")
);

CREATE TABLE "SentVerseUser" (
	"SentVerseUserId" INTEGER NOT NULL, 
	"SentVerseId" INTEGER NOT NULL, 
	"UserId" INTEGER, 
	"Datetime" VARCHAR, 
	PRIMARY KEY ("SentVerseUserId"), 
	FOREIGN KEY("SentVerseId") REFERENCES "SentVerse" ("SentVerseId"), 
	FOREIGN KEY("UserId") REFERENCES "User" ("UserId")
);

CREATE TABLE "User" (
	"UserId" INTEGER NOT NULL, 
	"TelegramUserId" INTEGER, 
	"LanguageId" INTEGER, 
	"FullName" VARCHAR, 
	"Status" INTEGER, 
	"AddedDatetime" VARCHAR, 
	"BotLanguage" VARCHAR, 
	PRIMARY KEY ("UserId"), 
	UNIQUE ("TelegramUserId"), 
	FOREIGN KEY("LanguageId") REFERENCES "Language" ("LanguageId")
);

CREATE TABLE "VideoMarker" (
	"VideoMarkerId" INTEGER NOT NULL, 
	"BibleChapterId" INTEGER NOT NULL, 
	"Label" VARCHAR, 
	"StartTime" VARCHAR, 
	"Duration" VARCHAR, 
	"VerseNumber" INTEGER, 
	"EndTransitionDuration" VARCHAR, 
	PRIMARY KEY ("VideoMarkerId"), 
	FOREIGN KEY("BibleChapterId") REFERENCES "BibleChapter" ("BibleChapterId")
);

