# scripts/migrate_questions_fixed.py
#!/usr/bin/env python
"""
FIXED HIGH-SPEED migration of questions and related data (handles duplicates)
Run: python scripts/migrate_questions_fixed.py
"""

import sqlite3
import sys
import re
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bibel_project.settings')

import django
django.setup()

from core.models import Language, Level, Book, Chapter, Question, QuestionText, Option, OptionText, Explanation
from django.utils import timezone

SOURCE_DB = Path('/home/efrem/bibel/app/bible_quiz.db')

def migrate_questions_fixed():
    print("=" * 60)
    print("⚡ FIXED HIGH-SPEED QUESTIONS MIGRATION")
    print("=" * 60)
    
    if not SOURCE_DB.exists():
        print(f"❌ Source database not found at {SOURCE_DB}")
        return False
    
    conn = sqlite3.connect(str(SOURCE_DB))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Step 1: Load mappings
    print("\n📥 Loading mappings...")
    
    # Language mapping
    languages = {lang.code: lang.id for lang in Language.objects.all()}
    print(f"  ✅ Languages: {len(languages)}")
    
    # Level mapping
    levels = {level.level_number: level.id for level in Level.objects.all()}
    print(f"  ✅ Levels: {len(levels)}")
    
    # Book mapping
    books = {}
    for book in Book.objects.select_related('testament'):
        books[book.name] = book.id
    print(f"  ✅ Books: {len(books)}")
    
    # Chapter mapping
    chapters = {}
    for chapter in Chapter.objects.select_related('book'):
        key = (chapter.book.name, chapter.chapter_number)
        chapters[key] = chapter.id
    print(f"  ✅ Chapters: {len(chapters)}")
    
    # Step 2: Read questions from source (deduplicate)
    print("\n📚 Reading questions from source...")
    cursor.execute("""
        SELECT DISTINCT 
            q.id, q.correct_option, q.verse_reference,
            b.name as book_name, l.level_number
        FROM questions q
        JOIN books b ON q.book_id = b.id
        LEFT JOIN levels l ON q.level_id = l.id
    """)
    source_questions = cursor.fetchall()
    print(f"  ✅ Found {len(source_questions)} questions")
    
    # Step 3: Read question texts
    print("\n📝 Reading question texts...")
    cursor.execute("""
        SELECT DISTINCT qt.question_id, qt.text, l.code as language_code
        FROM question_texts qt
        JOIN languages l ON qt.language_id = l.id
    """)
    question_texts = defaultdict(list)
    for row in cursor.fetchall():
        question_texts[row['question_id']].append({
            'text': row['text'],
            'language_code': row['language_code']
        })
    print(f"  ✅ Loaded texts for {len(question_texts)} questions")
    
    # Step 4: Read options (deduplicate)
    print("\n🔘 Reading options...")
    cursor.execute("""
        SELECT DISTINCT o.question_id, o.label
        FROM options o
    """)
    options = defaultdict(list)
    for row in cursor.fetchall():
        # Store as set to avoid duplicates
        if row['label'] not in [opt['label'] for opt in options[row['question_id']]]:
            options[row['question_id']].append({
                'label': row['label']
            })
    print(f"  ✅ Loaded options for {len(options)} questions")
    
    # Step 5: Read option texts
    print("\n📄 Reading option texts...")
    cursor.execute("""
        SELECT DISTINCT ot.option_id, ot.text, l.code as language_code
        FROM option_texts ot
        JOIN languages l ON ot.language_id = l.id
    """)
    option_texts = defaultdict(list)
    for row in cursor.fetchall():
        option_texts[row['option_id']].append({
            'text': row['text'],
            'language_code': row['language_code']
        })
    print(f"  ✅ Loaded texts for {len(option_texts)} options")
    
    # Step 6: Read explanations
    print("\n💡 Reading explanations...")
    cursor.execute("""
        SELECT DISTINCT e.question_id, e.text, l.code as language_code
        FROM explanations e
        JOIN languages l ON e.language_id = l.id
    """)
    explanations = defaultdict(list)
    for row in cursor.fetchall():
        explanations[row['question_id']].append({
            'text': row['text'],
            'language_code': row['language_code']
        })
    print(f"  ✅ Loaded explanations for {len(explanations)} questions")
    
    conn.close()
    
    # Step 7: Clear existing data
    print("\n🗑️ Clearing existing questions data...")
    OptionText.objects.all().delete()
    Option.objects.all().delete()
    QuestionText.objects.all().delete()
    Explanation.objects.all().delete()
    Question.objects.all().delete()
    print("  ✅ Cleared")
    
    # Step 8: Bulk create questions
    print("\n💾 Creating questions...")
    questions_to_create = []
    question_id_map = {}
    
    for sq in source_questions:
        # Get chapter
        chapter_num = 1
        if sq['verse_reference']:
            match = re.search(r'(\d+):', sq['verse_reference'])
            if match:
                chapter_num = int(match.group(1))
        
        chapter_key = (sq['book_name'], chapter_num)
        chapter_id = chapters.get(chapter_key)
        
        if not chapter_id:
            # Try to find or create chapter
            book_id = books.get(sq['book_name'])
            if book_id:
                chapter, created = Chapter.objects.get_or_create(
                    book_id=book_id,
                    chapter_number=chapter_num
                )
                chapter_id = chapter.id
                chapters[chapter_key] = chapter_id
        
        book_id = books.get(sq['book_name'])
        level_id = levels.get(sq['level_number'] or 1)
        if not level_id:
            level_id = list(levels.values())[0] if levels else None
        
        if book_id and chapter_id and level_id:
            questions_to_create.append(Question(
                book_id=book_id,
                chapter_id=chapter_id,
                level_id=level_id,
                correct_option=sq['correct_option'],
                verse_reference=sq['verse_reference'] or '',
                created_at=timezone.now()
            ))
    
    # Bulk insert questions
    if questions_to_create:
        Question.objects.bulk_create(questions_to_create)
        
        # Get the created questions with their IDs
        created_questions = list(Question.objects.order_by('id'))
        question_id_map = {src_q['id']: created_questions[i].id 
                          for i, src_q in enumerate(source_questions) 
                          if i < len(created_questions)}
    
    print(f"  ✅ Created {len(questions_to_create)} questions")
    
    # Step 9: Bulk create question texts
    print("\n📝 Creating question texts...")
    question_texts_to_create = []
    
    for src_q_id, texts in question_texts.items():
        target_q_id = question_id_map.get(src_q_id)
        if not target_q_id:
            continue
        
        for text_data in texts:
            lang_id = languages.get(text_data['language_code'])
            if lang_id:
                question_texts_to_create.append(QuestionText(
                    question_id=target_q_id,
                    language_id=lang_id,
                    text=text_data['text']
                ))
    
    if question_texts_to_create:
        QuestionText.objects.bulk_create(question_texts_to_create, ignore_conflicts=True)
    print(f"  ✅ Created {len(question_texts_to_create)} question texts")
    
    # Step 10: Create options individually (to handle duplicates)
    print("\n🔘 Creating options...")
    options_created = 0
    option_id_map = {}
    
    for src_q_id, opts in options.items():
        target_q_id = question_id_map.get(src_q_id)
        if not target_q_id:
            continue
        
        for opt_data in opts:
            # Use get_or_create to avoid duplicates
            option, created = Option.objects.get_or_create(
                question_id=target_q_id,
                label=opt_data['label']
            )
            if created:
                options_created += 1
            # Store mapping with a unique key
            key = (src_q_id, opt_data['label'])
            option_id_map[key] = option.id
    
    print(f"  ✅ Created {options_created} options (total: {Option.objects.count()})")
    
    # Step 11: Create option texts
    print("\n📄 Creating option texts...")
    option_texts_created = 0
    
    # Get mapping from source option_id to target option
    # First, get all options from source to map
    cursor = sqlite3.connect(str(SOURCE_DB))
    cursor.row_factory = sqlite3.Row
    cursor2 = cursor.cursor()
    
    cursor2.execute("""
        SELECT DISTINCT o.id, o.question_id, o.label
        FROM options o
    """)
    source_options = cursor2.fetchall()
    
    # Build mapping from source option_id to target option
    source_to_target_option = {}
    for src_opt in source_options:
        target_q_id = question_id_map.get(src_opt['question_id'])
        if target_q_id:
            key = (src_opt['question_id'], src_opt['label'])
            target_opt_id = option_id_map.get(key)
            if target_opt_id:
                source_to_target_option[src_opt['id']] = target_opt_id
    
    cursor2.close()
    
    # Now create option texts
    for src_opt_id, texts in option_texts.items():
        target_opt_id = source_to_target_option.get(src_opt_id)
        if not target_opt_id:
            continue
        
        for text_data in texts:
            lang_id = languages.get(text_data['language_code'])
            if lang_id:
                obj, created = OptionText.objects.get_or_create(
                    option_id=target_opt_id,
                    language_id=lang_id,
                    defaults={'text': text_data['text']}
                )
                if created:
                    option_texts_created += 1
    
    print(f"  ✅ Created {option_texts_created} option texts (total: {OptionText.objects.count()})")
    
    # Step 12: Create explanations
    print("\n💡 Creating explanations...")
    explanations_created = 0
    
    for src_q_id, texts in explanations.items():
        target_q_id = question_id_map.get(src_q_id)
        if not target_q_id:
            continue
        
        for text_data in texts:
            lang_id = languages.get(text_data['language_code'])
            if lang_id:
                obj, created = Explanation.objects.get_or_create(
                    question_id=target_q_id,
                    language_id=lang_id,
                    defaults={'text': text_data['text']}
                )
                if created:
                    explanations_created += 1
    
    print(f"  ✅ Created {explanations_created} explanations (total: {Explanation.objects.count()})")
    
    cursor.close()
    
    # Step 13: Show results
    print("\n" + "=" * 60)
    print("📊 MIGRATION RESULTS")
    print("=" * 60)
    print(f"  Questions: {Question.objects.count()}")
    print(f"  Question Texts: {QuestionText.objects.count()}")
    print(f"  Options: {Option.objects.count()}")
    print(f"  Option Texts: {OptionText.objects.count()}")
    print(f"  Explanations: {Explanation.objects.count()}")
    
    print("\n✅ FIXED HIGH-SPEED QUESTIONS MIGRATION COMPLETE!")
    return True

if __name__ == "__main__":
    print("\n⚠️  FIXED QUESTIONS MIGRATION TOOL")
    print("This will migrate questions, options, and explanations (handles duplicates)")
    
    response = input("\nContinue? (yes/no): ")
    if response.lower() == 'yes':
        migrate_questions_fixed()
        
        print("\n📌 Next steps:")
        print("1. Run: python manage.py runserver 8009")
        print("2. Test: curl http://127.0.0.1:8009/api/bible/languages")
        print("3. Test: curl 'http://127.0.0.1:8009/api/bible/books/by-language?language=en'")
    else:
        print("Cancelled.")