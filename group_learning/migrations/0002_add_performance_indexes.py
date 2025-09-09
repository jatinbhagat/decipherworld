# Generated manually for performance optimization

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('group_learning', '0001_initial'),
    ]

    operations = [
        # Index for session lookups by code (most frequent query)
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_gamesession_code ON group_learning_gamesession(session_code);"
        ),
        
        # Index for active games and scenarios
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_game_active ON group_learning_game(is_active) WHERE is_active = true;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_scenario_active_order ON group_learning_scenario(is_active, \"order\") WHERE is_active = true;"
        ),
        
        # Index for player actions by session and player
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_playeraction_session_player ON group_learning_playeraction(session_id, player_session_id);"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_playeraction_session_time ON group_learning_playeraction(session_id, decision_time);"
        ),
        
        # Index for reflections by session
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_reflection_session ON group_learning_reflectionresponse(session_id, created_at);"
        ),
        
        # Index for roles by activity status
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_role_active ON group_learning_role(is_active) WHERE is_active = true;"
        ),
        
        # Composite indexes for common joins
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_action_scenario_role ON group_learning_action(scenario_id, role_id, is_active);"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_scenario_game ON group_learning_scenario(game_id, is_active, \"order\");"
        ),
    ]