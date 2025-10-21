from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('group_learning', '0015_alter_teamsubmission_file_type'),
    ]

    operations = [
        # Index for session-based mission queries
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_team_progress_session_mission ON group_learning_teamprogress(session_id, mission_id);",
            reverse_sql="DROP INDEX IF EXISTS idx_team_progress_session_mission;"
        ),
        
        # Index for team-based progress lookups
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_team_progress_team_mission ON group_learning_teamprogress(team_id, mission_id);",
            reverse_sql="DROP INDEX IF EXISTS idx_team_progress_team_mission;"
        ),
        
        # Index for mission order-based queries
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_design_mission_order ON group_learning_designmission(\"order\", is_active);",
            reverse_sql="DROP INDEX IF EXISTS idx_design_mission_order;"
        ),
        
        # Index for submission queries by team and mission
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_team_submission_team_mission ON group_learning_teamsubmission(team_id, mission_id, submission_type);",
            reverse_sql="DROP INDEX IF EXISTS idx_team_submission_team_mission;"
        ),
        
        # Index for session current mission lookups (status is in parent table)
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_session_current_mission ON group_learning_designthinkingsession(current_mission_id);",
            reverse_sql="DROP INDEX IF EXISTS idx_session_current_mission;"
        ),
    ]