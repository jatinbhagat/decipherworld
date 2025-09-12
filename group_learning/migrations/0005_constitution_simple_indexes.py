# Simple indexes for Constitution Challenge - Production Safe

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('group_learning', '0004_add_visual_elements'),
    ]

    operations = [
        # Simple database indexes using Django's built-in index creation
        migrations.RunSQL(
            """
            -- Basic indexes for Constitution Challenge performance
            CREATE INDEX IF NOT EXISTS idx_constitution_team_session ON group_learning_constitutionteam (session_id, total_score DESC);
            CREATE INDEX IF NOT EXISTS idx_constitution_question_game ON group_learning_constitutionquestion (game_id, "order");
            CREATE INDEX IF NOT EXISTS idx_constitution_answer_team ON group_learning_constitutionanswer (team_id, created_at DESC);
            """,
            reverse_sql="""
            DROP INDEX IF EXISTS idx_constitution_team_session;
            DROP INDEX IF EXISTS idx_constitution_question_game;
            DROP INDEX IF EXISTS idx_constitution_answer_team;
            """
        ),
    ]