# Performance optimization indexes for Constitution Challenge

from django.db import migrations, connection


def create_indexes_forward(apps, schema_editor):
    """Create indexes with database-specific syntax"""
    db_vendor = connection.vendor
    
    if db_vendor == 'postgresql':
        # PostgreSQL with GIN indexes for JSON fields
        with connection.cursor() as cursor:
            cursor.execute("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_countrystate_visual_terrain ON group_learning_countrystate USING GIN ((visual_elements->'terrain'));")
            cursor.execute("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_countrystate_visual_buildings ON group_learning_countrystate USING GIN ((visual_elements->'buildings'));")
            cursor.execute("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_countrystate_visual_weather ON group_learning_countrystate USING GIN ((visual_elements->'weather'));")
            cursor.execute("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_constitutionteam_session_score ON group_learning_constitutionteam (session_id, total_score DESC);")
            cursor.execute("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_constitutionteam_completion ON group_learning_constitutionteam (completion_time) WHERE completion_time IS NOT NULL;")
            cursor.execute("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_constitutionquestion_game_order ON group_learning_constitutionquestion (game_id, \"order\");")
            cursor.execute("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_constitutionquestion_category ON group_learning_constitutionquestion (category);")
            cursor.execute("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_constitutionanswer_team_time ON group_learning_constitutionanswer (team_id, created_at DESC);")
            cursor.execute("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_constitutionanswer_question_team ON group_learning_constitutionanswer (question_id, team_id);")
            cursor.execute("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_countrystate_city_level ON group_learning_countrystate (current_city_level);")
            cursor.execute("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_countrystate_governance_scores ON group_learning_countrystate (democracy_score, fairness_score, freedom_score, stability_score);")
    else:
        # SQLite and other databases - basic indexes only
        with connection.cursor() as cursor:
            try:
                cursor.execute("CREATE INDEX idx_constitutionteam_session_score ON group_learning_constitutionteam (session_id, total_score);")
            except Exception:
                pass  # Index might already exist
            try:
                cursor.execute("CREATE INDEX idx_constitutionteam_completion ON group_learning_constitutionteam (completion_time);")
            except Exception:
                pass
            try:
                cursor.execute("CREATE INDEX idx_constitutionquestion_game_order ON group_learning_constitutionquestion (game_id, \"order\");")
            except Exception:
                pass
            try:
                cursor.execute("CREATE INDEX idx_constitutionquestion_category ON group_learning_constitutionquestion (category);")
            except Exception:
                pass
            try:
                cursor.execute("CREATE INDEX idx_constitutionanswer_team_time ON group_learning_constitutionanswer (team_id, created_at);")
            except Exception:
                pass
            try:
                cursor.execute("CREATE INDEX idx_constitutionanswer_question_team ON group_learning_constitutionanswer (question_id, team_id);")
            except Exception:
                pass
            try:
                cursor.execute("CREATE INDEX idx_countrystate_city_level ON group_learning_countrystate (current_city_level);")
            except Exception:
                pass


def drop_indexes_reverse(apps, schema_editor):
    """Drop indexes"""
    with connection.cursor() as cursor:
        indexes = [
            'idx_countrystate_visual_terrain',
            'idx_countrystate_visual_buildings', 
            'idx_countrystate_visual_weather',
            'idx_constitutionteam_session_score',
            'idx_constitutionteam_completion',
            'idx_constitutionquestion_game_order',
            'idx_constitutionquestion_category',
            'idx_constitutionanswer_team_time',
            'idx_constitutionanswer_question_team',
            'idx_countrystate_city_level',
            'idx_countrystate_governance_scores'
        ]
        
        for index in indexes:
            try:
                cursor.execute(f"DROP INDEX {index};")
            except Exception:
                pass  # Index might not exist


class Migration(migrations.Migration):

    dependencies = [
        ('group_learning', '0004_add_visual_elements'),
    ]

    operations = [
        migrations.RunPython(
            create_indexes_forward,
            drop_indexes_reverse,
            atomic=False,  # Required for CONCURRENTLY indexes
        ),
    ]