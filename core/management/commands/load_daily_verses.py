"""
Management command to load pre-curated daily verses into the database.
This command creates 11 categories and links 1,000 Bible verses to them.
"""

from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.db import transaction
from core.models import DailyVerseCategory, DailyVerse, Verse, Book, Chapter

# Mapping of verse reference names to actual database book names
BOOK_NAME_MAP = {
    'Psalm': 'Psalms',  # Handle singular vs plural
    # Add more mappings as needed
}

VERSE_DATA = {
    "Strength & Courage": [
        "Deuteronomy 31:6", "Deuteronomy 31:7", "Deuteronomy 31:8", "Joshua 1:6", "Joshua 1:7", "Joshua 1:9",
        "Joshua 10:25", "1 Chronicles 22:13", "1 Chronicles 28:10", "1 Chronicles 28:20", "Psalm 27:14", "Psalm 31:24",
        "Psalm 138:3", "Isaiah 35:4", "Isaiah 41:10", "Isaiah 41:13", "Isaiah 43:2", "Jeremiah 1:8", "Daniel 10:19",
        "Haggai 2:4", "Zechariah 8:13", "Matthew 14:27", "Mark 6:50", "Luke 12:32", "John 16:33", "Acts 18:9",
        "Acts 23:11", "1 Corinthians 16:13", "2 Corinthians 5:7", "Ephesians 6:10", "Philippians 4:13", "Colossians 1:11",
        "2 Timothy 1:7", "2 Timothy 2:1", "Hebrews 13:6", "1 Peter 5:9", "1 John 4:4", "Revelation 3:21", "Psalm 18:32",
        "Psalm 18:39", "Psalm 27:1", "Psalm 28:7", "Psalm 46:1", "Psalm 46:2", "Psalm 46:3", "Psalm 56:3", "Psalm 56:4",
        "Psalm 112:7", "Psalm 118:6", "Psalm 118:14", "Proverbs 3:5-6", "Proverbs 28:1", "Isaiah 12:2", "Isaiah 25:4",
        "Isaiah 26:3", "Isaiah 40:29", "Isaiah 40:30", "Isaiah 40:31", "Isaiah 41:14", "Isaiah 45:24", "Isaiah 49:5",
        "Isaiah 50:7", "Isaiah 51:7", "Isaiah 54:14", "Jeremiah 17:7", "Joel 3:10", "Nahum 1:7", "Zephaniah 3:17",
        "Matthew 10:28", "Mark 13:11", "Luke 21:19", "John 14:27", "Romans 8:31", "Romans 8:37", "1 Corinthians 4:20",
        "1 Corinthians 10:13", "2 Corinthians 12:9", "Galatians 2:20", "Ephesians 1:19", "Ephesians 3:16", "Ephesians 6:11",
        "Ephesians 6:12", "Ephesians 6:13", "Ephesians 6:14", "Ephesians 6:15", "Ephesians 6:16", "Ephesians 6:17",
        "Ephesians 6:18", "Philippians 1:28", "Philippians 2:14", "Philippians 4:6", "Philippians 4:7", "Colossians 2:5",
        "1 Thessalonians 3:8", "2 Thessalonians 3:3", "Titus 2:15", "Hebrews 10:35", "James 1:12", "1 Peter 4:1", "1 Peter 5:10"
    ],
    "Trust in God": [
        "Psalm 4:5", "Psalm 9:10", "Psalm 20:7", "Psalm 22:4", "Psalm 22:5", "Psalm 25:2", "Psalm 25:20", "Psalm 26:1",
        "Psalm 28:7", "Psalm 31:14", "Psalm 32:10", "Psalm 33:21", "Psalm 34:8", "Psalm 37:3", "Psalm 37:5", "Psalm 37:40",
        "Psalm 40:4", "Psalm 56:3", "Psalm 56:11", "Psalm 62:8", "Psalm 71:1", "Psalm 71:5", "Psalm 84:12", "Psalm 86:2",
        "Psalm 91:2", "Psalm 112:7", "Psalm 115:9", "Psalm 115:10", "Psalm 115:11", "Psalm 118:8", "Psalm 118:9", "Psalm 119:42",
        "Psalm 119:66", "Psalm 125:1", "Psalm 143:8", "Proverbs 3:5", "Proverbs 3:6", "Proverbs 28:25", "Proverbs 29:25",
        "Isaiah 12:2", "Isaiah 26:4", "Isaiah 50:10", "Jeremiah 17:7", "Nahum 1:7", "Daniel 3:28", "Romans 4:18", "Romans 15:13",
        "2 Corinthians 1:9", "Galatians 2:20", "Ephesians 1:12", "Colossians 1:4", "1 Timothy 4:10", "1 Timothy 6:17",
        "Hebrews 2:13", "Hebrews 13:6", "1 Peter 1:21", "1 Peter 3:5", "1 John 3:21", "1 John 4:16", "Psalm 16:1", "Psalm 17:7",
        "Psalm 18:30", "Psalm 19:14", "Psalm 20:5", "Psalm 21:7", "Psalm 22:8", "Psalm 23:4", "Psalm 25:3", "Psalm 25:4",
        "Psalm 25:5", "Psalm 27:14", "Psalm 28:7", "Psalm 31:1", "Psalm 31:6", "Psalm 33:4", "Psalm 33:5", "Psalm 34:22",
        "Psalm 36:7", "Psalm 37:7", "Psalm 39:7", "Psalm 40:3", "Psalm 41:12", "Psalm 42:5", "Psalm 42:11", "Psalm 43:5",
        "Psalm 44:6", "Psalm 49:6", "Psalm 52:8", "Psalm 55:22", "Psalm 57:1", "Psalm 61:4", "Psalm 62:10", "Psalm 64:10",
        "Psalm 65:5", "Psalm 73:28", "Psalm 78:22", "Psalm 84:5", "Psalm 86:7", "Psalm 89:26", "Psalm 94:22", "Psalm 119:8", "Psalm 119:30"
    ],
    "Hope & Future": [
        "Jeremiah 29:11", "Romans 8:24", "Romans 8:25", "Romans 12:12", "Romans 15:4", "Romans 15:13", "1 Corinthians 13:13",
        "2 Corinthians 3:12", "2 Corinthians 4:18", "Galatians 5:5", "Ephesians 1:18", "Ephesians 4:4", "Colossians 1:5",
        "Colossians 1:23", "Colossians 1:27", "1 Thessalonians 1:3", "1 Thessalonians 5:8", "2 Thessalonians 2:16", "1 Timothy 1:1",
        "1 Timothy 4:10", "Titus 1:2", "Titus 2:13", "Titus 3:7", "Hebrews 3:6", "Hebrews 6:11", "Hebrews 6:18", "Hebrews 6:19",
        "Hebrews 7:19", "Hebrews 10:23", "1 Peter 1:3", "1 Peter 1:13", "1 Peter 1:21", "1 Peter 3:15", "1 John 3:3", "Psalm 9:18",
        "Psalm 16:9", "Psalm 31:24", "Psalm 33:18", "Psalm 33:22", "Psalm 38:15", "Psalm 39:7", "Psalm 42:5", "Psalm 42:11",
        "Psalm 43:5", "Psalm 62:5", "Psalm 71:14", "Psalm 119:49", "Psalm 119:74", "Psalm 119:81", "Psalm 119:116", "Psalm 119:147",
        "Psalm 130:5", "Psalm 146:5", "Proverbs 10:28", "Proverbs 11:7", "Proverbs 13:12", "Proverbs 23:18", "Proverbs 24:14",
        "Isaiah 40:31", "Isaiah 49:23", "Lamentations 3:21", "Lamentations 3:24", "Ezekiel 37:11", "Zechariah 9:12", "Acts 2:26",
        "Acts 23:6", "Acts 24:15", "Acts 26:6", "Acts 26:7", "Acts 28:20", "Romans 5:2", "Romans 5:4", "Romans 5:5", "Romans 8:20",
        "Romans 8:21", "Romans 8:22", "Romans 8:23", "Romans 8:24", "Romans 8:25", "2 Corinthians 1:7", "2 Corinthians 1:10",
        "2 Corinthians 8:10", "Ephesians 4:4", "Philippians 1:20", "Colossians 1:5", "1 Thessalonians 2:19", "1 Thessalonians 4:13",
        "1 Thessalonians 5:8", "2 Thessalonians 3:5", "1 Timothy 6:17", "Titus 1:2", "Titus 3:7", "Hebrews 3:6", "Hebrews 6:11",
        "Hebrews 6:18", "Hebrews 6:19", "1 Peter 1:3", "1 Peter 1:21"
    ],
    "God's Love & Care": [
        "Psalm 23:1", "Psalm 23:2", "Psalm 23:3", "Psalm 23:4", "Psalm 23:5", "Psalm 23:6", "Psalm 27:10", "Psalm 33:5", "Psalm 36:5",
        "Psalm 36:7", "Psalm 40:11", "Psalm 42:8", "Psalm 48:9", "Psalm 51:1", "Psalm 59:10", "Psalm 59:17", "Psalm 62:12", "Psalm 63:3",
        "Psalm 66:20", "Psalm 69:16", "Psalm 86:5", "Psalm 86:15", "Psalm 89:1", "Psalm 89:2", "Psalm 90:14", "Psalm 94:18", "Psalm 94:19",
        "Psalm 100:5", "Psalm 103:4", "Psalm 103:8", "Psalm 103:11", "Psalm 103:13", "Psalm 106:1", "Psalm 107:1", "Psalm 108:4",
        "Psalm 116:1", "Psalm 117:2", "Psalm 118:1", "Psalm 118:2", "Psalm 118:3", "Psalm 118:4", "Psalm 119:64", "Psalm 119:76",
        "Psalm 130:7", "Psalm 136:1", "Psalm 136:2", "Psalm 136:3", "Psalm 136:4", "Psalm 136:5", "Psalm 136:6", "Psalm 136:7",
        "Psalm 136:8", "Psalm 136:9", "Psalm 136:10", "Psalm 136:11", "Psalm 136:12", "Psalm 136:13", "Psalm 136:14", "Psalm 136:15",
        "Psalm 136:16", "Psalm 136:17", "Psalm 136:18", "Psalm 136:19", "Psalm 136:20", "Psalm 136:21", "Psalm 136:22", "Psalm 136:23",
        "Psalm 136:24", "Psalm 136:25", "Psalm 136:26", "Psalm 138:8", "Psalm 145:8", "Psalm 145:9", "Psalm 145:17", "Psalm 146:8",
        "Proverbs 3:12", "Isaiah 38:17", "Isaiah 43:4", "Isaiah 49:15", "Isaiah 49:16", "Isaiah 54:10", "Jeremiah 31:3", "Lamentations 3:22",
        "Lamentations 3:23", "Hosea 11:4", "Zephaniah 3:17", "John 3:16", "John 10:11", "John 10:14", "John 15:9", "John 15:13",
        "Romans 5:8", "Romans 8:35", "Romans 8:38", "Romans 8:39", "1 John 3:1", "1 John 4:9", "1 John 4:10", "1 John 4:16"
    ],
    "Faith & Salvation": [
        "John 3:16", "John 3:36", "John 5:24", "John 6:29", "John 6:35", "John 6:40", "John 6:47", "John 7:38", "John 8:12",
        "John 9:35", "John 11:25", "John 11:26", "John 12:46", "John 14:6", "John 20:31", "Acts 4:12", "Acts 10:43", "Acts 13:39",
        "Acts 16:31", "Romans 1:16", "Romans 1:17", "Romans 3:22", "Romans 3:23", "Romans 3:24", "Romans 3:25", "Romans 3:26",
        "Romans 3:27", "Romans 3:28", "Romans 4:3", "Romans 4:5", "Romans 4:9", "Romans 4:11", "Romans 4:13", "Romans 4:16",
        "Romans 4:20", "Romans 4:21", "Romans 4:22", "Romans 4:23", "Romans 4:24", "Romans 5:1", "Romans 5:2", "Romans 5:9",
        "Romans 5:10", "Romans 5:11", "Romans 6:23", "Romans 9:33", "Romans 10:4", "Romans 10:9", "Romans 10:10", "Romans 10:11",
        "Romans 10:13", "1 Corinthians 1:21", "1 Corinthians 12:9", "2 Corinthians 4:13", "2 Corinthians 5:7", "Galatians 2:16",
        "Galatians 2:20", "Galatians 3:11", "Galatians 3:22", "Ephesians 2:8", "Ephesians 2:9", "Philippians 3:9", "Colossians 1:4",
        "1 Timothy 1:16", "2 Timothy 3:15", "Hebrews 4:2", "Hebrews 10:38", "Hebrews 11:1", "Hebrews 11:6", "James 2:14", "James 2:17",
        "James 2:18", "James 2:19", "James 2:20", "James 2:21", "James 2:22", "James 2:23", "James 2:24", "James 2:26", "1 Peter 1:5",
        "1 Peter 1:9", "1 John 5:1", "1 John 5:4", "1 John 5:5", "1 John 5:10", "1 John 5:11", "1 John 5:12", "1 John 5:13",
        "Jude 1:3", "Revelation 2:10", "Revelation 3:20", "Revelation 21:7", "Matthew 9:2", "Matthew 9:22", "Mark 1:15", "Mark 5:34",
        "Mark 10:52", "Luke 7:50", "Luke 8:48", "Luke 17:19"
    ],
    "Encouragement & Peace": [
        "Isaiah 26:3", "John 14:27", "John 16:33", "Romans 5:1", "Romans 14:17", "Romans 15:33", "Romans 16:20", "1 Corinthians 14:33",
        "2 Corinthians 13:11", "Galatians 5:22", "Ephesians 2:14", "Ephesians 2:15", "Ephesians 2:16", "Ephesians 2:17", "Philippians 4:7",
        "Philippians 4:9", "Colossians 3:15", "1 Thessalonians 5:23", "2 Thessalonians 3:16", "Hebrews 12:14", "James 3:18", "1 Peter 5:14",
        "Jude 1:2", "Psalm 4:8", "Psalm 29:11", "Psalm 34:14", "Psalm 37:37", "Psalm 85:8", "Psalm 119:165", "Psalm 122:6", "Psalm 122:7",
        "Psalm 122:8", "Psalm 125:5", "Psalm 128:6", "Proverbs 12:20", "Proverbs 14:30", "Proverbs 16:7", "Isaiah 9:6", "Isaiah 48:18",
        "Isaiah 52:7", "Isaiah 54:13", "Jeremiah 33:6", "Malachi 2:6", "Mark 9:50", "Luke 1:79", "Luke 2:14", "Luke 19:38", "Luke 24:36",
        "Acts 9:31", "Acts 10:36", "Romans 1:7", "Romans 2:10", "Romans 8:6", "1 Corinthians 7:15", "1 Corinthians 16:11", "2 Corinthians 1:2",
        "2 Corinthians 1:3", "2 Corinthians 1:4", "2 Corinthians 1:5", "2 Corinthians 1:6", "2 Corinthians 1:7", "2 Corinthians 1:8",
        "2 Corinthians 1:9", "2 Corinthians 1:10", "2 Corinthians 1:11", "Galatians 6:16", "Ephesians 1:2", "Ephesians 4:3", "Ephesians 6:23",
        "Philippians 1:2", "Philippians 4:6", "Philippians 4:7", "Colossians 1:2", "Colossians 3:15", "1 Thessalonians 1:1", "1 Thessalonians 5:13",
        "2 Thessalonians 1:2", "2 Thessalonians 3:16", "1 Timothy 1:2", "2 Timothy 1:2", "2 Timothy 2:22", "Titus 1:4", "Philemon 1:3",
        "Hebrews 13:20", "James 2:16", "1 Peter 1:2", "2 Peter 1:2", "2 John 1:3", "3 John 1:14", "Revelation 1:4", "Matthew 5:9",
        "Luke 10:5", "Luke 10:6", "John 20:19", "John 20:21", "John 20:26", "Acts 15:33", "Romans 15:13", "2 Corinthians 5:18", "2 Corinthians 5:19"
    ],
    "Strength in Christ": [
        "Philippians 4:13", "2 Corinthians 12:9", "2 Corinthians 12:10", "Ephesians 3:16", "Ephesians 6:10", "Colossians 1:11", "1 Timothy 1:12",
        "2 Timothy 2:1", "2 Timothy 4:17", "Hebrews 11:34", "1 Peter 4:11", "1 Peter 5:10", "Romans 8:37", "Romans 8:11", "Romans 6:14",
        "1 Corinthians 1:24", "1 Corinthians 1:18", "1 Corinthians 1:25", "1 Corinthians 15:57", "2 Corinthians 2:14", "2 Corinthians 3:5",
        "2 Corinthians 4:7", "2 Corinthians 4:16", "2 Corinthians 5:17", "2 Corinthians 9:8", "Galatians 2:20", "Galatians 6:14", "Ephesians 1:19",
        "Ephesians 3:7", "Ephesians 3:20", "Philippians 2:13", "Philippians 3:10", "Philippians 4:11", "Philippians 4:12", "Colossians 1:29",
        "Colossians 2:10", "2 Thessalonians 1:11", "2 Timothy 2:3", "2 Timothy 2:4", "Hebrews 2:18", "Hebrews 4:15", "Hebrews 4:16", "Hebrews 5:7",
        "Hebrews 12:2", "Hebrews 12:3", "Hebrews 12:12", "James 1:4", "1 Peter 5:6", "1 Peter 5:7", "1 John 2:14", "1 John 4:4", "Jude 1:24",
        "Revelation 3:8", "Revelation 12:11", "Psalm 18:1", "Psalm 18:2", "Psalm 18:32", "Psalm 22:19", "Psalm 27:1", "Psalm 28:7", "Psalm 28:8",
        "Psalm 29:11", "Psalm 31:24", "Psalm 46:1", "Psalm 59:17", "Psalm 62:7", "Psalm 68:28", "Psalm 68:35", "Psalm 71:16", "Psalm 73:26",
        "Psalm 81:1", "Psalm 84:5", "Psalm 84:7", "Psalm 86:16", "Psalm 89:17", "Psalm 105:4", "Psalm 118:14", "Psalm 138:3", "Isaiah 12:2",
        "Isaiah 25:4", "Isaiah 33:2", "Isaiah 40:29", "Isaiah 41:10", "Isaiah 45:24", "Isaiah 49:5", "Jeremiah 16:19", "Habakkuk 3:19",
        "Matthew 11:28", "Matthew 11:29", "Matthew 11:30", "Mark 12:30", "Luke 1:35", "Luke 1:37", "Luke 10:27", "John 5:5", "John 15:5",
        "Acts 1:8", "Acts 4:33", "Acts 9:22", "Romans 5:3", "Romans 5:4"
    ],
    "Identity in Christ": [
        "2 Corinthians 5:17", "Galatians 2:20", "Galatians 3:26", "Galatians 3:27", "Galatians 3:28", "Galatians 3:29", "Galatians 4:7",
        "Ephesians 1:3", "Ephesians 1:4", "Ephesians 1:5", "Ephesians 1:6", "Ephesians 1:7", "Ephesians 1:8", "Ephesians 1:9", "Ephesians 1:10",
        "Ephesians 1:11", "Ephesians 1:12", "Ephesians 1:13", "Ephesians 1:14", "Ephesians 1:15", "Ephesians 1:16", "Ephesians 1:17",
        "Ephesians 1:18", "Ephesians 1:19", "Ephesians 1:20", "Ephesians 1:21", "Ephesians 1:22", "Ephesians 1:23", "Ephesians 2:6",
        "Ephesians 2:10", "Ephesians 2:13", "Ephesians 2:19", "Ephesians 3:12", "Ephesians 4:24", "Colossians 1:13", "Colossians 1:14",
        "Colossians 2:9", "Colossians 2:10", "Colossians 3:3", "Colossians 3:4", "Colossians 3:12", "Romans 6:11", "Romans 8:1", "Romans 8:2",
        "Romans 8:14", "Romans 8:15", "Romans 8:16", "Romans 8:17", "Romans 8:18", "Romans 8:19", "Romans 8:20", "Romans 8:21", "Romans 8:22",
        "Romans 8:23", "Romans 8:29", "Romans 8:30", "Romans 8:31", "Romans 8:32", "Romans 8:33", "Romans 8:34", "Romans 8:35", "Romans 8:36",
        "Romans 8:37", "Romans 8:38", "Romans 8:39", "Romans 12:5", "1 Corinthians 6:17", "1 Corinthians 6:19", "1 Corinthians 6:20",
        "1 Corinthians 12:12", "1 Corinthians 12:13", "1 Corinthians 12:14", "1 Corinthians 12:15", "1 Corinthians 12:16", "1 Corinthians 12:17",
        "1 Corinthians 12:18", "1 Corinthians 12:19", "1 Corinthians 12:20", "1 Corinthians 12:21", "1 Corinthians 12:22", "1 Corinthians 12:23",
        "1 Corinthians 12:24", "1 Corinthians 12:25", "1 Corinthians 12:26", "1 Corinthians 12:27", "2 Corinthians 3:18", "2 Corinthians 4:6",
        "2 Corinthians 5:18", "2 Corinthians 5:19", "2 Corinthians 5:20", "2 Corinthians 5:21", "2 Corinthians 6:16", "Philippians 1:1",
        "Philippians 3:20", "Philippians 3:21", "1 Thessalonians 5:5", "2 Timothy 2:11", "1 Peter 2:9", "1 Peter 2:10", "1 John 3:1",
        "1 John 3:2", "1 John 4:17", "Revelation 1:6"
    ],
    "God is with you": [
        "Genesis 28:15", "Exodus 3:12", "Exodus 33:14", "Deuteronomy 20:1", "Deuteronomy 20:4", "Deuteronomy 31:6", "Deuteronomy 31:8",
        "Joshua 1:5", "Joshua 1:9", "Judges 6:12", "1 Samuel 3:19", "1 Kings 8:57", "2 Chronicles 15:2", "2 Chronicles 20:17", "Psalm 16:8",
        "Psalm 23:4", "Psalm 46:7", "Psalm 46:11", "Psalm 73:23", "Psalm 139:7", "Psalm 139:8", "Psalm 139:9", "Psalm 139:10", "Isaiah 41:10",
        "Isaiah 43:2", "Isaiah 43:5", "Jeremiah 1:8", "Jeremiah 15:20", "Jeremiah 30:11", "Ezekiel 34:11", "Daniel 3:25", "Haggai 1:13",
        "Zephaniah 3:17", "Matthew 1:23", "Matthew 11:28", "Matthew 18:20", "Matthew 28:20", "Luke 1:28", "John 10:28", "John 10:29",
        "John 14:16", "John 14:17", "John 14:18", "John 14:23", "John 15:4", "John 15:5", "John 16:32", "Acts 18:10", "Romans 8:31",
        "1 Corinthians 3:16", "2 Corinthians 13:14", "Ephesians 4:6", "Colossians 1:27", "Hebrews 13:5", "1 John 4:12", "1 John 4:13",
        "1 John 4:15", "Revelation 3:20", "Genesis 21:22", "Genesis 26:3", "Genesis 26:24", "Genesis 28:20", "Exodus 14:14", "Leviticus 26:12",
        "Numbers 14:9", "Numbers 23:21", "Deuteronomy 7:21", "Deuteronomy 31:23", "Joshua 3:10", "Joshua 23:10", "Judges 1:22", "Ruth 1:17",
        "1 Samuel 17:37", "1 Samuel 20:13", "2 Samuel 5:10", "1 Kings 1:37", "1 Kings 11:38", "2 Kings 6:16", "1 Chronicles 17:8", "2 Chronicles 32:8",
        "Ezra 7:28", "Nehemiah 6:16", "Job 5:19", "Psalm 3:3", "Psalm 5:12", "Psalm 9:9", "Psalm 18:6", "Psalm 34:17", "Psalm 34:18", "Psalm 37:28",
        "Psalm 42:8", "Psalm 55:22", "Psalm 91:15", "Psalm 94:14", "Psalm 121:5", "Proverbs 14:26", "Isaiah 8:10", "Isaiah 30:21", "Isaiah 58:9",
        "Zechariah 8:23", "Malachi 3:16"
    ],
    "God loves you deeply": [
        "Jeremiah 31:3", "Zephaniah 3:17", "John 3:16", "John 15:9", "John 15:13", "Romans 5:8", "Romans 8:35", "Romans 8:37", "Romans 8:38",
        "Romans 8:39", "1 John 3:1", "1 John 3:16", "1 John 4:9", "1 John 4:10", "1 John 4:16", "1 John 4:19", "Ephesians 2:4", "Ephesians 3:18",
        "Ephesians 3:19", "Psalm 36:7", "Psalm 63:3", "Psalm 86:15", "Psalm 103:8", "Psalm 103:11", "Psalm 103:13", "Psalm 145:8", "Isaiah 54:10",
        "Hosea 11:4", "Hosea 14:4", "Malachi 1:2", "John 10:11", "John 10:14", "John 13:1", "John 13:34", "John 14:21", "John 14:23", "John 16:27",
        "John 17:23", "John 17:26", "Romans 1:7", "Romans 9:25", "2 Corinthians 13:11", "Galatians 2:20", "Ephesians 1:4", "Ephesians 1:5",
        "Ephesians 5:2", "Colossians 3:12", "2 Thessalonians 2:13", "2 Thessalonians 2:16", "Titus 3:4", "1 John 4:7", "1 John 4:8", "1 John 4:11",
        "1 John 4:12", "1 John 4:17", "1 John 4:18", "1 John 4:20", "1 John 4:21", "1 John 5:1", "1 John 5:2", "1 John 5:3", "Jude 1:21",
        "Revelation 1:5", "Revelation 3:9", "Deuteronomy 7:7", "Deuteronomy 7:8", "Deuteronomy 10:15", "1 Kings 10:9", "2 Chronicles 2:11",
        "2 Chronicles 9:8", "Psalm 5:12", "Psalm 25:10", "Psalm 33:5", "Psalm 48:9", "Psalm 51:1", "Psalm 69:13", "Psalm 69:16", "Psalm 89:1",
        "Psalm 89:2", "Psalm 90:14", "Psalm 94:18", "Psalm 100:5", "Psalm 106:1", "Psalm 107:1", "Psalm 108:4", "Psalm 109:26", "Psalm 119:64",
        "Psalm 136:1", "Psalm 136:2", "Psalm 136:3", "Psalm 136:4", "Psalm 136:5", "Psalm 136:6", "Psalm 136:7", "Psalm 136:8", "Psalm 136:9",
        "Psalm 136:10", "Psalm 136:11", "Psalm 136:12", "Psalm 136:13", "Psalm 136:14"
    ],
    "You are chosen and valuable": [
        "Deuteronomy 7:6", "Deuteronomy 14:2", "Isaiah 43:10", "Isaiah 44:1", "Isaiah 44:2", "Isaiah 49:7", "Zechariah 2:12", "Malachi 3:17",
        "Matthew 5:13", "Matthew 5:14", "Luke 12:7", "John 15:16", "Acts 9:15", "Romans 9:11", "Romans 11:5", "Romans 11:7", "1 Corinthians 1:26",
        "1 Corinthians 1:27", "1 Corinthians 1:28", "1 Corinthians 1:29", "1 Corinthians 12:18", "Ephesians 1:4", "Ephesians 2:10", "Colossians 1:12",
        "Colossians 3:12", "1 Thessalonians 1:4", "2 Thessalonians 2:13", "1 Timothy 2:7", "2 Timothy 1:9", "Titus 1:1", "James 2:5", "1 Peter 1:1",
        "1 Peter 1:2", "1 Peter 2:4", "1 Peter 2:5", "1 Peter 2:6", "1 Peter 2:7", "1 Peter 2:8", "1 Peter 2:9", "1 Peter 2:10", "2 Peter 1:10",
        "Revelation 17:14", "Psalm 4:3", "Psalm 65:4", "Psalm 105:6", "Psalm 105:43", "Psalm 106:5", "Psalm 135:4", "Proverbs 12:10", "Isaiah 41:8",
        "Isaiah 41:9", "Isaiah 43:20", "Isaiah 44:7", "Isaiah 45:4", "Isaiah 48:10", "Isaiah 49:5", "Isaiah 51:2", "Isaiah 65:9", "Isaiah 65:15",
        "Isaiah 65:22", "Jeremiah 33:24", "Ezekiel 20:5", "Haggai 2:23", "Zechariah 1:17", "Zechariah 3:2", "Mark 13:20", "Luke 18:7", "John 13:18",
        "John 15:19", "John 17:6", "John 17:9", "John 17:24", "Acts 13:17", "Romans 8:33", "Romans 9:23", "Romans 11:28", "1 Corinthians 1:24",
        "1 Corinthians 7:22", "1 Corinthians 9:27", "1 Corinthians 15:23", "Ephesians 1:11", "Ephesians 3:10", "Colossians 3:12", "1 Thessalonians 5:9",
        "2 Timothy 2:10", "Hebrews 9:15", "James 1:18", "James 2:5", "1 Peter 1:1", "1 Peter 1:2", "1 Peter 2:4", "1 Peter 2:5", "1 Peter 2:9",
        "1 Peter 2:10", "1 Peter 5:13", "2 Peter 1:10", "2 John 1:1", "2 John 1:13", "Revelation 17:14"
    ],
}


class Command(BaseCommand):
    help = "Load pre-curated daily verses into the database"
    
    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Starting to load daily verses...")
        
        # Step 1: Create categories
        categories = {}
        for category_title in VERSE_DATA.keys():
            slug = slugify(category_title)
            category, created = DailyVerseCategory.objects.get_or_create(
                slug=slug,
                defaults={'title': category_title}
            )
            categories[category_title] = category
            status = "Created" if created else "Already exists"
            self.stdout.write(f"  ✓ {status}: {category_title}")
        
        self.stdout.write(self.style.SUCCESS(f"\n✅ All {len(categories)} categories loaded!"))
        
        # Step 2: Load verses
        total_verses_loaded = 0
        total_verses_skipped = 0
        skipped_books = set()
        
        for category_title, verse_refs in VERSE_DATA.items():
            category = categories[category_title]
            self.stdout.write(f"\nLoading {len(verse_refs)} verses for '{category_title}'...")
            
            for verse_ref in verse_refs:
                try:
                    # Parse reference: "Book Chapter:Verse" or "Book Chapter:Verse-EndVerse"
                    parts = verse_ref.split()
                    
                    # Handle books with multiple words (e.g., "1 Chronicles", "2 Corinthians")
                    if len(parts) == 3:  # e.g., ["1", "Chronicles", "22:13"]
                        book_name = f"{parts[0]} {parts[1]}"
                        verse_info = parts[2]
                    elif len(parts) == 2:  # e.g., ["Psalm", "27:14"]
                        book_name = parts[0]
                        verse_info = parts[1]
                    else:
                        total_verses_skipped += 1
                        continue
                    
                    # Apply book name mapping (e.g., Psalm → Psalms)
                    if book_name in BOOK_NAME_MAP:
                        book_name = BOOK_NAME_MAP[book_name]
                    
                    # Parse chapter:verse
                    if ":" in verse_info:
                        chapter_str, verse_str = verse_info.split(":")
                        chapter_num = int(chapter_str)
                        
                        # Handle verse ranges (e.g., "5-6")
                        if "-" in verse_str:
                            verse_num = int(verse_str.split("-")[0])
                        else:
                            verse_num = int(verse_str)
                    else:
                        total_verses_skipped += 1
                        continue
                    
                    # Find verse in database
                    try:
                        book = Book.objects.get(name=book_name)
                        chapter = Chapter.objects.get(book=book, chapter_number=chapter_num)
                        verse = Verse.objects.get(chapter=chapter, verse_number=verse_num)
                        
                        # Create DailyVerse entry
                        daily_verse, created = DailyVerse.objects.get_or_create(
                            category=category,
                            verse=verse
                        )
                        
                        if created:
                            total_verses_loaded += 1
                    
                    except (Book.DoesNotExist, Chapter.DoesNotExist, Verse.DoesNotExist) as e:
                        skipped_books.add(f"{book_name} ('{verse_ref}')")
                        total_verses_skipped += 1
                
                except Exception as e:
                    total_verses_skipped += 1
            
            self.stdout.write(f"  ✓ Processed category: {category_title}")
        
        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Daily verses loaded successfully!\n"
                f"   Total verses loaded: {total_verses_loaded}\n"
                f"   Total verses skipped: {total_verses_skipped}"
            )
        )
        
        if skipped_books and len(skipped_books) <= 20:
            self.stdout.write(
                self.style.WARNING(
                    f"\n⚠️  Books with missing verses (first 20):\n"
                    + "\n".join(f"   - {book}" for book in sorted(list(skipped_books))[:20])
                )
            )
