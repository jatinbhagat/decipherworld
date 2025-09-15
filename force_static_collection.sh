#!/bin/bash
# Force static files collection in Azure App Service

echo "🔄 Forcing static files collection in production..."

# Run collectstatic with clear cache
python manage.py collectstatic --clear --noinput --verbosity=2

echo "✅ Static files collected"

# Also run the team completion check
echo "🔍 Checking team completion status..."

python manage.py shell -c "
from group_learning.models import ConstitutionTeam, GameSession, ConstitutionAnswer
try:
    session = GameSession.objects.filter(session_code='SCD29Z').first()
    if session:
        print(f'Session: {session.game.title}')
        team = ConstitutionTeam.objects.filter(id=17, session=session).first()
        if team:
            print(f'Team {team.id}: {team.team_name}')
            print(f'Completion: {team.is_completed}')
            answers = ConstitutionAnswer.objects.filter(team=team).count()
            total = session.game.questions.count()
            print(f'Progress: {answers}/{total}')
            if answers >= total and not team.is_completed:
                team.is_completed = True
                team.save()
                print('Team marked as completed!')
        else:
            print('Team 17 not found')
    else:
        print('Session not found')
except Exception as e:
    print(f'Error: {e}')
"

echo "🎯 Process complete"