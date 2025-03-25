from app import create_app
from apscheduler.schedulers.background import BackgroundScheduler
from app.models import archive_monthly_spending
import atexit

app = create_app()

scheduler = BackgroundScheduler()
scheduler.add_job(archive_monthly_spending, 'cron', day=1, hour=0, minute=0)
scheduler.start()

atexit.register(lambda: scheduler.shutdown())

if __name__ == '__main__':
    app.run(debug=True)
