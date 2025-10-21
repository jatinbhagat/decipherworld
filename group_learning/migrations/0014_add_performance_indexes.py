from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('group_learning', '0013_designthinkinggame_designmission_and_more'),
    ]

    operations = [
        # Add composite indexes for frequently queried combinations on existing tables only
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_team_progress_session_team ON group_learning_teamprogress(session_id, team_id);",
            reverse_sql="DROP INDEX IF EXISTS idx_team_progress_session_team;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_team_progress_session_mission ON group_learning_teamprogress(session_id, mission_id);",
            reverse_sql="DROP INDEX IF EXISTS idx_team_progress_session_mission;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_team_progress_completed ON group_learning_teamprogress(is_completed) WHERE is_completed = true;",
            reverse_sql="DROP INDEX IF EXISTS idx_team_progress_completed;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_design_mission_order ON group_learning_designmission(\"order\") WHERE is_active = true;",
            reverse_sql="DROP INDEX IF EXISTS idx_design_mission_order;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_design_session_current_mission ON group_learning_designthinkingsession(current_mission_id);",
            reverse_sql="DROP INDEX IF EXISTS idx_design_session_current_mission;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_team_submission_mission_team ON group_learning_teamsubmission(mission_id, team_id);",
            reverse_sql="DROP INDEX IF EXISTS idx_team_submission_mission_team;"
        ),
    ]